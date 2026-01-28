"""
AI Service integrations for virtual try-on and talking avatar generation.
Supports multiple providers: Replicate, HeyGen, D-ID, Hugging Face, etc.
"""

import os
import requests
import time
from pathlib import Path
from typing import Optional
import base64
import mimetypes

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# Configuration from environment variables
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "")
DID_API_KEY = os.getenv("DID_API_KEY", "")
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "")
MIRAGIC_API_KEY = os.getenv("MIRAGIC_API_KEY", "")
MIRAGIC_BASE_URL = os.getenv("MIRAGIC_BASE_URL", "https://backend.miragic.ai").rstrip("/")
MIRAGIC_GARMENT_TYPE = os.getenv("MIRAGIC_GARMENT_TYPE", "full_body")
MIRAGIC_POLL_TIMEOUT = int(os.getenv("MIRAGIC_POLL_TIMEOUT_SECONDS", "600"))  # 10 minutes default

# Service selection
VIRTUAL_TRYON_SERVICE = os.getenv("VIRTUAL_TRYON_SERVICE", "miragic")  # miragic, replicate, huggingface, fallback
TALKING_AVATAR_SERVICE = os.getenv("TALKING_AVATAR_SERVICE", "did")  # replicate, heygen, did, huggingface, fallback


def virtual_tryon_replicate(face_path: str, clothes_path: str, out_image_path: str) -> bool:
    """
    Use Replicate API for virtual try-on.
    Model: IDM-VTON or similar virtual try-on models
    """
    if not REPLICATE_API_TOKEN:
        raise RuntimeError("REPLICATE_API_TOKEN not set. Get your token from https://replicate.com/account/api-tokens")
    
    try:
        import replicate
        
        # Upload images to Replicate
        with open(face_path, "rb") as f:
            face_file = f.read()
        with open(clothes_path, "rb") as f:
            clothes_file = f.read()
        
        # Use IDM-VTON model for virtual try-on
        # Alternative models: "cuuupid/idm-vton", "levihsu/ootdiffusion", etc.
        model = "cuuupid/idm-vton"
        
        print(f"Running Replicate model: {model}")
        output = replicate.run(
            model,
            input={
                "crop": False,
                "seed": 42,
                "steps": 30,
                "category": "upper_body",  # or "dresses", "lower_body", "full_body"
                "garm_img": open(clothes_path, "rb"),
                "human_img": open(face_path, "rb"),
            }
        )
        
        # Download result
        if isinstance(output, str):
            result_url = output
        elif isinstance(output, list) and len(output) > 0:
            result_url = output[0]
        else:
            raise RuntimeError("Unexpected output format from Replicate")
        
        # Download the image
        response = requests.get(result_url)
        response.raise_for_status()
        
        with open(out_image_path, "wb") as f:
            f.write(response.content)
        
        print(f"Virtual try-on completed using Replicate")
        return True
        
    except ImportError:
        raise RuntimeError("replicate package not installed. Run: pip install replicate")
    except Exception as e:
        raise RuntimeError(f"Replicate API error: {str(e)}")


