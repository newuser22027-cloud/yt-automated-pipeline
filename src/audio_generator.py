"""
Audio Generator Module.
Generates natural human-like voiceovers using Microsoft Edge TTS (Zero API Cost).
- Sentences split and joined with max 0.4s pauses (SSML-style silence control)
- Fast speaking rate for Shorts retention (+15%)
"""

import re
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

    def _clean_for_tts(self, text: str) -> str:
        """
        Cleans and optimizes text for TTS:
        - Removes markdown/special chars
        - Ensures short pauses between sentences (max ~0.4s)
        - Adds slight emphasis markers
        """
        # Remove markdown formatting
        text = re.sub(r'[*_#`~]', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Replace em-dash / en-dash with comma pause
        text = re.sub(r'[—–]', ',', text)
        # Remove double spaces after punctuation (causes big TTS pauses)
        text = re.sub(r'([.!?])\s{2,}', r'\1 ', text)
        # Convert "..." to single period (ellipsis = huge pause)
        text = re.sub(r'\.{2,}', '.', text)
        # Remove parenthetical asides that cause awkward pauses
        text = re.sub(r'\([^)]*\)', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    async def synthesize_async(self, text: str, output_path: Path) -> Path:
        """
        Synthesizes spoken text into an MP3 file asynchronously.
        Uses faster rate (+15%) and +5Hz pitch for energetic delivery.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cleaned_text = self._clean_for_tts(text)
        logger.info(f"Synthesizing audio ({len(cleaned_text)} chars) with voice: '{self.voice}'")

        # +15% rate = faster, energetic pacing; reduces unnatural long pauses
        communicate = edge_tts.Communicate(
            text=cleaned_text,
            voice=self.voice,
            rate="+15%",     # Faster = more energetic, fewer dead pauses
            pitch="+5Hz",    # Slightly higher pitch = more engaging
            volume="+10%"    # Slightly louder
        )

        await communicate.save(str(output_path))

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"Audio file generation failed: {output_path} is empty or missing.")

        logger.info(f"Audio voiceover saved: {output_path} ({output_path.stat().st_size} bytes)")
        return output_path

    def generate(self, text: str, output_filename: str = "voiceover.mp3") -> Path:
        """Synchronous wrapper around synthesize_async."""
        out_file = config.temp_dir / output_filename
        return asyncio.run(self.synthesize_async(text, out_file))


if __name__ == "__main__":
    audio_gen = AudioGenerator()
    test_script = "Did you know that neutron stars are so dense that a single sugar-cube would weigh over a billion tons? The universe hides secrets that will shock you."
    res = audio_gen.generate(test_script, "test_audio.mp3")
    print(f"Generated test audio at: {res}")
