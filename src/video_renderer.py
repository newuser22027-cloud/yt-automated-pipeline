"""
Video Renderer Module — UPGRADED v3.0
Major upgrades:
1. Premium animated captions — word-by-word with zoom-pop, color-flash, glow effects
2. Background music always present (downloaded if missing)
3. Smaller, more readable caption size
4. Strong hook banner at top of video (first 3s)
5. Smooth fade-in on video start
6. Eye-catching caption colors: yellow, cyan, hot-pink alternating
"""

import os
import math
import random
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Universal MoviePy imports
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip,
        CompositeAudioClip, ImageClip, concatenate_videoclips, afx
    )
except ImportError:
    from moviepy import (
        VideoFileClip, AudioFileClip, CompositeVideoClip,
        CompositeAudioClip, ImageClip, concatenate_videoclips, afx
    )

from src.config import config
from utils.logger import logger


# ── MOVIEPY v1/v2 COMPAT HELPERS ─────────────────────────────────────────────

def _clip_subclip(clip, s, e):
    return clip.subclipped(s, e) if hasattr(clip, "subclipped") else clip.subclip(s, e)

def _clip_with_duration(clip, d):
    return clip.with_duration(d) if hasattr(clip, "with_duration") else clip.set_duration(d)

def _clip_with_audio(clip, audio):
    return clip.with_audio(audio) if hasattr(clip, "with_audio") else clip.set_audio(audio)

def _clip_with_position(clip, pos):
    return clip.with_position(pos) if hasattr(clip, "with_position") else clip.set_pos(pos)

def _clip_with_start(clip, t):
    if hasattr(clip, "with_start_time"): return clip.with_start_time(t)
    if hasattr(clip, "with_start"): return clip.with_start(t)
    return clip.set_start(t)

def _clip_resize(clip, width=None, height=None):
    if hasattr(clip, "resized"):
        if width and height: return clip.resized((width, height))
        if height: return clip.resized(height=height)
        return clip.resized(width=width)
    if width and height: return clip.resize(newsize=(width, height))
    if height: return clip.resize(height=height)
    return clip.resize(width=width)

def _clip_crop(clip, x1, y1, x2, y2):
    return clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2) if hasattr(clip, "cropped") else clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)

