"use client";

import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Database,
  Download,
  FileText,
  GitBranch,
  Layers3,
  LineChart,
  Microscope,
  PlayCircle,
  Search,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Workflow,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Image from "next/image";
import { motion } from "framer-motion";

const basePath = "/main-repo";
const repositoryUrl = "https://github.com/capstone-group2-team3/main-repo";
const demoUrl = "#demo-video";
const presentationUrl = `${basePath}/MedDx-Assistant-Presentation.pdf`;

const metrics = [
  ["Top-3 Pattern Recall", "100%", "Clinical pattern coverage on held-out cases"],
  ["Evidence Grounding", "92.98%", "Retrieved sources aligned to matched patterns"],
  ["Critical Recall", "100%", "Critical cases protected by override logic"],
  ["Severity Accuracy", "63.16%", "Primary improvement area for calibration"],
  ["Safety Notice Presence", "100%", "Required clinician-only notice retained"],
  ["Average Latency", "~274 ms", "Mean end-to-end evaluation latency"],
];

type IconCard = [string, string, LucideIcon];

const technologies: IconCard[] = [
  ["Backend", "FastAPI, Python, SQLAlchemy, SQLite, Pydantic", Database],
  ["Frontend", "Next.js, React, TypeScript, Tailwind CSS, Framer Motion", Layers3],
  ["AI", "Fine-tuned DistilBERT, PubMedBERT embeddings, Transformers", BrainCircuit],
  ["Vector Search", "Qdrant semantic retrieval", Search],
  ["Infrastructure", "Docker and Docker Compose", Workflow],
];

const pipeline = [
  ["Normalize", "Lab names, aliases, units, symptoms, and panel requirements are standardized."],
  ["Analyze", "Reference ranges classify Normal, Low, High, Critical, and Unknown findings."],
  ["Score", "Clinical pattern logic ranks likely review patterns with evidence and missing labs."],
  ["Retrieve", "PubMedBERT embeddings query Qdrant for supporting medical knowledge chunks."],
  ["Prioritize", "Fine-tuned DistilBERT estimates severity with critical override and fallback."],
  ["Report", "Safety-sanitized Markdown, HTML, and PDF reports are generated for clinicians."],
];

const features: IconCard[] = [
  ["Laboratory review", "Panel-aware abnormal value detection with reference ranges.", Activity],
  ["Severity support", "Routine, Urgent, and Critical prioritization with protected override.", AlertTriangle],
  ["Evidence grounding", "Semantic search returns supporting snippets and similarity scores.", Search],
  ["Clinical patterns", "Ranked pattern cards show confidence, score, evidence, and sources.", LineChart],
  ["Professional reports", "Markdown, HTML, and embedded-font PDF reports for review.", FileText],
  ["Safety layer", "Unsafe language is sanitized and the mandatory notice is preserved.", ShieldCheck],
];

const screenshots = [
  ["Dashboard", "dashboard.png"],
  ["Severity Alert", "severity.png"],
  ["PDF Report", "report.png"],
  ["Charts", "charts.png"],
  ["Architecture", "architecture.png"],
  ["Hero", "hero.png"],
];

const team = [
  ["Hussam Rabaa", "Backend, database, AI/RAG/NLP, Docker, workflow, frontend support"],
  ["Deema", "AI evaluation, data analysis, RAG planning, product direction"],
  ["Rama", "Data engineering, ETL, semantic search, vector database, documentation"],
  ["Ali Alquraan", "ML/NLP, Docker, SQL, semantic search, RAG, API support"],
];

const challenges = [
  "Keeping severity safe while allowing the fine-tuned model to contribute useful prioritization.",
  "Grounding clinical pattern suggestions in retrievable evidence without using an LLM.",
  "Producing portfolio-ready PDF reports with stable typography and strict safety wording.",
  "Separating static configuration from runtime Docker volumes so model and reference data remain visible.",
];

