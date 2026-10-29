"""
Master Orchestration Engine — v3.0
Pipeline:
  0. Analytics check (avoid repeating recent topics)
  1. Content synthesis (drama script + SEO metadata)
  2. Neural TTS voiceover (fast, no dead pauses)
  3. Stock footage acquisition
  4. Premium vertical video render (animated captions + music + hook)
  5. YouTube upload (SEO metadata + auto thumbnail)
"""

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
    logger.info("=" * 70)
    logger.info(" YUMMY DRAMAZ — AUTOMATED SHORTS ENGINE v3.0")
    logger.info("=" * 70)

    content_gen  = ContentGenerator()
    audio_gen    = AudioGenerator()
    media_fetch  = MediaFetcher()
    renderer     = VideoRenderer()
    uploader     = YouTubeUploader() if not dry_run else None

    # ── Step 0: Analytics check ───────────────────────────────────────────────
    logger.info("[0/5] 📊 Checking channel analytics to pick fresh topic...")
    try:
        analytics = content_gen.get_analytics_summary()
        recent = analytics.get("recent_titles", [])
        if recent:
            logger.info(f"   Recent videos: {recent[:3]}")
        else:
            logger.info("   No previous videos found — picking fresh topic.")
    except Exception as e:
        logger.warning(f"   Analytics check skipped: {e}")

    # ── Step 1: Content Generation ────────────────────────────────────────────
    logger.info("[1/5] 🧠 Generating mind-blowing animal facts script + SEO metadata...")
    content = content_gen.generate(niche=niche)

    # Log what was generated
    logger.info(f"   📝 Title:    {content.get('title', 'N/A')}")
    logger.info(f"   🎯 Category: {content.get('category', 'Animals')}")
    logger.info(f"   🔍 Keyword:  {content.get('search_keyword', 'N/A')}")

    metadata_path = config.output_dir / "metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)

    # ── Step 2: Voiceover ─────────────────────────────────────────────────────
    logger.info("[2/5] 🎭 Synthesizing multi-voice character acting voiceover...")
    if "dialogues" in content and isinstance(content["dialogues"], list) and len(content["dialogues"]) > 0:
        audio_path = audio_gen.generate_dialogues(
            dialogues=content["dialogues"],
            output_filename="voiceover.mp3"
        )
    else:
        audio_path = audio_gen.generate(
            text=content["script"],
            output_filename="voiceover.mp3"
        )

    # ── Step 3: Stock Footage (Multi-Scene Cuts) ──────────────────────────────
    logger.info(f"[3/5] 🎬 Fetching multi-scene HD footage for: '{content['search_keyword']}'...")
    video_stock_paths = []
    for attempt in range(1, max_retries + 1):
        try:
            video_stock_paths = media_fetch.fetch_multiple_videos(keyword=content["search_keyword"], count=4)
            if video_stock_paths:
                break
        except Exception as e:
            logger.warning(f"   Media fetch attempt {attempt} failed: {e}")
            if attempt == max_retries:
                # Fallback to single video
                video_stock_paths = [media_fetch.fetch_video(keyword=content["search_keyword"])]

    # ── Step 4: Video Render ──────────────────────────────────────────────────
    logger.info("[4/5] ⚙️  Rendering premium 1080x1920 drama short...")
    output_video_path = config.output_dir / "final_output.mp4"
    for attempt in range(1, max_retries + 1):
        try:
            renderer.render(
                audio_path=audio_path,
                video_path=video_stock_paths,
                title_text=content.get("title", "YUMMY DRAMAZ"),
                script_text=content["script"],
                hook_text=content.get("hook"),
                output_path=output_video_path
            )
            if output_video_path.exists() and output_video_path.stat().st_size > 0:
                break
        except Exception as e:
            logger.warning(f"   Render attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            time.sleep(2)

    size_mb = output_video_path.stat().st_size / 1_000_000
    logger.info(f"   ✅ Video rendered: {size_mb:.1f} MB")

    # ── Step 5: Upload ────────────────────────────────────────────────────────
    if dry_run:
        logger.info("[5/5] 🧪 DRY-RUN — skipping YouTube upload.")
        send_alert(
            status="INFO",
            title="Dry-Run Complete",
            details=f"Video rendered locally.\nTitle: **{content['title']}**",
            fields={"Output": str(output_video_path), "Size": f"{size_mb:.1f} MB"}
        )
        return str(output_video_path)

    logger.info("[5/5] 📤 Publishing to YouTube with full SEO metadata...")
    video_id = uploader.upload(
        video_path=output_video_path,
        metadata=content,
        privacy_status=privacy_status
    )

    url = f"https://youtu.be/{video_id}"
    logger.info(f"   🔗 Live at: {url}")

    send_alert(
        status="SUCCESS",
        title="✅ New Drama Short Published!",
        details=f"Successfully published to Yummy Dramaz.",
        fields={
            "Title":    content["title"],
            "URL":      url,
            "Category": content.get("category", "Drama"),
            "Privacy":  privacy_status.capitalize()
        }
    )
    return video_id


def main():
    parser = argparse.ArgumentParser(description="Yummy Dramaz — Automated Shorts Engine")
    parser.add_argument("--niche",    type=str, default=None,
                        help="Custom topic override (e.g. 'a husband who hid a secret family')")
    parser.add_argument("--dry-run",  dest="dry_run", action="store_true",
                        help="Render video locally without uploading")
    parser.add_argument("--privacy",  type=str, default="public",
                        choices=["public", "unlisted", "private"])
    parser.add_argument("--retries",  type=int, default=3)

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
        tb = traceback.format_exc()
        logger.critical(f"FATAL PIPELINE ERROR:\n{tb}")
        send_alert(
            status="FAILURE",
            title="❌ Pipeline Crashed",
            details=f"```{str(e)[:1200]}```",
            fields={"Exception": type(e).__name__}
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
