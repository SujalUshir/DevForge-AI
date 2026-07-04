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
type ExecutionPhase = "PLANNING" | "ARCHITECTURE" | "ENGINEERING" | "VALIDATION" | "REVIEW" | "COMPLETED" | "FAILED";

// Base API configuration URL
const getApiBase = () => {
  if (typeof window !== "undefined") {
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envUrl) return envUrl;
  }
  return "http://127.0.0.1:8000/api/projects";
};

const API_BASE = getApiBase();

// ── Custom Markdown Preview Renderer ─────────────────────────────────────────

function renderMarkdownContent(text: string) {
  const lines = text.split("\n");
  return (
    <div className="space-y-4 text-zinc-300 text-sm leading-relaxed font-sans">
      {lines.map((line, idx) => {
        // Heading 1
        if (line.startsWith("# ")) {
          return (
            <h1 key={idx} className="text-2xl font-black text-white mt-6 mb-4 border-b border-zinc-800 pb-2 tracking-tight">
              {line.replace("# ", "")}
            </h1>
          );
        }
        // Heading 2
        if (line.startsWith("## ")) {
          return (
            <h2 key={idx} className="text-lg font-bold text-zinc-100 mt-6 mb-3 flex items-center gap-2 border-b border-zinc-900/50 pb-1 tracking-tight">
              <span className="text-indigo-400 font-semibold">#</span> {line.replace("## ", "")}
            </h2>
          );
        }
        // Heading 3
        if (line.startsWith("### ")) {
          return (
            <h3 key={idx} className="text-md font-semibold text-zinc-200 mt-4 mb-2 tracking-tight">
              {line.replace("### ", "")}
            </h3>
          );
        }
        // Bullet list
        if (line.startsWith("- ")) {
          return (
            <div key={idx} className="flex items-start gap-2.5 ml-4 my-1.5">
              <span className="text-indigo-500 mt-2 h-1.5 w-1.5 rounded-full bg-indigo-500 shrink-0" />
              <span className="text-zinc-300 text-sm">{line.replace("- ", "")}</span>
            </div>
          );
        }
        // Empty line spacer
        if (line.trim() === "") {
          return <div key={idx} className="h-2" />;
        }
        // Default text paragraph
        return <p key={idx} className="text-zinc-300 my-2">{line}</p>;
      })}
    </div>
  );
}

