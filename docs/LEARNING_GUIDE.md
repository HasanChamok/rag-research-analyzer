# The RAG Pipeline — Complete Learning Guide (Phases 0–1)

> A self-contained explanation of everything we built: the theory behind it, every line of
> code, variations you could have chosen, exercises to make it stick, and the complete
> interview speech. Written so you can rebuild the whole system from a blank folder with
> no help. Suggested repo location: `docs/LEARNING_GUIDE.md`.

---

# Part 1 — The Big Picture

## The problem RAG solves

An LLM is a next-token predictor with knowledge frozen in its weights at training time
(see Part 7 refs: Vaswani et al. 2017; Lewis et al. 2020). Two consequences:

1. It has never read *your* PDF — it cannot answer questions about it.
2. When it doesn't know, it often fabricates fluent, plausible nonsense (**hallucination**).

**RAG (Retrieval-Augmented Generation)** fixes both without touching the model: find the
relevant pieces of your documents, paste them into the prompt, and instruct the model to
answer only from them. The model becomes an open-book exam taker instead of a
closed-book one.

## The pipeline (our five modules)

```
 PDF file
    │
    ▼
┌──────────┐   pages: [{page, text}, ...]
│ loader   │──────────────┐
└──────────┘              ▼
                    ┌──────────┐   chunks: [{id, page, text}, ...]
                    │ chunker  │──────────────┐
                    └──────────┘              ▼
                                        ┌──────────┐   matrix (n_chunks × 384)
                                        │ embedder │──────────────┐
                                        └──────────┘              ▼
                                                            ┌──────────┐
                                 question ──── embedder ───▶│ search   │ top-k chunks
                                                            └────┬─────┘
                                                                 ▼
                                                            ┌──────────┐
                                                            │generator │ cited answer
                                                            └──────────┘
```

**Ingestion path** (once per document): load → chunk → embed → store vectors.
**Query path** (every question): embed question → search → build prompt → generate.

The key design invariant: **the page number is attached at load time and never dropped** —
it rides along through chunking, into search results, into the prompt, and out in the
answer as "(p. 5)". Citations cannot be bolted on later; they must survive the whole trip.

---

# Part 2 — loader.py (PDF → pages)

## Theory

PDFs are *layout* formats, not text formats — they store positioned glyphs, not paragraphs.
Extraction reconstructs reading order heuristically, so output is always imperfect
(headers/footers intermixed, formulas garbled, figure labels shredded into single words —
we saw all three). Foundational truth: **retrieval quality is capped by extraction
quality.** Garbage in, garbage retrieved.

## The code

```python
import fitz  # pymupdf — imports as "fitz" for historical reasons

def load_pdf(path: str) -> list[dict]:
    doc = fitz.open(path)
    pages = [{"page": i + 1, "text": p.get_text()} for i, p in enumerate(doc)]
    doc.close()
    return pages
```

Line by line:
- `fitz.open(path)` — opens the PDF, returns a document object you can iterate page by page.
- `enumerate(doc)` — gives `(0, page0), (1, page1)...`; we store `i + 1` because humans
  count pages from 1.
- `p.get_text()` — extracts that page's text in reading order (best effort).
- `doc.close()` — releases the file handle (on Windows, an open handle can block other
  programs from touching the file).

**Why per-page dicts and not one big string:** the page number must travel with the text.
One string = positional metadata destroyed = no citations, ever.

## Variations (and when you'd choose them)

| Variation | What | When |
|---|---|---|
| `page.get_text("blocks")` | returns positioned text blocks | filter headers/footers by position |
| pdfplumber library | strong table extraction | data-heavy papers |
| GROBID | ML model that parses papers into structured XML (title, sections, refs) | production-grade academic parsing (our Phase 8 candidate) |
| OCR (pytesseract) | image-based/scanned PDFs | when get_text() returns nothing |

## Exercise
Print `len(page.get_text())` per page for the Attention paper. Pages 13–15 are tiny/weird —
figure pages. How would you auto-detect and skip them? (One answer: threshold on
characters-per-page, or ratio of newlines to characters.)

---

# Part 3 — chunker.py (pages → chunks)

## Theory: the two opposing forces

1. **Small chunks → precise vectors.** An embedding is one vector summarizing the WHOLE
   input. Embed a full page and the vector is an average of ten topics — a query about one
   of them matches weakly ("the dropout sentence barely registers"). 
