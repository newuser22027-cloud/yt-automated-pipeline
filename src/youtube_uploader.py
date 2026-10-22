"""
YouTube Uploader Module.
Publishes videos headlessly using YouTube Data API v3 and OAuth 2.0 Refresh Tokens.
"""

import os
import json
import time
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
    """Manages authenticated uploads to YouTube without interactive browser prompts."""

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    def __init__(self):
        self.client_dict = None
        self.refresh_token = config.youtube_refresh_token

    def _get_authenticated_service(self):
        """Constructs an authorized YouTube service client via OAuth 2.0 refresh token."""
        client_dict = config.get_client_secret_dict()

        # Handle 'installed' or 'web' application credentials structure
        credentials_info = client_dict.get("installed") or client_dict.get("web")
        if not credentials_info:
            raise ValueError("Invalid client secret JSON: missing 'installed' or 'web' block.")

        client_id = credentials_info.get("client_id")
        client_secret = credentials_info.get("client_secret")
        token_uri = credentials_info.get("token_uri", "https://oauth2.googleapis.com/token")

        if not self.refresh_token:
            raise ValueError("YOUTUBE_REFRESH_TOKEN is not configured in environment or .env.")

        creds = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
            scopes=self.SCOPES
        )

        logger.info("Refreshing YouTube OAuth 2.0 access token...")
        creds.refresh(Request())
        logger.info("Access token successfully refreshed.")

        return build("youtube", "v3", credentials=creds)

    def upload(
        self,
        video_path: Path,
        metadata: Dict[str, Any],
        privacy_status: str = "public"
    ) -> str:
        """
        Uploads an MP4 file with metadata to YouTube.
        Returns the created video ID.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file to upload does not exist: {video_path}")

        logger.info(f"Authenticating with YouTube API to upload: {video_path.name}")
        youtube = self._get_authenticated_service()

        title = metadata.get("title", "Daily Discovery")[:100]
        description = metadata.get("description", "")
        tags = metadata.get("tags", ["shorts", "science"])
        category_id = metadata.get("category_id", "28")  # 28 = Science & Technology

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": str(category_id)
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        # 5 MB chunks for reliable upload stream
        media = MediaFileUpload(
            str(video_path),
            chunksize=5 * 1024 * 1024,
            resumable=True,
            mimetype="video/mp4"
        )

        logger.info(f"Uploading '{title}' (Privacy: {privacy_status})...")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        retry_count = 0
        max_retries = 5

        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    retry_count += 1
                    if retry_count > max_retries:
                        raise e
                    sleep_sec = 2 ** retry_count
                    logger.warning(f"Transient HTTP {e.resp.status}. Backing off {sleep_sec}s...")
                    time.sleep(sleep_sec)
                else:
                    raise e

        video_id = response.get("id")
        logger.info(f"Upload completed successfully! Video ID: {video_id}")
        return video_id


if __name__ == "__main__":
    uploader = YouTubeUploader()
    print("YouTubeUploader initialized.")
