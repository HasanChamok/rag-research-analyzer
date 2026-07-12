import fitz

def load_pdf(path: str) -> list[dict]:
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages.append({"page": i + 1, "text": text})
    doc.close()
    return pages

if __name__ == "__main__":
    pages = load_pdf("data/attention.pdf")
    print(f"Loaded {len(pages)} pages")
    print(f"Page 1 starts with:\n{pages[0]['text'][:300]}")
    total_chars = sum(len(p["text"]) for p in pages)
    print(f"Total characters: {total_chars}")