const futureWork = [
  "Clinician-reviewed severity labels and larger held-out evaluation sets.",
  "Expanded panels with documented source permissions and richer evidence coverage.",
  "Authentication, audit logs, and privacy controls before any real deployment.",
  "Calibration work to improve non-critical severity accuracy while preserving Critical recall.",
];

function Section({
  id,
  eyebrow,
  title,
  children,
}: {
  id: string;
  eyebrow: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="section">
      <motion.div
        initial={{ opacity: 0, y: 22 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.55 }}
      >
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        {children}
      </motion.div>
    </section>
  );
}

export default function Home() {
  return (
    <main>
      <nav className="nav" aria-label="Primary navigation">
        <a href="#top" className="brand">
          <Stethoscope size={22} />
          MedDx Assistant
        </a>
        <div>
          <a href="#architecture">Architecture</a>
          <a href="#evaluation">Results</a>
          <a href="#screenshots">Screenshots</a>
          <a href="#team">Team</a>
        </div>
      </nav>

      <header id="top" className="hero">
        <div className="heroGrid">
          <motion.div
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="heroCopy"
          >
            <p className="pill">
              <Sparkles size={16} />
              AI.SPIRE Capstone Portfolio Artifact
            </p>
            <h1>MedDx Assistant</h1>
            <p className="subtitle">AI-Powered Clinical Laboratory Review & Decision Support System</p>
            <p className="description">
              A clinician-facing AI system that analyzes laboratory findings, detects abnormal values,
              identifies clinical patterns, retrieves supporting medical evidence using semantic search,
              estimates severity using a fine-tuned DistilBERT classifier, and generates professional
              Markdown, HTML, and PDF reports.
            </p>
            <p className="safety">For clinicians only — supports review, not diagnosis or prescribing.</p>
            <div className="actions">
              <a className="primary" href={repositoryUrl} target="_blank" rel="noreferrer">
                <GitBranch size={18} />
                View Repository
              </a>
              <a className="secondary" href={demoUrl}>
                <PlayCircle size={18} />
                Watch Demo
              </a>
              <a className="secondary" href={presentationUrl}>
                <Download size={18} />
                Download Presentation
              </a>
            </div>
          </motion.div>
          <motion.div
            className="heroVisual"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.15 }}
          >
            <Image
              src={`${basePath}/images/hero.png`}
              alt="MedDx Assistant dashboard preview placeholder"
              width={1200}
              height={760}
              priority
            />
            <div className="scanLine" />
          </motion.div>
        </div>
      </header>

      <Section id="overview" eyebrow="Project overview" title="A guarded AI workflow for laboratory review">
        <div className="overviewGrid">
          <div className="copyBlock">
            <p>
              MedDx Assistant combines deterministic laboratory analysis, semantic retrieval, and a
              fine-tuned severity classifier into a safety-first review workflow. It was built as an
              end-to-end capstone system with FastAPI, Next.js, Qdrant, Docker, and SQLite.
            </p>
          </div>
          <div className="copyBlock">
            <p>
              The product goal is fast, evidence-aware review support for clinicians. It avoids diagnosis
              and prescribing claims, preserves a mandatory safety notice, and frames outputs as review
              assistance rather than clinical determination.
            </p>
          </div>
        </div>
      </Section>

      <Section id="problem" eyebrow="Problem" title="Lab review can be slow, fragmented, and hard to ground">
        <div className="problemGrid">
          {[
            "Clinical reviewers compare values against ranges, panels, symptoms, and medical context.",
            "Abnormal combinations can require evidence lookup and careful severity prioritization.",
            "Educational AI prototypes often fail by overclaiming, under-grounding, or hiding safety limits.",
          ].map((item) => (
            <div className="premiumCard" key={item}>
              <Microscope />
              <p>{item}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="solution" eyebrow="Solution" title="Structured analysis, grounded evidence, safe reporting">
        <div className="solutionBand">
          <ShieldCheck />
          <p>
            MedDx Assistant normalizes inputs, classifies lab findings, scores clinical patterns, retrieves
            evidence, estimates severity, applies safety sanitization, and generates reports that retain the
            exact clinician-only safety statement.
          </p>
        </div>
      </Section>

      <Section id="architecture" eyebrow="Architecture" title="System architecture">
        <div className="architecture">
          <Image
            src={`${basePath}/images/architecture.png`}
            alt="Architecture diagram placeholder"
            width={1200}
            height={760}
          />
          <div className="architectureSteps">
            {["Next.js UI", "FastAPI API", "Agent pipeline", "DistilBERT severity", "PubMedBERT + Qdrant", "SQLite + reports"].map(
              (step) => (
                <span key={step}>{step}</span>
              ),
            )}
          </div>
        </div>
      </Section>

      <Section id="pipeline" eyebrow="AI pipeline" title="From lab values to clinician-ready report">
        <div className="timeline">
          {pipeline.map(([title, text], index) => (
            <motion.div
              className="timelineItem"
              key={title}
              initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: index * 0.04 }}
            >
              <span>{String(index + 1).padStart(2, "0")}</span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </Section>

      <Section id="technologies" eyebrow="Technologies" title="Production-shaped stack">
        <div className="techGrid">
          {technologies.map(([area, text, Icon]) => (
            <div className="techCard" key={String(area)}>
              <Icon />
              <h3>{area}</h3>
              <p>{text}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="features" eyebrow="Features" title="What the system does">
        <div className="featureGrid">
          {features.map(([title, text, Icon]) => (
            <div className="featureCard" key={String(title)}>
              <Icon />
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="evaluation" eyebrow="Evaluation results" title="Measured on a 57-case held-out set">
        <div className="metricGrid">
          {metrics.map(([label, value, note]) => (
            <div className="metricCard" key={label}>
              <strong>{value}</strong>
              <span>{label}</span>
              <p>{note}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="screenshots" eyebrow="Screenshots" title="Portfolio gallery">
        <div className="gallery">
          {screenshots.map(([label, file]) => (
            <figure key={file}>
              <Image
                src={`${basePath}/images/${file}`}
                alt={`${label} placeholder`}
                width={1200}
                height={760}
              />
              <figcaption>{label}</figcaption>
            </figure>
          ))}
        </div>
      </Section>

      <Section id="demo-video" eyebrow="Demo video" title="Walkthrough placeholder">
        <div className="videoFrame">
          <PlayCircle size={64} />
          <p>Add the final 4-6 minute demo video link here before submission.</p>
        </div>
      </Section>

      <Section id="repository" eyebrow="Repository" title="Source code and documentation">
        <div className="repoPanel">
          <GitBranch size={34} />
          <div>
            <h3>capstone-group2-team3/main-repo</h3>
            <p>Backend, frontend, RAG pipeline, evaluation, Docker setup, model card, dataset card, and reports.</p>
          </div>
          <a href={repositoryUrl} target="_blank" rel="noreferrer">
            View Repository
          </a>
        </div>
      </Section>

      <Section id="team" eyebrow="Team" title="Contributors">
        <div className="teamGrid">
          {team.map(([name, role]) => (
            <div className="teamCard" key={name}>
              <CheckCircle2 />
              <h3>{name}</h3>
              <p>{role}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="challenges" eyebrow="Challenges" title="Engineering tradeoffs">
        <div className="listGrid">
          {challenges.map((item) => (
            <p key={item}>{item}</p>
          ))}
        </div>
      </Section>

      <Section id="future-work" eyebrow="Future work" title="Next steps after capstone">
        <div className="listGrid">
          {futureWork.map((item) => (
            <p key={item}>{item}</p>
          ))}
        </div>
      </Section>

      <footer className="footer">
        <div>
          <strong>MedDx Assistant</strong>
          <p>AI-Powered Clinical Laboratory Review & Decision Support System</p>
          <p>For clinicians only — supports review, not diagnosis or prescribing.</p>
        </div>
        <div className="footerLinks">
          <a href={repositoryUrl}>Repository</a>
          <a href="#demo-video">Demo</a>
          <a href={presentationUrl}>Presentation</a>
        </div>
      </footer>
    </main>
  );
}