def virtual_tryon_huggingface(face_path: str, clothes_path: str, out_image_path: str) -> bool:
    """
    Use Hugging Face Inference API for virtual try-on.
    Uses models like Kolors, StyleGen, or IDM-VTON.
    """
    if not HUGGINGFACE_API_TOKEN:
        raise RuntimeError("HUGGINGFACE_API_TOKEN not set. Get your token from https://huggingface.co/settings/tokens")
    
    try:
        # Try multiple models - start with Kolors which is popular
        models_to_try = [
            "levihsu/OOTDiffusion",  # OOTDiffusion
            "yisol/IDM-VTON",  # IDM-VTON
        ]
        
        # Read images as binary
        with open(face_path, "rb") as f:
            face_data = f.read()
        with open(clothes_path, "rb") as f:
            clothes_data = f.read()
        
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
        
        # Try each model until one works
        for model_name in models_to_try:
            try:
                API_URL = f"https://api-inference.huggingface.co/models/{model_name}"
                
                # Prepare files for multipart form data
                files = {
                    "model_image": ("face.jpg", face_data, "image/jpeg"),
                    "garment_image": ("clothes.jpg", clothes_data, "image/jpeg"),
                }
                
                # Some models use JSON with base64, others use multipart
                # Try multipart first (more common)
                response = requests.post(
                    API_URL, 
                    headers=headers, 
                    files=files,
                    timeout=180
                )
                
                # If multipart doesn't work, try JSON with base64
                if response.status_code == 422 or response.status_code == 400:
                    face_b64 = base64.b64encode(face_data).decode()
                    clothes_b64 = base64.b64encode(clothes_data).decode()
                    
                    payload = {
                        "inputs": {
                            "model_image": f"data:image/jpeg;base64,{face_b64}",
                            "garment_image": f"data:image/jpeg;base64,{clothes_b64}"
                        }
                    }
                    response = requests.post(
                        API_URL, 
                        headers=headers, 
                        json=payload,
                        timeout=180
                    )
                
                # Check if model is loading (503 status)
                if response.status_code == 503:
                    # Model is loading, wait and retry
                    print(f"Model {model_name} is loading, waiting 30 seconds...")
                    time.sleep(30)
                    response = requests.post(
                        API_URL, 
                        headers=headers, 
                        files=files,
                        timeout=180
                    )
                
                response.raise_for_status()
                
                # Save result image
                result_data = response.content
                if result_data.startswith(b'{'):
                    # Might be JSON response with image data
                    import json
                    result_json = json.loads(result_data)
                    if 'image' in result_json:
                        result_data = base64.b64decode(result_json['image'])
                    elif 'output' in result_json:
                        # Download from URL if provided
                        if isinstance(result_json['output'], str):
                            img_response = requests.get(result_json['output'])
                            result_data = img_response.content
                
                with open(out_image_path, "wb") as f:
                    f.write(result_data)
                
                print(f"Virtual try-on completed using Hugging Face model: {model_name}")
                return True
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # Model not found, try next one
                    continue
                elif e.response.status_code == 503:
                    # Model loading, already handled above
                    continue
                else:
                    # Other error, try next model
                    print(f"Error with model {model_name}: {str(e)}, trying next model...")
                    continue
            except Exception as e:
                print(f"Error with model {model_name}: {str(e)}, trying next model...")
                continue
        
        # If all models failed, raise error
        raise RuntimeError("All Hugging Face virtual try-on models failed. Check your API token and model availability.")
        
    except Exception as e:
        raise RuntimeError(f"Hugging Face API error: {str(e)}")


def _guess_mime_type(file_path: str, fallback: str = "application/octet-stream") -> str:
    mime, _ = mimetypes.guess_type(file_path)
    return mime or fallback


def _poll_miragic_job(job_id: str, headers: dict, timeout_seconds: int) -> dict:
    """Poll Miragic job status until completion or failure."""
    start_time = time.time()
    delay = 2.0  # seconds
    max_delay = 15.0

    while time.time() - start_time < timeout_seconds:
        status_resp = requests.get(
            f"{MIRAGIC_BASE_URL}/api/v1/virtual-try-on/{job_id}",
            headers=headers,
            timeout=45,
        )
        status_resp.raise_for_status()
        payload = status_resp.json()
        data = payload.get("data") or {}
        status = (data.get("status") or "").upper()

        if status == "COMPLETED":
            return data
        if status == "FAILED":
            error_msg = data.get("errorMessage") or "Miragic reported failure"
            raise RuntimeError(f"Miragic virtual try-on failed: {error_msg}")

        progress = data.get("progress")
        if progress is not None:
            print(f"Miragic progress: {progress}% (status={status})")
        else:
            print(f"Miragic status: {status or 'UNKNOWN'}; waiting {delay:.1f}s")

        time.sleep(delay)
        delay = min(delay * 1.5, max_delay)

    raise RuntimeError("Miragic virtual try-on timed out before completion")


