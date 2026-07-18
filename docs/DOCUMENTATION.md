# RAG Research Paper Analyzer — Project Documentation

> **Living document.** This is the single source of truth for the project. It is updated after
> every step: what was done, the exact commands/code, why it was done that way, errors hit,
> and how they were fixed. Lives at `docs/DOCUMENTATION.md` in the repo.

**Repo:** https://github.com/HasanChamok/rag-research-analyzer
**Author:** Hasan Chamok
**Started:** July 2026
**Status:** Phase 0 complete · Phase 1 next

---

## 1. Project Overview

A web application to upload academic papers (PDF), ask questions about them, and receive
answers grounded in the papers with precise citations (paper, section, page). Also supports
comparing findings across multiple papers.

**Secondary goal:** The RAG engine is built as a reusable, pip-installable Python package
(`ragcore`) so it can be dropped into any future project.

**Learning goal:** Build this the way a professional team would — clean architecture,
version control discipline, testing, CI/CD, and free-tier cloud deployment.

---

## 2. Architecture

```
┌─────────────────────────────┐
│  Frontend — Next.js          │  Vercel (free)
└──────────────┬──────────────┘
               │ HTTPS / JSON
┌──────────────▼──────────────┐
│  Backend — FastAPI           │  Render free tier / HF Spaces
└──────────────┬──────────────┘
               │ imports
┌──────────────▼──────────────┐
│  ragcore (Python package)    │  Loader → Chunker → Embedder
│  reusable RAG engine         │  → VectorStore → LLM → Answer
└──────┬───────────────┬──────┘
       │               │
┌──────▼──────┐ ┌──────▼──────┐
│ Vector DB    │ │ LLM API      │
│ Supabase     │ │ Gemini/Groq  │
│ (pgvector)   │ │ (free tiers) │
└─────────────┘ └─────────────┘
```

**Design principle:** every component in `ragcore` sits behind an abstract base class
(`BaseChunker`, `BaseEmbedder`, `BaseVectorStore`, `BaseLLM`), so any part can be swapped
or upgraded by writing one new class — never by rewriting the app.

### Stack decisions and rationale

| Layer | Choice | Why | Rejected alternative & why |
|---|---|---|---|
| Frontend | Next.js on Vercel | User requirement; best free DX; auto-deploy per push | Plain React — no routing/SSR, worse Vercel fit |
| Backend | FastAPI on Render | Python-native for ML; auto Swagger docs; Render auto-deploys from GitHub free | Vercel serverless Python — cold starts + timeouts hurt PDF ingestion |
| Vector DB | Supabase (pgvector) | Postgres + vectors + file storage + auth in ONE free account | Pinecone — separate account, less to learn from |
| Embeddings/LLM | Gemini free tier / Groq / local sentence-transformers | Actually free | OpenAI/Anthropic APIs — pay-per-use |
| CI/CD | GitHub Actions | Free, industry standard | — |
| AWS/Azure | Not used directly | Free tiers expire / surprise bills; Vercel/Supabase run on AWS anyway | Covered as theory in Phase 9 for interview literacy |

### Repository layout (target)

```
rag-research-analyzer/
├── .gitignore
├── README.md
├── docs/
│   └── DOCUMENTATION.md      ← this file
├── ragcore/                   ← reusable engine (Phase 2)
│   ├── pyproject.toml
│   ├── src/ragcore/
│   └── tests/
├── backend/                   ← FastAPI app (Phase 4)
└── frontend/                  ← Next.js app (Phase 5)
```

Monorepo pattern: one repo, multiple sub-projects. Reuse of the engine from any other
project still works via:

```
pip install "git+https://github.com/HasanChamok/rag-research-analyzer.git#subdirectory=ragcore"
```

---

## 3. Conventions (apply to every step from now on)

1. **Conventional Commits** — every message starts with a type:
   `feat:` new feature · `fix:` bug fix · `docs:` documentation · `test:` tests ·
   `chore:` housekeeping · `refactor:` restructuring without behavior change.
2. **`git status` before every commit** — verify exactly what enters history.
3. **Every session ends with a push** — GitHub is the source of truth; pip and CI only see pushed code.
4. **Secrets never touch Git** — API keys live in `.env`, which is in `.gitignore`.
5. **Virtual environment for all Python work** — `.venv` per project, never global installs.
6. **This document is updated after every step** — with a Step Log entry (section 5) and a
   changelog line (section 6).

---

