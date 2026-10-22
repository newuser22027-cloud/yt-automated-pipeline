"""
Media Fetcher Module.
Retrieves free HD vertical stock footage from Pexels Video API with fallback handling.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

from src.config import config
from utils.logger import logger


class MediaFetcher:
    """Fetches high-quality vertical footage from Pexels API."""

    PEXELS_VIDEO_SEARCH_URL = "https://api.pexels.com/videos/search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.pexels_api_key

    def fetch_video(self, keyword: str, output_path: Optional[Path] = None) -> Path:
        """
        Searches Pexels for portrait video clips and downloads the best HD candidate.
        If no key is configured or no videos are found, generates/provides a fallback video.
        """
        output_path = output_path or (config.temp_dir / "background.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.api_key:
            logger.warning("PEXELS_API_KEY is not configured. Creating procedural canvas fallback.")
            return self._create_procedural_fallback(output_path)

        headers = {"Authorization": self.api_key}
        params = {
            "query": keyword,
            "per_page": 10,
            "orientation": "portrait"
        }

        try:
            logger.info(f"Querying Pexels API for vertical video with keyword: '{keyword}'")
            res = requests.get(
                self.PEXELS_VIDEO_SEARCH_URL,
                headers=headers,
                params=params,
                timeout=15
            )

            if res.status_code == 200:
                data = res.json()
                videos = data.get("videos", [])
                if videos:
                    download_url = self._select_best_video_file(videos[0].get("video_files", []))
                    if download_url:
                        self._download_stream(download_url, output_path)
                        return output_path

            logger.warning(f"No direct portrait matches for '{keyword}'. Trying fallback keyword 'space galaxy'.")
            # Retry with high-availability generic background keyword
            params["query"] = "space galaxy"
            res = requests.get(
                self.PEXELS_VIDEO_SEARCH_URL,
                headers=headers,
                params=params,
                timeout=15
            )
            if res.status_code == 200:
                data = res.json()
                videos = data.get("videos", [])
                if videos:
                    download_url = self._select_best_video_file(videos[0].get("video_files", []))
                    if download_url:
                        self._download_stream(download_url, output_path)
                        return output_path

        except Exception as e:
            logger.error(f"Error querying Pexels API: {e}")

        logger.warning("Pexels fetch failed. Generating procedural vertical canvas fallback.")
        return self._create_procedural_fallback(output_path)

    def _select_best_video_file(self, video_files: List[Dict[str, Any]]) -> Optional[str]:
        """
        Selects optimal HD vertical video stream (prefers 1080x1920 or 720x1280).
        """
        if not video_files:
            return None

        # Filter for MP4s
        mp4_files = [f for f in video_files if f.get("file_type") == "video/mp4" or "mp4" in f.get("link", "")]
        candidates = mp4_files if mp4_files else video_files

        # Sort by height descending to choose the best available HD stream
        sorted_files = sorted(
            candidates,
            key=lambda x: (x.get("height") or 0),
            reverse=True
        )

        return sorted_files[0].get("link") if sorted_files else None

    def _download_stream(self, url: str, target_file: Path) -> None:
        """Streams remote video file to local disk."""
        logger.info(f"Downloading stock video from CDN...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(target_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        logger.info(f"Video asset downloaded successfully to: {target_file} ({target_file.stat().st_size} bytes)")

    def _create_procedural_fallback(self, target_file: Path) -> Path:
        """
        Generates a 10-second procedural dark gradient animated video
        using MoviePy if no external video is available.
        """
        logger.info("Building procedural 1080x1920 background clip...")
        try:
            # Handle both MoviePy v1 and v2 imports
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
