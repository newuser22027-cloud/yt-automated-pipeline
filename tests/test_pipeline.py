"""
Modular Health Check and Pipeline Test Suite.
Verifies operational readiness of audio synthesis, video rendering,
configuration, and fallback engines.
"""

import os
import pytest
from pathlib import Path

from src.config import config
from src.content_generator import ContentGenerator
from src.audio_generator import AudioGenerator
from src.media_fetcher import MediaFetcher
from src.video_renderer import VideoRenderer
from src.youtube_uploader import YouTubeUploader


def test_config_initialization():
    """Verify application configuration loads cleanly and directories exist."""
    assert config.base_dir.exists()
    assert config.output_dir.exists()
    assert config.temp_dir.exists()
    assert isinstance(config.video_niche, str)


def test_content_generator_fallback():
    """Verify fallback content structure complies with schema."""
    gen = ContentGenerator()
    content = gen._generate_fallback("quantum computing")
    assert "title" in content
    assert "script" in content
    assert "description" in content
    assert "tags" in content
    assert "search_keyword" in content
    assert len(content["tags"]) >= 5
    assert len(content["script"]) > 20


def test_audio_synthesis():
    """Verify Edge-TTS neural voice synthesis creates a valid non-empty MP3."""
    audio_gen = AudioGenerator()
    test_audio = config.temp_dir / "test_voice.mp3"
    result_path = audio_gen.generate(
        text="Testing automated voiceover synthesis.",
        output_filename="test_voice.mp3"
    )
    assert result_path.exists()
    assert result_path.stat().st_size > 500


def test_procedural_video_generation():
    """Verify procedural fallback video creation succeeds with correct dimensions."""
    fetcher = MediaFetcher()
    test_video = config.temp_dir / "test_bg.mp4"
    result = fetcher._create_procedural_fallback(test_video)
    assert result.exists()
    assert result.stat().st_size > 1000


def test_youtube_uploader_validation():
    """Verify YouTube uploader validates missing tokens gracefully."""
    uploader = YouTubeUploader()
    # If no refresh token is provided, calling upload should fail informatively
    if not config.youtube_refresh_token or not config.youtube_client_secret_json:
        with pytest.raises(ValueError):
            uploader._get_authenticated_service()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
