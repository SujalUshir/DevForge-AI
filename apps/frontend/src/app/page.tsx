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
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/projects";

// ── Custom Markdown Preview Renderer ─────────────────────────────────────────

function renderMarkdownContent(text: string) {
  const lines = text.split("\n");
  return (
    <div className="space-y-2 text-zinc-300 text-sm leading-relaxed">
      {lines.map((line, idx) => {
        // Heading 1
        if (line.startsWith("# ")) {
          return (
            <h1 key={idx} className="text-2xl font-black text-white mt-6 mb-3 border-b border-zinc-800 pb-2">
              {line.replace("# ", "")}
            </h1>
          );
        }
        // Heading 2
        if (line.startsWith("## ")) {
          return (
            <h2 key={idx} className="text-lg font-bold text-zinc-100 mt-5 mb-2 flex items-center gap-2">
              <span className="text-indigo-400">#</span> {line.replace("## ", "")}
            </h2>
          );
        }
        // Heading 3
        if (line.startsWith("### ")) {
          return (
            <h3 key={idx} className="text-md font-semibold text-zinc-200 mt-4 mb-2">
              {line.replace("### ", "")}
            </h3>
          );
        }
        // Bullet list
        if (line.startsWith("- ")) {
          return (
            <div key={idx} className="flex items-start gap-2 ml-4 my-1">
              <span className="text-indigo-500 mt-1.5 h-1.5 w-1.5 rounded-full bg-indigo-500 shrink-0" />
              <span>{line.replace("- ", "")}</span>
            </div>
          );
        }
        // Empty line spacer
        if (line.trim() === "") {
          return <div key={idx} className="h-2" />;
        }
        // Default text paragraph
        return <p key={idx}>{line}</p>;
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
    } catch (err: any) {
      console.error("Fetch artifacts error:", err);
      setErrorMsg(err.message || "Could not load artifacts.");
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

    } catch (err: any) {
      console.error("Generate submit error:", err);
      setErrorMsg(err.message || "Could not connect to the backend server.");
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

      {/* ── ERROR TOAST ─────────────────────────────────────────────────────── */}
      {errorMsg && (
        <div className="bg-red-500/15 border-b border-red-500/30 text-red-400 text-xs px-6 py-3 font-semibold flex items-center justify-between">
          <span>⚠️ {errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-red-400 hover:text-red-200">Dismiss</button>
        </div>
      )}

      {/* ── MAIN CONTENT ────────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col">
        
        {/* ── VIEW 1: LANDING PAGE ─────────────────────────────────────────── */}
        {view === "landing" && (
          <section className="flex-1 flex flex-col justify-center items-center px-6 py-20 relative overflow-hidden">
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />
            <div className="absolute bottom-10 left-10 w-72 h-72 rounded-full bg-emerald-500/5 blur-[100px] pointer-events-none" />

            <div className="max-w-4xl text-center flex flex-col items-center gap-8 relative z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-indigo-400 text-xs font-semibold tracking-wide">
                <span>✦</span> Release Candidate 1.0.0-rc1
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
                  className="px-8 py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-lg text-white transition-all shadow-lg glow-indigo flex items-center justify-center gap-2 animate-bounce"
                >
                  Get Started
                </button>
                <button
                  onClick={handleTrySampleProject}
                  className="px-8 py-4 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 font-bold text-lg text-zinc-300 transition-all flex items-center justify-center gap-2"
                >
                  ⚡ Try Sample Project
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
                  disabled={loading}
                  className="w-full mt-4 py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-lg text-white transition-all shadow-lg glow-indigo disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Initializing Workspace...
                    </>
                  ) : "Launch Forge Workspace"}
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
                      {projectName}
                    </h2>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold tracking-wide border ${
                    phase === "COMPLETED" 
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : phase === "FAILED"
                        ? "bg-red-500/10 border-red-500/30 text-red-400"
                        : "bg-indigo-500/10 border-indigo-500/30 text-indigo-400 animate-pulse-slow"
                  }`}>
                    {phase === "COMPLETED" ? "Completed" : phase === "FAILED" ? "Failed" : "Active Forge"}
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-zinc-950 rounded-full h-2 mb-2 overflow-hidden border border-zinc-800">
                  <div 
                    className={`h-full transition-all duration-500 ease-out ${
                      phase === "FAILED" ? "bg-red-500" : "bg-gradient-to-r from-indigo-500 to-violet-600"
                    }`}
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
                    const phaseKeys = ["PLANNING", "ARCHITECTURE", "ENGINEERING", "VALIDATION", "REVIEW", "COMPLETED"];
                    const currentIdx = phaseKeys.indexOf(phase);
                    const configIdx = phaseKeys.indexOf(p.key);
                    
                    const isPassed = currentIdx > configIdx;
                    const isActive = phase === p.key;
                    
                    return (
                      <div 
                        key={p.key} 
                        className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
                          isActive 
                            ? "bg-indigo-500/5 border-indigo-500/30 text-white animate-pulse" 
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
                
                <div className="flex items-center gap-4 bg-zinc-950/50 p-4 rounded-xl border border-zinc-800 animate-pulse-slow">
                  <div className="h-12 w-12 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-2xl">
                    🤖
                  </div>
                  <div>
                    <h4 className="text-lg font-bold text-white">{activeAgent}</h4>
                    <p className="text-xs text-zinc-500">Status: {phase === "COMPLETED" ? "IDLE" : "RUNNING"}</p>
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
                  <span className={`h-2 w-2 rounded-full ${
                    phase === "COMPLETED" ? "bg-emerald-500" : phase === "FAILED" ? "bg-red-500" : "bg-indigo-500 animate-pulse"
                  }`} />
                </h3>
                
                <div className="flex-1 overflow-y-auto bg-zinc-950/80 rounded-lg p-4 border border-zinc-800 font-mono text-xs flex flex-col gap-3">
                  {logs.map((log, idx) => (
                    <div key={idx} className="flex gap-2 items-start border-l-2 pl-3 border-zinc-800/80 hover:border-indigo-500/50 transition-all">
                      <span className="text-zinc-500 select-none">{log.time}</span>
                      <span className="text-indigo-400 font-semibold select-none">[{log.agent}]:</span>
                      <span className={`${
                        log.type === "success" ? "text-emerald-400" : log.type === "warning" ? "text-yellow-400" : log.type === "error" ? "text-red-400" : "text-zinc-300"
                      }`}>{log.message}</span>
                    </div>
                  ))}
                  {logs.length === 0 && (
                    <div className="text-zinc-600 italic">Connecting to background worker event queue...</div>
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
                  {phase === "COMPLETED" && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={copyToClipboard}
                        className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 font-bold text-xs rounded-lg transition-all"
                      >
                        {copied ? "Copied!" : "Copy"}
                      </button>
                      <button
                        onClick={downloadBlueprint}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 font-bold text-xs text-white rounded-lg transition-all shadow-md glow-indigo flex items-center gap-1.5"
                      >
                        Download Blueprint
                      </button>
                    </div>
                  )}
                </div>

                {phase !== "COMPLETED" ? (
                  <div className="flex-1 flex flex-col items-center justify-center gap-3 text-zinc-500">
                    <span className="text-4xl animate-pulse-slow">📦</span>
                    <p className="text-sm font-medium">
                      {phase === "FAILED" ? "Generation aborted due to validation fail." : "Artifact package generating..."}
                    </p>
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

                    {/* Styled Document / Code Preview pane */}
                    <div className="flex-1 bg-zinc-950/80 border border-zinc-800 rounded-lg p-5 overflow-y-auto max-h-[350px]">
                      {selectedFile?.language === "markdown" ? (
                        renderMarkdownContent(selectedFile.content)
                      ) : (
                        <pre className="font-mono text-xs text-zinc-300 whitespace-pre-wrap leading-5">
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
      <footer className="border-t border-zinc-800 px-6 py-6 text-center text-xs text-zinc-500">
        <p>© 2026 DevForge AI. All rights reserved. Structured Software Studio Blueprint Forge.</p>
      </footer>
    </div>
  );
}
