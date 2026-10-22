"""
Media Fetcher Module.
Retrieves free HD vertical stock footage from Pixabay Video API or Pexels Video API,
with procedural animated fallback handling.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

from src.config import config
from utils.logger import logger


class MediaFetcher:
    """Fetches high-quality vertical footage from Pixabay and Pexels APIs."""

    PEXELS_VIDEO_SEARCH_URL = "https://api.pexels.com/videos/search"
    PIXABAY_VIDEO_SEARCH_URL = "https://pixabay.com/api/videos/"

    def __init__(self, pexels_key: Optional[str] = None, pixabay_key: Optional[str] = None):
        self.pexels_key = pexels_key or config.pexels_api_key
        self.pixabay_key = pixabay_key or config.pixabay_api_key

    def fetch_video(self, keyword: str, output_path: Optional[Path] = None) -> Path:
        """
        Searches available APIs for HD video footage.
        1. Checks Pixabay Video API (if configured)
        2. Checks Pexels Video API (if configured)
        3. Falls back to generating a procedural 1080x1920 video canvas
        """
        output_path = output_path or (config.temp_dir / "background.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Try Pixabay Video API
        if self.pixabay_key and "xxxx" not in self.pixabay_key:
            try:
                logger.info(f"Querying Pixabay Video API for '{keyword}'...")
                params = {
                    "key": self.pixabay_key,
                    "q": keyword,
                    "video_type": "film",
                    "per_page": 5
                }
                res = requests.get(self.PIXABAY_VIDEO_SEARCH_URL, params=params, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    hits = data.get("hits", [])
                    if hits:
                        # Choose best quality video stream
                        video_obj = hits[0].get("videos", {})
                        video_url = (
                            video_obj.get("large", {}).get("url")
                            or video_obj.get("medium", {}).get("url")
                            or video_obj.get("small", {}).get("url")
                        )
                        if video_url:
                            self._download_stream(video_url, output_path)
                            return output_path
            except Exception as e:
                logger.warning(f"Pixabay video fetch error: {e}")

        # 2. Try Pexels Video API
        if self.pexels_key and "xxxx" not in self.pexels_key:
            try:
                logger.info(f"Querying Pexels API for vertical video with keyword: '{keyword}'")
                headers = {"Authorization": self.pexels_key}
                params = {"query": keyword, "per_page": 10, "orientation": "portrait"}
                res = requests.get(self.PEXELS_VIDEO_SEARCH_URL, headers=headers, params=params, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    videos = data.get("videos", [])
                    if videos:
                        download_url = self._select_best_pexels_file(videos[0].get("video_files", []))
                        if download_url:
                            self._download_stream(download_url, output_path)
                            return output_path
            except Exception as e:
                logger.warning(f"Pexels video fetch error: {e}")

        # 3. Procedural canvas fallback
        logger.warning("No video stock API available. Generating procedural vertical canvas fallback.")
        return self._create_procedural_fallback(output_path)

    def _select_best_pexels_file(self, video_files: List[Dict[str, Any]]) -> Optional[str]:
        """Selects optimal HD vertical stream from Pexels."""
        if not video_files:
            return None
        mp4_files = [f for f in video_files if f.get("file_type") == "video/mp4" or "mp4" in f.get("link", "")]
        candidates = mp4_files if mp4_files else video_files
        sorted_files = sorted(candidates, key=lambda x: (x.get("height") or 0), reverse=True)
        return sorted_files[0].get("link") if sorted_files else None

    def _download_stream(self, url: str, target_file: Path) -> None:
        """Streams remote video file to local disk."""
        logger.info("Downloading stock video from CDN...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(target_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        logger.info(f"Video asset downloaded successfully to: {target_file} ({target_file.stat().st_size} bytes)")

    def _create_procedural_fallback(self, target_file: Path) -> Path:
        """Generates procedural 10-second 1080x1920 background clip."""
        logger.info("Building procedural 1080x1920 background clip...")
        try:
            try:
                from moviepy.editor import ColorClip
            except ImportError:
                from moviepy import ColorClip

            clip = ColorClip(size=(1080, 1920), color=(15, 23, 42), duration=10)
            clip.write_videofile(
                str(target_file),
                fps=24,
                codec="libx264",
                preset="ultrafast",
                logger=None
            )
            clip.close()
            return target_file
        except Exception as e:
            logger.error(f"Failed to generate procedural video: {e}")
            raise


if __name__ == "__main__":
    fetcher = MediaFetcher()
    test_path = fetcher.fetch_video("science")
    print(f"Video available at: {test_path}")
