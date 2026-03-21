import React from "react";
import UploadForm from "./components/UploadForm";

export default function App() {
  return (
    <div style={{ 
      maxWidth: 900, 
      margin: "40px auto", 
      fontFamily: "system-ui, -apple-system, sans-serif",
      padding: "0 20px"
    }}>
      <header style={{ textAlign: "center", marginBottom: 40 }}>
        <h1 style={{ 
          fontSize: "2.5em", 
          marginBottom: 10,
          background: "linear-gradient(135deg, #646cff 0%, #535bf2 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text"
        }}>
          Talking Avatar Generator
        </h1>
        <p style={{ fontSize: "1.1em", color: "#666", marginTop: 10 }}>
          Create talking avatars by combining face photos, clothing images, and audio files
        </p>
      </header>
      <UploadForm />
    </div>
  );
}
