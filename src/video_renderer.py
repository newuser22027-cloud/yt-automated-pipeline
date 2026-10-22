"""
Video Renderer Module.
Assembles vertical 9:16 (1080x1920) YouTube Shorts using MoviePy and FFmpeg.
Includes smart auto-framing, robust clip looping, and resilient Pillow-backed text overlays.
Fully compatible with both MoviePy v1 and MoviePy v2+.
"""

import os
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont

# Universal MoviePy imports (MoviePy v1 and v2)
try:
    from moviepy.editor import (
        VideoFileClip,
        AudioFileClip,
        CompositeVideoClip,
        ImageClip,
        concatenate_videoclips
    )
except ImportError:
    from moviepy import (
        VideoFileClip,
        AudioFileClip,
        CompositeVideoClip,
        ImageClip,
        concatenate_videoclips
    )

from src.config import config
from utils.logger import logger


# Helper functions to normalize MoviePy 1 vs MoviePy 2 API differences
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


def _clip_resize(clip, width: Optional[int] = None, height: Optional[int] = None):
    if hasattr(clip, "resized"):
        if width is not None and height is not None:
            return clip.resized((width, height))
        if height is not None:
            return clip.resized(height=height)
        if width is not None:
            return clip.resized(width=width)
    # MoviePy 1 fallback
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
    """
    Universally loops a video clip to fill target duration.
    """
    if clip.duration >= target_duration:
        return _clip_subclip(clip, 0, target_duration)
    repeats = int(target_duration // clip.duration) + 2
    looped = concatenate_videoclips([clip] * repeats)
    return _clip_subclip(looped, 0, target_duration)


class VideoRenderer:
    """Assembles and exports 1080x1920 vertical videos for YouTube Shorts."""

    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    TARGET_FPS = 30

    def render(
        self,
        audio_path: Path,
        video_path: Path,
        title_text: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Renders complete vertical video with synchronized audio and hook overlay.
        """
        audio_path = Path(audio_path)
        video_path = Path(video_path)
        output_path = output_path or (config.output_dir / "final_output.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initiating video render -> Output: {output_path}")

        audio_clip = None
        video_clip = None
        final_clip = None
        title_clip = None

        try:
            # 1. Load Audio
            audio_clip = AudioFileClip(str(audio_path))
            target_duration = audio_clip.duration
            logger.info(f"Target video duration determined by audio: {target_duration:.2f} seconds")

            # 2. Load and Prepare Video Clip
            video_clip = VideoFileClip(str(video_path))

            # Auto-loop or trim video to match exact audio duration
            if video_clip.duration < target_duration:
                logger.info(f"Video ({video_clip.duration:.1f}s) shorter than audio ({target_duration:.1f}s). Looping...")
                video_clip = _loop_clip(video_clip, target_duration)
            else:
                video_clip = _clip_subclip(video_clip, 0, target_duration)

            # 3. Smart Framing & Aspect Ratio Conversion to 1080x1920 (9:16)
            video_clip = self._fit_vertical(video_clip)

            # Attach voiceover audio track
            video_clip = _clip_with_audio(video_clip, audio_clip)

            # 4. Optional Title Hook Overlay (Pillow-backed transparent overlay)
            layers = [video_clip]
            if title_text:
                title_overlay_path = self._create_title_overlay_image(title_text)
                if title_overlay_path and title_overlay_path.exists():
                    title_clip = ImageClip(str(title_overlay_path))
                    title_clip = _clip_with_duration(title_clip, min(5.0, target_duration))
                    title_clip = _clip_with_position(title_clip, ("center", 240))
                    layers.append(title_clip)

            final_clip = CompositeVideoClip(layers, size=(self.TARGET_WIDTH, self.TARGET_HEIGHT))

            # 5. Export Video File
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

            logger.info(f"Render completed successfully! File size: {output_path.stat().st_size} bytes")
            return output_path

        finally:
            # Guarantee resource cleanup on Windows
            for clip in [final_clip, title_clip, video_clip, audio_clip]:
                if clip:
                    try:
                        clip.close()
                    except Exception:
                        pass

    def _fit_vertical(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Crops and scales any aspect ratio into exact 1080x1920 vertical without distortion.
        """
        w, h = clip.size
        target_aspect = self.TARGET_WIDTH / self.TARGET_HEIGHT  # 9/16 = 0.5625
        clip_aspect = w / h

        if clip_aspect > target_aspect:
            # Clip is wider than 9:16 -> scale height to 1920, then crop width to 1080 centered
            scaled = _clip_resize(clip, height=self.TARGET_HEIGHT)
            new_w, _ = scaled.size
            x1 = (new_w - self.TARGET_WIDTH) // 2
            cropped = _clip_crop(scaled, x1=x1, y1=0, x2=x1 + self.TARGET_WIDTH, y2=self.TARGET_HEIGHT)
            return cropped
        else:
            # Clip is narrower or taller -> scale width to 1080, then crop height to 1920 centered
            scaled = _clip_resize(clip, width=self.TARGET_WIDTH)
            _, new_h = scaled.size
            y1 = (new_h - self.TARGET_HEIGHT) // 2
            cropped = _clip_crop(scaled, x1=0, y1=y1, x2=self.TARGET_WIDTH, y2=y1 + self.TARGET_HEIGHT)
            return cropped

    def _create_title_overlay_image(self, title: str) -> Optional[Path]:
        """
        Generates a sleek, high-contrast title banner PNG using Pillow.
        Avoids external ImageMagick dependencies.
        """
        try:
            overlay_file = config.temp_dir / "title_overlay.png"
            img_width, img_height = 960, 240
            img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Draw rounded rectangle backdrop with dark translucent background
            draw.rounded_rectangle(
                [(0, 0), (img_width, img_height)],
                radius=25,
                fill=(0, 0, 0, 180),
                outline=(255, 215, 0, 220),  # Gold accent border
                width=4
            )

            # System fonts fallback
            font = None
            try:
                font = ImageFont.truetype("arialbd.ttf", 44)
            except IOError:
                try:
                    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 42)
                except IOError:
                    font = ImageFont.load_default()

            # Word wrap title text
            words = title.upper().split()
            lines = []
            curr_line = []
            for w in words:
                curr_line.append(w)
                if len(" ".join(curr_line)) > 24:
                    lines.append(" ".join(curr_line))
                    curr_line = []
            if curr_line:
                lines.append(" ".join(curr_line))

            # Limit to 3 lines
            lines = lines[:3]
            text = "\n".join(lines)

            # Draw text centered
            draw.multiline_text(
                (img_width // 2, img_height // 2),
                text,
                fill=(255, 255, 255, 255),
                font=font,
                anchor="mm",
                align="center",
                spacing=8
            )

            img.save(overlay_file, "PNG")
            return overlay_file
        except Exception as e:
            logger.warning(f"Failed to generate title overlay graphic: {e}")
            return None


if __name__ == "__main__":
    renderer = VideoRenderer()
    print("VideoRenderer initialized.")
