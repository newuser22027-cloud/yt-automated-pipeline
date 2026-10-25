"""
Video Renderer Module.
Assembles viral 1080x1920 vertical YouTube Shorts with:
1. Real cinematic HD stock video background (smart auto-cropped to 9:16)
2. Dynamic animated word-by-word / phrase-by-phrase captions (Hormozi style)
3. Balanced background ambient music (ducked under neural voiceover)
4. Sleek top-header category pill
"""

import os
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont

# Universal MoviePy imports
try:
    from moviepy.editor import (
        VideoFileClip,
        AudioFileClip,
        CompositeVideoClip,
        CompositeAudioClip,
        ImageClip,
        concatenate_videoclips,
        afx
    )
except ImportError:
    from moviepy import (
        VideoFileClip,
        AudioFileClip,
        CompositeVideoClip,
        CompositeAudioClip,
        ImageClip,
        concatenate_videoclips,
        afx
    )

from src.config import config
from utils.logger import logger


def _clip_subclip(clip, start_time: float, end_time: float):
    if hasattr(clip, "subclipped"):
        return clip.subclipped(start_time, end_time)
    return clip.subclip(start_time, end_time)


def _clip_with_duration(clip, duration: float):
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)


def _clip_with_audio(clip, audio):
    if hasattr(clip, "with_audio"):
        return clip.with_audio(audio)
    return clip.set_audio(audio)


def _clip_with_position(clip, position):
    if hasattr(clip, "with_position"):
        return clip.with_position(position)
    return clip.set_pos(position)


def _clip_with_start(clip, start_time: float):
    if hasattr(clip, "with_start_time"):
        return clip.with_start_time(start_time)
    if hasattr(clip, "with_start"):
        return clip.with_start(start_time)
    return clip.set_start(start_time)


def _clip_resize(clip, width: Optional[int] = None, height: Optional[int] = None):
    if hasattr(clip, "resized"):
        if width is not None and height is not None:
            return clip.resized((width, height))
        if height is not None:
            return clip.resized(height=height)
        if width is not None:
            return clip.resized(width=width)
    if width is not None and height is not None:
        return clip.resize(newsize=(width, height))
    if height is not None:
        return clip.resize(height=height)
    if width is not None:
        return clip.resize(width=width)
    return clip


def _clip_crop(clip, x1: int, y1: int, x2: int, y2: int):
    if hasattr(clip, "cropped"):
        return clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
    return clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)


