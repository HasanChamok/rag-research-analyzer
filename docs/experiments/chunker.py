# Split pages text into overlapping chunks, cutting at word boundaries. Each chunk keeps its source page number as citation metadata.
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
                next_space = text.find(" ", end)
                if next_space != -1:
                    end = next_space
                print(f"Chunking page {page['page']} from {start} to {end} (next space at {next_space})")
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({"id": len(chunks), "page": page["page"], "text": chunk_text})
            start = end - overlap
                        
    return chunks