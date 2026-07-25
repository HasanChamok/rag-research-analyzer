// All backend communication lives here.
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Citation {
  doc_id: string;
  page: number;
  score: number;
  snippet: string;
}

export interface Answer {
  answer: string;
  is_refusal: boolean;
  citations: Citation[];
}

export interface Paper {
  id: string;
  chunks: number | null;
}

export async function listPapers(): Promise<Paper[]> {
  const res = await fetch(`${API}/papers`);
  if (!res.ok) throw new Error(`Failed to list papers (${res.status})`);
  return res.json();
}

export async function uploadPaper(file: File): Promise<void> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/papers`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed (${res.status})`);
}

export async function askQuestion(question: string, topK = 5): Promise<Answer> {
  const res = await fetch(`${API}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
  });
  if (!res.ok) throw new Error(`Ask failed (${res.status})`);
  return res.json();
}