2. **Big chunks → usable context.** The LLM answers from what you hand it; a 50-char
   fragment ("rate of 0.1 was used") lacks the context to be understood.

Sweet spot for prose: ~500–1500 characters (we verified empirically: 300 → incoherent
fragments; 3000 → multi-topic mush). **Overlap** exists because any cut boundary splits
whatever sentence sits on it; repeating the previous chunk's tail guarantees every
sentence survives whole in at least one chunk.

```
1. No chunking      [████████████ whole page ████████████]   one muddy vector
2. Fixed, no overlap [chunk 1][chunk 2]✂[chunk 3][chunk 4]   ✂ = sentence cut in half
3. Fixed + overlap   [chunk 1▓][▓chunk 2▓][▓chunk 3▓][▓4]    ▓ = shared text, sentences survive
4. Structure-aware   [ Intro  ][  Method ][Results][Refs]    follows sections, harder to build
```

## The code

```python
def chunk_pages(pages: list[dict], chunk_size: int = 1000, overlap: int = 200) -> list[dict]:
    chunks = []
    for page in pages:                      # one page at a time (chunks never cross pages)
        text = page["text"]
        start = 0                           # the cutting cursor
        while start < len(text):
            end = start + chunk_size        # propose a cut 1000 chars ahead
            if end < len(text):             # (skip on the final leftover piece)
                next_space = text.find(" ", end)
                if next_space != -1:
                    end = next_space        # nudge the cut to a word boundary
            chunk_text = text[start:end].strip()
            if chunk_text:                  # skip pure-whitespace fragments
                chunks.append({"id": len(chunks), "page": page["page"], "text": chunk_text})
            start = end - overlap           # advance BUT step 200 back → the overlap
    return chunks
```

Mental model: *a cursor slides across each page in ~1000-char steps, nudges each cut to a
space, saves the slice with its page number, and steps 200 back before the next cut.*

**The bug we hit (and its universal lesson):** an indentation slip put `start = end - overlap`
inside the `if end < len(text):` block. On each page's final chunk that condition is false,
the body is skipped, `start` never advances → infinite loop. **Golden rule: a while-loop's
variable must advance on every iteration, unconditionally.** Debugging trick learned:
Ctrl+C on a hung program prints a traceback showing exactly which line it was stuck on.

## Variations

| Strategy | Idea | Pros | Cons |
|---|---|---|---|
| Fixed size (ours) | cut every N chars | trivial, fast, predictable | structure-blind |
| Sentence-based | split on sentences, group to ~N chars | never cuts mid-sentence | needs sentence detection (abbreviations break naive splitting) |
| Recursive (LangChain-style) | try splitting on \n\n, then \n, then ". ", then " " | respects structure when present | more logic |
| Section-aware | split at headings ("3.2 Attention") | best coherence for papers | fragile PDF heading detection; uneven sizes |
| Semantic | embed sentences, cut where similarity between neighbors drops | topically pure chunks | slow, needs embeddings during chunking |

Known flaws of ours (documented, scheduled for Phase 2/8): min=2-char page-tail chunks
(fix: `min_chunk_size` filter), no overlap across page boundaries, mid-formula cuts.

## Exercise
Rebuild `chunk_pages` from the mental model without looking. Then add a
`min_chunk_size: int = 50` parameter that drops smaller chunks. Verify `min` in the stats
jumps from 2 to ≥50.

---

# Part 4 — embedder.py (text → vectors)

## Theory

An **embedding** is a list of numbers (ours: 384) representing a text's meaning as a
position in space, produced by a neural network trained on billions of text pairs with one
objective: *similar meanings → nearby points* (Reimers & Gurevych 2019, Sentence-BERT).
"The dog chased the cat" and "A puppy ran after a kitten" share no keywords but land close
together. Think GPS coordinates for meaning.

Inside, the embedding model runs the same first steps as an LLM — tokenize, embed tokens,
transformer attention layers — but instead of predicting a next token, it pools the output
into one fixed-size vector.

## The code

```python
import numpy as np
from sentence_transformers import SentenceTransformer

def load_model(name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    return SentenceTransformer(name)        # downloads ~90MB once, then cached

def embed_texts(texts: list[str], model: SentenceTransformer) -> np.ndarray:
    return np.array(model.encode(texts, show_progress_bar=True))
```

- Output is a **matrix**: one row per text, one column per dimension. 55 chunks →
  shape `(55, 384)`. `shape` reads as (rows, columns).
