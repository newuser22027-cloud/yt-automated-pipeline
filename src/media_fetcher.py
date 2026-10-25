"""
Media Fetcher Module.
Retrieves free HD vertical/horizontal cinematic footage without API key restrictions
from Mixkit HD Video Library, Pixabay, or Pexels, with procedural fallback.
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
    """Fetches high-quality real HD stock footage matching niche queries."""

    # Free high-relevance stock categories on Mixkit (Zero API Key required)
    KEYWORD_MAP = {
        "space": ["space", "stars", "galaxy", "nebula", "astronaut", "universe"],
        "money": ["money", "finance", "currency", "cash", "crypto", "wealth", "gold", "bank"],
        "technology": ["technology", "circuit", "computer", "code", "ai", "robot", "futuristic", "cyber"],
        "luxury": ["luxury", "supercar", "mansion", "lifestyle", "jewelry", "watch", "yacht"],
        "psychology": ["brain", "thinking", "mind", "shadow", "abstract", "human", "face"],
        "city": ["city", "traffic", "skyline", "architecture", "street", "night-city"],
        "nature": ["ocean", "storm", "lightning", "waterfall", "volcano", "earth"]
    }

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def __init__(self, pexels_key: Optional[str] = None, pixabay_key: Optional[str] = None):
        self.pexels_key = pexels_key or config.pexels_api_key
        self.pixabay_key = pixabay_key or config.pixabay_api_key

    def fetch_video(self, keyword: str, output_path: Optional[Path] = None) -> Path:
        """
        Retrieves real HD stock video:
        1. Mixkit HD Library (Free, zero API key)
        2. Pixabay API (if configured)
        3. Pexels API (if configured)
        4. Procedural animated canvas fallback
        """
        output_path = output_path or (config.temp_dir / "background.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Querying high-definition stock video for keyword: '{keyword}'")

        # 1. Fetch from Mixkit HD (Instant & 100% Free)
        try:
            category = self._map_keyword_to_category(keyword)
            mixkit_url = self._fetch_mixkit_video_url(category)
            if mixkit_url:
                logger.info(f"Downloading Mixkit HD stock video [{category}]...")
                self._download_stream(mixkit_url, output_path)
                return output_path
        except Exception as e:
            logger.warning(f"Mixkit fetch attempt encountered issue: {e}")

        # 2. Try Pixabay (if key available)
        if self.pixabay_key and "xxxx" not in self.pixabay_key:
            try:
                pixabay_url = self._fetch_pixabay_video_url(keyword)
                if pixabay_url:
                    logger.info("Downloading Pixabay HD video...")
                    self._download_stream(pixabay_url, output_path)
                    return output_path
            except Exception as e:
                logger.warning(f"Pixabay fetch error: {e}")

        # 3. Try Pexels (if key available)
        if self.pexels_key and "xxxx" not in self.pexels_key:
            try:
                pexels_url = self._fetch_pexels_video_url(keyword)
                if pexels_url:
                    logger.info("Downloading Pexels HD video...")
                    self._download_stream(pexels_url, output_path)
                    return output_path
            except Exception as e:
                logger.warning(f"Pexels fetch error: {e}")

        # 4. Fallback procedural canvas
        logger.warning("Stock APIs unavailable. Building procedural vertical canvas fallback.")
        return self._create_procedural_fallback(output_path)

    def _map_keyword_to_category(self, keyword: str) -> str:
        """Finds closest Mixkit category for the search term."""
        kw = keyword.lower()
        for cat, synonyms in self.KEYWORD_MAP.items():
            if any(s in kw for s in synonyms) or cat in kw:
                return cat
        # Default high-retention visual categories
        return random.choice(["space", "technology", "money", "luxury"])

    def _fetch_mixkit_video_url(self, category: str) -> Optional[str]:
        """Scrapes free 720p HD MP4 download links from Mixkit category pages."""
        url = f"https://mixkit.co/free-stock-video/{category}/"
        res = requests.get(url, headers=self.HEADERS, timeout=12)
        if res.status_code == 200:
            # Extract video IDs from asset URLs
            video_ids = list(set(re.findall(r'https://assets\.mixkit\.co/videos/(\d+)/\1-360\.mp4', res.text)))
            if video_ids:
                selected_id = random.choice(video_ids)
                # Prefer 720p HD stream
                return f"https://assets.mixkit.co/videos/{selected_id}/{selected_id}-720.mp4"
        return None

    def _fetch_pixabay_video_url(self, keyword: str) -> Optional[str]:
        url = f"https://pixabay.com/api/videos/?key={self.pixabay_key}&q={keyword}&video_type=film&per_page=5"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            hits = res.json().get("hits", [])
            if hits:
                v_obj = hits[0].get("videos", {})
                return v_obj.get("large", {}).get("url") or v_obj.get("medium", {}).get("url")
        return None

    def _fetch_pexels_video_url(self, keyword: str) -> Optional[str]:
        url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=5&orientation=portrait"
        headers = {"Authorization": self.pexels_key}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            videos = res.json().get("videos", [])
            if videos:
                files = videos[0].get("video_files", [])
                mp4s = [f for f in files if "mp4" in f.get("link", "")]
                if mp4s:
                    sorted_files = sorted(mp4s, key=lambda x: (x.get("height") or 0), reverse=True)
                    return sorted_files[0].get("link")
        return None

    def _download_stream(self, url: str, target_file: Path) -> None:
        """Streams remote MP4 file to local storage."""
        response = requests.get(url, headers=self.HEADERS, stream=True, timeout=30)
        response.raise_for_status()

        with open(target_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        logger.info(f"Video file saved: {target_file} ({target_file.stat().st_size} bytes)")

    def _create_procedural_fallback(self, target_file: Path) -> Path:
        """Generates procedural 1080x1920 background clip."""
        try:
            from moviepy import ColorClip
        except ImportError:
            from moviepy.editor import ColorClip

        clip = ColorClip(size=(1080, 1920), color=(15, 23, 42), duration=10)
        clip.write_videofile(str(target_file), fps=24, codec="libx264", preset="ultrafast", logger=None)
        clip.close()
        return target_file


if __name__ == "__main__":
    fetcher = MediaFetcher()
    path = fetcher.fetch_video("money")
    print(f"Downloaded video to: {path}")
