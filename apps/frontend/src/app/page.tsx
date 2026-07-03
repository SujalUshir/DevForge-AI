"use client";

import React, { useState, useEffect, useRef } from "react";

// ── Types & Interfaces ───────────────────────────────────────────────────────

interface LogItem {
  time: string;
  agent: string;
  dept: string;
  message: string;
  type?: "info" | "success" | "warning" | "error";
}

interface FileArtifact {
  name: string;
  content: string;
  language: string;
}

type ViewState = "landing" | "submission" | "workspace";
type ExecutionPhase = "PLANNING" | "ARCHITECTURE" | "ENGINEERING" | "VALIDATION" | "REVIEW" | "COMPLETED";

// ── Simulation Data Helpers ──────────────────────────────────────────────────

const MOCK_STEPS = [
  {
    phase: "PLANNING",
    progress: 10,
    agent: "CEO Agent",
    dept: "Management",
    message: "Initializing forge workspace and project context parameters.",
    type: "info"
  },
  {
    phase: "PLANNING",
    progress: 18,
    agent: "Product Lead",
    dept: "Planning",
    message: "Started requirements compilation. Drafted persona use cases and functional specifications.",
    type: "info"
  },
  {
    phase: "PLANNING",
    progress: 25,
    agent: "Market Analyst",
    dept: "Planning",
    message: "Analyzing competitor SaaS features. Compiled SWOT market report.",
    type: "info"
  },
  {
    phase: "PLANNING",
    progress: 32,
    agent: "Design Lead",
    dept: "Planning",
    message: "Structuring visual layout guides and wireframe component specs.",
    type: "info"
  },
  {
    phase: "ARCHITECTURE",
    progress: 40,
    agent: "Principal Architect",
    dept: "Architecture",
    message: "Mapping system topology. Created Mermaid C4 gateway and data flow schemas.",
    type: "info"
  },
  {
    phase: "ARCHITECTURE",
    progress: 48,
    agent: "Principal Architect",
    dept: "Architecture",
    message: "Drafting microservices framework configurations and design rationale.",
    type: "success"
  },
  {
    phase: "ENGINEERING",
    progress: 55,
    agent: "Backend Lead",
    dept: "Engineering",
    message: "Creating OpenAPI routes and compiling database DDL schemas.",
    type: "info"
  },
  {
    phase: "ENGINEERING",
    progress: 62,
    agent: "Frontend Lead",
    dept: "Engineering",
    message: "Scaffolding component routes hierarchy and state configurations.",
    type: "info"
  },
  {
    phase: "VALIDATION",
    progress: 70,
    agent: "Security Lead",
    dept: "Validation",
    message: "Conducting threat model audit. Sanity checking token sessions and CORS policies.",
    type: "warning"
  },
  {
    phase: "VALIDATION",
    progress: 78,
    agent: "QA Lead",
    dept: "Validation",
    message: "Establishing integration and serialization unit test suites.",
    type: "info"
  },
  {
    phase: "VALIDATION",
    progress: 85,
    agent: "Platform Engineer",
    dept: "Validation",
    message: "Composing Dockerfiles, docker-compose.yml, and deployment templates.",
    type: "info"
  },
  {
    phase: "REVIEW",
    progress: 90,
    agent: "Engineering Director",
    dept: "Review",
    message: "Cross-referencing database structure, API specs, and PRD specifications.",
    type: "info"
  },
  {
    phase: "REVIEW",
    progress: 95,
    agent: "Engineering Director",
    dept: "Review",
    message: "All validation gates passed successfully. Signing off on blueprint delivery.",
    type: "success"
  },
  {
    phase: "COMPLETED",
    progress: 100,
    agent: "CEO Agent",
    dept: "Management",
    message: "Forge workspace exported successfully. Blueprints available for download.",
    type: "success"
  }
];