export default function Page() {
  // ── State variables ────────────────────────────────────────────────────────
  const [view, setView] = useState<ViewState>("landing");
  
  // Submission values
  const [projectName, setProjectName] = useState("");
  const [userIdea, setUserIdea] = useState("");
  const [frontendStack, setFrontendStack] = useState("Next.js + Tailwind");
  const [backendStack, setBackendStack] = useState("FastAPI");
  const [databaseStack, setDatabaseStack] = useState("PostgreSQL");

  // Integration execution values
  const [projectId, setProjectId] = useState<string | null>(null);
  const [phase, setPhase] = useState<ExecutionPhase>("PLANNING");
  const [progress, setProgress] = useState(0);
  const [activeAgent, setActiveAgent] = useState("CEO Agent");
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // File explorer values
  const [files, setFiles] = useState<FileArtifact[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileArtifact | null>(null);
  const [copied, setCopied] = useState(false);

  const logsEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // ── Auto-scroll logs ───────────────────────────────────────────────────────
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // ── Close EventSource on unmount ───────────────────────────────────────────
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // ── Fetch Artifacts upon completion ────────────────────────────────────────
  const fetchArtifacts = async (projId: string) => {
    try {
      const res = await fetch(`${API_BASE}/${projId}/artifacts`);
      if (!res.ok) {
        throw new Error("Failed to fetch generated project files.");
      }
      const data = await res.json();
      setFiles(data);
      if (data.length > 0) {
        setSelectedFile(data[0]);
      }
    } catch (err) {
      console.error("Fetch artifacts error:", err);
      setErrorMsg(err instanceof Error ? err.message : "Could not load artifacts.");
    }
  };

  // ── Setup Real-time SSE Stream ─────────────────────────────────────────────
  const connectSSE = (projId: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`${API_BASE}/${projId}/stream`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const { event: eventType, data } = payload;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        if (eventType === "connected") {
          setLogs(prev => [
            ...prev,
            { time: timeString, agent: "System", dept: "Network", message: "SSE stream connection established.", type: "info" }
          ]);
        }
        else if (eventType === "phase_started") {
          const newPhase = data.phase as ExecutionPhase;
          setPhase(newPhase);
          
          // Calculate phase-specific progress bar percentages
          const progressMap: Record<string, number> = {
            PLANNING: 20,
            ARCHITECTURE: 45,
            ENGINEERING: 65,
            VALIDATION: 85,
            REVIEW: 95,
            COMPLETED: 100,
            FAILED: 0
          };
          setProgress(progressMap[newPhase] || 0);

          setLogs(prev => [
            ...prev,
            { time: timeString, agent: "Orchestrator", dept: "Management", message: `Transitioning to phase: ${newPhase}`, type: "info" }
          ]);
        }
        else if (eventType === "agent_started") {
          setActiveAgent(data.agent);
          setLogs(prev => [
            ...prev,
            { time: timeString, agent: data.agent, dept: data.dept, message: `Started execution task.`, type: "info" }
          ]);
        }
        else if (eventType === "agent_completed") {
          setLogs(prev => [
            ...prev,
            { time: timeString, agent: data.agent, dept: "Validation", message: `Completed task successfully.`, type: "success" }
          ]);
        }
        else if (eventType === "agent_failed") {
          setLogs(prev => [
            ...prev,
            { time: timeString, agent: data.agent, dept: "Validation", message: `Task execution failed: ${data.error}`, type: "error" }
          ]);
        }
        else if (eventType === "revision_triggered") {
          setLogs(prev => [
            ...prev,
            { time: timeString, agent: "Director", dept: "Review", message: `Rejected blueprint. Triggering loop: ${data.revision}. Feedback: ${JSON.stringify(data.feedback)}`, type: "warning" }
          ]);
        }
        else if (eventType === "pipeline_completed") {
          setPhase("COMPLETED");
          setProgress(100);
          setLogs(prev => [
            ...prev,
            { time: timeString, agent: "CEO Agent", dept: "Management", message: "Orchestration pipeline completed successfully!", type: "success" }
          ]);
          eventSource.close();
          fetchArtifacts(projId);
        }
        else if (eventType === "pipeline_failed") {
          setPhase("FAILED");
          setLogs(prev => [
            ...prev,
            { time: timeString, agent: "CEO Agent", dept: "Management", message: `Pipeline aborted: ${data.error}`, type: "error" }
          ]);
          setErrorMsg(data.error || "Generation pipeline failed.");
          eventSource.close();
        }
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE Connection error:", err);
      const now = new Date();
      const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setLogs(prev => [
        ...prev,
        { time: timeString, agent: "System", dept: "Network", message: "Disconnected from server log stream. Retrying connection...", type: "warning" }
      ]);
      eventSource.close();
    };
  };

  // ── Event Handlers ─────────────────────────────────────────────────────────

  const triggerSubmitFlow = async (pName: string, pIdea: string, fe: string, be: string, db: string) => {
    setLoading(true);
    setErrorMsg(null);
    setLogs([]);
    setFiles([]);
    setSelectedFile(null);

    try {
      const response = await fetch(`${API_BASE}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_name: pName,
          user_idea: pIdea,
          frontend_stack: fe,
          backend_stack: be,
          database_stack: db
        })
      });

      if (!response.ok) {
        throw new Error("Failed to start project generation. Make sure backend is running.");
      }

      const result = await response.json();
      setProjectId(result.project_id);
      setView("workspace");
      
      // Connect real-time log event stream
      connectSSE(result.project_id);

    } catch (err) {
      console.error("Generate submit error:", err);
      setErrorMsg(err instanceof Error ? err.message : "Could not connect to the backend server.");
    } finally {
      setLoading(false);
    }
  };

  const handleStartForge = (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName.trim() || !userIdea.trim()) return;
    triggerSubmitFlow(projectName, userIdea, frontendStack, backendStack, databaseStack);
  };

  const handleTrySampleProject = () => {
    const sampleName = "FinTech PayFlow Hub";
    const sampleIdea = "A robust payment orchestration gateway routing credit card API services dynamically, featuring a dashboard monitor panel and secret scanners.";
    setProjectName(sampleName);
    setUserIdea(sampleIdea);
    setFrontendStack("Next.js + Tailwind");
    setBackendStack("FastAPI");
    setDatabaseStack("PostgreSQL");
    
    triggerSubmitFlow(sampleName, sampleIdea, "Next.js + Tailwind", "FastAPI", "PostgreSQL");
  };

  const copyToClipboard = () => {
    if (!selectedFile) return;
    navigator.clipboard.writeText(selectedFile.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadBlueprint = () => {
    if (!projectId) return;
    window.location.href = `${API_BASE}/${projectId}/download`;
  };

  // Dynamic phase message mappings
  const getPhaseMessage = () => {
    switch (phase) {
      case "PLANNING":
        return "Planning Department actively aligning specifications...";
      case "ARCHITECTURE":
        return "Architecture Department drafting system topology...";
      case "ENGINEERING":
        return "Engineering Department compiling backend & frontend blueprints...";
      case "VALIDATION":
        return "Validation Department reviewing security, compliance & pipelines...";
      case "REVIEW":
        return "Engineering Director reviewing final compliance checklists...";
      case "COMPLETED":
        return "Project blueprints successfully compiled and validated!";
      case "FAILED":
        return "Pipeline aborted due to critical review rejections.";
      default:
        return "Processing orchestrator tasks...";
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex flex-col selection:bg-indigo-500 selection:text-white font-sans antialiased">
      
      {/* ── HEADER ──────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-[#09090b]/80 backdrop-blur-md border-b border-zinc-800/80 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer group" onClick={() => setView("landing")} aria-label="DevForge AI Homepage">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center font-bold text-white text-lg tracking-wider glow-indigo transition-transform group-hover:scale-105 duration-200">
            DF
          </div>
          <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
            DevForge <span className="text-indigo-400 font-semibold transition-colors group-hover:text-indigo-300">AI</span>
          </span>
        </div>
        <nav className="flex items-center gap-6" aria-label="Main Navigation">
          <button 
            onClick={() => setView("landing")}
            className={`text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-[#09090b] rounded px-2 py-1 ${view === "landing" ? "text-indigo-400" : "text-zinc-400 hover:text-zinc-200"}`}
          >
            Home
          </button>
          <button 
            onClick={() => setView("submission")}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 hover:-translate-y-0.5 active:translate-y-0 active:scale-98 font-bold text-sm text-white transition-all shadow-md glow-indigo focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-[#09090b]"
          >
            Forge Blueprint
          </button>
        </nav>
      </header>

      {/* ── ERROR TOAST ─────────────────────────────────────────────────────── */}
      {errorMsg && (
        <div className="bg-red-500/10 border-b border-red-500/30 text-red-400 text-xs px-6 py-3 font-semibold flex items-center justify-between animate-fade-in">
          <span className="flex items-center gap-2">
            <svg className="h-4 w-4 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            {errorMsg}
          </span>
          <button 
            onClick={() => setErrorMsg(null)} 
            className="text-red-400 hover:text-red-200 transition-colors focus:outline-none focus:ring-1 focus:ring-red-400 rounded px-1.5 py-0.5"
            aria-label="Dismiss error message"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ── MAIN CONTENT ────────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col">
        
        {/* ── VIEW 1: LANDING PAGE ─────────────────────────────────────────── */}
        {view === "landing" && (
          <section className="flex-1 flex flex-col justify-center items-center px-6 py-16 md:py-24 relative overflow-hidden">
            {/* Glowing backgrounds */}
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-indigo-600/5 blur-[120px] pointer-events-none" />
            <div className="absolute bottom-10 left-10 w-96 h-96 rounded-full bg-emerald-500/5 blur-[100px] pointer-events-none" />

            <div className="max-w-4xl text-center flex flex-col items-center gap-8 relative z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-indigo-400 text-xs font-semibold tracking-wide shadow-sm">
                <span className="text-indigo-500 animate-pulse">✦</span> Production Release 1.0.0
              </div>
              
              <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-white leading-[1.1] max-w-3xl">
                Transform Software Ideas into{" "}
                <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-indigo-500 bg-clip-text text-transparent font-black block mt-2">
                  Production-Ready Blueprints
                </span>
              </h1>

              <p className="text-zinc-400 text-base sm:text-lg md:text-xl max-w-2xl leading-relaxed font-normal">
                DevForge AI is an autonomous software studio where specialized AI agents—from Product Leads to Platform Engineers—collaborate to compile complete architecture blueprints, REST APIs, and database schemas.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 mt-6">
                <button
                  onClick={() => setView("submission")}
                  className="px-8 py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 hover:-translate-y-0.5 active:translate-y-0 active:scale-98 font-bold text-lg text-white transition-all shadow-lg glow-indigo flex items-center justify-center gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                >
                  Get Started
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </button>
                <button
                  onClick={handleTrySampleProject}
                  className="px-8 py-4 rounded-xl bg-zinc-900/60 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 font-bold text-lg text-zinc-300 transition-all flex items-center justify-center gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-700"
                >
                  ⚡ Try Sample Project
                </button>
              </div>
            </div>

            {/* Feature Highlights Grid */}
            <div className="max-w-6xl w-full grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 md:mt-32 px-4 relative z-10">
              <div className="p-6 rounded-2xl border border-zinc-850 bg-zinc-900/30 glass-panel hover:border-zinc-700 hover:-translate-y-1 transition-all duration-300 flex flex-col gap-4 group">
                <div className="h-10 w-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-lg transition-colors group-hover:bg-indigo-500/20 group-hover:text-indigo-300">
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white tracking-tight">11 Specialist Agents</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  Specialized AI workflows split across Planning, Architecture, Engineering, Validation, and Review departments for multi-perspective design.
                </p>
              </div>
              
              <div className="p-6 rounded-2xl border border-zinc-850 bg-zinc-900/30 glass-panel hover:border-zinc-700 hover:-translate-y-1 transition-all duration-300 flex flex-col gap-4 group">
                <div className="h-10 w-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-lg transition-colors group-hover:bg-emerald-500/20 group-hover:text-emerald-300">
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white tracking-tight">Rigorous Verification</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  Blueprints must pass structured validation steps including threat modeling, testing strategy plans, and an Engineering Director approval gate.
                </p>
              </div>

              <div className="p-6 rounded-2xl border border-zinc-850 bg-zinc-900/30 glass-panel hover:border-zinc-700 hover:-translate-y-1 transition-all duration-300 flex flex-col gap-4 group">
                <div className="h-10 w-10 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 flex items-center justify-center font-bold text-lg transition-colors group-hover:bg-violet-500/20 group-hover:text-violet-300">
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white tracking-tight">Ready-to-Deploy Blueprints</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  Downloads complete zipped packages containing detailed PRDs, system diagrams, OpenAPI specs, database SQL files, and documentation.
                </p>
              </div>
            </div>
          </section>
        )}

        {/* ── VIEW 2: SUBMISSION FORM ──────────────────────────────────────── */}
        {view === "submission" && (
          <section className="flex-1 flex justify-center items-center px-6 py-12 relative overflow-hidden">
            <div className="absolute top-10 left-10 w-72 h-72 bg-indigo-600/5 blur-[100px] pointer-events-none" />

            <div className="max-w-2xl w-full border border-zinc-800/80 bg-zinc-900/35 glass-panel rounded-2xl p-8 md:p-10 shadow-2xl relative z-10">
              <h2 className="text-3xl font-extrabold tracking-tight text-white mb-2">
                Launch Your Idea
              </h2>
              <p className="text-zinc-400 text-sm mb-8 leading-relaxed">
                Provide parameters for your application and watch DevForge AI agents debate, validate, and compile your architecture package.
              </p>

              <form onSubmit={handleStartForge} className="flex flex-col gap-6">
                <div className="flex flex-col gap-2">
                  <label htmlFor="projectName" className="text-sm font-bold text-zinc-300 flex items-center justify-between">
                    Project Name
                    <span className="text-xs text-zinc-500 font-normal">Identifies your blueprint files</span>
                  </label>
                  <input
                    type="text"
                    id="projectName"
                    placeholder="e.g., FinTech Payment Gateway"
                    required
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    className="w-full bg-zinc-950/80 border border-zinc-800 hover:border-zinc-700 focus:border-indigo-500 rounded-xl px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-sm transition-all"
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <label htmlFor="userIdea" className="text-sm font-bold text-zinc-300 flex items-center justify-between">
                    Software Idea Description
                    <span className="text-xs text-zinc-500 font-normal">Minimally 1-2 descriptive sentences</span>
                  </label>
                  <textarea
                    id="userIdea"
                    rows={4}
                    placeholder="Describe what your software should do, its target audience, and key functionalities..."
                    required
                    value={userIdea}
                    onChange={(e) => setUserIdea(e.target.value)}
                    className="w-full bg-zinc-950/80 border border-zinc-800 hover:border-zinc-700 focus:border-indigo-500 rounded-xl px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-sm transition-all resize-none leading-relaxed"
                  />
                </div>

                <div className="border-t border-zinc-800/60 pt-6">
                  <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest block mb-4">
                    Technology Stack Options
                  </span>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex flex-col gap-2">
                      <label htmlFor="feStack" className="text-xs font-bold text-zinc-500 uppercase tracking-wide">
                        Frontend
                      </label>
                      <input
                        type="text"
                        id="feStack"
                        value={frontendStack}
                        onChange={(e) => setFrontendStack(e.target.value)}
                        placeholder="Next.js + Tailwind"
                        className="w-full bg-zinc-950/80 border border-zinc-800 hover:border-zinc-700 focus:border-indigo-500 rounded-xl px-3.5 py-3 text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-xs transition-all"
                      />
                    </div>

                    <div className="flex flex-col gap-2">
                      <label htmlFor="beStack" className="text-xs font-bold text-zinc-500 uppercase tracking-wide">
                        Backend Service
                      </label>
                      <input
                        type="text"
                        id="beStack"
                        value={backendStack}
                        onChange={(e) => setBackendStack(e.target.value)}
                        placeholder="FastAPI"
                        className="w-full bg-zinc-950/80 border border-zinc-800 hover:border-zinc-700 focus:border-indigo-500 rounded-xl px-3.5 py-3 text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-xs transition-all"
                      />
                    </div>

                    <div className="flex flex-col gap-2">
                      <label htmlFor="dbStack" className="text-xs font-bold text-zinc-500 uppercase tracking-wide">
                        Database Store
                      </label>
                      <input
                        type="text"
                        id="dbStack"
                        value={databaseStack}
                        onChange={(e) => setDatabaseStack(e.target.value)}
                        placeholder="PostgreSQL"
                        className="w-full bg-zinc-950/80 border border-zinc-800 hover:border-zinc-700 focus:border-indigo-500 rounded-xl px-3.5 py-3 text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-xs transition-all"
                      />
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-4 py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 hover:-translate-y-0.5 active:translate-y-0 active:scale-98 font-bold text-lg text-white transition-all shadow-lg glow-indigo disabled:opacity-50 flex items-center justify-center gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 cursor-pointer"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Initializing Forge Workspace...
                    </>
                  ) : "Launch Forge Workspace"}
                </button>
              </form>
            </div>
          </section>
        )}

        {/* ── VIEW 3: LIVE WORKSPACE ────────────────────────────────────────── */}
        {view === "workspace" && (
          <section className="flex-1 flex flex-col lg:flex-row gap-6 p-6 max-w-7xl mx-auto w-full animate-fade-in">
            
            {/* Left Column: Progress timeline & Agent cards */}
            <div className="flex-1 flex flex-col gap-6 max-w-full lg:max-w-md">
              
              {/* Workspace Header Info */}
              <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/30 glass-panel shadow-sm relative overflow-hidden">
                <div className="flex justify-between items-start mb-4">
                  <div className="pr-4">
                    <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest block mb-1">
                      Project Generation
                    </span>
                    <h2 className="text-2xl font-extrabold text-white tracking-tight break-words">
                      {projectName}
                    </h2>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shrink-0 ${
                    phase === "COMPLETED" 
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : phase === "FAILED"
                        ? "bg-red-500/10 border-red-500/30 text-red-400"
                        : "bg-indigo-500/10 border-indigo-500/30 text-indigo-400 animate-pulse-slow"
                  }`}>
                    {phase === "COMPLETED" ? "Completed" : phase === "FAILED" ? "Failed" : "Active Forge"}
                  </span>
                </div>

                {/* Progress message */}
                <p className="text-zinc-400 text-xs font-medium mb-3 italic">
                  {getPhaseMessage()}
                </p>

                {/* Progress bar */}
                <div className="w-full bg-zinc-950 rounded-full h-2.5 mb-2 overflow-hidden border border-zinc-850">
                  <div 
                    className={`h-full transition-all duration-700 ease-out rounded-full ${
                      phase === "FAILED" 
                        ? "bg-red-500" 
                        : "bg-gradient-to-r from-indigo-500 to-violet-600"
                    }`}
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <div className="flex justify-between items-center text-[10px] text-zinc-500 font-bold uppercase tracking-wider">
                  <span>Pipeline Progress</span>
                  <span>{progress}%</span>
                </div>
              </div>

              {/* Department workflow sequence */}
              <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/30 glass-panel flex flex-col gap-4 shadow-sm">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                  Department Roadmap Flow
                </h3>
                
                <div className="flex flex-col gap-3 relative">
                  {/* Visual connecting line */}
                  <div className="absolute left-[23px] top-6 bottom-6 w-0.5 bg-zinc-800/80 -z-10" />

                  {[
                    { key: "PLANNING", label: "Planning Department", agents: "Product Lead, Analyst, Designer" },
                    { key: "ARCHITECTURE", label: "Architecture Department", agents: "Principal Architect" },
                    { key: "ENGINEERING", label: "Engineering Department", agents: "Backend & Frontend Leads" },
                    { key: "VALIDATION", label: "Validation Department", agents: "Security, QA, Platform Engineers" },
                    { key: "REVIEW", label: "Review Department", agents: "Engineering Director" }
                  ].map((p, idx) => {
                    const phaseKeys = ["PLANNING", "ARCHITECTURE", "ENGINEERING", "VALIDATION", "REVIEW", "COMPLETED", "FAILED"];
                    const currentIdx = phaseKeys.indexOf(phase);
                    const configIdx = phaseKeys.indexOf(p.key);
                    
                    const isPassed = phase === "COMPLETED" || (phase !== "FAILED" && currentIdx > configIdx);
                    const isActive = phase === p.key;
                    const isFailed = phase === "FAILED" && currentIdx === configIdx;
                    
                    return (
                      <div 
                        key={p.key} 
                        className={`flex items-center justify-between p-3.5 rounded-xl border transition-all duration-300 relative z-10 ${
                          isActive 
                            ? "bg-indigo-500/5 border-indigo-500/30 text-white shadow-md shadow-indigo-500/5 ring-1 ring-indigo-500/20" 
                            : isPassed 
                              ? "bg-zinc-950/40 border-zinc-900/60 text-zinc-400"
                              : isFailed
                                ? "bg-red-500/5 border-red-500/30 text-red-400"
                                : "bg-zinc-950/15 border-zinc-900/40 text-zinc-600"
                        }`}
                      >
                        <div className="flex items-center gap-3.5">
                          <span className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 transition-all ${
                            isActive 
                              ? "bg-indigo-600 text-white shadow-sm shadow-indigo-500/50"
                              : isPassed 
                                ? "bg-emerald-950 border border-emerald-500/40 text-emerald-400"
                                : isFailed
                                  ? "bg-red-950 border border-red-500/40 text-red-400"
                                  : "bg-zinc-900 border border-zinc-800 text-zinc-600"
                          }`}>
                            {isPassed ? "✓" : isFailed ? "✗" : idx + 1}
                          </span>
                          <div>
                            <p className={`text-sm font-bold tracking-tight ${isActive ? "text-white" : isFailed ? "text-red-400" : isPassed ? "text-zinc-300" : "text-zinc-500"}`}>{p.label}</p>
                            <p className="text-[11px] text-zinc-500 mt-0.5">{p.agents}</p>
                          </div>
                        </div>
                        {isActive && (
                          <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-widest animate-pulse">
                            Running
                          </span>
                        )}
                        {isPassed && (
                          <span className="text-[10px] text-emerald-500 font-bold uppercase tracking-widest">
                            Done
                          </span>
                        )}
                        {isFailed && (
                          <span className="text-[10px] text-red-500 font-bold uppercase tracking-widest">
                            Failed
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Active Agent Status Card */}
              <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/30 glass-panel flex flex-col gap-3 shadow-sm">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                  Active Specialist Agent
                </h3>
                
                <div className="flex items-center gap-4 bg-zinc-950/60 p-4 rounded-xl border border-zinc-850">
                  <div className="h-12 w-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center text-2xl shadow-inner shrink-0">
                    🤖
                  </div>
                  <div className="min-w-0 flex-1">
                    <h4 className="text-md font-bold text-white tracking-tight truncate">{activeAgent}</h4>
                    <p className="text-xs text-zinc-500 mt-0.5">
                      Status: <span className={phase === "COMPLETED" ? "text-zinc-400 font-medium" : "text-indigo-400 font-semibold animate-pulse"}>
                        {phase === "COMPLETED" ? "IDLE" : "RUNNING"}
                      </span>
                    </p>
                  </div>
                </div>
              </div>

            </div>

            {/* Right Column: Logging timeline feed & Artifact Explorer */}
            <div className="flex-1 flex flex-col gap-6">
              
              {/* Event Streams Log Panel */}
              <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/30 glass-panel h-80 flex flex-col shadow-sm">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-3.5 flex items-center justify-between">
                  <span>Orchestrator SSE Log Stream</span>
                  <span className={`h-2.5 w-2.5 rounded-full border transition-all ${
                    phase === "COMPLETED" 
                      ? "bg-emerald-500 border-emerald-500/30 shadow-emerald" 
                      : phase === "FAILED" 
                        ? "bg-red-500 border-red-500/30 shadow-red" 
                        : "bg-indigo-500 border-indigo-500/30 animate-pulse"
                  }`} />
                </h3>
                
                <div className="flex-1 overflow-y-auto bg-zinc-950/80 rounded-xl p-4 border border-zinc-850 font-mono text-[11px] flex flex-col gap-2.5 scrollbar-thin">
                  {logs.map((log, idx) => (
                    <div key={idx} className="flex gap-2.5 items-start pl-2 transition-all leading-relaxed">
                      <span className="text-zinc-600 select-none text-[10px] mt-0.5 shrink-0">{log.time}</span>
                      <span className="text-indigo-400 font-semibold select-none shrink-0">[{log.agent}]:</span>
                      <span className={`break-words ${
                        log.type === "success" 
                          ? "text-emerald-400 font-medium" 
                          : log.type === "warning" 
                            ? "text-amber-400 font-medium" 
                            : log.type === "error" 
                              ? "text-red-400 font-medium" 
                              : "text-zinc-300"
                      }`}>{log.message}</span>
                    </div>
                  ))}
                  {logs.length === 0 && (
                    <div className="text-zinc-650 italic flex items-center gap-2 p-2">
                      <svg className="animate-spin h-3.5 w-3.5 text-zinc-600" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Connecting to background worker event queue...
                    </div>
                  )}
                  <div ref={logsEndRef} />
                </div>
              </div>

              {/* Artifacts Preview Explorer */}
              <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/30 glass-panel flex-1 flex flex-col min-h-[450px] shadow-sm">
                <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 mb-4 pb-2 border-b border-zinc-800/60">
                  <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                    Generated Blueprint Explorer
                  </h3>
                  {phase === "COMPLETED" && (
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={copyToClipboard}
                        className="px-3.5 py-2 bg-zinc-800 hover:bg-zinc-750 text-zinc-200 border border-zinc-700 hover:border-zinc-600 font-bold text-xs rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-zinc-600"
                      >
                        {copied ? "Copied!" : "Copy"}
                      </button>
                      <button
                        onClick={downloadBlueprint}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 font-bold text-xs text-white rounded-lg transition-all shadow-md hover:-translate-y-0.5 active:translate-y-0 glow-indigo flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        Download Blueprint
                      </button>
                    </div>
                  )}
                </div>

                {phase !== "COMPLETED" ? (
                  <div className="flex-1 flex flex-col items-center justify-center gap-3 text-zinc-500 py-10">
                    <span className="text-5xl animate-pulse-slow">📦</span>
                    <p className="text-sm font-medium">
                      {phase === "FAILED" ? "Generation aborted due to validation fail." : "Artifact package generating..."}
                    </p>
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col gap-4 animate-fade-in">
                    
                    {/* Completion Success Header */}
                    <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 flex items-center justify-between gap-4">
                      <div>
                        <h4 className="text-emerald-400 font-bold text-sm">Project Generated Successfully</h4>
                        <p className="text-zinc-400 text-xs mt-0.5">All blueprints and artifact packages are ready for deployment.</p>
                      </div>
                      <span className="h-8 w-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-black shrink-0">
                        ✓
                      </span>
                    </div>

                    {/* Tab Selection */}
                    <div className="flex overflow-x-auto gap-2 pb-1 scrollbar-thin">
                      {files.map(f => (
                        <button
                          key={f.name}
                          onClick={() => setSelectedFile(f)}
                          className={`px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all border focus:outline-none focus:ring-1 focus:ring-indigo-500 ${
                            selectedFile?.name === f.name
                              ? "bg-zinc-800 border-zinc-700 text-white"
                              : "bg-zinc-900/40 border-zinc-850 hover:border-zinc-750 text-zinc-400 hover:text-zinc-200"
                          }`}
                        >
                          {f.name}
                        </button>
                      ))}
                    </div>

                    {/* Styled Document / Code Preview pane */}
                    <div className="flex-1 bg-zinc-950/80 border border-zinc-850 rounded-xl p-5 overflow-y-auto max-h-[400px] scrollbar-thin shadow-inner">
                      {selectedFile?.language === "markdown" ? (
                        renderMarkdownContent(selectedFile.content)
                      ) : (
                        <pre className="font-mono text-[11px] text-zinc-300 whitespace-pre-wrap leading-6 font-medium selection:bg-indigo-600/30">
                          {selectedFile?.content}
                        </pre>
                      )}
                    </div>
                  </div>
                )}
              </div>

            </div>

          </section>
        )}

      </main>

      {/* ── FOOTER ──────────────────────────────────────────────────────────── */}
      <footer className="border-t border-zinc-900 px-6 py-6 text-center text-xs text-zinc-650 bg-[#09090b]">
        <p>© 2026 DevForge AI. All rights reserved. Structured Software Studio Blueprint Forge.</p>
      </footer>
    </div>
  );
}
