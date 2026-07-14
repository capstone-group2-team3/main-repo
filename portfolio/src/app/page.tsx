"use client";

import { useState } from "react";
import Image from "next/image";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  Database,
  ExternalLink,
  FileText,
  GitBranch,
  Layers3,
  LineChart,
  Lock,
  Microscope,
  Search,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Workflow,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const basePath = "/main-repo";
const assetPath = (path: string) => `${basePath}${path}`;

const repositoryUrl = "https://github.com/capstone-group2-team3/main-repo";
const presentationUrl =
  "https://docs.google.com/presentation/d/19NANhXar5wKF0_93dJpCv-5kOkg2wsmXMYxD2zPP4l4/edit?usp=sharing";
const sampleReportUrl = assetPath("/reports/meddx-sample-report.pdf");

type PortfolioImage = {
  title: string;
  src: string;
  alt: string;
  description: string;
};

type IconCard = [string, string, LucideIcon];

const metrics = [
  ["Top-3 Pattern Recall", "100%", "Clinical pattern coverage on held-out cases"],
  ["Evidence Grounding Rate", "92.98%", "Retrieved sources aligned to matched patterns"],
  ["Critical Recall", "100%", "Critical cases protected by safety override logic"],
  ["Severity Accuracy", "63.16%", "Primary improvement area for calibration"],
  ["Safety Notice Presence", "100%", "Required clinician-only notice retained"],
  ["Average Latency", "~274 ms", "Mean end-to-end evaluation latency"],
];

const technologies: IconCard[] = [
  ["Backend", "FastAPI, Python, SQLAlchemy, SQLite, Pydantic", Database],
  ["Frontend", "Next.js, React, TypeScript, Tailwind CSS, Framer Motion", Layers3],
  ["AI", "Fine-tuned DistilBERT, PubMedBERT embeddings, Hugging Face Transformers", BrainCircuit],
  ["Vector Search", "Qdrant semantic retrieval over a controlled medical knowledge base", Search],
  ["Infrastructure", "Docker and Docker Compose for reproducible local orchestration", Workflow],
];

const features: IconCard[] = [
  ["Panel-aware lab review", "Reference-aware abnormal value detection from configurable panels.", Activity],
  ["Severity support", "Routine, Urgent, and Critical prioritization with protected override behavior.", AlertTriangle],
  ["Evidence grounding", "Semantic search returns supporting snippets, source metadata, and similarity scores.", Search],
  ["Clinical pattern ranking", "Deterministic pattern scoring ranks review patterns without claiming diagnosis.", LineChart],
  ["Structured reports", "Markdown, HTML, and PDF reports preserve context, evidence, and limitations.", FileText],
  ["Safety layer", "Mandatory clinician-only notice and non-diagnostic language are preserved.", ShieldCheck],
];

const inputWorkflow: PortfolioImage[] = [
  {
    title: "Panel Selection",
    src: "/images/panel-selection.png",
    alt: "MedDx panel selection screen showing the CBC sample and Select Analysis Template area.",
    description: "Configurable panel templates load required tests, reference ranges and supported symptoms.",
  },
  {
    title: "Patient Context",
    src: "/images/patient-context.png",
    alt: "MedDx patient context form with age, sex, symptoms, and clinical notes.",
    description: "Clinicians enter age, sex, symptoms and concise supporting notes.",
  },
  {
    title: "Laboratory Values",
    src: "/images/lab-values.png",
    alt: "MedDx lab value input cards for hemoglobin, WBC, and platelets.",
    description: "Lab values are entered using backend-configured units and educational reference ranges.",
  },
];

const aiResults: PortfolioImage[] = [
  {
    title: "Severity Classification",
    src: "/images/severity-alert.png",
    alt: "MedDx severity alert showing a Critical review alert with model confidence and source.",
    description:
      "Fine-tuned DistilBERT predicts Routine, Urgent or Critical severity, supported by confidence thresholds, deterministic fallback and critical-value safety rules.",
  },
  {
    title: "Visual Summary",
    src: "/images/visual-summary.png",
    alt: "MedDx visual summary with donut chart and summary counters for lab review status.",
    description: "A concise overview of normal, abnormal, critical and missing findings.",
  },
  {
    title: "Patient Summary",
    src: "/images/patient-summary.png",
    alt: "MedDx patient summary showing age, sex, selected panel, symptoms, notes, and generated timestamp.",
    description: "The dashboard preserves submitted context and displays the report generation time.",
  },
];

const findings: PortfolioImage[] = [
  {
    title: "Laboratory Results",
    src: "/images/lab-results.png",
    alt: "MedDx lab results table showing value, unit, reference range, status, and evidence.",
    description: "Each laboratory value is shown with its unit, educational reference range, status and evidence statement.",
  },
  {
    title: "Abnormal Findings and Warnings",
    src: "/images/abnormal-findings.png",
    alt: "MedDx abnormal findings and clinical warnings cards for hemoglobin and platelets.",
    description: "Important abnormalities are highlighted with clinician-facing review warnings.",
  },
];