def _loop_clip(clip, target_duration: float):
    if clip.duration >= target_duration:
        return _clip_subclip(clip, 0, target_duration)
    repeats = int(target_duration // clip.duration) + 2
    looped = concatenate_videoclips([clip] * repeats)
    return _clip_subclip(looped, 0, target_duration)


def _set_volume(audio_clip, volume_factor: float):
    if hasattr(audio_clip, "with_effects"):
        try:
            return audio_clip.with_effects([afx.MultiplyVolume(volume_factor)])
        except Exception:
            pass
    if hasattr(audio_clip, "volumex"):
        return audio_clip.volumex(volume_factor)
    return audio_clip


class VideoRenderer:
    """Assembles professional high-retention 1080x1920 vertical videos."""

    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    TARGET_FPS = 30

    def render(
        self,
        audio_path: Path,
        video_path: Path,
        title_text: Optional[str] = None,
        script_text: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Renders complete vertical video with synchronized audio, dynamic captions,
        ambient music, and smart framing.
        """
        audio_path = Path(audio_path)
        video_path = Path(video_path)
        output_path = output_path or (config.output_dir / "final_output.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initiating high-retention video render -> Output: {output_path}")

        voice_clip = None
        music_clip = None
        combined_audio = None
        video_clip = None
        final_clip = None
        caption_clips = []
        header_clip = None

        try:
            # 1. Voiceover Audio
            voice_clip = AudioFileClip(str(audio_path))
            target_duration = voice_clip.duration
            logger.info(f"Audio voiceover duration: {target_duration:.2f} seconds")

            # 2. Ambient Background Music Mixing
            ambient_music_path = config.base_dir / "assets" / "ambient_music.mp3"
            if ambient_music_path.exists():
                try:
                    music_clip = AudioFileClip(str(ambient_music_path))
                    music_clip = _loop_clip(music_clip, target_duration)
                    # Duck music volume to 12% so voiceover is crisp & prominent
                    music_clip = _set_volume(music_clip, 0.12)
                    combined_audio = CompositeAudioClip([voice_clip, music_clip])
                except Exception as e:
                    logger.warning(f"Audio mixing issue: {e}. Using voiceover track directly.")
                    combined_audio = voice_clip
            else:
                combined_audio = voice_clip

            # 3. Stock Footage Preparation (Smart 9:16 Vertical Crop)
            video_clip = VideoFileClip(str(video_path))
            if video_clip.duration < target_duration:
                video_clip = _loop_clip(video_clip, target_duration)
            else:
                video_clip = _clip_subclip(video_clip, 0, target_duration)

            video_clip = self._fit_vertical(video_clip)
            video_clip = _clip_with_audio(video_clip, combined_audio)

            layers = [video_clip]

            # 4. Top Header Pill Banner
            header_img = self._create_header_pill(title_text or "DAILY DISCOVERY")
            if header_img and header_img.exists():
                header_clip = ImageClip(str(header_img))
                header_clip = _clip_with_duration(header_clip, target_duration)
                header_clip = _clip_with_position(header_clip, ("center", 180))
                layers.append(header_clip)

            # 5. Dynamic Animated Subtitles / Captions (Word/Phrase timing)
            if script_text:
                caption_clips = self._generate_caption_clips(script_text, target_duration)
                layers.extend(caption_clips)

            final_clip = CompositeVideoClip(layers, size=(self.TARGET_WIDTH, self.TARGET_HEIGHT))

            # 6. Encode Video
            logger.info("Encoding final video with H.264 & AAC...")
            final_clip.write_videofile(
                str(output_path),
                fps=self.TARGET_FPS,
                codec="libx264",
                audio_codec="aac",
                preset="fast",
                threads=4,
                logger="bar"
            )

            logger.info(f"Video produced successfully! Size: {output_path.stat().st_size} bytes")
            return output_path

        finally:
            # Guarantee memory and file descriptor release
            all_clips = [final_clip, header_clip, video_clip, voice_clip, music_clip] + caption_clips
            for c in all_clips:
                if c:
                    try:
                        c.close()
                    except Exception:
                        pass

    def _fit_vertical(self, clip: VideoFileClip) -> VideoFileClip:
        """Crops and centers footage into exact 1080x1920 vertical."""
        w, h = clip.size
        target_aspect = self.TARGET_WIDTH / self.TARGET_HEIGHT
        clip_aspect = w / h

        if clip_aspect > target_aspect:
            scaled = _clip_resize(clip, height=self.TARGET_HEIGHT)
            new_w, _ = scaled.size
            x1 = (new_w - self.TARGET_WIDTH) // 2
            return _clip_crop(scaled, x1=x1, y1=0, x2=x1 + self.TARGET_WIDTH, y2=self.TARGET_HEIGHT)
        else:
            scaled = _clip_resize(clip, width=self.TARGET_WIDTH)
            _, new_h = scaled.size
            y1 = (new_h - self.TARGET_HEIGHT) // 2
            return _clip_crop(scaled, x1=0, y1=y1, x2=self.TARGET_WIDTH, y2=y1 + self.TARGET_HEIGHT)

    def _create_header_pill(self, title: str) -> Optional[Path]:
        """Creates modern aesthetic top-pill tag."""
        try:
            overlay_file = config.temp_dir / "header_pill.png"
            img_width, img_height = 800, 100
            img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Translucent dark pill with gold accent outline
            draw.rounded_rectangle(
                [(0, 0), (img_width, img_height)],
                radius=50,
                fill=(0, 0, 0, 200),
                outline=(255, 215, 0, 240),
                width=3
            )

            font = None
            for font_name in ["arialbd.ttf", "DejaVuSans-Bold.ttf"]:
                try:
                    font = ImageFont.truetype(font_name, 36)
                    break
                except IOError:
                    pass
            if not font:
                font = ImageFont.load_default()

            short_title = title.upper()
            if len(short_title) > 36:
                short_title = short_title[:33] + "..."

            draw.text(
                (img_width // 2, img_height // 2),
                short_title,
                fill=(255, 255, 255, 255),
                font=font,
                anchor="mm"
            )

            img.save(overlay_file, "PNG")
            return overlay_file
        except Exception as e:
            logger.warning(f"Header pill error: {e}")
            return None

    def _generate_caption_clips(self, script: str, total_duration: float) -> List[ImageClip]:
        """
        Creates dynamic punchy animated subtitle cards timed to speech.
        """
        clips = []
        words = script.strip().split()
        if not words:
            return clips

        # Group words into short 3-to-4 word punchy phrases
        chunk_size = 4
        chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        total_words = len(words)

        current_time = 0.0
        font = None
        for font_name in ["arialbd.ttf", "DejaVuSans-Bold.ttf"]:
            try:
                font = ImageFont.truetype(font_name, 56)
                break
            except IOError:
                pass
        if not font:
            font = ImageFont.load_default()

        caption_dir = config.temp_dir / "captions"
        caption_dir.mkdir(parents=True, exist_ok=True)

        for idx, chunk in enumerate(chunks):
            chunk_word_count = len(chunk.split())
            chunk_duration = total_duration * (chunk_word_count / total_words)

            img_w, img_h = 1000, 260
            img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Alternate bold yellow / bright white for high engagement
            highlight_color = (255, 235, 59, 255) if idx % 2 == 0 else (255, 255, 255, 255)
            text_str = chunk.upper()

            # Heavy black outline stroke for maximum readability over footage
            stroke_width = 5
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    draw.text(
                        (img_w // 2 + dx, img_h // 2 + dy),
                        text_str,
                        font=font,
                        fill=(0, 0, 0, 255),
                        anchor="mm",
                        align="center"
                    )

            # Draw highlighted main text
            draw.text(
                (img_w // 2, img_h // 2),
                text_str,
                font=font,
                fill=highlight_color,
                anchor="mm",
                align="center"
            )

            caption_file = caption_dir / f"caption_{idx}.png"
            img.save(caption_file, "PNG")

            c_clip = ImageClip(str(caption_file))
            c_clip = _clip_with_duration(c_clip, chunk_duration)
            c_clip = _clip_with_start(c_clip, current_time)
            # Positioned in the sweet spot (lower-center)
            c_clip = _clip_with_position(c_clip, ("center", 1100))

            clips.append(c_clip)
            current_time += chunk_duration

        return clips


if __name__ == "__main__":
    renderer = VideoRenderer()
    print("VideoRenderer upgraded.")
