"use client";

import { useEffect, useState } from "react";
import { askQuestion, listPapers, uploadPaper, type Answer, type Paper } from "@/lib/api";

export default function Home() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  // Load the paper list when the page opens, and refresh it.
  async function refreshPapers() {
    try {
      setPapers(await listPapers());
    } catch (e) {
      setError(String(e));
    }
  }
  useEffect(() => {
    refreshPapers();
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await uploadPaper(file);
      // Ingestion is async on the backend; poll a few times for the paper to appear.
      for (let i = 0; i < 10; i++) {
        await new Promise((r) => setTimeout(r, 1500));
        await refreshPapers();
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setUploading(false);
    }
  }

  async function handleAsk() {
    if (question.trim().length < 3) return;
    setLoading(true);
    setError("");
    setAnswer(null);
    try {
      setAnswer(await askQuestion(question));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-2xl font-semibold mb-1">Research Paper Analyzer</h1>
      <p className="text-gray-500 mb-8">Upload papers, ask questions, get cited answers.</p>

      {error && (
        <div className="mb-6 rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Upload */}
      <section className="mb-8">
        <label className="block text-sm font-medium mb-2">Upload a PDF</label>
        <input
          type="file"
          accept="application/pdf"
          onChange={handleUpload}
          disabled={uploading}
          className="block w-full text-sm file:mr-4 file:rounded-md file:border-0
                     file:bg-gray-900 file:px-4 file:py-2 file:text-white
                     hover:file:bg-gray-700 disabled:opacity-50"
        />
        {uploading && <p className="mt-2 text-sm text-gray-500">Processing…</p>}
      </section>

      {/* Papers */}
      <section className="mb-8">
        <h2 className="text-sm font-medium mb-2">Papers ({papers.length})</h2>
        {papers.length === 0 ? (
          <p className="text-sm text-gray-400">No papers yet.</p>
        ) : (
          <ul className="text-sm text-gray-700 space-y-1">
            {papers.map((p) => (
              <li key={p.id} className="rounded bg-gray-50 px-3 py-1.5">{p.id}</li>
            ))}
          </ul>
        )}
      </section>

      {/* Ask */}
      <section className="mb-8">
        <label className="block text-sm font-medium mb-2">Ask a question</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            placeholder="How many attention heads does the model use?"
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
          <button
            onClick={handleAsk}
            disabled={loading || question.trim().length < 3}
            className="rounded-md bg-gray-900 px-4 py-2 text-sm text-white
                       hover:bg-gray-700 disabled:opacity-50"
          >
            {loading ? "Thinking…" : "Ask"}
          </button>
        </div>
      </section>

      {/* Answer */}
      {answer && (
        <section className="rounded-lg border border-gray-200 p-5">
          <p className="mb-4 whitespace-pre-wrap">{answer.answer}</p>
          {!answer.is_refusal && answer.citations.length > 0 && (
            <div className="border-t border-gray-100 pt-4">
              <h3 className="text-xs font-medium text-gray-500 mb-2">Sources</h3>
              <ul className="space-y-2">
                {answer.citations.map((c, i) => (
                  <li key={i} className="text-xs text-gray-600">
                    <span className="font-medium">{c.doc_id}, p.{c.page}</span>
                    <span className="text-gray-400"> · score {c.score.toFixed(2)}</span>
                    <p className="mt-0.5 text-gray-500 line-clamp-2">{c.snippet}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </main>
  );
}