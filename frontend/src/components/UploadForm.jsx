import React, { useState } from "react";
import axios from "axios";

export default function UploadForm() {
  const [face, setFace] = useState(null);
  const [clothes, setClothes] = useState(null);
  const [audio, setAudio] = useState(null);
  const [status, setStatus] = useState("");
  const [videoUrl, setVideoUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [facePreview, setFacePreview] = useState(null);
  const [clothesPreview, setClothesPreview] = useState(null);

  const handleFaceChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError("Face image must be less than 10MB");
        return;
      }
      // Validate file type
      if (!file.type.startsWith("image/")) {
        setError("Face must be an image file");
        return;
      }
      setFace(file);
      setError(null);
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => setFacePreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleClothesChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        setError("Clothes image must be less than 10MB");
        return;
      }
      if (!file.type.startsWith("image/")) {
        setError("Clothes must be an image file");
        return;
      }
      setClothes(file);
      setError(null);
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => setClothesPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleAudioChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 50 * 1024 * 1024) {
        setError("Audio file must be less than 50MB");
        return;
      }
      if (!file.type.startsWith("audio/")) {
        setError("Audio must be an audio file");
        return;
      }
      setAudio(file);
      setError(null);
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    
    if (!face || !clothes || !audio) {
      setError("Please provide all three files.");
      return;
    }

    setIsLoading(true);
    setStatus("Uploading files...");
    setVideoUrl(null);
    
    const form = new FormData();
    form.append("face", face);
    form.append("clothes", clothes);
    form.append("audio", audio);

    try {
      setStatus("Generating avatar (this may take a while)...");
      const resp = await axios.post("http://localhost:8000/generate-avatar", form, {
        responseType: "blob",
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 300000, // 5 minutes timeout
      });
      
      // Convert blob to object URL
      const blob = new Blob([resp.data], { type: "video/mp4" });
      const url = window.URL.createObjectURL(blob);
      setVideoUrl(url);
      setStatus("Done! Your avatar video is ready.");
    } catch (err) {
      console.error(err);
      let errorMessage = "An error occurred";
      
      if (err.response) {
        // Server responded with error
        if (err.response.data instanceof Blob) {
          // Try to read error message from blob
          const text = await err.response.data.text();
          try {
            const json = JSON.parse(text);
            errorMessage = json.detail || errorMessage;
          } catch {
            errorMessage = text || errorMessage;
          }
        } else {
          errorMessage = err.response.data?.detail || err.response.statusText || errorMessage;
        }
      } else if (err.request) {
        errorMessage = "No response from server. Is the backend running?";
      } else {
        errorMessage = err.message || errorMessage;
      }
      
      setError(errorMessage);
      setStatus(`Error: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setFace(null);
    setClothes(null);
    setAudio(null);
    setStatus("");
    setVideoUrl(null);
    setError(null);
    setFacePreview(null);
    setClothesPreview(null);
    // Reset file inputs
    document.querySelectorAll('input[type="file"]').forEach(input => input.value = '');
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <form onSubmit={submit} style={{ marginBottom: 24 }}>
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", marginBottom: 8, fontWeight: 500 }}>
            Face Photo (JPEG/PNG, max 10MB):
          </label>
          <input
            type="file"
            accept="image/jpeg,image/png,image/jpg"
            onChange={handleFaceChange}
            disabled={isLoading}
            style={{ width: "100%", padding: 8 }}
          />
          {facePreview && (
            <img
              src={facePreview}
              alt="Face preview"
              style={{
                marginTop: 8,
                maxWidth: 200,
                maxHeight: 200,
                borderRadius: 8,
                border: "1px solid #ccc",
              }}
            />
          )}
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", marginBottom: 8, fontWeight: 500 }}>
            Clothes Sample (PNG/JPEG, max 10MB):
          </label>
          <input
            type="file"
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleClothesChange}
            disabled={isLoading}
            style={{ width: "100%", padding: 8 }}
          />
          {clothesPreview && (
            <img
              src={clothesPreview}
              alt="Clothes preview"
              style={{
                marginTop: 8,
                maxWidth: 200,
                maxHeight: 200,
                borderRadius: 8,
                border: "1px solid #ccc",
              }}
            />
          )}
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", marginBottom: 8, fontWeight: 500 }}>
            Audio File (WAV/MP3, max 50MB):
          </label>
          <input
            type="file"
            accept="audio/wav,audio/mp3,audio/mpeg,audio/m4a,audio/aac"
            onChange={handleAudioChange}
            disabled={isLoading}
            style={{ width: "100%", padding: 8 }}
          />
          {audio && (
            <p style={{ marginTop: 8, fontSize: 14, color: "#666" }}>
              Selected: {audio.name} ({(audio.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}
        </div>

        <div style={{ display: "flex", gap: 12 }}>
          <button
            type="submit"
            disabled={isLoading || !face || !clothes || !audio}
            style={{
              padding: "12px 24px",
              fontSize: 16,
              fontWeight: 600,
              backgroundColor: isLoading ? "#ccc" : "#646cff",
              color: "white",
              border: "none",
              borderRadius: 8,
              cursor: isLoading ? "not-allowed" : "pointer",
              flex: 1,
            }}
          >
            {isLoading ? "Generating..." : "Generate Avatar"}
          </button>
          {!isLoading && (face || clothes || audio || videoUrl) && (
            <button
              type="button"
              onClick={resetForm}
              style={{
                padding: "12px 24px",
                fontSize: 16,
                backgroundColor: "#f0f0f0",
                border: "1px solid #ccc",
                borderRadius: 8,
                cursor: "pointer",
              }}
            >
              Reset
            </button>
          )}
        </div>
      </form>

      {error && (
        <div
          style={{
            padding: 12,
            backgroundColor: "#fee",
            border: "1px solid #fcc",
            borderRadius: 8,
            color: "#c33",
            marginBottom: 20,
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      {status && !error && (
        <div
          style={{
            padding: 12,
            backgroundColor: isLoading ? "#eef" : "#efe",
            border: `1px solid ${isLoading ? "#ccf" : "#cfc"}`,
            borderRadius: 8,
            color: isLoading ? "#339" : "#363",
            marginBottom: 20,
          }}
        >
          {isLoading && "⏳ "}
          {status}
        </div>
      )}

      {videoUrl && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ marginBottom: 12 }}>Generated Avatar Video:</h3>
          <video
            controls
            width="100%"
            style={{ maxWidth: 800, borderRadius: 8, boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}
            src={videoUrl}
          />
          <div style={{ marginTop: 12 }}>
            <a
              href={videoUrl}
              download="avatar.mp4"
              style={{
                display: "inline-block",
                padding: "10px 20px",
                backgroundColor: "#646cff",
                color: "white",
                textDecoration: "none",
                borderRadius: 8,
                fontWeight: 500,
              }}
            >
              Download Video
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