def virtual_tryon_miragic(face_path: str, clothes_path: str, out_image_path: str) -> bool:
    """
    Use Miragic virtual try-on API.
    Documentation: https://backend.miragic.ai/api/v1/virtual-try-on
    """
    if not MIRAGIC_API_KEY:
        raise RuntimeError("MIRAGIC_API_KEY not set. Get your key from https://miragic.ai/")

    headers = {"X-API-Key": MIRAGIC_API_KEY}
    garment_type = MIRAGIC_GARMENT_TYPE or "full_body"

    try:
        print(f"Submitting Miragic virtual try-on request (garmentType={garment_type})")
        with open(face_path, "rb") as human_file, open(clothes_path, "rb") as cloth_file:
            files = [
                (
                    "humanImage",
                    (Path(face_path).name, human_file, _guess_mime_type(face_path)),
                ),
                (
                    "clothImage",
                    (Path(clothes_path).name, cloth_file, _guess_mime_type(clothes_path)),
                ),
            ]
            data = {"garmentType": garment_type}

            response = requests.post(
                f"{MIRAGIC_BASE_URL}/api/v1/virtual-try-on",
                headers=headers,
                data=data,
                files=files,
                timeout=120,
            )
            response.raise_for_status()
            job_payload = response.json()

        if not job_payload.get("success"):
            raise RuntimeError(f"Miragic API error: {job_payload}")

        job_data = job_payload.get("data") or {}
        job_id = job_data.get("jobId")
        if not job_id:
            raise RuntimeError(f"Miragic response missing jobId: {job_payload}")

        print(f"Miragic job created: {job_id}")
        result_data = _poll_miragic_job(job_id, headers, MIRAGIC_POLL_TIMEOUT)

        result_url = (
            result_data.get("processedUrl")
            or result_data.get("resultImagePath")
            or result_data.get("result_image_url")
        )
        if not result_url:
            raise RuntimeError(f"Miragic job completed but no result URL found: {result_data}")

        print(f"Downloading Miragic result image from {result_url}")
        image_response = requests.get(result_url, timeout=180)
        image_response.raise_for_status()

        with open(out_image_path, "wb") as out_file:
            out_file.write(image_response.content)

        print(f"Virtual try-on completed using Miragic. Saved to {out_image_path}")
        return True

    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = f": {e.response.json()}"
        except Exception:
            error_detail = f": {e.response.text}"
        raise RuntimeError(f"Miragic HTTP error {e.response.status_code}{error_detail}")
    except Exception as e:
        raise RuntimeError(f"Miragic API error: {str(e)}")


def talking_avatar_replicate(avatar_image_path: str, audio_path: str, out_video_path: str) -> bool:
    """
    Use Replicate API for talking avatar (lip-sync).
    Models: Wav2Lip, SadTalker, etc.
    """
    if not REPLICATE_API_TOKEN:
        raise RuntimeError("REPLICATE_API_TOKEN not set")
    
    try:
        import replicate
        
        # Use Wav2Lip or SadTalker model
        # SadTalker is better for full head movement
        model = "devxpy/cog-wav2lip"  # or "anotherjesse/sadtalker"
        
        print(f"Running Replicate talking avatar model: {model}")
        
        with open(avatar_image_path, "rb") as img_file, open(audio_path, "rb") as audio_file:
            output = replicate.run(
                model,
                input={
                    "face": img_file,
                    "audio": audio_file,
                }
            )
        
        # Download result video
        if isinstance(output, str):
            result_url = output
        elif isinstance(output, list) and len(output) > 0:
            result_url = output[0]
        else:
            raise RuntimeError("Unexpected output format from Replicate")
        
        # Download the video
        response = requests.get(result_url)
        response.raise_for_status()
        
        with open(out_video_path, "wb") as f:
            f.write(response.content)
        
        print(f"Talking avatar completed using Replicate")
        return True
        
    except ImportError:
        raise RuntimeError("replicate package not installed. Run: pip install replicate")
    except Exception as e:
        raise RuntimeError(f"Replicate API error: {str(e)}")


