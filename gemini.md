# Gradio PDF Extract & Merge Tool (Enhanced)

## Overview

This Gradio app lets you upload **two PDF files**, pick page ranges from each, and arrange pages **visually** with drag‑and‑drop thumbnails (*default*). Power users can still switch to the original textbox‑based sequence (e.g. `A1‑3, B5, A10`). Finally choose a layout (sequential or 2‑up) and download a single merged PDF.

---

## Core Features

1. **PDF Upload** – Two independent upload components for *PDF A* and *PDF B*.
2. **Page Range Selection** – Flexible range syntax (`1, 3‑5, 8` etc.) for *each* PDF.
3. **WYSIWYG Ordering (Default)** – After ranges are parsed, each selected page appears as a draggable thumbnail in a unified gallery. Users reorder pages visually.
4. **Fallback Manual Ordering** – A toggle reveals the classic textbox where pages can be specified as `A1‑3, B5, A10`.
5. **Layout Choice** – **Sequential** (default) or **2‑Up** (two logical pages per sheet).
6. **Preview & Download** – Live thumbnail gallery plus one‑click download of the merged PDF.

---

## UI Design (Gradio 4.x Blocks)

| Row | Component                                                              | Purpose                                                                             |
| --- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1   | `gr.File` (PDF A) & `gr.File` (PDF B)\`                                | Upload source PDFs                                                                  |
| 2   | `gr.Textbox` ×2                                                        | Page ranges for A & B (e.g. `1,3‑5`)                                                |
| 3   | `gr.Radio` **Ordering Mode**                                           | `Drag‑and‑Drop` (default) · `Manual Text`                                           |
| 4a  | `gr.Gallery` **Thumbnail Gallery** *(shown when mode = Drag‑and‑Drop)* | Displays selected pages as thumbnails; supports drag‑reorder via `interactive=True` |
| 4b  | `gr.Textbox` **Final Order** *(visible when mode = Manual Text)*       | Mixed sequence (`A1‑3,B5,A10`)                                                      |
| 5   | `gr.Radio` **Layout**                                                  | `Sequential` or `2‑Up`                                                              |
| 6   | `gr.Button` **Generate** → `gr.File` output                            | Build & download merged PDF                                                         |

> **Conditional visibility** is handled with Gradio component `.visible` property and a callback on the Ordering Mode radio.

---

## Data Flow

```
Upload PDFs
   │
Parse page‑range inputs → Build page‑lists per source
   │
Ordering Mode? ─► Drag‑and‑Drop → Gallery index order → list[(src,page)]
              └► Manual Text   → parse_final_order()     ─┘
   │
Apply layout (seq / 2‑up) → PdfWriter → TempFile → Download
```

---

## Thumbnail Generation

We create thumbnails with **PyMuPDF** (`pymupdf`) because it is pure‑python and fast:

```python
import fitz  # PyMuPDF
from PIL import Image
import io, base64

def pdf_page_to_thumbnail(pdf_path: str, page_num: int, thumb_w=160):
    doc  = fitz.open(pdf_path)
    page = doc[page_num-1]
    pix  = page.get_pixmap(matrix=fitz.Matrix(thumb_w/100, thumb_w/100))
    img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    buf  = io.BytesIO()
    img.save(buf, format="PNG")
    data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    return data_uri
```

Each thumbnail is stored alongside its `(src, page)` tuple so we can reconstruct order after drag‑n‑drop.

---

## Key Parsing Helpers (unchanged)

```python
# parse_ranges() & parse_final_order() as in previous version …
```

---

## `app.py` (excerpt with new ordering logic)

```python
import gradio as gr, tempfile, os, json
from pypdf import PdfReader, PdfWriter
from helpers import parse_ranges, parse_final_order, pdf_page_to_thumbnail

def build_gallery(pdf_a_path, rng_a, pdf_b_path, rng_b):
    thumbs, meta = [], []
    mapping = {"A": (pdf_a_path, parse_ranges(rng_a)),
               "B": (pdf_b_path, parse_ranges(rng_b))}
    for src, (path, pages) in mapping.items():
        for p in pages:
            thumb = pdf_page_to_thumbnail(path, p)
            thumbs.append(thumb)
            meta.append(json.dumps({"src": src, "page": p}))  # keep track
    return thumbs, meta

