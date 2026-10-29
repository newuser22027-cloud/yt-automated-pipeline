"""
Media Fetcher Module — UPGRADED v5.0 (Animals & Wildlife Footage Edition)
Fetches high-definition wildlife, animal predators, ocean, and nature stock video
from Mixkit (Zero API key), Pixabay, or Pexels for fast-paced visual cuts.
"""

import os
import re
import random
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

from src.config import config
from utils.logger import logger


class MediaFetcher:
    """Fetches high-quality HD animal and wildlife video footage with multi-scene cuts."""

    KEYWORD_MAP = {
        "animals": ["animals", "wildlife", "lion", "tiger", "bear", "wolf", "cheetah", "leopard", "safari"],
        "nature": ["forest", "jungle", "river", "mountain", "trees", "waterfall", "storm", "nature"],
        "ocean": ["ocean", "underwater", "fish", "shark", "whale", "coral", "deep-sea", "marine"],
        "birds": ["eagle", "falcon", "bird", "flying", "hawk", "owl", "sky"],
        "predators": ["hunting", "running", "chase", "danger", "wildlife", "predator"]
    }

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def __init__(self, pexels_key: Optional[str] = None, pixabay_key: Optional[str] = None):
        self.pexels_key = pexels_key or config.pexels_api_key
        self.pixabay_key = pixabay_key or config.pixabay_api_key

    def fetch_multiple_videos(self, keyword: str, count: int = 4) -> List[Path]:
        """Retrieves multiple distinct HD stock clips for multi-scene fast cuts."""
        temp_scenes_dir = config.temp_dir / "scenes"
        temp_scenes_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"🐾 Querying {count} distinct wildlife video scenes for '{keyword}'...")

        category = self._map_keyword_to_category(keyword)
        urls = self._fetch_mixkit_multiple_urls(category, count=count * 2)

        saved_clips: List[Path] = []
        for idx, url in enumerate(urls[:count]):
            out_clip = temp_scenes_dir / f"scene_{idx:02d}.mp4"
            try:
                self._download_stream(url, out_clip)
                if out_clip.exists() and out_clip.stat().st_size > 100_000:
                    saved_clips.append(out_clip)
            except Exception as e:
                logger.warning(f"Scene {idx} download failed: {e}")

        # Fallback if less than 2 clips downloaded
        if len(saved_clips) < 2:
            logger.warning("Fewer than 2 scenes downloaded, falling back to single video...")
            single = self.fetch_video(keyword)
            return [single]

        logger.info(f"✅ Successfully downloaded {len(saved_clips)} distinct animal footage scenes!")
        return saved_clips

    def fetch_video(self, keyword: str, output_path: Optional[Path] = None) -> Path:
        """Retrieves a single HD wildlife stock video."""
        output_path = output_path or (config.temp_dir / "background.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Querying single animal video for: '{keyword}'")
        try:
            category = self._map_keyword_to_category(keyword)
            mixkit_url = self._fetch_mixkit_video_url(category)
            if mixkit_url:
                self._download_stream(mixkit_url, output_path)
                return output_path
        except Exception as e:
            logger.warning(f"Mixkit fetch error: {e}")

        return self._create_procedural_fallback(output_path)

    def _map_keyword_to_category(self, keyword: str) -> str:
        """Finds closest Mixkit category for animals/nature."""
        kw = keyword.lower()
        if any(w in kw for w in ["ocean", "shrimp", "octopus", "fish", "whale", "water"]):
            return "nature"
        if any(w in kw for w in ["falcon", "eagle", "bird", "fly"]):
            return "nature"
        for cat, synonyms in self.KEYWORD_MAP.items():
            if any(s in kw for s in synonyms) or cat in kw:
                return cat
        return random.choice(["nature", "animals", "forest"])

    def _fetch_mixkit_multiple_urls(self, category: str, count: int = 6) -> List[str]:
        """Scrapes free 720p HD MP4 download links from Mixkit nature/animal category pages."""
        urls = []
        categories_to_try = ["nature", "animals", "ocean", "forest", "wildlife"]
        
        for cat in categories_to_try:
            page_url = f"https://mixkit.co/free-stock-video/{cat}/"
            try:
                res = requests.get(page_url, headers=self.HEADERS, timeout=12)
                if res.status_code == 200:
                    video_ids = list(set(re.findall(r'https://assets\.mixkit\.co/videos/(\d+)/\1-360\.mp4', res.text)))
                    for vid in video_ids:
                        mp4_url = f"https://assets.mixkit.co/videos/{vid}/{vid}-720.mp4"
                        if mp4_url not in urls:
                            urls.append(mp4_url)
                        if len(urls) >= count:
                            return urls
            except Exception:
                pass
        return urls

    def _fetch_mixkit_video_url(self, category: str) -> Optional[str]:
        urls = self._fetch_mixkit_multiple_urls(category, count=1)
        return urls[0] if urls else None

    def _download_stream(self, url: str, target_file: Path) -> None:
        """Streams remote MP4 file to local storage."""
        response = requests.get(url, headers=self.HEADERS, stream=True, timeout=30)
        response.raise_for_status()

        with open(target_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        logger.info(f"Footage saved: {target_file.name} ({target_file.stat().st_size / 1_000_000:.1f} MB)")

    def _create_procedural_fallback(self, target_file: Path) -> Path:
        """Generates procedural 1080x1920 fallback clip."""
        try:
            from moviepy import ColorClip
        except ImportError:
            from moviepy.editor import ColorClip

        clip = ColorClip(size=(1080, 1920), color=(10, 40, 20), duration=10)
        clip.write_videofile(str(target_file), fps=24, codec="libx264", preset="ultrafast", logger=None)
        clip.close()
        return target_file


if __name__ == "__main__":
    fetcher = MediaFetcher()
    clips = fetcher.fetch_multiple_videos("lion animal", count=3)
    print(f"Downloaded {len(clips)} animal scenes.")
