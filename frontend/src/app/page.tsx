"use client";

import { useEffect, useState } from "react";
import { healthCheck } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";
import { AnalysisForm } from "@/components/meddx/AnalysisForm";
import { Footer } from "@/components/meddx/Footer";
import { Header } from "@/components/meddx/Header";
import { HeroSection } from "@/components/meddx/HeroSection";
import { IntroOverlay } from "@/components/meddx/IntroOverlay";
import { ResultsDashboard } from "@/components/meddx/ResultsDashboard";

export default function Home() {
  const [showIntro, setShowIntro] = useState(true);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    void healthCheck().then(setBackendOnline).catch(() => setBackendOnline(false));
  }, []);

  return (
    <main className="min-h-screen bg-[#F8FAFC] text-[#0F172A]">
      {showIntro && <IntroOverlay onContinue={() => setShowIntro(false)} />}
      <Header backendOnline={backendOnline} />
      <div className="mx-auto max-w-[1440px] space-y-20 px-4 py-6 md:px-8 md:py-9">
        <HeroSection />
        <AnalysisForm onResult={setResult} />
        {result && <ResultsDashboard result={result} />}
      </div>
      <Footer />
    </main>
  );
}
