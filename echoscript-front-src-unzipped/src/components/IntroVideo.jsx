// src/components/IntroVideo.jsx
import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion, useAnimation } from 'framer-motion';
import { Volume2, VolumeX } from 'lucide-react';
import PropTypes from 'prop-types';
import introVideo from '../assets/videos/intro.mp4';

const overlayVariants = {
  visible: { opacity: 1, transition: { duration: 0.8 } },
  hidden: { opacity: 0, transition: { duration: 0.8 } },
};

const controlsVariants = {
  hidden: { opacity: 0, y: 20, transition: { duration: 0.4 } },
  visible: i => ({
    opacity: 1, y: 0,
    transition: { delay: 0.2 + i * 0.1, duration: 0.5, ease: 'easeOut' },
  }),
};

export default function IntroVideo({
  poster,
  skipAfter = 3,
  skipLabel = 'Skip Intro',
  sources = [{ src: introVideo, type: 'video/mp4' }],
  onFinish,
  playOnceKey = 'intro_seen_v1',      // <-- plays once per user (stored in localStorage)
  force = false,                      // set true to force-show (for QA)
}) {
  const videoRef = useRef(null);
  const controlsAnim = useAnimation();
  const hasPlayed = useRef(false);

  const [loading, setLoading] = useState(true);
  const [muted, setMuted] = useState(true); // Start muted for Safari
  const [showIntro, setShowIntro] = useState(false);
  const defaultVolume = 0.3;

  useEffect(() => {
    const alreadySeen =
      !force &&
      typeof window !== 'undefined' &&
      (window.__introPlayed || localStorage.getItem(playOnceKey) === '1');

    if (!alreadySeen) {
      window.__introPlayed = true;     // in-page
      setShowIntro(true);
    }
  }, [force, playOnceKey]);

  useEffect(() => {
    if (showIntro && !hasPlayed.current) {
      const v = videoRef.current;
      hasPlayed.current = true;
      if (v) {
        v.playsInline = true;
        v.preload = 'auto';
        v.defaultPlaybackRate = 1;
        v.volume = defaultVolume;
        v.muted = true; // necessary for autoplay

        if (v.children.length === 0) {
          sources.forEach(({ src, type }) => {
            const source = document.createElement('source');
            source.src = src;
            source.type = type;
            v.appendChild(source);
          });
        }

        v.play().catch(() => { /* autoplay might need user gesture on some browsers */ });
      }
    }
  }, [showIntro, sources]);

  useEffect(() => {
    const v = videoRef.current;
    if (v) v.muted = muted;
  }, [muted]);

  useEffect(() => {
    if (!showIntro) return;
    controlsAnim.start('hidden').then(() =>
      setTimeout(() => controlsAnim.start('visible'), skipAfter * 1000)
    );
  }, [showIntro, skipAfter, controlsAnim]);

  const handleCanPlay = () => setLoading(false);

  const toggleMute = () => {
    const v = videoRef.current;
    setMuted(prev => {
      const next = !prev;
      if (v) v.muted = next;
      return next;
    });
  };

  const exitIntro = async () => {
    try { localStorage.setItem(playOnceKey, '1'); } catch {}
    await controlsAnim.start('hidden');
    setShowIntro(false);
    onFinish?.();
  };

  const handleSkip = () => {
    const v = videoRef.current;
    if (v) v.pause();
    exitIntro();
  };

  return (
    <AnimatePresence onExitComplete={onFinish}>
      {showIntro && (
        <motion.div
          className="fixed inset-0 z-[9999] bg-black flex items-center justify-center"
          variants={overlayVariants}
          initial="visible"
          animate="visible"
          exit="hidden"
        >
          {loading && (
            <motion.div
              className="absolute inset-0 flex items-center justify-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <div className="animate-spin border-4 border-teal-500 border-t-transparent rounded-full h-12 w-12" />
            </motion.div>
          )}

          <video
            ref={videoRef}
            className="w-full h-full object-cover"
            playsInline
            preload="auto"
            poster={poster}
            muted={muted}
            onCanPlay={handleCanPlay}
            onEnded={exitIntro}
          />

          <motion.div
            className="absolute bottom-6 right-6 flex space-x-3"
            variants={controlsVariants}
            initial="hidden"
            animate={controlsAnim}
          >
            <motion.button
              onClick={handleSkip}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="bg-teal-500/60 hover:bg-teal-500/80 text-white text-sm font-medium py-2 px-4 rounded-lg shadow-lg"
            >
              {skipLabel}
            </motion.button>
            <motion.button
              onClick={toggleMute}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="bg-white/20 hover:bg-white/40 text-white text-sm font-medium py-2 px-4 rounded-lg shadow-lg flex items-center space-x-1"
            >
              {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
              <span>{muted ? 'Unmute' : 'Mute'}</span>
            </motion.button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

IntroVideo.propTypes = {
  poster: PropTypes.string,
  skipAfter: PropTypes.number,
  skipLabel: PropTypes.string,
  sources: PropTypes.arrayOf(
    PropTypes.shape({ src: PropTypes.string.isRequired, type: PropTypes.string.isRequired })
  ),
  onFinish: PropTypes.func,
  playOnceKey: PropTypes.string,
  force: PropTypes.bool,
};
