import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

def load_client() -> genai.client:
    """
    Load the Google GenAI client using the API key from the environment variable.
    
    Returns:
        genai.client: The initialized Google GenAI client.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    
    client = genai.Client(api_key=api_key)
    return client

def build_prompt(question: str, results: list[dict]) -> str:
    context = "\n\n".join(f"[page {r['page']}]\n {r['text']}" for r in results)
    return f"""You are a research assistant. Answer the question using ONLY the context below.
Rules:
- Cite the page number for every claim, like (p. 7).
- If the context does not contain the answer, say exactly: "Not found in the provided paper."
- Be precise with numbers and metrics. Do not add outside knowledge.

Context:
{context}

Question: {question}

Answer:"""

def generate_answer(client: genai.Client, question: str, results: list[dict],
                    min_score: float = 0.35) -> str:
    if not results or results[0]["score"] < min_score:
        return "Not found in the provided paper (retrieval confidence too low)."
    prompt = build_prompt(question, results)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
        contents=prompt,
    )
    return response.text