// SoundContext.jsx
import React, { createContext, useContext, useState, useEffect, useRef, useCallback, useMemo } from 'react';

const SoundContext = createContext();
const OFF_INDEX = 0;

const TRACKS = [
  { label: 'OFF', src: null, gain: 0 },
  { label: 'BG 1', src: new URL('../assets/sounds/ambient-loop-1.mp3', import.meta.url).href, gain: 0.2 },
  { label: 'BG 2', src: new URL('../assets/sounds/ambient-loop-2.mp3', import.meta.url).href, gain: 0.4 },
  { label: 'BG 3', src: new URL('../assets/sounds/ambient-loop-3.mp3', import.meta.url).href, gain: 0.4 },
];

export function SoundProvider({ children, initialVolume = 0.4 }) {
  const [isMuted, setIsMuted] = useState(true);
  const [sfxMuted, setSfxMuted] = useState(false);
  const [trackIndex, setTrackIndex] = useState(OFF_INDEX);
  const [volume, setVolume] = useState(initialVolume);
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [nowPlaying, setNowPlaying] = useState(TRACKS[OFF_INDEX].label);
  const [isPlaying, setIsPlaying] = useState(false);

  const mainAudioRef = useRef(null);
  const clickRef = useRef(null);
  const fadeRef = useRef(null);
  const transitionLock = useRef(false);

  const CLICK_SRC = useMemo(() => new URL('../assets/sounds/playPop.mp3', import.meta.url).href, []);

  // Load saved settings
  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem('sound-settings') || '{}');
    setIsMuted(saved.isMuted ?? true);
    setSfxMuted(saved.sfxMuted ?? false);
    setVolume(saved.volume ?? initialVolume);
    setTrackIndex(saved.trackIndex ?? OFF_INDEX);
  }, [initialVolume]);

  // Persist settings
  useEffect(() => {
    localStorage.setItem('sound-settings', JSON.stringify({ isMuted, sfxMuted, volume, trackIndex }));
  }, [isMuted, sfxMuted, volume, trackIndex]);

  // Initialize audio elements
  useEffect(() => {
    const audio = new Audio();
    audio.loop = true;
    audio.volume = 0;
    mainAudioRef.current = audio;

    const clickAudio = new Audio(CLICK_SRC);
    clickAudio.preload = 'auto';
    clickRef.current = clickAudio;

    return () => {
      audio.pause();
      cancelAnimationFrame(fadeRef.current);
    };
  }, [CLICK_SRC]);

  // Fade helper
  const fadeTo = useCallback((audio, target, duration = 800) => {
    cancelAnimationFrame(fadeRef.current);
    const start = audio.volume;
    const delta = target - start;
    const t0 = performance.now();
    const step = (now) => {
      const t = Math.min((now - t0) / duration, 1);
      audio.volume = start + delta * t;
      if (t < 1) fadeRef.current = requestAnimationFrame(step);
    };
    fadeRef.current = requestAnimationFrame(step);
  }, []);

  // Apply real-time volume & gain
  useEffect(() => {
    const audio = mainAudioRef.current;
    const gain = TRACKS[trackIndex].gain;
    audio.volume = volume * gain;
  }, [volume, trackIndex]);

  // Play a specific ambient track
  const playAmbientTrack = useCallback((index) => {
    if (transitionLock.current) return;
    transitionLock.current = true;
    const audio = mainAudioRef.current;
    const track = TRACKS[index];
    if (!track.src || isMuted || !isUnlocked) {
      fadeTo(audio, 0);
      setTimeout(() => audio.pause(), 500);
      setTrackIndex(OFF_INDEX);
      setNowPlaying(TRACKS[OFF_INDEX].label);
      setIsPlaying(false);
      transitionLock.current = false;
      return;
    }
    if (audio.src !== track.src) {
      audio.pause();
      audio.src = track.src;
      audio.currentTime = 0;
    }
    audio.play().then(() => {
      fadeTo(audio, volume * track.gain);
      setTrackIndex(index);
      setNowPlaying(track.label);
      setIsPlaying(true);
    }).catch((e) => console.warn('Playback error', e))
      .finally(() => { transitionLock.current = false; });
  }, [isMuted, isUnlocked, volume, fadeTo]);

  // Toggle play/pause
  const togglePlay = useCallback(() => {
    const audio = mainAudioRef.current;
    const track = TRACKS[trackIndex];
    if (!track.src || isMuted || !isUnlocked) return;
    if (audio.paused) {
      audio.play().then(() => {
        fadeTo(audio, volume * track.gain);
        setIsPlaying(true);
      }).catch((e) => console.warn('Play failed', e));
    } else {
      fadeTo(audio, 0);
      setTimeout(() => audio.pause(), 400);
      setIsPlaying(false);
    }
  }, [trackIndex, isMuted, isUnlocked, volume, fadeTo]);

  // Next/Prev
  const nextTrack = useCallback(() => playAmbientTrack((trackIndex + 1) % TRACKS.length), [trackIndex, playAmbientTrack]);
  const prevTrack = useCallback(() => playAmbientTrack((trackIndex - 1 + TRACKS.length) % TRACKS.length), [trackIndex, playAmbientTrack]);

  // Cycle ambient state
  const toggleAmbient = useCallback(() => {
    const next = (trackIndex + 1) % TRACKS.length;
    playAmbientTrack(next);
    setIsMuted(next === OFF_INDEX);
  }, [trackIndex, playAmbientTrack]);

  // Enable/Disable
  const enableSound = useCallback(() => {
    setIsMuted(false);
    setIsUnlocked(true);
    if (trackIndex !== OFF_INDEX) playAmbientTrack(trackIndex);
  }, [trackIndex, playAmbientTrack]);

  const disableSound = useCallback(() => {
    setIsMuted(true);
    const audio = mainAudioRef.current;
    fadeTo(audio, 0);
    setTimeout(() => audio.pause(), 400);
    setIsPlaying(false);
    setTrackIndex(OFF_INDEX);
    setNowPlaying(TRACKS[OFF_INDEX].label);
  }, [fadeTo]);

  const toggleMute = useCallback(() => (isMuted ? enableSound() : disableSound()), [isMuted, enableSound, disableSound]);

  // SFX
  const playClick = useCallback(() => {
    const click = clickRef.current;
    if (!click || sfxMuted || !isUnlocked) return;
    click.pause();
    click.currentTime = 0;
    click.volume = volume;
    click.play().catch((e) => console.warn('Click error', e));
  }, [sfxMuted, isUnlocked, volume]);

  // Unlock on first interaction
  useEffect(() => {
    const unlock = () => {
      setIsUnlocked(true);
      if (!isMuted && trackIndex !== OFF_INDEX) playAmbientTrack(trackIndex);
    };
    window.addEventListener('click', unlock, { once: true });
    window.addEventListener('keydown', unlock, { once: true });
    return () => {
      window.removeEventListener('click', unlock);
      window.removeEventListener('keydown', unlock);
    };
  }, [isMuted, trackIndex, playAmbientTrack]);

  return (
    <SoundContext.Provider value={{
      isMuted,
      sfxMuted,
      volume,
      setVolume,
      trackIndex,
      setTrackIndex,
      nowPlaying,
      isPlaying,
      playAmbientTrack,
      togglePlay,
      nextTrack,
      prevTrack,
      toggleAmbient,
      toggleMute,
      enableSound,
      disableSound,
      playClick,
      setSfxMuted,
      setIsMuted,
      isUnlocked,
    }}>
      {children}
    </SoundContext.Provider>
  );
}

export const useSound = () => useContext(SoundContext);