def talking_avatar_heygen(avatar_image_path: str, audio_path: str, out_video_path: str) -> bool:
    """
    Use HeyGen API for talking avatar generation.
    Requires HeyGen API key and avatar setup.
    """
    if not HEYGEN_API_KEY:
        raise RuntimeError("HEYGEN_API_KEY not set. Get it from https://www.heygen.com/")
    
    try:
        # HeyGen API endpoint
        API_URL = "https://api.heygen.com/v1/video.generate"
        
        headers = {
            "X-Api-Key": HEYGEN_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Upload avatar image and audio first
        # Note: HeyGen requires avatar to be created first, then video generation
        # This is a simplified example - actual implementation may require multiple API calls
        
        # For now, raise informative error
        raise RuntimeError(
            "HeyGen integration requires avatar setup first. "
            "See https://docs.heygen.com/ for full API documentation. "
            "Consider using Replicate or D-ID for simpler integration."
        )
        
    except Exception as e:
        raise RuntimeError(f"HeyGen API error: {str(e)}")


def talking_avatar_did(avatar_image_path: str, audio_path: str, out_video_path: str) -> bool:
    """
    Use D-ID API for talking avatar generation.
    D-ID API workflow:
    1. Upload source image
    2. Create a talk with the image and audio
    3. Poll for completion
    4. Download the result video
    """
    if not DID_API_KEY:
        raise RuntimeError("DID_API_KEY not set. Get it from https://studio.d-id.com/")
    
    try:
        base_url = "https://api.d-id.com"
        
        # D-ID uses Basic auth with base64 encoded email:api_key
        # The API key format from D-ID is already email:api_key
        # We need to base64 encode it for Basic auth
        if ":" in DID_API_KEY:
            # Already in email:api_key format
            auth_string = base64.b64encode(DID_API_KEY.encode()).decode()
        else:
            # Assume it's just the API key, need email
            raise RuntimeError("D-ID API key should be in format 'email:api_key'. Get it from https://studio.d-id.com/")
        
        headers = {
            "Authorization": f"Basic {auth_string}",
            "Accept": "application/json"
        }
        
        # Step 1: Upload source image
        print("Step 1: Uploading image to D-ID...")
        with open(avatar_image_path, "rb") as img_file:
            files = {"image": (Path(avatar_image_path).name, img_file, "image/jpeg")}
            upload_response = requests.post(
                f"{base_url}/images",
                headers=headers,
                files=files,
                timeout=60
            )
            upload_response.raise_for_status()
            image_data = upload_response.json()
            source_url = image_data.get("url") or image_data.get("id")
            
            if not source_url:
                # If URL format, use it directly
                if "url" in image_data:
                    source_url = image_data["url"]
                else:
                    raise RuntimeError("Failed to get image URL from D-ID upload response")
        
        print(f"Image uploaded: {source_url}")
        
        # Step 2: Upload audio file
        print("Step 2: Uploading audio to D-ID...")
        with open(audio_path, "rb") as audio_file:
            files = {"audio": (Path(audio_path).name, audio_file, "audio/mpeg")}
            audio_upload_response = requests.post(
                f"{base_url}/audios",
                headers=headers,
                files=files,
                timeout=60
            )
            audio_upload_response.raise_for_status()
            audio_data = audio_upload_response.json()
            audio_url = audio_data.get("url") or audio_data.get("id")
            
            if not audio_url:
                raise RuntimeError("Failed to get audio URL from D-ID upload response")
        
        print(f"Audio uploaded: {audio_url}")
        
        # Step 3: Create a talk
        print("Step 3: Creating talk...")
        talk_payload = {
            "source_url": source_url,
            "script": {
                "type": "audio",
                "audio_url": audio_url,
                "reduce_noise": True
            },
            "config": {
                "result_format": "mp4"
            }
        }
        
        talk_response = requests.post(
            f"{base_url}/talks",
            headers=headers,
            json=talk_payload,
            timeout=60
        )
        talk_response.raise_for_status()
        talk_data = talk_response.json()
        talk_id = talk_data.get("id")
        
        if not talk_id:
            raise RuntimeError("Failed to create talk. Response: " + str(talk_data))
        
        print(f"Talk created: {talk_id}")
        
        # Step 4: Poll for completion
        print("Step 4: Waiting for video generation...")
        max_attempts = 60  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            status_response = requests.get(
                f"{base_url}/talks/{talk_id}",
                headers=headers,
                timeout=30
            )
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data.get("status", "unknown")
            
            if status == "done":
                result_url = status_data.get("result_url")
                if not result_url:
                    raise RuntimeError("Talk completed but no result URL found")
                
                # Step 5: Download the video
                print("Step 5: Downloading video...")
                video_response = requests.get(result_url, timeout=300)
                video_response.raise_for_status()
                
                with open(out_video_path, "wb") as f:
                    f.write(video_response.content)
                
                print(f"Talking avatar completed using D-ID. Video saved to {out_video_path}")
                return True
                
            elif status == "error":
                error_msg = status_data.get("error", "Unknown error")
                raise RuntimeError(f"D-ID talk failed: {error_msg}")
            
            # Still processing
            attempt += 1
            time.sleep(5)  # Wait 5 seconds before checking again
            print(f"Status: {status}... (attempt {attempt}/{max_attempts})")
        
        raise RuntimeError("Talk generation timed out after 5 minutes")
        
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_json = e.response.json()
            error_detail = f": {error_json}"
        except:
            error_detail = f": {e.response.text}"
        raise RuntimeError(f"D-ID API HTTP error {e.response.status_code}{error_detail}")
    except Exception as e:
        raise RuntimeError(f"D-ID API error: {str(e)}")


def talking_avatar_huggingface(avatar_image_path: str, audio_path: str, out_video_path: str) -> bool:
    """
    Use Hugging Face Inference API for talking avatar.
    """
    if not HUGGINGFACE_API_TOKEN:
        raise RuntimeError("HUGGINGFACE_API_TOKEN not set")
    
    try:
        # Encode files
        with open(avatar_image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        with open(audio_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        
        # Use a talking avatar model (example - actual model may vary)
        API_URL = "https://api-inference.huggingface.co/models/OpenTalker/SadTalker"
        
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
        
        payload = {
            "inputs": {
                "image": f"data:image/png;base64,{img_b64}",
                "audio": f"data:audio/wav;base64,{audio_b64}"
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        
        # Save result
        with open(out_video_path, "wb") as f:
            f.write(response.content)
        
        print(f"Talking avatar completed using Hugging Face")
        return True
        
    except Exception as e:
        raise RuntimeError(f"Hugging Face API error: {str(e)}")


def virtual_tryon(face_path: str, clothes_path: str, out_image_path: str) -> bool:
    """
    Main virtual try-on function that routes to the selected service.
    """
    service = VIRTUAL_TRYON_SERVICE.lower()
    
    if service == "miragic":
        return virtual_tryon_miragic(face_path, clothes_path, out_image_path)
    elif service == "replicate":
        return virtual_tryon_replicate(face_path, clothes_path, out_image_path)
    elif service == "huggingface":
        return virtual_tryon_huggingface(face_path, clothes_path, out_image_path)
    else:
        # Fallback to basic implementation
        from .pipeline import virtual_tryon_fallback
        return virtual_tryon_fallback(face_path, clothes_path, out_image_path)


def talking_avatar(avatar_image_path: str, audio_path: str, out_video_path: str) -> bool:
    """
    Main talking avatar function that routes to the selected service.
    """
    service = TALKING_AVATAR_SERVICE.lower()
    
    if service == "replicate":
        return talking_avatar_replicate(avatar_image_path, audio_path, out_video_path)
    elif service == "heygen":
        return talking_avatar_heygen(avatar_image_path, audio_path, out_video_path)
    elif service == "did":
        return talking_avatar_did(avatar_image_path, audio_path, out_video_path)
    elif service == "huggingface":
        return talking_avatar_huggingface(avatar_image_path, audio_path, out_video_path)
    else:
        # Fallback to basic implementation
        from .pipeline import talking_avatar_fallback
        return talking_avatar_fallback(avatar_image_path, audio_path, out_video_path)