const ragCards: PortfolioImage[] = [
  {
    title: "Top Clinical Patterns",
    src: "/images/clinical-patterns.png",
    alt: "MedDx top clinical patterns cards showing ranks, confidence, scores, and evidence.",
    description: "Deterministic pattern scoring ranks relevant clinical review patterns without producing a final diagnosis.",
  },
  {
    title: "Retrieved Medical Evidence",
    src: "/images/retrieved-sources.png",
    alt: "MedDx retrieved sources section with relevant findings, clinical context, source IDs, and similarity scores.",
    description:
      "PubMedBERT embeddings and Qdrant retrieve supporting medical evidence from a controlled knowledge base with similarity scores and traceable source metadata.",
  },
];

const team = [
  ["Hussam Rabaa", "Backend, database, AI/RAG/NLP, Docker, workflow, frontend support"],
  ["Deema", "AI evaluation, data analysis, RAG planning, product direction"],
  ["Rama", "Data engineering, ETL, semantic search, vector database, documentation"],
  ["Ali Alquraan", "ML/NLP, Docker, SQL, semantic search, RAG, API support"],
];

const limitations = [
  "Educational capstone artifact only; not a medical device or clinical deployment.",
  "Outputs support clinician review and do not diagnose, prescribe, or replace judgment.",
  "Severity performance needs larger clinician-reviewed datasets before real-world use.",
];

const futureWork = [
  "Clinician-reviewed severity labels and larger held-out evaluation sets.",
  "Expanded panels with documented source permissions and richer evidence coverage.",
  "Authentication, audit logs, and privacy controls before any real deployment.",
  "Calibration work to improve non-critical severity accuracy while preserving Critical recall.",
];

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="sectionHeading">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {description ? <p>{description}</p> : null}
    </div>
  );
}

function Section({
  id,
  eyebrow,
  title,
  description,
  children,
}: {
  id: string;
  eyebrow: string;
  title: string;
  description?: string;
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
        <SectionHeading eyebrow={eyebrow} title={title} description={description} />
        {children}
      </motion.div>
    </section>
  );
}

function ProjectImageCard({
  image,
  onOpen,
  large = false,
}: {
  image: PortfolioImage;
  onOpen: (image: PortfolioImage) => void;
  large?: boolean;
}) {
  return (
    <article className={large ? "imageCard imageCardLarge" : "imageCard"}>
      <button type="button" className="imageButton" onClick={() => onOpen(image)} aria-label={`Open ${image.title} image`}>
        <span className="screenshotFrame">
          <Image src={assetPath(image.src)} alt={image.alt} width={1800} height={980} />
        </span>
      </button>
      <div className="imageCardBody">
        <h3>{image.title}</h3>
        <p>{image.description}</p>
      </div>
    </article>
  );
}

function ImageGrid({
  images,
  columns = "three",
  onOpen,
}: {
  images: PortfolioImage[];
  columns?: "two" | "three";
  onOpen: (image: PortfolioImage) => void;
}) {
  return (
    <div className={columns === "two" ? "imageGrid imageGridTwo" : "imageGrid"}>
      {images.map((image) => (
        <ProjectImageCard key={image.src} image={image} onOpen={onOpen} large={columns === "two"} />
      ))}
    </div>
  );
}

function Lightbox({
  image,
  onClose,
}: {
  image: PortfolioImage | null;
  onClose: () => void;
}) {
  if (!image) {
    return null;
  }

  return (
    <div className="lightbox" role="dialog" aria-modal="true" aria-label={image.title}>
      <button type="button" className="lightboxBackdrop" onClick={onClose} aria-label="Close image preview" />
      <div className="lightboxPanel">
        <div className="lightboxTop">
          <strong>{image.title}</strong>
          <button type="button" onClick={onClose} aria-label="Close image preview">
            <X size={20} />
          </button>
        </div>
        <Image src={assetPath(image.src)} alt={image.alt} width={1900} height={1100} />
        <p>{image.description}</p>
      </div>
    </div>
  );
}

