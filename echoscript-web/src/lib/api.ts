export const API_BASE = import.meta.env.VITE_API_BASE as string;

export type JobOut = {
  job_id: string;
  status: string;
  filename: string;
  transcript?: string;
};

export async function transcribe(file: File, language?: string): Promise<JobOut> {
  const fd = new FormData();
  fd.append("file", file); // FormData is the standard way to send files (multipart/form-data) :contentReference[oaicite:3]{index=3}
  const url = language
    ? `${API_BASE}/api/v1/transcribe?language=${encodeURIComponent(language)}`
    : `${API_BASE}/api/v1/transcribe`;

  const res = await fetch(url, { method: "POST", body: fd });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
