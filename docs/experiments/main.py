
from loader import load_pdf
from chunker import chunk_pages
from embedder import load_model, embed_texts
from search import search

if __name__ == "__main__":
    pages = load_pdf("data/attention.pdf")
    print(f"Loaded {len(pages)} pages")
    
    chunks = chunk_pages(pages)
    print(f"Created {len(chunks)} chunks")
    
    sizes = [len(c["text"]) for c in chunks]
    print(f"Chunk sizes: min={min(sizes)}, max={max(sizes)},avg = {sum(sizes)/len(sizes):.2f}")
    
    print(f"\n --- chunk 5 (page {chunks[5]['page']}) ---")
    print(chunks[5]["text"][:400])
    
    print(f"Page 1 starts with:\n{pages[0]['text'][:300]}")
    total_chars = sum(len(p["text"]) for p in pages)
    print(f"Total characters: {total_chars}")
    
    model = load_model()
    vectors = embed_texts([c["text"] for c in chunks], model)
    print(f"Vector matrix shape: {vectors.shape}")
    
    for query in ["attention is the new electricity", "the brain is a complex organ","What dropout rate was used?",
        "How many attention heads does the model have?",
        "What datasets were used for training?",]:
        q_vec = embed_texts([query], model)[0]
        results = search(q_vec, vectors, chunks)
        print(f"\nQuery: {query}")
        for r in results:
            print(f"Score: {r['score']:.4f}, Page: {r['page']}, Chunk ID: {r['id']}")
            print(f"Text snippet: {r['text'][:100]}...\n")