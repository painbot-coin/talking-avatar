from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uuid
import shutil
from app.pipeline import run_pipeline

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Save results in a results folder at the same level as backend
# This creates: talking-avatar/results/
BACKEND_DIR = Path(__file__).parent.parent  # backend directory
PROJECT_ROOT = BACKEND_DIR.parent  # talking-avatar directory
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Talking Avatar API is running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

def cleanup_directory(workdir: Path):
    """Background task to clean up temporary files (optional - not used by default now)"""
    if workdir.exists():
        shutil.rmtree(workdir, ignore_errors=True)

@app.post("/generate-avatar")
async def generate_avatar(
    background_tasks: BackgroundTasks,
    face: UploadFile = File(...), 
    clothes: UploadFile = File(...), 
    audio: UploadFile = File(...)
):
    # create run-specific directory in results folder
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
    workdir = RESULTS_DIR / run_id
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        # Validate file types
        face_ext = Path(face.filename).suffix.lower()
        clothes_ext = Path(clothes.filename).suffix.lower()
        audio_ext = Path(audio.filename).suffix.lower()
        
        if face_ext not in ['.jpg', '.jpeg', '.png']:
            raise HTTPException(status_code=400, detail=f"Face image must be JPG or PNG, got {face_ext}")
        if clothes_ext not in ['.jpg', '.jpeg', '.png']:
            raise HTTPException(status_code=400, detail=f"Clothes image must be JPG or PNG, got {clothes_ext}")
        if audio_ext not in ['.wav', '.mp3', '.m4a', '.aac']:
            raise HTTPException(status_code=400, detail=f"Audio must be WAV, MP3, M4A, or AAC, got {audio_ext}")

        face_path = workdir / f"face_{face.filename}"
        clothes_path = workdir / f"clothes_{clothes.filename}"
        audio_path = workdir / f"audio_{audio.filename}"
        out_video = workdir / "result.mp4"

        # save files
        with open(face_path, "wb") as f:
            content = await face.read()
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="Face image file is empty")
            f.write(content)
        with open(clothes_path, "wb") as f:
            content = await clothes.read()
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="Clothes image file is empty")
            f.write(content)
        with open(audio_path, "wb") as f:
            content = await audio.read()
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="Audio file is empty")
            f.write(content)

        # run pipeline (virtual try-on + talking avatar)
        run_pipeline(str(face_path), str(clothes_path), str(audio_path), str(out_video), workdir=str(workdir))

        if not out_video.exists():
            raise HTTPException(status_code=500, detail="Pipeline failed to create video")
        
        # Save result path info (optional: you can log this)
        result_info = {
            "run_id": run_id,
            "result_path": str(out_video),
            "workdir": str(workdir),
            "timestamp": timestamp
        }
        print(f"Result saved to: {out_video}")
        
        # Note: Files are kept in results folder, not cleaned up automatically
        # You can manually clean old results or set up a cleanup job if needed
        
        # return file response
        return FileResponse(
            path=str(out_video), 
            media_type="video/mp4", 
            filename=f"avatar_{run_id}.mp4"
        )
    except HTTPException:
        # Cleanup on error
        if workdir.exists():
            shutil.rmtree(workdir, ignore_errors=True)
        raise
    except Exception as e:
        # Cleanup on error
        if workdir.exists():
            shutil.rmtree(workdir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