## 4. Environment

| Tool | Version | Verified |
|---|---|---|
| OS | Windows (PowerShell) | — |
| Python | 3.11.9 | ✅ |
| Git | 2.45.1.windows.1 | ✅ |
| Node.js | 24.14.0 | ✅ |
| Editor | VS Code | ✅ |

Git identity configured globally: `user.name "Hasan Chamok"`, `user.email hasan.chamok16@gmail.com`
(matches GitHub account → commits link to profile), `init.defaultBranch main`.

Known local quirk: project path contains spaces
(`C:\Users\hasan\Downloads\Github Main Projects\RAG - Research Paper Analyzer`).
Decision: accepted by owner; all commands must quote paths. If a build tool fails
mysteriously on paths, suspect this first.

---

## 5. Step Log

Each entry: **What / How (exact commands) / Why / Result**.
Errors get their own entry with the fix — errors are part of the record, not embarrassments.


### Phase 0 — Developer Foundations

#### Step 0.1 — Environment verification
- **What:** Confirmed Python, Git, Node installed.
- **How:** `python --version`, `git --version`, `node --version`
- **Result:** Python 3.11.9, Git 2.45.1, Node 24.14.0 — all sufficient.

#### Step 0.2 — Git identity configuration
- **What:** Set global identity and default branch.
- **How:**
  ```powershell
  git config --global user.name "Hasan Chamok"
  git config --global user.email "hasan.chamok16@gmail.com"
  git config --global init.defaultBranch main
  ```
- **Why:** The email links commits to the GitHub profile. `init.defaultBranch main` makes
  every future `git init` start on `main`.
- **Note:** First attempt had a typo (`init.defaultBranchmain`, missing space) which silently
  set a garbage key. Harmless, but corrected. Lesson: Git config accepts anything; typos
  fail silently.

#### Step 0.3 — Repo initialization with monorepo skeleton
- **What:** Created the local repo with `ragcore` package skeleton inside.
- **How:**
  ```powershell
  git init
  git branch -m main
  mkdir docs
  mkdir ragcore\src\ragcore -Force
  mkdir ragcore\tests -Force
  New-Item ragcore\src\ragcore\__init__.py -ItemType File
  New-Item ragcore\tests\__init__.py -ItemType File
  ```
  Plus three files created in VS Code: `.gitignore`, `README.md`, `ragcore/pyproject.toml`.
- **Why each piece:**
  - **src layout** (`ragcore/src/ragcore/`): forces the package to be *installed* to be used,
    so tests exercise it exactly as future users will. PyPA-recommended.
  - **`pyproject.toml`**: modern replacement for `setup.py`; declares name/version/deps and
    build backend; this file alone is what makes the folder pip-installable.
  - **`.gitignore` before first commit**: blocks `__pycache__/`, `.venv/`, `.env` (secrets!),
    `*.egg-info/`, `dist/`, and preemptively `node_modules/` + `.next/` for the future
    frontend. Once junk is committed, scrubbing history is painful — prevention is cheap.
  - **`__init__.py` files**: mark directories as Python packages.

#### Step 0.4 — First commit
- **How:**
  ```powershell
  git add .
  git status        # verified: exactly 5 expected files staged
  git commit -m "chore: initialize monorepo with ragcore package skeleton"
  ```
- **Result:** Root commit `d06b40f`, 5 files.

#### Step 0.5 — GitHub remote and first push
- **What:** Created empty repo `rag-research-analyzer` on GitHub (NO initialization
  checkboxes — GitHub-created files would conflict with local ones on first push).
- **How:**
  ```powershell
  git remote add origin https://github.com/HasanChamok/rag-research-analyzer.git
  git push -u origin main
  ```
- **Why HTTPS:** On Windows, Git Credential Manager pops a one-time browser login; smoothest path.
- **Why `-u`:** Links local `main` to `origin/main` permanently; afterwards plain `git push` suffices.
- **Result:** Push succeeded; repo live.

#### Step 0.6 — Reuse test: pip install from GitHub ❌→✅
- **What:** Proved the package is installable from GitHub into any environment.
- **How:**
  ```powershell
  pip install "git+https://github.com/HasanChamok/rag-research-analyzer.git#subdirectory=ragcore"
  ```
- **Error hit:**
  ```
  ValueError: invalid pyproject.toml config: `project`.
  configuration error: `project` must not contain {'depenedencies'} properties
  ```