export default function Home() {
  const [activeImage, setActiveImage] = useState<PortfolioImage | null>(null);

  return (
    <main>
      <nav className="nav" aria-label="Primary navigation">
        <a href="#top" className="brand">
          <Stethoscope size={22} />
          MedDx Assistant
        </a>
        <div>
          <a href="#workflow">Workflow</a>
          <a href="#architecture">Architecture</a>
          <a href="#results">Results</a>
          <a href="#metrics">Metrics</a>
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
              A clinician-facing system that analyzes laboratory findings, identifies abnormal results and clinical
              patterns, estimates severity, retrieves supporting medical evidence, and generates structured clinical
              reports.
            </p>
            <p className="safety">For clinicians only — supports review, not diagnosis or prescribing.</p>
            <div className="actions">
              <a className="primary" href="#workflow">
                Explore the Workflow
                <ArrowRight size={18} />
              </a>
              <a className="secondary" href={presentationUrl} target="_blank" rel="noopener noreferrer">
                View Presentation
                <ExternalLink size={18} />
              </a>
              <a className="secondary" href={repositoryUrl} target="_blank" rel="noopener noreferrer">
                View Repository
                <GitBranch size={18} />
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
              src={assetPath("/images/hero-doctors.jpg")}
              alt="Two clinicians in protective laboratory coats reviewing materials together."
              width={1500}
              height={1000}
              priority
            />
            <div className="heroOverlay" />
          </motion.div>
        </div>
      </header>

      <Section
        id="overview"
        eyebrow="Project overview"
        title="A guarded AI workflow for laboratory review"
        description="MedDx Assistant combines deterministic laboratory analysis, semantic retrieval, and a fine-tuned severity classifier into an end-to-end capstone system."
      >
        <div className="overviewGrid">
          <div className="copyBlock">
            <h3>Recruiter-facing system summary</h3>
            <p>
              The project connects a polished Next.js interface with a FastAPI backend, SQLite persistence, Qdrant vector
              search, PubMedBERT embeddings, a fine-tuned DistilBERT classifier, and structured report generation.
            </p>
          </div>
          <div className="copyBlock">
            <h3>Clinical safety posture</h3>
            <p>
              The system presents educational review support for clinicians, keeps evidence traceable, avoids diagnosis
              and prescribing claims, and preserves the mandatory clinician-only safety notice.
            </p>
          </div>
        </div>
      </Section>

      <Section id="problem-solution" eyebrow="Problem and solution" title="From fragmented review to traceable support">
        <div className="problemSolutionGrid">
          <article className="premiumCard">
            <Microscope />
            <h3>Problem</h3>
            <p>
              Lab review requires context, reference ranges, abnormality detection, pattern awareness, and evidence lookup
              across multiple screens and sources.
            </p>
          </article>
          <article className="premiumCard">
            <ShieldCheck />
            <h3>Solution</h3>
            <p>
              MedDx structures the workflow from clinical input to severity support, clinical patterns, retrieved evidence,
              and downloadable reports with explicit limitations.
            </p>
          </article>
        </div>
      </Section>

      <Section
        id="architecture"
        eyebrow="System architecture"
        title="End-to-end clinical review architecture"
        description="An end-to-end clinical review workflow connecting the Next.js interface, FastAPI backend, deterministic lab analysis, fine-tuned DistilBERT severity classification, PubMedBERT and Qdrant evidence retrieval, safety validation, and structured report generation."
      >
        <figure className="architectureFrame">
          <button
            type="button"
            className="imageButton"
            onClick={() =>
              setActiveImage({
                title: "System Architecture",
                src: "/images/system-architecture.png",
                alt: "Dark MedDx system architecture diagram showing frontend, backend, AI pipeline, data stores, and outputs.",
                description:
                  "The architecture connects the clinician UI, FastAPI services, severity model, RAG retrieval, data stores, and report outputs.",
              })
            }
            aria-label="Open system architecture diagram"
          >
            <Image
              src={assetPath("/images/system-architecture.png")}
              alt="Dark MedDx system architecture diagram showing frontend, backend, AI pipeline, data stores, and outputs."
              width={1800}
              height={1200}
            />
          </button>
          <figcaption>
            Static export-safe architecture diagram showing UI, API services, agent pipeline, model services, Qdrant,
            SQLite, report storage, and clinician-facing outputs.
          </figcaption>
        </figure>
      </Section>

      <Section id="workflow" eyebrow="Clinical input workflow" title="From template selection to lab entry">
        <ImageGrid images={inputWorkflow} onOpen={setActiveImage} />
      </Section>

      <Section id="results" eyebrow="AI analysis results" title="Severity, summary, and submitted context">
        <ImageGrid images={aiResults} onOpen={setActiveImage} />
      </Section>

      <Section id="findings" eyebrow="Clinical findings" title="Reference-aware results and review warnings">
        <ImageGrid images={findings} columns="two" onOpen={setActiveImage} />
      </Section>

      <Section
        id="rag"
        eyebrow="Clinical patterns and RAG"
        title="Pattern scoring with retrieved medical evidence"
        description="The RAG flow is intentionally constrained: abnormal findings lead to pattern scoring, embedding search, Qdrant retrieval, and traceable evidence cards."
      >
        <div className="pipelineStrip" aria-label="Clinical patterns and evidence retrieval pipeline">
          {["Abnormal findings", "Clinical pattern scoring", "PubMedBERT embedding query", "Qdrant similarity search", "Retrieved medical evidence"].map(
            (step, index) => (
              <span key={step}>
                {step}
                {index < 4 ? <ArrowRight size={16} aria-hidden="true" /> : null}
              </span>
            ),
          )}
        </div>
        <ImageGrid images={ragCards} columns="two" onOpen={setActiveImage} />
      </Section>

      <Section
        id="generated-report"
        eyebrow="Generated report"
        title="Generated Clinical Review Report"
        description="MedDx automatically creates structured Markdown, HTML and PDF reports containing the patient context, laboratory findings, severity alert, clinical patterns, retrieved evidence, limitations and safety notice."
      >
        <div className="reportGrid">
          <ProjectImageCard
            image={{
              title: "Sample PDF Report Preview",
              src: "/images/generated-report.png",
              alt: "First page preview of a synthetic MedDx generated clinical review PDF report.",
              description:
                "A synthetic sample report preview rendered from the backend-generated PDF. The source case contains educational demo data only.",
            }}
            onOpen={setActiveImage}
            large
          />
          <div className="reportPanel">
            <div className="badgeRow">
              <span>PDF</span>
              <span>HTML</span>
              <span>Markdown</span>
            </div>
            <p>
              The sample PDF included here uses only synthetic educational data from Case 53 and contains no patient names
              or identifiers.
            </p>
            <a className="primary" href={sampleReportUrl} target="_blank" rel="noopener noreferrer">
              View Sample Report
              <ExternalLink size={18} />
            </a>
          </div>
        </div>
      </Section>

      <Section id="features" eyebrow="Core features" title="What the system demonstrates">
        <div className="featureGrid">
          {features.map(([title, text, Icon]) => (
            <article className="featureCard" key={title}>
              <Icon />
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </Section>

      <Section id="technologies" eyebrow="Technology stack" title="Production-shaped tools">
        <div className="techGrid">
          {technologies.map(([area, text, Icon]) => (
            <article className="techCard" key={area}>
              <Icon />
              <h3>{area}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </Section>

      <Section id="metrics" eyebrow="Evaluation metrics" title="Measured capstone outcomes">
        <div className="metricGrid">
          {metrics.map(([label, value, note]) => (
            <article className="metricCard" key={label}>
              <strong>{value}</strong>
              <span>{label}</span>
              <p>{note}</p>
            </article>
          ))}
        </div>
      </Section>

      <Section id="demo" eyebrow="Demo and presentation" title="Explore the project">
        <div className="ctaPanel demoCtaPanel">
          <div>
            <h3>Portfolio-ready project links</h3>
            <p>
              Review the Capstone presentation, inspect the repository, and watch the complete technical walkthrough.
            </p>
          </div>
          <div className="actions">
            <a className="primary" href={presentationUrl} target="_blank" rel="noopener noreferrer">
              View Presentation
              <ExternalLink size={18} />
            </a>
            <a className="secondary" href={repositoryUrl} target="_blank" rel="noopener noreferrer">
              View Repository
              <GitBranch size={18} />
            </a>
            <a className="secondary" href="#demo-video">
              Demo Video
              <ArrowRight size={18} />
            </a>
          </div>
        </div>
        <div id="demo-video" className="demoVideoPanel">
          <div className="demoVideoHeader">
            <h3>Demo Video</h3>
            <p>Complete MedDx Assistant technical demonstration.</p>
          </div>
          <video className="demoVideo" controls preload="metadata" playsInline>
            <source src={assetPath("/images/Demo-Video.mp4")} type="video/mp4" />
            Your browser does not support the video element.
          </video>
        </div>
      </Section>

      <Section id="team" eyebrow="Team contributions" title="Capstone team">
        <div className="teamGrid">
          {team.map(([name, role]) => (
            <article className="teamCard" key={name}>
              <CheckCircle2 />
              <h3>{name}</h3>
              <p>{role}</p>
            </article>
          ))}
        </div>
      </Section>

      <Section id="safety" eyebrow="Safety and limitations" title="Clear boundaries for clinical use">
        <div className="listGrid">
          {limitations.map((item) => (
            <p key={item}>
              <Lock size={18} />
              {item}
            </p>
          ))}
        </div>
      </Section>

      <Section id="future-work" eyebrow="Future work" title="Next steps after capstone">
        <div className="listGrid">
          {futureWork.map((item) => (
            <p key={item}>
              <ArrowRight size={18} />
              {item}
            </p>
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
          <a href={repositoryUrl} target="_blank" rel="noopener noreferrer">
            Repository
          </a>
          <a href={presentationUrl} target="_blank" rel="noopener noreferrer">
            Presentation
          </a>
          <a href="#generated-report">Sample Report</a>
        </div>
      </footer>

      <Lightbox image={activeImage} onClose={() => setActiveImage(null)} />
    </main>
  );
}
