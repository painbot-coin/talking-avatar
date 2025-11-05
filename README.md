# Talking Avatar Generator

A web application that generates talking avatars by combining face photos, clothing images, and audio files. The system performs virtual try-on and creates a lip-synced talking avatar video.

## Features

- Upload face photo, clothes image, and audio file
- **AI-Powered Virtual Try-On**: Uses Replicate, Hugging Face, or other AI services for realistic clothing overlay
- **AI-Powered Talking Avatar**: Uses Replicate, HeyGen, D-ID, or Hugging Face for lip-synced video generation
- Real-time preview of uploaded images
- Download generated avatar videos
- Flexible service selection - switch between different AI providers

## Project Structure

```
talking-avatar/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── main.py      # FastAPI application and endpoints
│   │   ├── pipeline.py  # Avatar generation pipeline
│   │   └── utils.py     # Utility functions
│   └── requirements.txt # Python dependencies
└── frontend/         # React frontend
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   │   └── UploadForm.jsx
    │   └── main.jsx
    └── package.json
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure AI Services** (Required for AI features):
   
   Create a `.env` file in the `backend` directory:
   ```bash
   cp env.example .env
   ```
   
   Then edit `.env` and add your API keys:
   
   **Recommended: Replicate API** (Easiest to use)
   - Sign up at https://replicate.com
   - Get your API token from https://replicate.com/account/api-tokens
   - Add to `.env`: `REPLICATE_API_TOKEN=your_token_here`
   
   **Alternative Services:**
   - **HeyGen**: For talking avatars - https://www.heygen.com/
   - **D-ID**: For talking avatars - https://studio.d-id.com/
   - **Hugging Face**: For both services - https://huggingface.co/settings/tokens
   
   **Service Selection:**
   - Set `VIRTUAL_TRYON_SERVICE=replicate` (or `huggingface`, `fallback`)
   - Set `TALKING_AVATAR_SERVICE=replicate` (or `heygen`, `did`, `huggingface`, `fallback`)

6. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173` (or the port shown in the terminal)

## Usage

1. Start both backend and frontend servers
2. Open the frontend URL in your browser
3. Upload:
   - A face photo (JPEG/PNG, max 10MB)
   - A clothes image (PNG/JPEG, max 10MB)
   - An audio file (WAV/MP3, max 50MB)
4. Click "Generate Avatar"
5. Wait for processing (may take a while)
6. Download or view the generated video

## API Endpoints

### POST `/generate-avatar`

Generates a talking avatar video from uploaded files.

**Request:**
- `face`: Image file (multipart/form-data)
- `clothes`: Image file (multipart/form-data)
- `audio`: Audio file (multipart/form-data)

**Response:**
- Video file (MP4)

## Technical Details

### Pipeline

The avatar generation pipeline consists of two main steps:

1. **Virtual Try-On**: Uses AI services (Replicate, Hugging Face) to realistically overlay clothes onto the face image
2. **Talking Avatar**: Uses AI services (Replicate, HeyGen, D-ID, Hugging Face) to generate lip-synced video from the avatar image and audio

### AI Service Integration

The system supports multiple AI service providers:

- **Replicate** (Recommended): Easy-to-use API with pre-trained models
  - Virtual Try-On: IDM-VTON model
  - Talking Avatar: Wav2Lip, SadTalker models
  
- **Hugging Face**: Open-source models via Inference API
  
- **HeyGen / D-ID**: Commercial talking avatar services
  
- **Fallback**: Basic implementation when no API keys are configured

The system automatically falls back to basic implementations if AI services fail or are not configured.

### Dependencies

**Backend:**
- FastAPI: Web framework
- Uvicorn: ASGI server
- Pillow: Image processing
- MoviePy: Video processing
- NumPy: Numerical operations

**Frontend:**
- React: UI framework
- Axios: HTTP client
- Vite: Build tool

## Development Notes

- Temporary files are stored in the system temp directory
- Files are automatically cleaned up after processing
- CORS is enabled for local development
- The pipeline supports Windows, Linux, and macOS

## Future Improvements

- Integrate real virtual try-on models (e.g., IDM-VTON, OOTDiffusion)
- Integrate real talking avatar models (e.g., SadTalker, Wav2Lip, HeyGen)
- Add progress tracking for long-running operations
- Support for video input/output
- Batch processing capabilities
- User authentication and history

