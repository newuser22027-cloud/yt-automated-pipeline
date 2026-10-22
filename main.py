"""
Master Orchestration Engine.
Coordinates the end-to-end headless pipeline: script synthesis, TTS generation,
stock media acquisition, vertical shorts rendering, and YouTube auto-publication.
"""

import os
import sys
import json
import time
import argparse
import traceback
from pathlib import Path

from src.config import config
from src.content_generator import ContentGenerator
from src.audio_generator import AudioGenerator
from src.media_fetcher import MediaFetcher
from src.video_renderer import VideoRenderer
from src.youtube_uploader import YouTubeUploader
from utils.logger import logger, send_alert


def execute_pipeline(
    niche: str = None,
    dry_run: bool = False,
    privacy_status: str = "public",
    max_retries: int = 3
) -> str:
    """
    Executes the automated content engine with built-in retries and telemetry.
    Returns the YouTube video ID if uploaded, or local output path if dry-run.
    """
    logger.info("=" * 70)
    logger.info(" STARTING AUTOMATED YOUTUBE CONTENT ENGINE")
    logger.info("=" * 70)

    # Initialize submodules
    content_gen = ContentGenerator()
    audio_gen = AudioGenerator()
    media_fetcher = MediaFetcher()
    renderer = VideoRenderer()
    uploader = YouTubeUploader() if not dry_run else None

    # Step 1: Content Synthesis
    logger.info("[1/5] Generating script, metadata, and visual keywords...")
    content = content_gen.generate(niche=niche)
    
    metadata_path = config.output_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    logger.info(f"Metadata recorded to: {metadata_path}")

    # Step 2: Voiceover Synthesis
    logger.info("[2/5] Synthesizing neural TTS voiceover...")
    audio_path = audio_gen.generate(
        text=content["script"],
        output_filename="voiceover.mp3"
    )

    # Step 3: Stock Video Acquisition with retry
    logger.info(f"[3/5] Querying visual stock footage for '{content['search_keyword']}'...")
    video_stock_path = None
    for attempt in range(1, max_retries + 1):
        try:
            video_stock_path = media_fetcher.fetch_video(
                keyword=content["search_keyword"]
            )
            if video_stock_path and video_stock_path.exists():
                break
        except Exception as e:
            logger.warning(f"Media fetch attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise

    # Step 4: Vertical Video Assembly & Encoding
    logger.info("[4/5] Rendering 1080x1920 vertical Shorts video...")
    output_video_path = config.output_dir / "final_output.mp4"
    for attempt in range(1, max_retries + 1):
        try:
            renderer.render(
                audio_path=audio_path,
                video_path=video_stock_path,
                title_text=content["title"],
                output_path=output_video_path
            )
            if output_video_path.exists() and output_video_path.stat().st_size > 0:
                break
        except Exception as e:
            logger.warning(f"Video render attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            time.sleep(2)

    # Step 5: Publishing & Telemetry
    if dry_run:
        logger.info("[5/5] DRY-RUN enabled. Skipping YouTube publication.")
        send_alert(
            status="INFO",
            title="Pipeline Executed in Dry-Run Mode",
            details=f"Video successfully rendered locally.\nTitle: **{content['title']}**",
            fields={
                "Output Video": str(output_video_path),
                "Keywords": content["search_keyword"]
            }
        )
        return str(output_video_path)

    logger.info("[5/5] Publishing video to YouTube...")
    video_id = uploader.upload(
        video_path=output_video_path,
        metadata=content,
        privacy_status=privacy_status
    )

    youtube_url = f"https://youtu.be/{video_id}"
    logger.info(f"Video live at: {youtube_url}")

    # Dispatch Success Alert
    send_alert(
        status="SUCCESS",
        title="New Daily Video Published!",
        details=f"Successfully rendered and published YouTube Shorts video.",
        fields={
            "Title": content["title"],
            "YouTube URL": youtube_url,
            "Privacy": privacy_status.capitalize(),
            "Search Keyword": content["search_keyword"]
        }
    )

    return video_id


def main():
    parser = argparse.ArgumentParser(description="Headless YouTube Shorts Automation Engine")
    parser.add_argument("--niche", type=str, default=None, help="Custom topic niche for script generation")
    parser.add_argument("--dry-run", "--skip-upload", dest="dry_run", action="store_true", help="Render video without uploading to YouTube")
    parser.add_argument("--privacy", type=str, default="public", choices=["public", "unlisted", "private"], help="YouTube publication privacy level")
    parser.add_argument("--retries", type=int, default=3, help="Max retry attempts for network/rendering steps")

    args = parser.parse_args()

    try:
        execute_pipeline(
            niche=args.niche,
            dry_run=args.dry_run,
            privacy_status=args.privacy,
            max_retries=args.retries
        )
        sys.exit(0)
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.critical(f"FATAL PIPELINE CRASH:\n{error_trace}")

        # Dispatch Failure Alert to Webhook
        send_alert(
            status="FAILURE",
            title="Automation Pipeline Crashed",
            details=f"An unhandled error occurred during workflow execution:\n```{str(e)[:1500]}```",
            fields={"Exception Type": type(e).__name__}
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
