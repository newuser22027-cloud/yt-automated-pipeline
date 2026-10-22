"""
Audio Generator Module.
Generates natural human-like voiceovers using Microsoft Edge TTS (Zero API Cost).
"""

import os
import asyncio
from pathlib import Path
from typing import Optional
import edge_tts

from src.config import config
from utils.logger import logger


class AudioGenerator:
    """Handles asynchronous neural voice synthesis via edge-tts."""

    def __init__(self, voice: Optional[str] = None):
        self.voice = voice or config.tts_voice

    async def synthesize_async(self, text: str, output_path: Path) -> Path:
        """
        Synthesizes spoken text into an MP3 file asynchronously.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Synthesizing audio ({len(text)} chars) with voice: '{self.voice}'")
        
        # Edge TTS Communicate object
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate="+0%",
            pitch="+0Hz"
        )

        await communicate.save(str(output_path))

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"Audio file generation failed: {output_path} is empty or missing.")

        logger.info(f"Audio voiceover saved to: {output_path} ({output_path.stat().st_size} bytes)")
        return output_path

    def generate(self, text: str, output_filename: str = "voiceover.mp3") -> Path:
        """
        Synchronous wrapper around synthesize_async.
        """
        out_file = config.temp_dir / output_filename
        return asyncio.run(self.synthesize_async(text, out_file))


if __name__ == "__main__":
    audio_gen = AudioGenerator()
    test_script = "Did you know that neutron stars are so dense that a single sugar-cube-sized amount would weigh over one billion tons?"
    res = audio_gen.generate(test_script, "test_audio.mp3")
    print(f"Generated test audio at: {res}")
