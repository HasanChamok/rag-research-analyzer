import fitz

def load_pdf(path: str) -> list[dict]:
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages.append({"page": i + 1, "text": text})
    doc.close()
    return pages

def chunk_pages(pages: list[dict], chunk_size: int = 1000, overlap:int = 200) -> list[dict]:
    """Split pages text into overlapping chunks, cutting at word bounderies. And each chunk keeps its source page number which is 
    citatiohn metadata"""
    chunks = []
    for page in pages:
        text = page["text"]
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                #Don't cut a word in half:  extend to the next space(if not at text end)
                if end< len(text):
                    next_space = text.find(" ", end)
                    if next_space != -1:
                        end = next_space
                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append({"id": len(chunks), "page": page["page"], "text": chunk_text})
                start = end - overlap
                        
    return chunks

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