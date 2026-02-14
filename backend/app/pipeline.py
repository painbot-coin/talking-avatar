"""
Pipeline orchestrator.

- virtual_tryon(face_path, clothes_path) -> generated_avatar_image_path
- talking_avatar(avatar_image_path, audio_path) -> final_video_path

This file uses simple fallback implementations so you can test the flow immediately.
Replace virtual_tryon() and talking_avatar() with real model calls (SadTalker/Wav2Lip/HeyGen/etc).
"""

from pathlib import Path
from PIL import Image, ImageOps
import numpy as np
import subprocess
import os

# Compatibility fix for Pillow 10.0.0+ (ANTIALIAS was removed)
# MoviePy still uses the old constant, so we need to add it back
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

def run_pipeline(face_path, clothes_path, audio_path, out_video, workdir):
    """
    Main pipeline orchestrator.
    Runs virtual try-on followed by talking avatar generation.
    """
    workdir = Path(workdir)
    avatar_image = workdir / "avatar.png"
    
    try:
        # 1) Virtual try-on: produce avatar image (placeholder)
        print(f"Step 1: Running virtual try-on...")
        virtual_tryon(face_path, clothes_path, str(avatar_image))
        
        if not Path(avatar_image).exists():
            raise RuntimeError("Virtual try-on failed to create avatar image")
        
        # 2) Create talking avatar video using audio (placeholder)
        print(f"Step 2: Generating talking avatar video...")
        talking_avatar(str(avatar_image), audio_path, out_video)
        
        if not Path(out_video).exists():
            raise RuntimeError("Talking avatar generation failed to create video")
        
        print("Pipeline completed successfully")
    except Exception as e:
        print(f"Pipeline error: {str(e)}")
        raise

def virtual_tryon_fallback(face_path, clothes_path, out_image_path):
    """
    Fallback: Basic overlay implementation when AI services are not available.
    """
    try:
        face = Image.open(face_path).convert("RGBA")
        clothes = Image.open(clothes_path).convert("RGBA")
    except Exception as e:
        raise RuntimeError(f"Failed to load images: {str(e)}")

    # Basic heuristic: scale clothes to face width and paste below top half
    fw, fh = face.size
    cw, ch = clothes.size
    scale = fw / cw * 0.9
    new_cw = int(cw * scale)
    new_ch = int(ch * scale)
    clothes_resized = clothes.resize((new_cw, new_ch), Image.LANCZOS)

    # create canvas larger to include torso (if needed)
    canvas_h = int(fh * 1.8)
    canvas = Image.new("RGBA", (fw, canvas_h), (255,255,255,255))
    # paste face at top center
    canvas.paste(face, (0, 0), face)
    # paste clothes below face (simple positioning)
    clothes_x = int((fw - new_cw) / 2)
    clothes_y = int(fh * 0.6)
    canvas.paste(clothes_resized, (clothes_x, clothes_y), clothes_resized)

    # Convert to RGB before applying autocontrast (autocontrast doesn't support RGBA)
    canvas_rgb = canvas.convert("RGB")
    # optional: simple smoothing
    canvas_rgb = ImageOps.autocontrast(canvas_rgb)

    try:
        canvas_rgb.save(out_image_path, "PNG")
        print(f"Saved virtual try-on image to {out_image_path} (fallback mode)")
    except Exception as e:
        raise RuntimeError(f"Failed to save avatar image: {str(e)}")


def virtual_tryon(face_path, clothes_path, out_image_path):
    """
    Virtual try-on using AI services. Routes to selected service or fallback.
    """
    try:
        from .ai_services import virtual_tryon as ai_virtual_tryon
        return ai_virtual_tryon(face_path, clothes_path, out_image_path)
    except Exception as e:
        print(f"AI service error, using fallback: {str(e)}")
        virtual_tryon_fallback(face_path, clothes_path, out_image_path)

def talking_avatar_fallback(avatar_image_path, audio_path, out_video_path):
    """
    Fallback: Basic video creation with static image and audio.
    """
    avatar = str(avatar_image_path)
    audio = str(audio_path)
    out = str(out_video_path)

    try:
        # Load audio to get duration
        audio_clip = AudioFileClip(audio)
        duration = audio_clip.duration
        
        if duration <= 0:
            raise RuntimeError("Audio file has invalid duration")
        
        # Create image clip with audio duration
        clip = ImageClip(avatar).set_duration(duration)
        # Optionally, you can create a sequence of image clips with small transforms to simulate motion.
        # For now we just produce a static image with audio — good for testing.
        clip = clip.set_audio(audio_clip).set_fps(24).resize(width=640)

        # write the final video
        clip.write_videofile(
            out, 
            codec="libx264", 
            audio_codec="aac", 
            verbose=False, 
            logger=None,
            preset="medium"  # Balance between speed and quality
        )
        print(f"Saved talking avatar video to {out} (fallback mode)")
        
        # Clean up clips to free memory
        clip.close()
        audio_clip.close()
    except Exception as e:
        raise RuntimeError(f"Failed to create talking avatar video: {str(e)}")


def talking_avatar(avatar_image_path, audio_path, out_video_path):
    """
    Talking avatar using AI services. Routes to selected service or fallback.
    """
    try:
        from .ai_services import talking_avatar as ai_talking_avatar
        return ai_talking_avatar(avatar_image_path, audio_path, out_video_path)
    except Exception as e:
        print(f"AI service error, using fallback: {str(e)}")
        talking_avatar_fallback(avatar_image_path, audio_path, out_video_path)