- Deliberate design: takes plain strings, not chunk dicts — the embedder doesn't know
  chunks exist. Low coupling = the same function embeds queries. 
- Model choice `all-MiniLM-L6-v2`: 384-dim, fast on CPU, free, good-enough quality —
  the standard learning/prototyping model.

## Variations

| Embedder | Dim | Trade |
|---|---|---|
| all-MiniLM-L6-v2 (ours) | 384 | free, local, weakest at vocabulary gaps |
| all-mpnet-base-v2 | 768 | free, local, better quality, ~3x slower |
| Gemini / Voyage / OpenAI embedding APIs | 768–3072 | best quality, network + key needed, per-call cost/quota |

Rule: dimensions ↑ usually quality ↑, but storage and compute scale with it. The vector DB
must be told the dimension — switching models means re-embedding EVERYTHING (vectors from
different models are not comparable!).

## Exercise
Embed the sentences "I love pizza", "Pizza is my favorite food", "The stock market fell"
and compute pairwise similarities (using Part 5's math). Predict the ranking first.

---

# Part 5 — search.py (query vector → top-k chunks)

## Theory: cosine similarity

Similarity between two vectors = the cosine of the angle between them: 1 = same direction
(same meaning), 0 = perpendicular (unrelated). Computed as the **dot product of
length-normalized vectors**. We normalize because raw dot products also reward vector
*length*, and length correlates with text length — without normalization, long chunks
would win just for being long. (Classic IR theory: Manning et al., *Introduction to
Information Retrieval*, ch. 6.)

Toy example you can verify on paper (2-D instead of 384-D):

```
chunk vectors:  A=[0.9, 0.1]  B=[0.2, 0.8]  C=[0.7, 0.3]
query:          q=[0.7, 0.7]
normalize all to length 1 (divide by √(x²+y²)), then dot:
score(A)=0.77  score(B)=0.85  score(C)=0.92  → ranking: C, B, A
```

## The code

```python
import numpy as np

def search(q_vec, vectors, chunks, k: int = 3) -> list[dict]:
    q_norm = q_vec / np.linalg.norm(q_vec)                              # ① 
    v_norms = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)  # ②
    scores = v_norms @ q_norm                                           # ③
    top_idx = np.argsort(scores)[::-1][:k]                              # ④
    return [{**chunks[i], "score": float(scores[i])} for i in top_idx]  # ⑤
```

① Normalize the query: `np.linalg.norm` = vector length (Pythagoras); dividing by it
   makes length 1, direction preserved.
② Normalize every chunk row at once. `axis=1` = "one norm per row" (axis=0 would be per
   column). `keepdims=True` keeps the norms shaped as a column so numpy's broadcasting
   pairs row-with-its-norm correctly.
③ Matrix @ vector = dot product of EVERY row against the query in one shot → one score
   per chunk. **This single line is what a vector database does at its core**, just
   industrialized for millions of vectors with approximate-nearest-neighbor indexes.
④ `argsort` returns *indices* sorted by score (ascending); `[::-1]` reverses to
   descending; `[:k]` takes the top k. Indices, not values — because the index is the
   key back to the chunk that produced the score.
⑤ `{**chunks[i], "score": ...}` = copy of the chunk dict plus its score.

Four beats to rebuild it from memory: **normalize → dot → argsort → fetch.**

## What we measured (calibration — this is gold)

| Query | Top score | Verdict |
|---|---|---|
| "How many attention heads..." | 0.55 | correct chunk — vocabulary matched the paper |
| "attention is the new electricity" | 0.44 | trap: literal word "Attention" in junk figure text |
| "What datasets were used..." | 0.33 | marginal |
| "What dropout rate was used?" | 0.31 | MISS — right chunk existed but ranked low |
| "the brain is a complex organ" | 0.27 | unrelated, garbage results |

Empirical threshold adopted: **below ~0.35, refuse to answer.** The dropout miss diagnosis:
*vocabulary mismatch* — the paper says "P_drop = 0.1" and "residual dropout", never
"dropout rate". Small embedders bridge such gaps poorly. This is THE core practical
problem of RAG retrieval.

## The improvement ladder (Phase 8 preview, cheap → powerful)
1. Wider k with softer gating
2. **Query rewriting** — LLM rephrases the question into paper vocabulary before embedding
3. **Hybrid search** — blend vector scores with keyword scores (BM25); keywords catch
   exact terms (P_drop, BLEU), vectors catch paraphrases
4. **Reranking** — vector-retrieve top-20 cheaply, re-score with a cross-encoder that
   reads actual (query, chunk) pairs
5. Better chunks (section-aware; filter junk)
6. Bigger embedding model
Anti-pattern: lowering the threshold — treats the symptom, invites hallucination.

## Exercise
Add the query "residual dropout P_drop regularization" and rerun. Compare its top score
with "What dropout rate was used?" — same chunks, same vectors, different vocabulary.
That delta IS the vocabulary-mismatch problem, measured.

---

# Part 6 — generator.py (chunks + question → cited answer)

## Theory

This is the "AG" of RAG: **augment** the prompt with retrieved evidence, then **generate**.
The prompt is an instruction contract with three clauses (grounding rules — Lewis et al.
2020 formalized the retrieve-then-generate pattern):
1. answer ONLY from the provided context (anti-hallucination),
2. cite the page for every claim (traceability),
3. if absent, say "not found" (honest refusal beats confident fabrication).

Plus a **pre-LLM gate**: if the best retrieval score is below threshold, refuse *before*
spending an API call. Two independent defense layers — gate (cheap, blunt) and prompt
rule (costs a call, finer-grained).

## The code

```python
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()                                # read .env into environment variables

def load_client() -> genai.Client:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set. Copy .env.example to .env and add your key.")
    return genai.Client(api_key=api_key)     # Client — capital C, it's a class

def build_prompt(question: str, results: list[dict]) -> str:
    context = "\n\n".join(f"[page {r['page']}]\n{r['text']}" for r in results)
    return f"""You are a research assistant. Answer the question using ONLY the context below.

Rules:
- Cite the page number for every claim, like (p. 7).
- If the context does not contain the answer, say exactly: "Not found in the provided paper."
- Be precise with numbers and metrics. Do not add outside knowledge.

Context:
{context}

Question: {question}

Answer:"""

def generate_answer(client, question, results, min_score: float = 0.35) -> str:
    if not results or results[0]["score"] < min_score:      # the gate
        return "Not found in the provided paper (retrieval confidence too low)."
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),  # config, not code
        contents=build_prompt(question, results),
    )
    return response.text
```

Design points:
- **Secrets pattern:** key lives in `.env` (gitignored); `.env.example` (committed)
  documents which keys are needed without containing any. New teammate: copy, fill, run.
- **Helpful failure:** the RuntimeError tells the reader exactly how to fix their setup.
- **Model name from env with fallback:** `os.getenv("GEMINI_MODEL", default)`. Adopted
  after gemini-2.5-flash was retired mid-project — providers sunset models on their own
  schedule; names are configuration, not code (Twelve-Factor App, factor III).
- **k=5 for generation** vs 3 for inspection: wider net is cheap insurance against
  near-miss rankings.

## Verified end-to-end results
- "How many attention heads..." → *"The model employs h = 8 parallel attention layers,
  or heads (p. 5)."* ✅ correct, cited
- "What is the price of Bitcoin?" → refused ✅
- "What dropout rate was used?" → refused (honest: retrieval genuinely failed) ✅ standing
  Phase 8 test case

## Exercise
Remove the three Rules from the prompt and ask the Bitcoin question with the gate disabled
(min_score=0). Watch what the model does without its contract. Put the rules back.

---

# Part 7 — Incidents Log (each one is a transferable lesson)

| # | Incident | Root cause | Transferable lesson |
|---|---|---|---|
| 1 | pip install failed | `depenedencies` typo in pyproject.toml | Read tracebacks BOTTOM-UP; the last lines name the cause |
| 2 | PDF nearly committed | .gitignore added after staging | gitignore filters untracked files only; `git status` is the last line of defense; `git check-ignore -v` explains rules |
| 3 | Infinite loop | loop-advance line inside a conditional | while-loop variable must advance unconditionally; Ctrl+C traceback shows the stuck line |
| 4 | Model download 401 | `MiniLm` typo, then HF Xet backend flakiness | identical-looking errors, different causes — read details; purge partial caches |
| 5 | API key pasted in chat | habit not yet formed | any key that leaves .env is compromised — rotate without debate |
| 6 | 'module' not callable | `genai.client` vs `genai.Client` | classes are CapWords; this error usually = capitalization typo |
| 7 | Model 404 | provider retired the model | model names are config, not code → .env with fallback |

Meta-lesson: four of seven were single-character mistakes. Professional debugging is
mostly careful *reading*, not cleverness.

---

# Part 8 — The Complete Interview Speech

**The 90-second full version** (pause points marked ▸):

> "I built a RAG system for analyzing research papers — and I deliberately built the
> pipeline by hand before using any framework, so I understand every stage. ▸
>
> The project is a monorepo with the engine as a separate pip-installable package, so
> it's reusable across projects — I verified that by installing it from GitHub into a
> clean environment. ▸
>
> **Extraction:** PyMuPDF, per-page — because page numbers must travel with the text from
> the very first step or citations become impossible later. I also learned extraction
> quality caps retrieval quality: figure-heavy pages produced junk text I now know to filter. ▸
>
> **Chunking:** fixed-size with overlap. Small chunks keep embedding vectors precise;
> overlap protects sentences that land on cut boundaries. I validated the size
> empirically — 300 characters gave incoherent fragments, 3000 gave multi-topic mush,
> so I settled near 1000. ▸
>
> **Embedding and search:** sentence-transformers locally, cosine similarity implemented
> myself in numpy — normalize, dot product, argsort. That taught me a vector database is
> essentially that dot product, industrialized. ▸
>
> **The most valuable result was a retrieval failure.** The query 'what dropout rate was
> used' missed, because the paper says 'P_drop = 0.1' — a vocabulary mismatch between
> casual questions and formal paper language. I measured that unrelated queries score
> below ~0.35, so I added a refusal gate at that threshold — the system says 'not found'
> instead of hallucinating. And I kept that failing query as a standing test case for the
> upgrades: query rewriting, hybrid BM25-plus-vector search, and cross-encoder reranking. ▸
>
> **Generation:** Gemini's free tier, with a grounding prompt — answer only from context,
> cite pages, refuse if absent. Keys and model names live in environment config, not
> code — a lesson I learned when Google retired a model mid-project and my fix was a
> one-line env change. ▸
>
> Everything is under Git with conventional commits, and every component sits behind a
> swappable interface, so each upgrade is one new class, not a rewrite."

**Why this speech works:** every stage comes with a *why*; it includes a measured
experiment (chunk sizes, score threshold); it features a FAILURE and its diagnosis —
which reads as more senior than a string of successes; and it ends with architecture
foresight. Interviewers probe decisions, not code — this is all decisions.

**Likely follow-up questions and your one-liners:**
- *Why not LangChain?* — "I wanted to understand what frameworks abstract; now I can use
  one knowingly, or skip it — our pipeline is ~150 lines."
- *Why RAG over fine-tuning?* — "Cheaper, instantly updatable when documents change,
  and citable — fine-tuning bakes knowledge in without sources."
- *How would you scale it?* — "Swap the numpy store for pgvector/a vector DB behind the
  same interface; batch and cache embeddings; move ingestion to background jobs."
- *Biggest weakness?* — "Retrieval on vocabulary mismatch, measured and documented;
  the fix ladder is query rewriting, hybrid search, reranking."

---

# Part 9 — References (theory sources worth actually reading)

- **Vaswani et al., "Attention Is All You Need" (2017)** — the transformer paper; also our
  test document. arxiv.org/abs/1706.03762
- **Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
  (2020)** — the paper that named RAG. arxiv.org/abs/2005.11401
- **Reimers & Gurevych, "Sentence-BERT" (2019)** — the sentence-embedding approach behind
  sentence-transformers. arxiv.org/abs/1908.10084
- **Manning, Raghavan & Schütze, *Introduction to Information Retrieval*** — free online;
  ch. 6 covers vector space scoring/cosine similarity (the classical foundation).
- **The Twelve-Factor App** (12factor.net) — factor III "Config" is the env-var principle
  we adopted.
- **Pro Git** (git-scm.com/book) — free; chapters 1–3 cover everything we used.

---

# Part 10 — Rebuild-From-Scratch Checklist (test yourself)

Blank folder. No peeking. Can you:
1. `git init`, gitignore (with .env!), venv, install pymupdf/sentence-transformers/numpy
2. loader: fitz.open → per-page dicts (why per-page?)
3. chunker: cursor loop, word-boundary nudge, overlap step-back (why unconditional advance?)
4. embedder: load model, texts → matrix (what's the shape?)
5. search: normalize → dot → argsort → fetch (why normalize? why indices?)
6. generator: .env key, gate at 0.35, grounding prompt with 3 rules, model from env
7. wire in main, run, get a cited answer
8. commit with a conventional message, push

When all eight are yes — and they will be sooner than you think — Phase 1 is not just
complete, it's *yours*.