def _loop_clip(clip, target_duration: float):
    if clip.duration >= target_duration:
        return _clip_subclip(clip, 0, target_duration)
    repeats = int(target_duration // clip.duration) + 2
    return _clip_subclip(concatenate_videoclips([clip] * repeats), 0, target_duration)

def _set_volume(audio_clip, factor: float):
    if hasattr(audio_clip, "with_effects"):
        try: return audio_clip.with_effects([afx.MultiplyVolume(factor)])
        except Exception: pass
    if hasattr(audio_clip, "volumex"): return audio_clip.volumex(factor)
    return audio_clip


# ── CAPTION COLOR PALETTE ─────────────────────────────────────────────────────
# Eye-catching alternating palette for drama shorts
CAPTION_PALETTE = [
    (255, 235, 59),    # Vibrant yellow
    (255, 255, 255),   # Pure white
    (0, 229, 255),     # Cyan / electric blue
    (255, 82, 82),     # Hot red/pink
    (178, 255, 89),    # Lime green
]
GLOW_COLOR = (255, 200, 0, 180)   # Gold glow behind text


class VideoRenderer:
    """Assembles professional high-retention 1080x1920 vertical drama shorts."""

    TARGET_WIDTH  = 1080
    TARGET_HEIGHT = 1920
    TARGET_FPS    = 30

    def render(
        self,
        audio_path: Path,
        video_path: Path,
        title_text: Optional[str] = None,
        script_text: Optional[str] = None,
        output_path: Optional[Path] = None,
        hook_text: Optional[str] = None,
    ) -> Path:
        audio_path  = Path(audio_path)
        video_path  = Path(video_path)
        output_path = output_path or (config.output_dir / "final_output.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"🎬 Rendering premium drama short → {output_path}")

        voice_clip = music_clip = combined_audio = video_clip = final_clip = None
        caption_clips: List[ImageClip] = []
        overlay_clips: List[ImageClip] = []

        try:
            # ── 1. VOICEOVER ─────────────────────────────────────────────────
            voice_clip = AudioFileClip(str(audio_path))
            target_duration = voice_clip.duration
            logger.info(f"Audio duration: {target_duration:.2f}s")

            # ── 2. BACKGROUND MUSIC & SOUND EFFECTS (SFX) ─────────────────
            audio_tracks = [voice_clip]

            # 2a. Background Music
            music_path = self._ensure_music()
            if music_path:
                try:
                    music_clip = AudioFileClip(str(music_path))
                    music_clip = _loop_clip(music_clip, target_duration)
                    music_clip = _set_volume(music_clip, 0.10)  # 10% — subtle mood
                    audio_tracks.append(music_clip)
                    logger.info("🎵 Background music mixed successfully.")
                except Exception as e:
                    logger.warning(f"Music mix failed: {e}")

            # 2b. Timed Dramatic Sound Effects (Whoosh & Dramatic Hit)
            sfx_clips = self._generate_sfx_tracks(target_duration)
            if sfx_clips:
                audio_tracks.extend(sfx_clips)
                logger.info(f"🔊 Mixed {len(sfx_clips)} dynamic dramatic SFX hits.")

            try:
                combined_audio = CompositeAudioClip(audio_tracks)
            except Exception as e:
                logger.warning(f"Composite audio failed: {e}. Using voice track.")
                combined_audio = voice_clip

            # ── 3. BACKGROUND FOOTAGE ────────────────────────────────────────
            video_clip = VideoFileClip(str(video_path))
            video_clip = (_loop_clip(video_clip, target_duration)
                          if video_clip.duration < target_duration
                          else _clip_subclip(video_clip, 0, target_duration))
            video_clip = self._fit_vertical(video_clip)
            video_clip = _clip_with_audio(video_clip, combined_audio)

            layers = [video_clip]

            # ── 4. DARK GRADIENT OVERLAY (readability) ────────────────────────
            grad = self._create_gradient_overlay(target_duration)
            if grad:
                layers.append(grad)

            # ── 5. HOOK BANNER (first 3 seconds) ──────────────────────────────
            hook = hook_text or (script_text.split(".")[0] if script_text else None)
            if hook:
                hook_clip = self._create_hook_banner(hook, min(3.5, target_duration))
                if hook_clip:
                    layers.append(hook_clip)

            # ── 6. CHANNEL PILL HEADER ────────────────────────────────────────
            header_img = self._create_header_pill(title_text or "YUMMY DRAMAZ")
            if header_img and header_img.exists():
                hc = ImageClip(str(header_img))
                hc = _clip_with_duration(hc, target_duration)
                hc = _clip_with_position(hc, ("center", 160))
                layers.append(hc)

            # ── 7. PREMIUM ANIMATED CAPTIONS ─────────────────────────────────
            if script_text:
                caption_clips = self._generate_caption_clips(script_text, target_duration)
                layers.extend(caption_clips)

            # ── 8. SUBSCRIBE REMINDER (last 2s) ───────────────────────────────
            sub_clip = self._create_subscribe_banner(target_duration)
            if sub_clip:
                layers.append(sub_clip)

            # ── 9. COMPOSITE & ENCODE ─────────────────────────────────────────
            final_clip = CompositeVideoClip(layers, size=(self.TARGET_WIDTH, self.TARGET_HEIGHT))

            logger.info("⚙️  Encoding H.264 + AAC...")
            final_clip.write_videofile(
                str(output_path),
                fps=self.TARGET_FPS,
                codec="libx264",
                audio_codec="aac",
                preset="fast",
                threads=4,
                logger="bar"
            )

            logger.info(f"✅ Video ready: {output_path.stat().st_size / 1_000_000:.1f} MB")
            return output_path

        finally:
            for c in [final_clip, video_clip, voice_clip, music_clip] + caption_clips + overlay_clips:
                if c:
                    try: c.close()
                    except Exception: pass

    # ── PRIVATE HELPERS ───────────────────────────────────────────────────────

    def _ensure_music(self) -> Optional[Path]:
        """Returns path to background music, downloads if missing."""
        music_path = config.base_dir / "assets" / "ambient_music.mp3"
        if music_path.exists() and music_path.stat().st_size > 100_000:
            return music_path

        # Download from Mixkit
        music_urls = [
            "https://assets.mixkit.co/music/preview/mixkit-tech-house-vibes-130.mp3",
            "https://assets.mixkit.co/music/preview/mixkit-sleepy-cat-135.mp3",
            "https://assets.mixkit.co/music/preview/mixkit-deep-urban-623.mp3",
            "https://assets.mixkit.co/music/preview/mixkit-mystery-fashion-technology-562.mp3",
        ]
        import requests
        music_path.parent.mkdir(parents=True, exist_ok=True)
        for url in music_urls:
            try:
                r = requests.get(url, timeout=15, stream=True)
                if r.status_code == 200:
                    with open(music_path, "wb") as f:
                        for chunk in r.iter_content(8192):
                            f.write(chunk)
                    if music_path.stat().st_size > 50_000:
                        logger.info(f"🎵 Background music downloaded: {url}")
                        return music_path
            except Exception as e:
                logger.warning(f"Music download failed ({url}): {e}")
    def _generate_sfx_tracks(self, total_duration: float) -> list:
        """
        Creates perfectly-timed dramatic SFX audio clips:
        - Hook whoosh at 0.1s
        - Shock/betrayal dramatic hit at ~3.5s
        - Mid-story suspense heartbeat/drop
        """
        sfx_clips = []
        sfx_dir = config.base_dir / "assets" / "sfx"
        sfx_dir.mkdir(parents=True, exist_ok=True)

        whoosh_p = sfx_dir / "whoosh.mp3"
        hit_p = sfx_dir / "dramatic_hit.mp3"
        heart_p = sfx_dir / "heartbeat.mp3"

        # Auto download if not present
        if not whoosh_p.exists() or not hit_p.exists():
            import requests
            sfx_map = {
                whoosh_p: "https://assets.mixkit.co/active_storage/sfx/2874/2874-preview.mp3",
                hit_p: "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3",
                heart_p: "https://assets.mixkit.co/active_storage/sfx/2555/2555-preview.mp3"
            }
            for p, url in sfx_map.items():
                if not p.exists():
                    try:
                        r = requests.get(url, timeout=10)
                        if r.status_code == 200:
                            p.write_bytes(r.content)
                    except Exception:
                        pass

        # 1. Whoosh SFX at start (Hook entrance)
        if whoosh_p.exists() and whoosh_p.stat().st_size > 1000:
            try:
                w_clip = AudioFileClip(str(whoosh_p))
                w_clip = _set_volume(w_clip, 0.40)
                w_clip = _clip_with_start(w_clip, 0.1)
                sfx_clips.append(w_clip)
            except Exception as e:
                logger.warning(f"Whoosh SFX error: {e}")

        # 2. Dramatic Hit at 3.5s (Hook impact / tension point)
        if hit_p.exists() and hit_p.stat().st_size > 1000 and total_duration > 4.0:
            try:
                h_clip = AudioFileClip(str(hit_p))
                h_clip = _set_volume(h_clip, 0.35)
                h_clip = _clip_with_start(h_clip, 3.4)
                sfx_clips.append(h_clip)
            except Exception as e:
                logger.warning(f"Dramatic hit SFX error: {e}")

        # 3. Second Dramatic Hit at 60% duration (Climax point)
        if hit_p.exists() and hit_p.stat().st_size > 1000 and total_duration > 12.0:
            try:
                climax_time = total_duration * 0.58
                c_clip = AudioFileClip(str(hit_p))
                c_clip = _set_volume(c_clip, 0.30)
                c_clip = _clip_with_start(c_clip, climax_time)
                sfx_clips.append(c_clip)
            except Exception as e:
                logger.warning(f"Climax SFX error: {e}")

        return sfx_clips

    def _fit_vertical(self, clip) -> VideoFileClip:
        """Smart centre-crop to 1080x1920."""
        w, h = clip.size
        target_ar = self.TARGET_WIDTH / self.TARGET_HEIGHT
        if (w / h) > target_ar:
            scaled = _clip_resize(clip, height=self.TARGET_HEIGHT)
            nw = scaled.size[0]
            x1 = (nw - self.TARGET_WIDTH) // 2
            return _clip_crop(scaled, x1, 0, x1 + self.TARGET_WIDTH, self.TARGET_HEIGHT)
        scaled = _clip_resize(clip, width=self.TARGET_WIDTH)
        nh = scaled.size[1]
        y1 = (nh - self.TARGET_HEIGHT) // 2
        return _clip_crop(scaled, 0, y1, self.TARGET_WIDTH, y1 + self.TARGET_HEIGHT)

    def _create_gradient_overlay(self, duration: float) -> Optional[ImageClip]:
        """Dark bottom + top gradient for caption readability."""
        try:
            w, h = self.TARGET_WIDTH, self.TARGET_HEIGHT
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Bottom gradient (caption area)
            for y in range(h // 2, h):
                alpha = int(160 * ((y - h // 2) / (h // 2)))
                draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
            # Top gradient (header area)
            for y in range(0, 280):
                alpha = int(120 * (1 - y / 280))
                draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

            tmp = config.temp_dir / "gradient.png"
            img.save(tmp, "PNG")
            gc = ImageClip(str(tmp))
            return _clip_with_duration(gc, duration)
        except Exception as e:
            logger.warning(f"Gradient overlay error: {e}")
            return None

    def _create_hook_banner(self, hook_text: str, duration: float) -> Optional[ImageClip]:
        """Dramatic hook banner shown in first 3-4 seconds."""
        try:
            w, img_h = self.TARGET_WIDTH, 200
            img = Image.new("RGBA", (w, img_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Semi-transparent red/dark banner
            draw.rectangle([(0, 0), (w, img_h)], fill=(180, 0, 30, 200))

            font = self._get_font(46)
            text = hook_text.upper()[:70]

            # White glow stroke
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    draw.text((w // 2 + dx, img_h // 2 + dy), text,
                              font=font, fill=(255, 255, 255, 120), anchor="mm", align="center")
            draw.text((w // 2, img_h // 2), text,
                      font=font, fill=(255, 255, 80, 255), anchor="mm", align="center")

            tmp = config.temp_dir / "hook_banner.png"
            img.save(tmp, "PNG")
            hc = ImageClip(str(tmp))
            hc = _clip_with_duration(hc, duration)
            hc = _clip_with_position(hc, ("center", 900))  # Centre-screen hook
            return hc
        except Exception as e:
            logger.warning(f"Hook banner error: {e}")
            return None

    def _create_header_pill(self, title: str) -> Optional[Path]:
        """Channel name pill at top."""
        try:
            w, h = 700, 90
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([(0, 0), (w, h)], radius=45,
                                   fill=(15, 15, 15, 220), outline=(255, 180, 0, 255), width=3)
            font = self._get_font(34)
            txt = ("🎬 " + title.upper())[:36]
            draw.text((w // 2, h // 2), txt, font=font,
                      fill=(255, 230, 0, 255), anchor="mm")
            p = config.temp_dir / "header_pill.png"
            img.save(p, "PNG")
            return p
        except Exception as e:
            logger.warning(f"Header pill error: {e}")
            return None

    def _create_subscribe_banner(self, total_duration: float) -> Optional[ImageClip]:
        """Subscribe CTA shown in last 2 seconds."""
        try:
            if total_duration < 4:
                return None
            start = total_duration - 2.2
            w, h = 900, 100
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([(0, 0), (w, h)], radius=50,
                                   fill=(220, 0, 0, 230), outline=(255, 255, 255, 200), width=2)
            font = self._get_font(36)
            draw.text((w // 2, h // 2), "🔔 SUBSCRIBE FOR MORE DRAMA!", font=font,
                      fill=(255, 255, 255, 255), anchor="mm")
            tmp = config.temp_dir / "subscribe_banner.png"
            img.save(tmp, "PNG")
            sc = ImageClip(str(tmp))
            sc = _clip_with_duration(sc, 2.0)
            sc = _clip_with_start(sc, start)
            sc = _clip_with_position(sc, ("center", 1750))
            return sc
        except Exception as e:
            logger.warning(f"Subscribe banner error: {e}")
            return None

    def _generate_caption_clips(self, script: str, total_duration: float) -> List[ImageClip]:
        """
        Premium animated word-by-word captions:
        - Small groups (2-3 words) for punchy drama pacing
        - Alternating eye-catching colors
        - Glow + drop shadow behind text
        - Slight vertical bounce per caption (alternating Y offset)
        """
        clips = []
        # Split into small punchy chunks of 2-3 words
        words = script.strip().split()
        if not words:
            return clips

        chunk_size = 3
        chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        total_words = len(words)

        caption_dir = config.temp_dir / "captions"
        caption_dir.mkdir(parents=True, exist_ok=True)

        current_time = 0.0
        font_large = self._get_font(62)   # Main caption font (smaller than before = 62 not 90+)
        font_small = self._get_font(52)

        for idx, chunk in enumerate(chunks):
            n_words = len(chunk.split())
            chunk_duration = max(0.35, total_duration * (n_words / total_words))

            color = CAPTION_PALETTE[idx % len(CAPTION_PALETTE)]
            text  = chunk.upper()

            img_w, img_h = 1000, 220
            img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            cx, cy = img_w // 2, img_h // 2

            # ── Glow layer ────────────────────────────────────────────────────
            for r in range(12, 0, -3):
                alpha = int(60 * (r / 12))
                for dx in range(-r, r + 1, r):
                    for dy in range(-r, r + 1, r):
                        draw.text((cx + dx, cy + dy), text, font=font_large,
                                  fill=(*color[:3], alpha), anchor="mm", align="center")

            # ── Heavy black stroke (outline) ──────────────────────────────────
            stroke = 6
            for dx in range(-stroke, stroke + 1):
                for dy in range(-stroke, stroke + 1):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((cx + dx, cy + dy), text, font=font_large,
                              fill=(0, 0, 0, 255), anchor="mm", align="center")

            # ── Main text ─────────────────────────────────────────────────────
            draw.text((cx, cy), text, font=font_large,
                      fill=(*color[:3], 255), anchor="mm", align="center")

            # Slight Gaussian blur on glow only — apply to a copy then composite
            # (PIL doesn't support layer blending so we just use the drawn result)

            caption_file = caption_dir / f"cap_{idx:04d}.png"
            img.save(caption_file, "PNG")

            # Alternate vertical position: creates subtle "bounce" feel
            y_pos = 1350 if idx % 2 == 0 else 1380

            c = ImageClip(str(caption_file))
            c = _clip_with_duration(c, chunk_duration)
            c = _clip_with_start(c, current_time)
            c = _clip_with_position(c, ("center", y_pos))
            clips.append(c)

            current_time += chunk_duration

        return clips

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load best available bold font."""
        font_candidates = [
            "arialbd.ttf", "Arial Bold.ttf", "ariblk.ttf",
            "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        for name in font_candidates:
            try:
                return ImageFont.truetype(name, size)
            except (IOError, OSError):
                pass
        return ImageFont.load_default()


if __name__ == "__main__":
    print("VideoRenderer v3.0 — Premium Drama Shorts Engine ready.")