def build_pdf_drag(meta_json_list, layout):
    """meta_json_list is a list of json strings in gallery order."""
    writer = PdfWriter()
    readers = {}
    for meta_json in meta_json_list:
        item = json.loads(meta_json)
        src, page = item["src"], item["page"]
        if src not in readers:
            readers[src] = PdfReader(globals()[f"pdf_{src.lower()}"].value)
        writer.add_page(readers[src].pages[page-1])
    # TODO 2‑Up layout if requested
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    with open(tmp.name, "wb") as f:
        writer.write(f)
    return tmp.name

with gr.Blocks(title="PDF Extract & Merge") as demo:
    gr.Markdown("## Upload PDFs, pick pages, and reorder them →")

    pdf_a = gr.File(label="PDF A", file_types=[".pdf"])
    pdf_b = gr.File(label="PDF B", file_types=[".pdf"])
    pages_a = gr.Textbox(label="Pages from A (e.g. 1,3‑5)")
    pages_b = gr.Textbox(label="Pages from B (e.g. 2,4)")

    ordering_mode = gr.Radio(["Drag‑and‑Drop", "Manual Text"], value="Drag‑and‑Drop", label="Ordering Mode")
    gallery       = gr.Gallery(label="Reorder Pages (drag)", interactive=True, visible=True, columns=[5])
    gallery_meta  = gr.State([])  # parallel list storing meta json

    final_order   = gr.Textbox(label="Final Order (A1‑3,B5,A10)", visible=False)
    layout        = gr.Radio(["Sequential", "2‑Up"], value="Sequential", label="Layout")
    generate      = gr.Button("Generate PDF")
    result        = gr.File(label="Merged PDF")

    # Build thumbnails when ranges are entered / files uploaded
    build_btn = gr.Button("Build Thumbnails")
    build_btn.click(build_gallery, inputs=[pdf_a, pages_a, pdf_b, pages_b],
                    outputs=[gallery, gallery_meta])

    # Toggle visibility based on ordering mode
    def toggle(mode):
        return gr.update(visible=(mode=="Drag‑and‑Drop")), gr.update(visible=(mode=="Manual Text"))
    ordering_mode.change(toggle, inputs=ordering_mode, outputs=[gallery, final_order])

    # Generate PDF depending on mode
    generate.click(
        fn=lambda mode, meta, order, lay: build_pdf_drag(meta, lay) if mode=="Drag‑and‑Drop" else build_pdf_manual(order, lay),
        inputs=[ordering_mode, gallery_meta, final_order, layout],
        outputs=result)

if __name__ == "__main__":
    demo.launch()
```

*(Full code includes **`build_pdf_manual()`** identical to previous implementation.)*

---

## `requirements.txt`

```
gradio>=4.19.0
pypdf>=4.0.0
pymupdf>=1.24.3   # for thumbnails
pillow            # prerequisite for PyMuPDF image export
```

> **Note:** PyMuPDF is pure‑python but relies on MuPDF C libs already bundled in the wheel for most OS‑arch combos.

---

## README Snippet (updated)

```bash
# 1. Install dependencies (Poppler *not* required)
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Run the app
python app.py
```

1. Upload *PDF A* & *PDF B*.
2. Enter page ranges (`1,3‑5`).
3. Click **Build Thumbnails**.
4. Drag pages in the gallery **or** switch to **Manual Text** and enter `A1‑3,B5,A10`.
5. Choose layout & hit **Generate PDF**.

---

## Gemini CLI Prompt Template (revised)

```
You are an AI coding assistant.
Generate a Python Gradio app named app.py that:
1. Lets users upload two PDF files.
2. Input page ranges for each PDF.
3. Offers two ordering modes: Drag‑and‑Drop thumbnail gallery (default) and Manual text string (e.g. A1‑3,B5,A10).
4. Optional layout Sequential / 2‑Up.
5. Returns the merged PDF.
Use pypdf for merging and PyMuPDF (pymupdf) to generate thumbnails. Provide runnable code + README.
```

---

## Future Enhancements

- **Live Thumbnail Preview on Range Change** (auto‑update without Build button)
- **N‑Up & Booklet Layouts** (beyond 2‑Up)
- **Support More Than 2 PDFs** (dynamic uploader list)
- **Error Handling & Validation** (invalid ranges, missing pages)