- **Diagnosis:** Read the traceback **bottom-up** — last two lines contain the cause.
  `depenedencies` is a typo of `dependencies` in `ragcore/pyproject.toml`; the TOML
  validator rejects unknown keys.
- **Fix:**
  ```powershell
  # corrected the line to: dependencies = []
  git add ragcore/pyproject.toml
  git commit -m "fix: correct typo in pyproject.toml dependencies field"
  git push
  ```
- **Key lesson:** pip cloned from **GitHub**, not the local disk. Local fixes are invisible
  to pip (and later to CI and deploys) until pushed. Local ≠ remote.
- **Verification:**
  ```powershell
  pip install "git+https://github.com/HasanChamok/rag-research-analyzer.git#subdirectory=ragcore"
  python -c "import ragcore; print('ragcore installed and importable')"
  ```

#### Observations logged for later
- `WARNING: Ignoring invalid distribution ~ympy` in pip output → a past global-Python install
  got corrupted. Harmless, but it is the argument for virtual environments: from Phase 1 on,
  all installs happen inside `.venv`.

**✅ Phase 0 checkpoint met:** repo live · clean conventional commits · reuse mechanism
proven end-to-end · traceback-reading and local-vs-remote lessons internalized.

---

### Phase 1 — RAG by Hand *(next)*

### Phase 1 — RAG by Hand

#### Step 1.1 — Virtual environment
- **How:** `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`
- **Why:** Per-project isolation; global Python already showed corruption (`~ympy`).
  Re-activate per terminal; VS Code interpreter set to `.venv`.

#### Step 1.2 — Dependencies
- **How:** `pip install pymupdf sentence-transformers numpy` then `pip freeze > requirements-dev.txt`
- **Why:** pymupdf = per-page PDF text; sentence-transformers = free local embeddings
  (no API key); numpy = hand-rolled cosine similarity. `requirements-dev.txt` makes the
  environment reproducible anywhere.

#### Step 1.3 — Test data
- **How:** Downloaded "Attention Is All You Need" (arXiv 1706.03762) to `data/attention.pdf`;
  added `data/` to `.gitignore`.
- **Why:** Binary documents don't belong in Git history.

#### Step 1.4 — Stage 1: PDF loading
- **What:** `docs/experiments/rag_by_hand.py` — `load_pdf()` returns per-page dicts.
- **Why per-page:** page numbers must travel with text from extraction onward — citations
  are designed in at load time, impossible to bolt on later.
- **Observation:** extraction is imperfect (headers, formulas, tables) → retrieval quality
  is capped by extraction quality. Improvement scheduled for Phase 8.


- **Incident:** `git status` before commit caught `data/attention.pdf` staged despite the
  `data/` ignore rule. Cause: `.gitignore` only filters *untracked* files — it does not
  unstage anything already added. Fix: `git restore --staged data/attention.pdf`.
  Lesson: gitignore is a gate for new files, not a cleaner; `git status` is the last line
  of defense before history.
- **Incident 2:** `data/` kept appearing as untracked. Cause: ignore rule was written as
  `.data/` (leading dot) — matches a folder named `.data`, not `data`. Fix: rule changed
  to `data/`. Debugging tool learned: `git check-ignore -v <path>` shows exactly which
  rule (file + line) matches a path, or nothing if no rule does.


  #### Step 1.5 — Stage 2: Chunking
- **What:** `chunk_pages()` — fixed-size chunks (default 1000 chars) with 200-char overlap,
  cut at word boundaries, each chunk carrying `{id, page, text}`.
- **Why size ~1000:** small chunks → precise vectors (one topic per vector); large chunks →
  enough context for the LLM to use. 500–1500 chars is the prose sweet spot; verified by
  experiment with 300 (incoherent fragments) and 3000 (multi-topic mud).
- **Why overlap:** sentences on a cut boundary would be split into two meaningless halves;
  overlap guarantees every sentence exists whole in ≥1 chunk.
- **Known flaws (accepted for now, Phase 8 fixes):** structure-blind (cuts mid-paragraph /
  mid-formula); tiny leftover chunks at page tails; no overlap across page boundaries
  (traded for simple page citations).

#### Step 1.6 — Chunk quality inspection
- **What:** manually inspected chunk output: verified overlap between consecutive chunks,
  found tiny leftover chunks at page tails, found structure-blind cuts (mid-sentence).
- **Experiment:** reran with chunk_size=300 (incoherent fragments) and 3000 (multi-topic
  chunks) → validated ~1000 as the sweet spot empirically.
