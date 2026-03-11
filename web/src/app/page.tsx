"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Note {
  title?: string;
  themes?: string[];
  quotes?: { theme: string; text: string }[];
  actions?: string[];
  meta?: { date_range?: string; total_reviews?: number };
}

export default function Home() {
  const [note, setNote] = useState<Note | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [recipientEmail, setRecipientEmail] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [dryRun, setDryRun] = useState(false);
  const [sending, setSending] = useState(false);

  const runPipeline = async () => {
    setLoading(true);
    setMessage({ type: "success", text: "Pipeline started. This may take 2–5 minutes. Please wait…" });
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 min timeout
      const res = await fetch(`${API_URL}/api/pipeline`, {
        method: "POST",
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.message || "Pipeline failed");
      setNote(data.note);
      setMessage({ type: "success", text: data.message });
    } catch (e) {
      if (e instanceof Error) {
        const msg = e.name === "AbortError" ? "Request timed out. Try again or use Load Latest Note." : e.message;
        setMessage({ type: "error", text: msg });
      } else {
        setMessage({ type: "error", text: "Pipeline failed. Is the API running on port 8000?" });
      }
    } finally {
      setLoading(false);
    }
  };

  const loadNote = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`${API_URL}/api/note`);
      const data = await res.json();
      if (!data.note) throw new Error(data.message || "No note found");
      setNote(data.note);
      setMessage({ type: "success", text: "Note loaded" });
    } catch (e) {
      setMessage({ type: "error", text: e instanceof Error ? e.message : "Failed" });
    } finally {
      setLoading(false);
    }
  };

  const sendEmail = async () => {
    const email = recipientEmail.trim();
    if (!email) {
      setMessage({ type: "error", text: "Recipient email is required. Replace you@example.com with a real address." });
      return;
    }
    if (email === "you@example.com") {
      setMessage({ type: "error", text: "Please enter a real recipient email, not the placeholder." });
      return;
    }
    setSending(true);
    setMessage(null);
    try {
      const res = await fetch(`${API_URL}/api/send-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipient_email: email,
          recipient_name: recipientName.trim() || undefined,
          dry_run: dryRun,
        }),
      });
      let data: { message?: string; detail?: string };
      try {
        data = await res.json();
      } catch {
        throw new Error("Invalid response from server");
      }
      if (!res.ok) throw new Error(data.detail || data.message || "Send failed");
      setMessage({ type: "success", text: data.message || "Email sent." });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to send. Check SMTP settings in .env.";
      setMessage({ type: "error", text: msg });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="relative max-w-3xl mx-auto px-6 py-8">
      {/* INDMoney-style top nav */}
      <nav className="flex items-center justify-between mb-12 pb-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold bg-gradient-to-r from-[#00d4aa] via-[#0ea5e9] to-[#6366f1] bg-clip-text text-transparent">
            INDmoney
          </span>
          <span className="text-white/60">|</span>
          <span className="text-white/90 font-medium">Review Insights</span>
        </div>
      </nav>

      <header className="mb-10">
        <h1 className="text-3xl font-bold text-white tracking-tight">
          Weekly Review Pulse
        </h1>
        <p className="text-white/60 mt-2 text-lg">Generate one-pager and send email to stakeholders</p>
      </header>

      {/* Generate / Load */}
      <section className="mb-10">
        <div className="flex gap-4 flex-wrap">
          <button
            onClick={runPipeline}
            disabled={loading}
            className="px-6 py-3 bg-gradient-to-r from-[#00d4aa] to-[#0ea5e9] hover:from-[#00e6b8] hover:to-[#38bdf8] disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed text-slate-900 font-semibold rounded-xl shadow-lg shadow-emerald-500/20 transition-all duration-200"
          >
            {loading ? "Running…" : "Generate One-Pager"}
          </button>
          <button
            onClick={loadNote}
            disabled={loading}
            className="px-6 py-3 bg-white/10 hover:bg-white/15 backdrop-blur-sm border border-white/20 disabled:opacity-60 text-white font-medium rounded-xl transition-all duration-200"
          >
            Load Latest Note
          </button>
        </div>
        <p className="text-sm text-white/50 mt-3">
          Generate runs Phases 1–3 (fetch, themes, weekly note) — takes 2–5 min. Load fetches existing note.
        </p>
      </section>

      {message && (
        <div
          className={`mb-6 px-4 py-3 rounded-xl backdrop-blur-sm border ${
            message.type === "success"
              ? "bg-emerald-500/20 text-emerald-100 border-emerald-400/30"
              : "bg-red-500/20 text-red-100 border-red-400/30"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Note display */}
      {note && (
        <section className="mb-10 p-6 bg-white/[0.07] backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl shadow-black/20">
          <h2 className="text-xl font-semibold text-white mb-4">
            {note.title || "Weekly Pulse"}
          </h2>
          {note.meta && (
            <p className="text-sm text-white/60 mb-5">
              {note.meta.date_range} · {note.meta.total_reviews} reviews
            </p>
          )}
          {note.themes && note.themes.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-[#00d4aa] mb-3">Key Themes</h3>
              <ul className="space-y-2">
                {note.themes.map((t, i) => (
                  <li key={i} className="text-white/90 pl-3 border-l-2 border-[#00d4aa]/50">
                    {i + 1}. {t}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {note.quotes && note.quotes.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-[#00d4aa] mb-3">Quotes</h3>
              <ul className="space-y-4">
                {note.quotes.map((q, i) => (
                  <li key={i} className="text-white/80 text-sm pl-4 border-l-2 border-[#00d4aa]/40">
                    <span className="font-medium text-[#00d4aa]/90">{q.theme}:</span> &quot;{q.text}&quot;
                  </li>
                ))}
              </ul>
            </div>
          )}
          {note.actions && note.actions.length > 0 && (
            <div>
              <h3 className="font-semibold text-[#00d4aa] mb-3">Recommended Actions</h3>
              <ol className="list-decimal list-inside space-y-2 text-white/80 text-sm">
                {note.actions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ol>
            </div>
          )}
        </section>
      )}

      {/* Send email */}
      <section className="p-6 bg-white/[0.07] backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl shadow-black/20">
        <h2 className="text-xl font-semibold text-white mb-5">
          Send Email
        </h2>
        <div className="space-y-5">
          <div>
            <label className="block text-sm text-white/70 mb-1.5 font-medium">Recipient email</label>
            <input
              type="email"
              value={recipientEmail}
              onChange={(e) => setRecipientEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-[#00d4aa]/50 focus:border-[#00d4aa]/50"
            />
          </div>
          <div>
            <label className="block text-sm text-white/70 mb-1.5 font-medium">Recipient name (for greeting)</label>
            <input
              type="text"
              value={recipientName}
              onChange={(e) => setRecipientName(e.target.value)}
              placeholder="Dhaval Patel"
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-[#00d4aa]/50 focus:border-[#00d4aa]/50"
            />
          </div>
          <label className="flex items-center gap-3 text-sm text-white/70 cursor-pointer">
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
              className="rounded border-white/30 bg-white/10 text-[#00d4aa] focus:ring-[#00d4aa]"
            />
            Dry run (save draft only, don&apos;t send)
          </label>
          <button
            onClick={sendEmail}
            disabled={sending}
            className="px-6 py-3 bg-gradient-to-r from-[#00d4aa] to-[#0ea5e9] hover:from-[#00e6b8] hover:to-[#38bdf8] disabled:from-slate-600 disabled:to-slate-700 disabled:opacity-60 text-slate-900 font-semibold rounded-xl shadow-lg shadow-emerald-500/20 transition-all duration-200"
          >
            {sending ? "Sending…" : dryRun ? "Save Draft" : "Send Email"}
          </button>
        </div>
      </section>

      <footer className="mt-14 pt-6 border-t border-white/10 text-center">
        <p className="text-white/60" style={{ fontSize: "26px" }}>
          Crafted by <span className="text-[#00d4aa] font-medium">Dhaval Patel</span> for the Smart Investing
        </p>
      </footer>
    </div>
  );
}
