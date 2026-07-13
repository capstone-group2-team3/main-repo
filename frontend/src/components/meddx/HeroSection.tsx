"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Activity, ShieldCheck } from "lucide-react";

const safety = "For clinicians only — supports review, not diagnosis or prescribing.";

const heroImages = [
  {
    src: "/assets/pexels-gustavo-fring-3985163.jpg",
    alt: "Clinical team ready for emergency lab review",
    position: "object-[50%_48%]",
  },
  {
    src: "/assets/pexels-karola-g-8539140.jpg",
    alt: "Doctor preparing clinical supplies",
    position: "object-[50%_42%]",
  },
  {
    src: "/assets/pexels-mikhail-nilov-9243372.jpg",
    alt: "Doctor reviewing patient information",
    position: "object-[52%_44%]",
  },
  {
    src: "/assets/pexels-pavel-danilyuk-8442611.jpg",
    alt: "Doctors reviewing clinical information",
    position: "object-[46%_45%]",
  },
  {
    src: "/assets/pexels-polina-tankilevitch-3735709.jpg",
    alt: "Laboratory sample analysis",
    position: "object-[47%_52%]",
  },
  {
    src: "/assets/pexels-thirdman-7659690.jpg",
    alt: "Clinician reviewing medical records",
    position: "object-[50%_40%]",
  },
] as const;

type HeroImage = {
  src: string;
  alt: string;
  position: string;
};

export function HeroSection() {
  const [activeImage, setActiveImage] = useState(0);
  const currentImage: HeroImage = heroImages[activeImage];

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActiveImage((index) => (index + 1) % heroImages.length);
    }, 3000);

    return () => window.clearInterval(interval);
  }, []);

  return (
    <section id="overview" className="hero-shell relative flex h-[520px] scroll-mt-24 items-center overflow-hidden rounded-3xl border border-white/15 bg-slate-950 px-6 py-6 shadow-[0_32px_90px_rgba(15,23,42,.28)] md:h-[460px] md:px-10 md:py-8 lg:h-[470px] xl:h-[480px] xl:px-14">
      <AnimatePresence mode="sync">
        <motion.div
          key={currentImage.src}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.2, ease: "easeInOut" }}
          className="absolute -inset-8"
        >
          <motion.div
            initial={{ scale: 1.04, x: 30 }}
            animate={{ scale: 1.08, x: -30 }}
            transition={{ duration: 3.2, ease: "easeInOut" }}
            className="relative h-full w-full"
          >
            <Image
              src={currentImage.src}
              alt={currentImage.alt}
              fill
              priority={activeImage === 0}
              className={`object-cover ${currentImage.position}`}
              sizes="100vw"
            />
          </motion.div>
        </motion.div>
      </AnimatePresence>

      <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(15,23,42,0.95)_0%,rgba(15,23,42,0.78)_46%,rgba(15,118,110,0.30)_100%)] md:bg-[linear-gradient(90deg,rgba(15,23,42,0.95)_0%,rgba(15,23,42,0.70)_52%,rgba(15,118,110,0.30)_100%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_82%_26%,rgba(34,211,238,0.35),transparent_34%),radial-gradient(circle_at_92%_80%,rgba(45,212,191,0.24),transparent_32%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(2,6,23,.12),rgba(2,6,23,.22))]" />

      <div className="relative z-10 max-w-[620px] text-left">
        <div className="mb-4 flex flex-wrap gap-2">
          <span className="inline-flex items-center gap-2 rounded-full border border-cyan-200/20 bg-white/10 px-3.5 py-1.5 text-xs font-bold uppercase tracking-[.16em] text-cyan-100 shadow-lg shadow-cyan-950/15 backdrop-blur">
            <Activity size={14} /> Focused clinical review
          </span>
          <span className="rounded-full border border-white/10 bg-white/[0.08] px-3.5 py-1.5 text-xs font-bold uppercase tracking-[.16em] text-teal-50/90 backdrop-blur">
            Lab Signals
          </span>
          <span className="rounded-full border border-white/10 bg-white/[0.08] px-3.5 py-1.5 text-xs font-bold uppercase tracking-[.16em] text-teal-50/90 backdrop-blur">
            Safety First
          </span>
        </div>
        <h1 className="text-4xl font-bold tracking-[-.055em] text-white drop-shadow-2xl sm:text-5xl lg:text-6xl">MedDx Assistant</h1>
        <p className="mt-3 text-lg text-cyan-50 md:text-xl">Doctor-Facing Emergency &amp; Lab Report Dashboard</p>
        <p className="mt-4 max-w-xl text-sm leading-6 text-slate-100/90 md:text-base">
          Review lab findings, abnormal signals, clinical warnings, and missing evidence in one focused doctor-facing dashboard.
        </p>
        <div className="mt-4 flex max-w-xl items-start gap-2 rounded-2xl border border-white/10 bg-slate-950/35 px-3.5 py-2.5 text-left text-sm leading-6 text-teal-50 shadow-2xl shadow-slate-950/20 backdrop-blur-md">
          <ShieldCheck className="mt-0.5 shrink-0 text-cyan-200" size={17} />
          {safety}
        </div>
        <a href="#analysis" className="premium-button mt-5 inline-flex">
          Start Lab Analysis <ArrowRight size={18} />
        </a>
      </div>

      <div className="absolute bottom-5 right-5 z-20 flex items-center gap-2 rounded-full border border-white/10 bg-slate-950/35 px-3 py-2 shadow-2xl shadow-slate-950/20 backdrop-blur-md md:bottom-7 md:right-7">
        {heroImages.map((image, index) => (
          <button
            key={image.src}
            type="button"
            aria-label={`Show hero image ${index + 1}`}
            aria-pressed={activeImage === index}
            onClick={() => setActiveImage(index)}
            className={`h-2.5 rounded-full transition-all duration-300 ${
              activeImage === index ? "w-7 bg-cyan-300 shadow-[0_0_18px_rgba(103,232,249,.8)]" : "w-2.5 bg-white/45 hover:bg-white/75"
            }`}
          />
        ))}
      </div>
    </section>
  );
}
