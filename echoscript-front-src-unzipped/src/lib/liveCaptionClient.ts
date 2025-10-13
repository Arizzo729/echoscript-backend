// src/lib/liveCaptionClient.ts
export function openTranscribeSocket(): WebSocket {
  const wsUrl = (location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/api/v1/transcribe/stream";
  return new WebSocket(wsUrl);
}