- **Also here:** infinite-loop incident + fix (see Incident 3), and the code walkthrough
  of the chunker.

#### Step 1.7 — Refactor: one module per stage
- **What:** split rag_by_hand.py into loader.py / chunker.py / embedder.py / search.py /
  main.py (pipeline conductor).
- **Why:** separation of concerns — each stage upgradeable in isolation. embedder takes
  plain strings (doesn't know chunks exist); search takes pre-embedded vectors (doesn't
  know the model exists). Low coupling = high reusability.
- **Gotcha learned:** sibling-file imports resolve from the running directory → run
  `python main.py` from inside docs/experiments/; PDF path adjusted to ../../data/.
#### Step 1.8 — Stage 3+4: embeddings and similarity search
- (unchanged from plan: MiniLM 384-dim vectors, cosine = normalized dot product,
  scores ~0.5–0.8 = good hit, unrelated query → collapsed scores)

- **Incident 4 (model download failure):** OSError loading 'all-MiniLm-L6-v2' + 401 from
  HF storage. Cause: typo in model name — lowercase 'm', correct is 'all-MiniLM-L6-v2'.
  Fix: corrected name, purged partial cache under ~/.cache/huggingface/hub, redownloaded.
  Lessons: (1) bottom line of traceback contained the misspelled name verbatim;
  (2) partially-downloaded model caches must be deleted before retry;
  (3) fallback for HF xet 401s: HF_HUB_DISABLE_XET=1.
- **Observation:** chunk stats min=2 → confirmed tiny page-tail chunks; min_chunk_size
  filter scheduled for the Phase 2 Chunker class. Removed leftover debug prints from chunker.


  - **Incident 4, part 2:** After fixing the name, download still failed with 401 from
  cas-server.xethub.hf.co — a separate issue: HF's Xet download backend flakiness, not
  our code. Distinguishing evidence: model name now correct in the error; only the large
  weights file fails. Fix: `pip uninstall hf_xet` (falls back to plain HTTPS), purge
  partial cache, retry. Lesson: identical-looking errors can have different causes —
  read the details, not just the error type.

  #### Step 1.8 — Embeddings + search: first real results
- **Setup:** 55 chunks → (55, 384) matrix, MiniLM local. HF Xet backend 401 resolved by
  falling back to plain HTTP download (hf_xet not installed).
- **Results analysis:**
  - "attention heads" → 0.55, correct chunk (multi-head section). Hit.
  - "dropout rate" → MISS: top 0.31, correct chunk (30, §5.4 Regularization, P_drop=0.1)
    didn't rank. Cause: vocabulary mismatch — casual question wording vs formal paper
    wording ("P_drop"). This is the core RAG retrieval problem; Phase 8 upgrades
    (reranking, hybrid search, query rewriting) target exactly this.
  - Probe queries: unrelated query scored ~0.27 with garbage results → empirical
    threshold: below ~0.35, system should say "not found" instead of answering.
  - Figure pages (13–15) extract as one-word-per-line junk chunks → extraction quality
    caps retrieval quality; candidate for filtering.
- **Cleanup:** removed leftover debug prints from chunker (they also silently skipped
  single-chunk pages — misleading output).

  #### Step 1.9–1.12 — Stage 5: Generation (pipeline complete)
- **What:** generator.py — Gemini free tier (gemini-2.5-flash) turns top-k chunks into a
  cited answer. Prompt rules: cite pages, refuse if absent from context, no outside knowledge.
- **Secrets:** key in .env (gitignored, verified with git check-ignore); .env.example
  committed as the template — standard team-onboarding pattern.
- **Safety gate:** answers refused when top retrieval score < 0.35 (threshold from our own
  Step 1.8 measurements) — garbage never reaches the LLM.
- **k=5 for generation** (vs 3 for search inspection): wider net partially compensates
  for known retrieval misses like the dropout query.
- **PHASE 1 COMPLETE:** load → chunk → embed → search → generate, all hand-built.

- **Incident 5 (security — key leak):** Real API key pasted into an external chat while
  debugging. Response: immediate rotation (delete + recreate in AI Studio). Rule adopted:
  any key that leaves .env by any channel is compromised — rotate without debate. Also
  standardized .env format: no spaces around `=` (portable across shell/Docker/Render).
