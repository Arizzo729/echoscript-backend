// src/components/VideoWithSubs.tsx
import { useRef, useState } from "react";

// Default to the Netlify proxy /api; allow override via VITE_API_BASE_URL
const API_BASE = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/+$/, "");

export default function VideoWithSubs() {
  const [videoUrl, setVideoUrl] = useState<string>("");
  const [trackUrl, setTrackUrl] = useState<string>("");
  const videoRef = useRef<HTMLVideoElement|null>(null);

  const onVideoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setVideoUrl(URL.createObjectURL(f));
  };

  const makeSubtitles = async () => {
    const input = document.getElementById("fileVideo") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);

    // Hit the /api/subtitles route (backend mounts under /api/* and /v1/* separately)
    const res = await fetch(`${API_BASE}/subtitles`, { method: "POST", body: fd, credentials: "include" });
    if (!res.ok) { alert("Failed to make subtitles"); return; }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    setTrackUrl(url);
  };

  return (
    <div className="p-4 space-y-3">
      <h2 className="text-xl font-semibold">Video + Subtitles</h2>
      <input id="fileVideo" type="file" accept="video/*" onChange={onVideoSelect} />
      <button onClick={makeSubtitles} className="px-3 py-2 rounded bg-teal-600 text-white">Generate Subtitles</button>

      {videoUrl && (
        <video ref={videoRef} className="w-full rounded-lg mt-3" controls crossOrigin="anonymous">
          <source src={videoUrl} />
          {trackUrl && (
            <track kind="subtitles" src={trackUrl} srcLang="en" label="English" default />
          )}
        </video>
      )}
    </div>
  );
}

