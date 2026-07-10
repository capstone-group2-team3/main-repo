"use client";

import { useRef, useState } from "react";
import { ArrowRight, ShieldCheck, Volume2, VolumeX, X } from "lucide-react";

const safety = "For clinicians only — supports review, not diagnosis or prescribing.";

export function IntroOverlay({ onContinue }: { onContinue: () => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [soundOn, setSoundOn] = useState(false);
  const [playbackError, setPlaybackError] = useState("");

  async function playWithSound() {
    const video = videoRef.current;
    if (!video) return;
    setPlaybackError("");
    video.muted = false;
    video.volume = 1;
    video.currentTime = 0;
    try {
      await video.play();
      setSoundOn(true);
    } catch {
      video.muted = true;
      setSoundOn(false);
      setPlaybackError("Your browser blocked autoplay with sound. Click Play Intro with Sound.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-[#07111f]/95 p-4 backdrop-blur-xl">
      <div className="absolute inset-0 intro-grid opacity-30" />
      <button
        type="button"
        onClick={onContinue}
        className="absolute right-5 top-5 z-10 flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-4 py-2 text-sm text-white transition hover:bg-white/20"
      >
        <X size={16} /> Skip Intro
      </button>
      <div className="relative grid w-full max-w-6xl items-center gap-8 rounded-[2rem] border border-white/15 bg-white/[0.07] p-5 shadow-2xl md:grid-cols-[1fr_1.1fr] md:p-9">
        <div>
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">
            <ShieldCheck size={14} /> Clinical decision support
          </div>
          <h1 className="text-4xl font-bold tracking-[-0.04em] text-white md:text-6xl">MedDx Assistant</h1>
          <p className="mt-4 max-w-lg text-xl leading-relaxed text-slate-200">
            Doctor-Facing Emergency &amp; Lab Report Dashboard
          </p>
          <p className="mt-6 text-sm leading-6 text-teal-100">{safety}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button type="button" onClick={onContinue} className="premium-button">
              Start Lab Analysis <ArrowRight size={18} />
            </button>
            <button type="button" onClick={onContinue} className="rounded-2xl border border-white/20 bg-white/10 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/20">
              Continue to Dashboard
            </button>
          </div>
        </div>
        <div className="overflow-hidden rounded-3xl border border-white/20 bg-slate-950/60 p-2 shadow-[0_25px_80px_rgba(6,182,212,0.15)]">
          <div className="relative">
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              preload="auto"
              onEnded={onContinue}
              onVolumeChange={(event) => setSoundOn(!event.currentTarget.muted && event.currentTarget.volume > 0)}
              className="intro-video aspect-video w-full rounded-[1.15rem] object-cover"
              aria-label="MedDx Assistant introduction"
            >
              <source src="/assets/Video%20Project%204.mp4" type="video/mp4" />
            </video>
            <span className="absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-slate-950/75 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur">
              {soundOn ? <Volume2 size={14} /> : <VolumeX size={14} />}
              {soundOn ? "Sound On" : "Muted"}
            </span>
          </div>
          <button
            type="button"
            onClick={() => void playWithSound()}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-50"
          >
            <Volume2 size={17} /> Play Intro with Sound
          </button>
          {playbackError && <p role="alert" className="mt-2 rounded-xl bg-amber-400/10 px-3 py-2 text-xs text-amber-100">{playbackError}</p>}
        </div>
      </div>
    </div>
  );
}