- **Incident 6 (TypeError):** `genai.client(...)` — lowercase = module, not callable.
  Fix: `genai.Client`. Convention: classes are CapWords; "'module' object is not callable"
  usually means a class-name capitalization typo.

  - **Incident 7 (model retirement):** 404 — gemini-2.5-flash "no longer available to new
  users." Nothing wrong with our code: providers sunset models on their own schedule.
  Fix: switched to gemini-3-flash-preview (current free-tier default, 10 RPM / 1,500 RPD)
  AND moved the model name into .env (GEMINI_MODEL) with a code-side fallback default.
  Principle adopted: model names are configuration, not code — future retirements become
  a one-line .env edit instead of a code change. (Twelve-factor config.)
- **Gate validation:** "dropout rate" query was refused at score 0.31 < 0.35 before any
  API spend — the safety gate works; the query stays as our standing Phase 8 test case.

### Phase 2 — ragcore package

#### Step 2.1–2.3 — Data models + first tests
- **What:** models.py — Document, Chunk, Citation, Answer dataclasses; installed package
  editable (`pip install -e`); pytest with 3 passing tests.
- **Why dataclasses over dicts:** contract enforcement (typos explode at creation site,
  not later as KeyError), editor discoverability, type-checkability.
- **Key patterns:** field(default_factory=...) for mutable defaults (shared-dict trap —
  covered by a dedicated test); `| None` for lifecycle-optional fields (embedding);
  @property is_refusal — computed, can't drift; str IDs (int counters break at 2 papers);
  doc_id on Chunk (multi-paper readiness); Citation as a first-class type for the API.
- **Testing principle adopted:** tests are decisions frozen as executable proof.

- **Incident 8 (pytest collected 0 items):** File and names were correct; cause was an
  unsaved editor buffer — pytest reads the DISK, the editor holds the truth in memory
  until Ctrl+S. Diagnosed with `pytest --collect-only -q` (show what would run without
  running). Pattern reinforced: when a tool misbehaves, use its introspection mode
  (git check-ignore, traceback bottom line, --collect-only) instead of re-running and hoping.

  #### Step 2.4–2.6 — Loader class + first ABC
- **Design decision:** loading and chunking are separate responsibilities (SRP) — enables
  independent swapping in Phase 8. Added Page dataclass; Document carries pages.
- **BaseLoader ABC:** the enforced job description — inheritors missing load() cannot even
  be instantiated. Dataclasses protect data shape; ABCs protect behavior shape.
- **PDFLoader:** Phase 1 load_pdf wrapped in the contract; pathlib for cross-OS paths;
  fail-fast FileNotFoundError. Known tradeoff: id = filename stem (collision risk,
  revisit with DB in Phase 3).
- **Tests:** pytest.raises for error paths; two tests assert the ABC enforcement itself —
  tests can protect architecture, not just logic. 6 passing total.


## 6. Changelog

| Date | Commit | Type | Description |
|---|---|---|---|
| 2026-07 | `d06b40f` | chore | Initialize monorepo with ragcore package skeleton |
| 2026-07 | — | fix | Correct typo in pyproject.toml dependencies field |
| 2026-07 | — | docs | Add project documentation (this file) |
| 2026-07 | — | feat | Phase 1: venv, deps, PDF loading stage of hand-built RAG |
| 2026-07 | — | feat | Phase 1: overlapping chunker with page metadata |
| 2026-07 | — | refactor | Phase 1: pipeline split into per-stage modules |
| 2026-07 | — | feat | Phase 1: embeddings + search working; retrieval miss analyzed |
| 2026-07 | — | feat | Phase 1 complete: end-to-end RAG with cited answers |
| 2026-07 | — | feat | Phase 2: ragcore data models + first pytest suite |
| 2026-07 | — | feat | Phase 2: BaseLoader ABC + PDFLoader |
---

## 7. Glossary (grows as we go)

- **RAG** — Retrieval-Augmented Generation: retrieve relevant document chunks, insert them
  into the LLM prompt, generate an answer grounded in them.
- **Monorepo** — one repository containing multiple sub-projects.
- **src layout** — package code under `src/<package>/`, forcing installation before use.
- **pyproject.toml** — modern Python packaging config file.
- **Conventional Commits** — `type: message` commit format (`feat:`, `fix:`, `docs:`...).
- **Remote** — the GitHub-hosted copy of the repo (`origin`).
- **Virtual environment (venv)** — per-project isolated Python interpreter + packages.
- **Traceback** — Python's error report; read bottom-up, the cause is in the last lines.