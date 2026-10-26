"""
Audio Generator Module — UPGRADED v3.1 (Multi-Voice Acting & Seamless Concatenation)
Supports:
- Narrator Voice: en-US-ChristopherNeural (Deep, suspenseful, authoritative)
- Male Character Voice: en-US-GuyNeural (Emotional, expressive male)
- Female Character Voice: en-US-JennyNeural (Passionate, emotive female)
- Stitching with micro-pauses (< 0.2s) between dialogue lines
"""

import re
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import edge_tts

# MoviePy audio clip for seamless concatenation
try:
    from moviepy.editor import AudioFileClip, concatenate_audioclips
except ImportError:
    from moviepy import AudioFileClip, concatenate_audioclips

from src.config import config
from utils.logger import logger


# Character Voice Roster (All 100% Free Edge-TTS Neural Voices)
VOICE_MAP = {
    "narrator": "en-US-ChristopherNeural",
    "male":     "en-US-GuyNeural",
    "female":   "en-US-JennyNeural"
}


class AudioGenerator:
    """Handles multi-character neural voice synthesis via edge-tts."""

    def __init__(self, default_voice: Optional[str] = None):
        self.default_voice = default_voice or config.tts_voice

    def _clean_for_tts(self, text: str) -> str:
        """Cleans text to avoid awkward pauses."""
        text = re.sub(r'[*_#`~]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[—–]', ',', text)
        text = re.sub(r'([.!?])\s{2,}', r'\1 ', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\([^)]*\)', '', text)
        return text.strip()

    async def _synthesize_line(self, text: str, voice: str, output_path: Path, rate: str = "+12%"):
        """Synthesizes a single dialogue line."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch="+3Hz",
            volume="+8%"
        )
        await communicate.save(str(output_path))

    async def synthesize_dialogues_async(self, dialogues: List[Dict[str, str]], output_path: Path) -> Path:
        """
        Synthesizes each dialogue line with the character's designated voice,
        then stitches them together seamlessly.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        temp_audio_dir = config.temp_dir / "dialogues_audio"
        temp_audio_dir.mkdir(parents=True, exist_ok=True)

        segment_paths: List[Path] = []

        logger.info(f"🎭 Synthesizing multi-character audio ({len(dialogues)} dialogue turns)...")

        for idx, line in enumerate(dialogues):
            speaker = str(line.get("speaker", "narrator")).lower().strip()
            voice = VOICE_MAP.get(speaker, VOICE_MAP["narrator"])
            raw_text = line.get("text", "").strip()
            cleaned_text = self._clean_for_tts(raw_text)

            if not cleaned_text:
                continue

            seg_file = temp_audio_dir / f"line_{idx:02d}_{speaker}.mp3"
            logger.info(f"   [{idx+1}/{len(dialogues)}] Voice '{voice}' ({speaker}): \"{cleaned_text[:35]}...\"")
            await self._synthesize_line(cleaned_text, voice, seg_file)

            if seg_file.exists() and seg_file.stat().st_size > 0:
                segment_paths.append(seg_file)

        if not segment_paths:
            raise RuntimeError("No dialogue audio lines were successfully generated.")

        # Stitch all segments together using MoviePy
        clips = []
        try:
            for p in segment_paths:
                clips.append(AudioFileClip(str(p)))

            logger.info(f"Stitching {len(clips)} dialogue audio clips seamlessly...")
            combined = concatenate_audioclips(clips)
            combined.write_audiofile(
                str(output_path),
                fps=44100,
                nbytes=2,
                codec="libmp3lame",
                logger=None
            )
        finally:
            for c in clips:
                try:
                    c.close()
                except Exception:
                    pass

        logger.info(f"✅ Multi-voice audio track generated: {output_path} ({output_path.stat().st_size} bytes)")
        return output_path

    def generate_dialogues(self, dialogues: List[Dict[str, str]], output_filename: str = "voiceover.mp3") -> Path:
        """Synchronous wrapper for multi-character dialogue generation."""
        out_file = config.temp_dir / output_filename
        return asyncio.run(self.synthesize_dialogues_async(dialogues, out_file))

    def generate(self, text: str, output_filename: str = "voiceover.mp3") -> Path:
        """Fallback for plain single-text generation."""
        dialogues = [{"speaker": "narrator", "text": text}]
        return self.generate_dialogues(dialogues, output_filename)


if __name__ == "__main__":
    audio_gen = AudioGenerator()
    test_dialogues = [
        {"speaker": "narrator", "text": "Nobody warned her. She grabbed his phone."},
        {"speaker": "female", "text": "Who is Karen? Why are there photos of three kids?"},
        {"speaker": "male", "text": "Put that down! You were never supposed to see that!"},
        {"speaker": "narrator", "text": "His secret was out. Karma had arrived."}
    ]
    res = audio_gen.generate_dialogues(test_dialogues, "test_multi_voice.mp3")
    print(f"Generated multi-voice test at: {res}")