export default function Page() {
  // ── State variables ────────────────────────────────────────────────────────
  const [view, setView] = useState<ViewState>("landing");
  
  // Submission values
  const [projectName, setProjectName] = useState("");
  const [userIdea, setUserIdea] = useState("");
  const [frontendStack, setFrontendStack] = useState("Next.js + Tailwind");
  const [backendStack, setBackendStack] = useState("FastAPI");
  const [databaseStack, setDatabaseStack] = useState("PostgreSQL");

  // Simulation execution values
  const [phase, setPhase] = useState<ExecutionPhase>("PLANNING");
  const [progress, setProgress] = useState(0);
  const [activeAgent, setActiveAgent] = useState("CEO Agent");
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [simStepIndex, setSimStepIndex] = useState(0);
  const [isSimulating, setIsSimulating] = useState(false);

  // File explorer values
  const [files, setFiles] = useState<FileArtifact[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileArtifact | null>(null);

  const logsEndRef = useRef<HTMLDivElement>(null);

  // ── Auto-scroll logs ───────────────────────────────────────────────────────
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // ── Generate dynamic mock blueprints based on user inputs ──────────────────
  const populateBlueprints = (pName: string, idea: string, fe: string, be: string, db: string) => {
    const prd = `# Product Requirements Document: ${pName}

## 1. Product Vision
${idea}

## 2. Technology Stack Parameters
- **Frontend Framework:** ${fe}
- **Backend Service:** ${be}
- **Database Engine:** ${db}

## 3. User Stories & Functional Specs
- **US-101 (User Session):** As a registered user, I need to log in securely so that I can access my workspace.
- **US-102 (Live Updates):** As a builder, I need real-time status feeds so I can trace operations live.
`;

    const arch = `# System Architecture: ${pName}

## 1. Component Topology
\`\`\`mermaid
graph TD
  Client[Web Client: ${fe}] --> Gateway[API Gateway: ${be}]
  Gateway --> Service[Orchestration Engine]
  Service --> Cache[(Redis Cache)]
  Service --> DB[Database Store: ${db}]
\`\`\`

## 2. Design Rationale
- Decoupled single-page UI architecture using ${fe} to optimize rendering speeds.
- Asynchronous service routing managed via a ${be} engine to ensure low-latency request pipelines.
`;

    const api = `# OpenAPI Specification (YAML)
openapi: 3.0.3
info:
  title: ${pName} API Services
  version: 1.0.0
paths:
  /api/health:
    get:
      summary: Health Probe Endpoint
      responses:
        '200':
          description: Healthy status payload.
  /api/workspace/generate:
    post:
      summary: Launch multi-agent blueprint forge
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                idea:
                  type: string
`;

    const sql = `-- Database Schema DDL: ${pName}
-- Generated for DB engine: ${db}

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_workspaces (
  id UUID PRIMARY KEY,
  owner_id UUID REFERENCES users(id),
  project_name VARCHAR(100) NOT NULL,
  status VARCHAR(20) NOT NULL,
  specs JSONB
);
`;

    const readme = `# ⚡ ${pName}

Production-ready architecture blueprints and specifications generated by **DevForge AI**.

## Recommended Stack
- **Frontend:** ${fe}
- **Backend:** ${be}
- **Database:** ${db}

## File Blueprint Structure
- \`PRD.md\`: Product requirements, user flows, and MVP metrics.
- \`architecture.md\`:mermaid architecture components topology.
- \`api_spec.yaml\`: OpenAPI REST route specifications.
- \`database_schema.sql\`: DB schema initialization DDL scripts.
`;

    const parsedFiles = [
      { name: "README.md", content: readme, language: "markdown" },
      { name: "PRD.md", content: prd, language: "markdown" },
      { name: "architecture.md", content: arch, language: "markdown" },
      { name: "api_spec.yaml", content: api, language: "yaml" },
      { name: "database_schema.sql", content: sql, language: "sql" }
    ];

    setFiles(parsedFiles);
    setSelectedFile(parsedFiles[0]);
  };

  // ── Simulation Logic Loop ──────────────────────────────────────────────────
  useEffect(() => {
    if (!isSimulating) return;

    if (simStepIndex >= MOCK_STEPS.length) {
      setIsSimulating(false);
      populateBlueprints(
        projectName || "MyDevForgeApp",
        userIdea || "An automated planning system.",
        frontendStack,
        backendStack,
        databaseStack
      );
      return;
    }

    const timer = setTimeout(() => {
      const step = MOCK_STEPS[simStepIndex];
      
      // Update execution parameters
      setPhase(step.phase as ExecutionPhase);
      setProgress(step.progress);
      setActiveAgent(step.agent);
      
      const now = new Date();
      const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

      setLogs(prev => [
        ...prev,
        {
          time: timeString,
          agent: step.agent,
          dept: step.dept,
          message: step.message,
          type: step.type as any
        }
      ]);

      setSimStepIndex(prev => prev + 1);
    }, 1800);

    return () => clearTimeout(timer);
  }, [isSimulating, simStepIndex]);

  // ── Event Handlers ─────────────────────────────────────────────────────────

  const handleStartForge = (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName.trim() || !userIdea.trim()) return;

    setView("workspace");
    setIsSimulating(true);
    setProgress(0);
    setSimStepIndex(0);
    setLogs([]);
    setPhase("PLANNING");
    setFiles([]);
    setSelectedFile(null);
  };

  const downloadBlueprint = () => {
    // Generate simple blob contents for the README/PRD
    const readmeFile = files.find(f => f.name === "README.md");
    if (!readmeFile) return;
    
    const blob = new Blob([readmeFile.content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${projectName.toLowerCase().replace(/\s+/g, "-")}-blueprint.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      
      {/* ── HEADER ──────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 glass-panel border-b border-zinc-800/80 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setView("landing")}>
          <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center font-bold text-white text-lg tracking-wider glow-indigo">
            DF
          </div>
          <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
            DevForge <span className="text-indigo-400 font-medium">AI</span>
          </span>
        </div>
        <nav className="flex items-center gap-6">
          <button 
            onClick={() => setView("landing")}
            className={`text-sm font-medium transition-colors ${view === "landing" ? "text-indigo-400" : "text-zinc-400 hover:text-zinc-200"}`}
          >
            Home
          </button>
          <button 
            onClick={() => setView("submission")}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-semibold text-sm text-white transition-all shadow-md glow-indigo"
          >
            Forge Blueprint
          </button>
        </nav>
      </header>

      {/* ── MAIN CONTENT ────────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col">
        
        {/* ── VIEW 1: LANDING PAGE ─────────────────────────────────────────── */}
        {view === "landing" && (
          <section className="flex-1 flex flex-col justify-center items-center px-6 py-20 relative overflow-hidden">
            {/* Background glowing effects */}
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />
            <div className="absolute bottom-10 left-10 w-72 h-72 rounded-full bg-emerald-500/5 blur-[100px] pointer-events-none" />

            <div className="max-w-4xl text-center flex flex-col items-center gap-8 relative z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-indigo-400 text-xs font-semibold tracking-wide">
                <span>✦</span> Powered by Multi-Agent Swarms
              </div>
              
              <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white leading-tight">
                Transform Software Ideas into{" "}
                <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-indigo-500 bg-clip-text text-transparent font-black block mt-2">
                  Production-Ready Blueprints
                </span>
              </h1>

              <p className="text-zinc-400 text-lg md:text-xl max-w-2xl leading-relaxed">
                DevForge AI is an autonomous software studio where specialized AI agents—from Product Managers to Security Engineers—collaborate to compile complete architecture blueprints, REST APIs, and database schemas.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 mt-4">
                <button
                  onClick={() => setView("submission")}
                  className="px-8 py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-lg text-white transition-all shadow-lg glow-indigo flex items-center justify-center gap-2"
                >
                  Get Started
                </button>
                <button
                  onClick={() => {
                    setProjectName("Demo Planner");
                    setUserIdea("An offline planning dashboard utilizing local storages.");
                    setView("workspace");
                    setIsSimulating(true);
                  }}
                  className="px-8 py-4 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 font-bold text-lg text-zinc-300 transition-all flex items-center justify-center gap-2"
                >
                  Live Run Demo
                </button>
              </div>
            </div>

            {/* Feature Highlights Grid */}
            <div className="max-w-6xl w-full grid grid-cols-1 md:grid-cols-3 gap-6 mt-28 px-4">
              <div className="p-6 rounded-xl border border-zinc-800/80 bg-zinc-900/40 glass-panel hover:border-zinc-700 transition-all flex flex-col gap-4">
                <div className="h-10 w-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-lg">
                  11
                </div>
                <h3 className="text-xl font-bold text-white">Specialist Agents</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  Structured swarms split across Planning, Architecture, Engineering, Validation, and Review departments.
                </p>
              </div>
              
              <div className="p-6 rounded-xl border border-zinc-800/80 bg-zinc-900/40 glass-panel hover:border-zinc-700 transition-all flex flex-col gap-4">
                <div className="h-10 w-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-lg">
                  ✓
                </div>
                <h3 className="text-xl font-bold text-white">Strict Verification</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  Outputs must pass rigorous validation checks, threat model reports, and director reviews.
                </p>
              </div>

              <div className="p-6 rounded-xl border border-zinc-800/80 bg-zinc-900/40 glass-panel hover:border-zinc-700 transition-all flex flex-col gap-4">
                <div className="h-10 w-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-lg">
                  ⚡
                </div>
                <h3 className="text-xl font-bold text-white">Ready-to-Deploy</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  Downloads complete packages containing PRD, API specs, schemas, and README templates.
                </p>
              </div>
            </div>
          </section>
        )}

        {/* ── VIEW 2: SUBMISSION FORM ──────────────────────────────────────── */}
        {view === "submission" && (
          <section className="flex-1 flex justify-center items-center px-6 py-12 relative overflow-hidden">
            <div className="absolute top-10 left-10 w-72 h-72 bg-indigo-600/5 blur-[100px] pointer-events-none" />

            <div className="max-w-2xl w-full border border-zinc-800 bg-zinc-900/30 glass-panel rounded-2xl p-8 shadow-2xl relative z-10">
              <h2 className="text-3xl font-extrabold tracking-tight text-white mb-2">
                Launch Your Idea
              </h2>
              <p className="text-zinc-400 text-sm mb-8 leading-relaxed">
                Provide basic parameters and watch DevForge AI agents debate, validate, and write your architecture package.
              </p>

              <form onSubmit={handleStartForge} className="flex flex-col gap-6">
                <div className="flex flex-col gap-2">
                  <label htmlFor="projectName" className="text-sm font-bold text-zinc-300">
                    Project Name
                  </label>
                  <input
                    type="text"
                    id="projectName"
                    placeholder="e.g. PayFlow Dashboard"
                    required
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    className="w-full bg-zinc-950/80 border border-zinc-800 rounded-xl px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-indigo-500 text-sm transition-all"
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <label htmlFor="userIdea" className="text-sm font-bold text-zinc-300">
                    Software Idea Description
                  </label>
                  <textarea
                    id="userIdea"
                    rows={4}
                    placeholder="Describe what your software should do..."
                    required
                    value={userIdea}
                    onChange={(e) => setUserIdea(e.target.value)}
                    className="w-full bg-zinc-950/80 border border-zinc-800 rounded-xl px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-indigo-500 text-sm transition-all resize-none"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex flex-col gap-2">
                    <label htmlFor="feStack" className="text-xs font-bold text-zinc-400 uppercase tracking-wide">
                      Frontend Framework
                    </label>
                    <input
                      type="text"
                      id="feStack"
                      value={frontendStack}
                      onChange={(e) => setFrontendStack(e.target.value)}
                      className="w-full bg-zinc-950/80 border border-zinc-800 rounded-xl px-3 py-2.5 text-zinc-200 focus:outline-none focus:border-indigo-500 text-xs transition-all"
                    />
                  </div>

                  <div className="flex flex-col gap-2">
                    <label htmlFor="beStack" className="text-xs font-bold text-zinc-400 uppercase tracking-wide">
                      Backend Service
                    </label>
                    <input
                      type="text"
                      id="beStack"
                      value={backendStack}
                      onChange={(e) => setBackendStack(e.target.value)}
                      className="w-full bg-zinc-950/80 border border-zinc-800 rounded-xl px-3 py-2.5 text-zinc-200 focus:outline-none focus:border-indigo-500 text-xs transition-all"
                    />
                  </div>

                  <div className="flex flex-col gap-2">
                    <label htmlFor="dbStack" className="text-xs font-bold text-zinc-400 uppercase tracking-wide">
                      Database Store
                    </label>
                    <input
                      type="text"
                      id="dbStack"
                      value={databaseStack}
                      onChange={(e) => setDatabaseStack(e.target.value)}
                      className="w-full bg-zinc-950/80 border border-zinc-800 rounded-xl px-3 py-2.5 text-zinc-200 focus:outline-none focus:border-indigo-500 text-xs transition-all"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full mt-4 py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-lg text-white transition-all shadow-lg glow-indigo"
                >
                  Launch Forge Workspace
                </button>
              </form>
            </div>
          </section>
        )}

        {/* ── VIEW 3: LIVE WORKSPACE ────────────────────────────────────────── */}
        {view === "workspace" && (
          <section className="flex-1 flex flex-col lg:flex-row gap-6 p-6 max-w-7xl mx-auto w-full">
            
            {/* Left Column: Progress timeline & Agent cards */}
            <div className="flex-1 flex flex-col gap-6 max-w-2xl">
              
              {/* Workspace Header Info */}
              <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/30 glass-panel">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest block mb-1">
                      Project Generation
                    </span>
                    <h2 className="text-2xl font-extrabold text-white">
                      {projectName || "DevForge Dashboard"}
                    </h2>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold tracking-wide border ${
                    progress === 100 
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : "bg-indigo-500/10 border-indigo-500/30 text-indigo-400 animate-pulse-slow"
                  }`}>
                    {progress === 100 ? "Completed" : "Active Forge"}
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-zinc-950 rounded-full h-2 mb-2 overflow-hidden border border-zinc-800">
                  <div 
                    className="bg-gradient-to-r from-indigo-500 to-violet-600 h-full transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <div className="flex justify-between items-center text-xs text-zinc-400">
                  <span>Pipeline Progress</span>
                  <span>{progress}%</span>
                </div>
              </div>

              {/* Department workflow sequence */}
              <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/30 glass-panel flex flex-col gap-4">
                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wide">
                  Department Roadmap Flow
                </h3>
                
                <div className="flex flex-col gap-3">
                  {[
                    { key: "PLANNING", label: "Planning Department", agents: "Product Lead, Analyst, Designer" },
                    { key: "ARCHITECTURE", label: "Architecture Department", agents: "Principal Architect" },
                    { key: "ENGINEERING", label: "Engineering Department", agents: "Backend & Frontend Leads" },
                    { key: "VALIDATION", label: "Validation Department", agents: "Security, QA, Platform Engineers" },
                    { key: "REVIEW", label: "Review Department", agents: "Engineering Director" }
                  ].map((p, idx) => {
                    const isPassed = MOCK_STEPS.findIndex(s => s.phase === p.key) < simStepIndex;
                    const isActive = phase === p.key;
                    
                    return (
                      <div 
                        key={p.key} 
                        className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
                          isActive 
                            ? "bg-indigo-500/5 border-indigo-500/30 text-white" 
                            : isPassed 
                              ? "bg-zinc-950/40 border-zinc-900 text-zinc-400"
                              : "bg-zinc-950/20 border-zinc-900/50 text-zinc-600"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold ${
                            isActive 
                              ? "bg-indigo-600 text-white"
                              : isPassed 
                                ? "bg-emerald-950 border border-emerald-500/30 text-emerald-400"
                                : "bg-zinc-900 text-zinc-600"
                          }`}>
                            {isPassed ? "✓" : idx + 1}
                          </span>
                          <div>
                            <p className="text-sm font-bold">{p.label}</p>
                            <p className="text-xs text-zinc-500">{p.agents}</p>
                          </div>
                        </div>
                        {isActive && (
                          <span className="text-xs text-indigo-400 font-medium animate-pulse">
                            Processing
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Active Agent Status Card */}
              <div className="p-6 rounded-xl border border-zinc-800 bg-gradient-to-tr from-zinc-900/40 to-zinc-900/20 glass-panel flex flex-col gap-3">
                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wide">
                  Active Specialist Agent
                </h3>
                
                <div className="flex items-center gap-4 bg-zinc-950/50 p-4 rounded-xl border border-zinc-800">
                  <div className="h-12 w-12 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-2xl animate-pulse-slow">
                    🤖
                  </div>
                  <div>
                    <h4 className="text-lg font-bold text-white">{activeAgent}</h4>
                    <p className="text-xs text-zinc-500">Status: {progress === 100 ? "IDLE" : "RUNNING"}</p>
                  </div>
                </div>
              </div>

            </div>

            {/* Right Column: Logging timeline feed & Artifact Explorer */}
            <div className="flex-1 flex flex-col gap-6">
              
              {/* Event Streams Log Panel */}
              <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/30 glass-panel h-80 flex flex-col">
                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wide mb-3 flex items-center justify-between">
                  <span>Orchestrator SSE Log Stream</span>
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                </h3>
                
                <div className="flex-1 overflow-y-auto bg-zinc-950/80 rounded-lg p-4 border border-zinc-800 font-mono text-xs flex flex-col gap-3">
                  {logs.map((log, idx) => (
                    <div key={idx} className="flex gap-2 items-start border-l-2 pl-3 border-zinc-800/80 hover:border-indigo-500/50 transition-all">
                      <span className="text-zinc-500 select-none">{log.time}</span>
                      <span className="text-indigo-400 font-semibold select-none">[{log.agent}]:</span>
                      <span className={`${
                        log.type === "success" ? "text-emerald-400" : log.type === "warning" ? "text-yellow-400" : "text-zinc-300"
                      }`}>{log.message}</span>
                    </div>
                  ))}
                  {logs.length === 0 && (
                    <div className="text-zinc-600 italic">Awaiting pipeline trigger signal...</div>
                  )}
                  <div ref={logsEndRef} />
                </div>
              </div>

              {/* Artifacts Preview Explorer */}
              <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/30 glass-panel flex-1 flex flex-col min-h-[400px]">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wide">
                    Generated Blueprint Explorer
                  </h3>
                  {progress === 100 && (
                    <button
                      onClick={downloadBlueprint}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 font-bold text-xs text-white rounded-lg transition-all shadow-md glow-indigo flex items-center gap-1.5"
                    >
                      Download Blueprint
                    </button>
                  )}
                </div>

                {progress < 100 ? (
                  <div className="flex-1 flex flex-col items-center justify-center gap-3 text-zinc-500">
                    <span className="text-4xl animate-pulse-slow">📦</span>
                    <p className="text-sm font-medium">Artifact package generating...</p>
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col gap-4">
                    {/* Tab Selection */}
                    <div className="flex overflow-x-auto gap-2 border-b border-zinc-800 pb-2">
                      {files.map(f => (
                        <button
                          key={f.name}
                          onClick={() => setSelectedFile(f)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all border ${
                            selectedFile?.name === f.name
                              ? "bg-zinc-800 border-zinc-700 text-white"
                              : "bg-transparent border-transparent text-zinc-400 hover:text-zinc-200"
                          }`}
                        >
                          {f.name}
                        </button>
                      ))}
                    </div>

                    {/* Syntax Code Pane */}
                    <div className="flex-1 bg-zinc-950/80 border border-zinc-800 rounded-lg p-4 font-mono text-xs overflow-y-auto max-h-[300px] text-zinc-300 whitespace-pre-wrap">
                      {selectedFile?.content}
                    </div>
                  </div>
                )}
              </div>

            </div>

          </section>
        )}

      </main>

      {/* ── FOOTER ──────────────────────────────────────────────────────────── */}
      <footer className="border-t border-zinc-800 px-6 py-6 text-center text-xs text-zinc-500">
        <p>© 2026 DevForge AI. All rights reserved. Structured Software Studio Blueprint Forge.</p>
      </footer>
    </div>
  );
}
