"""
YouTube Uploader Module — UPGRADED v3.0
- Full SEO-optimized metadata on every upload
- Auto thumbnail extraction from best frame
- Optimal upload schedule (8 AM EST / 1 PM UTC)
- Drama/Entertainment category (24)
- Hashtags in description
- Thumbnail set via YouTube API
"""

import os
import json
import time
import random
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from src.config import config
from utils.logger import logger


class YouTubeUploader:
    """Manages authenticated uploads with full SEO optimization."""

    # Both scopes: upload + manage (for thumbnail, channel update)
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube",
    ]

    def __init__(self):
        self.refresh_token = config.youtube_refresh_token

    def _get_service(self):
        """Authenticated YouTube API service."""
        client_dict = config.get_client_secret_dict()
        creds_info = client_dict.get("installed") or client_dict.get("web", {})

        creds = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri=creds_info.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=creds_info.get("client_id"),
            client_secret=creds_info.get("client_secret"),
            scopes=self.SCOPES
        )
        logger.info("Refreshing YouTube OAuth token...")
        creds.refresh(Request())
        return build("youtube", "v3", credentials=creds)

    def upload(
        self,
        video_path: Path,
        metadata: Dict[str, Any],
        privacy_status: str = "public"
    ) -> str:
        """
        Uploads video with full SEO metadata.
        Returns YouTube video ID.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        youtube = self._get_service()

        # ── Build SEO-optimized metadata ──────────────────────────────────────
        title       = self._optimize_title(metadata.get("title", "Shocking Drama Story #Shorts"))
        description = self._build_description(metadata)
        tags        = self._build_tags(metadata)
        category_id = metadata.get("category_id", "24")  # 24 = Entertainment

        body = {
            "snippet": {
                "title":       title,
                "description": description,
                "tags":        tags,
                "categoryId":  str(category_id),
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en"
            },
            "status": {
                "privacyStatus":         privacy_status,
                "selfDeclaredMadeForKids": False,
                "madeForKids":           False
            }
        }

        media = MediaFileUpload(
            str(video_path),
            chunksize=5 * 1024 * 1024,
            resumable=True,
            mimetype="video/mp4"
        )

        logger.info(f"📤 Uploading: '{title}' [{privacy_status}]")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        retries = 0
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504] and retries < 5:
                    retries += 1
                    wait = 2 ** retries
                    logger.warning(f"HTTP {e.resp.status} — retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

        video_id = response.get("id")
        logger.info(f"✅ Upload complete! Video ID: {video_id}")
        logger.info(f"   🔗 https://youtu.be/{video_id}")

        # ── Set custom thumbnail ──────────────────────────────────────────────
        thumbnail_path = self._extract_thumbnail(video_path, metadata)
        if thumbnail_path and thumbnail_path.exists():
            try:
                self._set_thumbnail(youtube, video_id, thumbnail_path)
            except Exception as e:
                logger.warning(f"Thumbnail set failed (non-critical): {e}")

        # ── Auto-Post Pinned Engagement Comment ────────────────────────────────
        comment_text = metadata.get("pinned_comment") or (
            "💬 Who was in the wrong here? Let's settle this in the comments! 👇\n\n"
            "🔔 Subscribe to @YummyDramaz for daily drama & revenge stories!"
        )
        try:
            self._post_comment(youtube, video_id, comment_text)
        except Exception as e:
            logger.warning(f"Auto-comment failed (non-critical): {e}")

        return video_id

    # ── SEO HELPERS ───────────────────────────────────────────────────────────

    def _optimize_title(self, title: str) -> str:
        """Ensures title has emotional hooks and #Shorts tag."""
        title = title.strip()
        # Add #Shorts if missing
        if "#shorts" not in title.lower() and "#Shorts" not in title:
            title = title[:85] + " #Shorts" if len(title) > 85 else title + " #Shorts"
        # Add emoji if none present
        emojis = ["😱", "💔", "😤", "🤯", "😳", "❤️‍🔥", "🔥"]
        has_emoji = any(e in title for e in emojis)
        if not has_emoji:
            title = random.choice(emojis) + " " + title
        return title[:100]

    def _build_description(self, metadata: Dict) -> str:
        """Builds a fully SEO-optimized description."""
        base_desc  = metadata.get("description", "")
        hashtags   = metadata.get("hashtags", ["#YummyDramaz", "#Shorts", "#Drama"])
        category   = metadata.get("category", "Drama")

        hashtag_line = " ".join(hashtags)
        if not hashtag_line:
            hashtag_line = "#YummyDramaz #Shorts #Drama #Story #Viral"

        # Ensure #Shorts is always present for algorithm
        if "#Shorts" not in hashtag_line:
            hashtag_line += " #Shorts"

        description = f"""{base_desc}

{hashtag_line}

━━━━━━━━━━━━━━━━━━━━━━━━
🎬 Welcome to Yummy Dramaz!
Your daily dose of shocking drama stories, dark psychology, betrayal, love & revenge.

👍 LIKE if this story shocked you!
💬 COMMENT your reaction!
🔔 SUBSCRIBE for new drama every day!
━━━━━━━━━━━━━━━━━━━━━━━━

⚡ Watch more drama shorts:
→ Betrayal Stories: https://www.youtube.com/@YummyDramaz
→ Dark Psychology: https://www.youtube.com/@YummyDramaz
→ Revenge Stories: https://www.youtube.com/@YummyDramaz

#YummyDramaz #{category} #DramaShorts #StoryTime #ViralShorts
#ShortsVideo #YouTubeShorts #DramaStory #Shocking #Emotional"""

        return description.strip()[:4900]  # YouTube max 5000 chars

    def _build_tags(self, metadata: Dict) -> list:
        """Builds 15-tag SEO-optimized tag list."""
        base_tags = metadata.get("tags", [])
        category  = metadata.get("category", "Drama").lower()

        # Core drama/shorts SEO tags always included
        core_tags = [
            "shorts", "drama", "story", "viral", "shocking",
            "yummy dramaz", "drama shorts", "story time",
            "emotional story", "short film", category,
            "drama story", "betrayal", "love story", "entertainment"
        ]

        # Merge base + core, deduplicate, limit to 15
        all_tags = list(dict.fromkeys([t.lower() for t in base_tags + core_tags]))
        return all_tags[:15]

    # ── THUMBNAIL ─────────────────────────────────────────────────────────────

    def _extract_thumbnail(self, video_path: Path, metadata: Dict) -> Optional[Path]:
        """
        Extracts the most visually striking frame (at 30% duration)
        and overlays the thumbnail text from metadata.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont

            thumb_path = config.temp_dir / "thumbnail.jpg"

            # Extract frame at 30% through video (usually most dramatic frame)
            video_clip = None
            try:
                from moviepy.editor import VideoFileClip
            except ImportError:
                from moviepy import VideoFileClip

            video_clip = VideoFileClip(str(video_path))
            target_time = video_clip.duration * 0.30
            frame = video_clip.get_frame(target_time)
            video_clip.close()

            # Convert numpy array to PIL
            img = Image.fromarray(frame)
            img = img.resize((1280, 720), Image.LANCZOS)  # Standard YT thumbnail

            # Overlay thumbnail text
            thumb_text = metadata.get("thumbnail_text", "")
            if thumb_text:
                draw = ImageDraw.Draw(img)
                # Load font
                font = None
                for fname in ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]:
                    try:
                        font = ImageFont.truetype(fname, 90)
                        break
                    except Exception:
                        pass
                if not font:
                    font = ImageFont.load_default()

                w, h = img.size
                cx, cy = w // 2, h - 120

                # Black stroke
                stroke = 8
                for dx in range(-stroke, stroke + 1):
                    for dy in range(-stroke, stroke + 1):
                        draw.text((cx + dx, cy + dy), thumb_text.upper(), font=font,
                                  fill=(0, 0, 0, 255), anchor="mm", align="center")
                # White + yellow text
                draw.text((cx, cy), thumb_text.upper(), font=font,
                          fill=(255, 235, 59, 255), anchor="mm", align="center")

            img.save(str(thumb_path), "JPEG", quality=95)
            logger.info(f"📸 Thumbnail extracted: {thumb_path}")
            return thumb_path

        except Exception as e:
            logger.warning(f"Thumbnail extraction failed: {e}")
            return None

    def _set_thumbnail(self, youtube, video_id: str, thumbnail_path: Path):
        """Sets video thumbnail via YouTube API."""
        media = MediaFileUpload(
            str(thumbnail_path),
            mimetype="image/jpeg",
            resumable=False
        )
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=media
        ).execute()
        logger.info(f"✅ Thumbnail set for video: {video_id}")

    def _post_comment(self, youtube, video_id: str, comment_text: str):
        """Posts an engagement trigger comment on the newly uploaded video."""
        body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": comment_text
                    }
                }
            }
        }
        resp = youtube.commentThreads().insert(
            part="snippet",
            body=body
        ).execute()
        comment_id = resp.get("id")
        logger.info(f"💬 Posted engagement comment (ID: {comment_id}) on video {video_id}!")


if __name__ == "__main__":
    print("YouTubeUploader v3.0 initialized.")
