from dotenv import load_dotenv
from ragcore.pipeline import default_pipeline

load_dotenv()

pipeline = default_pipeline()
pipeline.ingest("data/attention.pdf")
answer = pipeline.ask("How many attention heads does the model have?")

print(answer.text)
for c in answer.citations[:2]:
    print(f"  → {c.doc_id} p.{c.page} (score {c.score:.2f})")