"""
Environment and Application Configuration.
Manages all API keys, secrets, and operational constants using Pydantic.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """
    Centralized application configuration.
    Loads values from environment variables or .env file.
    """

    # 1. AI Content Generation
    openai_api_key: str = Field(
        default="",
        alias="OPENAI_API_KEY",
        description="OpenAI API key for GPT-4o-mini generation"
    )

    # 2. Free Visual Stock Assets
    pexels_api_key: str = Field(
        default="",
        alias="PEXELS_API_KEY",
        description="Pexels API key for HD video clips"
    )

    # 3. YouTube Data API v3 & OAuth 2.0
    youtube_client_secret_json: Optional[str] = Field(
        default=None,
        alias="YOUTUBE_CLIENT_SECRET_JSON",
        description="Either raw JSON string or filepath to client_secret.json"
    )
    youtube_refresh_token: Optional[str] = Field(
        default=None,
        alias="YOUTUBE_REFRESH_TOKEN",
        description="OAuth 2.0 refresh token for headless uploading"
    )

    # 4. Telemetry & Alerting
    discord_webhook_url: Optional[str] = Field(
        default=None,
        alias="DISCORD_WEBHOOK_URL",
        description="Discord incoming webhook URL for pipeline alerts"
    )
    telegram_bot_token: Optional[str] = Field(
        default=None,
        alias="TELEGRAM_BOT_TOKEN",
        description="Optional Telegram Bot Token"
    )
    telegram_chat_id: Optional[str] = Field(
        default=None,
        alias="TELEGRAM_CHAT_ID",
        description="Optional Telegram Chat ID"
    )

    # 5. Pipeline Customization & Monetization
    video_niche: str = Field(
        default="mind-blowing science and technology facts",
        alias="VIDEO_NICHE",
        description="Topic niche for script generation"
    )
    tts_voice: str = Field(
        default="en-US-ChristopherNeural",
        alias="TTS_VOICE",
        description="Edge-TTS voice identifier"
    )
    amazon_affiliate_tag: str = Field(
        default="automate-20",
        alias="AMAZON_AFFILIATE_TAG",
        description="Amazon Associates tag for automated monetization"
    )
    vidiq_affiliate_id: str = Field(
        default="creator_tool",
        alias="VIDIQ_AFFILIATE_ID",
        description="Affiliate ID for ranking tool promotions"
    )

    # Directory Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    output_dir: Path = base_dir / "output"
    temp_dir: Path = base_dir / "temp"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_client_secret_dict(self) -> Dict[str, Any]:
        """
        Parses `youtube_client_secret_json` whether provided as a raw JSON
        string or as a path to a client_secret.json file.
        """
        if not self.youtube_client_secret_json:
            raise ValueError(
                "YOUTUBE_CLIENT_SECRET_JSON is not configured in environment or .env"
            )

        raw = self.youtube_client_secret_json.strip()

        # Check if it's a file path
        possible_path = Path(raw)
        if possible_path.exists() and possible_path.is_file():
            with open(possible_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # Check relative to base_dir
        rel_path = self.base_dir / raw
        if rel_path.exists() and rel_path.is_file():
            with open(rel_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # Parse as raw JSON
        try:
            return json.loads(raw)
        except json.JSONDecodeError as err:
            raise ValueError(
                f"Failed to parse YOUTUBE_CLIENT_SECRET_JSON. Ensure it is valid JSON or a valid file path: {err}"
            )


# Singleton config instance
config = AppConfig()

# Ensure directories exist
config.output_dir.mkdir(parents=True, exist_ok=True)
config.temp_dir.mkdir(parents=True, exist_ok=True)
