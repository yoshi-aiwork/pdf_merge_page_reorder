# Gradio PDF Extract & Merge Tool

## Overview

This Gradio app lets you upload **two PDF files**, pick page ranges from each, arrange pages in *any* order you like (e.g. `A1‑3, B5, A10`), choose a layout (sequential or 2‑up), and download a single merged PDF.

---

## Core Features

1. **PDF Upload** – Two independent upload components for *PDF A* and *PDF B*.
2. **Page Range Selection** – Flexible range syntax (`1, 3‑5, 8` etc.) for *each* PDF.
3. **Arbitrary Final Order** – Enter a mixed sequence such as `A1‑3, B5, A10` to interleave pages from both PDFs exactly as you want.
4. **Layout Choice** – **Sequential** (default) or **2‑Up** (two logical pages per sheet).
5. **Preview & Download** – Optional page thumbnails plus one‑click download of the merged PDF.

---

## UI Design (Gradio 4.x Blocks)

| Row | Component                                   | Purpose                                                                                 |
| --- | ------------------------------------------- | --------------------------------------------------------------------------------------- |
| 1   | `gr.File` (PDF A) & `gr.File` (PDF B)       | Upload source PDFs                                                                      |
| 2   | `gr.Textbox` ×2                             | Page ranges for A & B (e.g. `1,3‑5`)                                                    |
| 3   | `gr.Textbox` **Final Order**                | Mixed sequence (`A1‑3,B5,A10`). If left blank, default = pages from A then pages from B |
| 4   | `gr.Radio` **Layout**                       | `Sequential` or `2‑Up`                                                                  |
| 5   | `gr.Button` **Generate** → `gr.File` output | Build + download merged PDF                                                             |

---

## Data Flow

```
Upload PDFs -> Parse range A & B -> Expand to page lists
        -> Parse final‑order string (if provided) -> Build Writer
        -> Apply layout (seq / 2‑up) -> TempFile -> Download
```

---

## Key Parsing Helpers

```python
import re
from typing import List, Tuple

PAGE_RE   = re.compile(r"([AB])[:]?([0-9]+(?:-[0-9]+)?)", re.I)
SEP_RE    = re.compile(r"[ ,;]+")
RANGE_RE  = re.compile(r"(\d+)-(\d+)")

def parse_ranges(rng: str) -> List[int]:
    """Return sorted unique 1‑based page numbers."""
    pages: List[int] = []
    for part in SEP_RE.split(rng.strip()):
        if not part:
            continue
        m = RANGE_RE.fullmatch(part)
        if m:
            s, e = map(int, m.groups())
            pages.extend(range(s, e+1))
        elif part.isdigit():
            pages.append(int(part))
        else:
            raise ValueError(f"Invalid token '{part}'.")
    return sorted(dict.fromkeys(pages))

def parse_final_order(order_str: str) -> List[Tuple[str,int]]:
    """Return list of (src, page_num) preserving appearance order."""
    out: List[Tuple[str,int]] = []
    for token in SEP_RE.split(order_str.strip()):
        if not token:
            continue
        m = PAGE_RE.fullmatch(token)
        if not m:
            raise ValueError(f"Invalid order token '{token}'. Use e.g. A1 or B5‑7.")
        src, spec = m.groups()
        src = src.upper()
        if "-" in spec:
            s, e = map(int, spec.split('-'))
            out.extend([(src,p) for p in range(s, e+1)])
        else:
            out.append((src, int(spec)))
    return out
```

---

## `app.py` (Complete MVP)

```python
import gradio as gr, tempfile, os
from pypdf import PdfReader, PdfWriter
from helpers import parse_ranges, parse_final_order  # assume same dir or inline

def build_pdf(pdf_a, pages_a, pdf_b, pages_b, final_order, layout):
    reader_a, reader_b = PdfReader(pdf_a), PdfReader(pdf_b)
    pages_map = {
        "A": {idx+1: pg for idx, pg in enumerate(reader_a.pages)},
        "B": {idx+1: pg for idx, pg in enumerate(reader_b.pages)},
    }

    # Expand default order if user didn\'t supply custom sequence
    if not final_order.strip():
        order = [("A", p) for p in parse_ranges(pages_a)] + \
                [("B", p) for p in parse_ranges(pages_b)]
    else:
        order = parse_final_order(final_order)

    writer = PdfWriter()
    for src, pnum in order:
        try:
            writer.add_page(pages_map[src][pnum])
        except KeyError:
            raise ValueError(f"Page {pnum} missing in PDF {src}.")

    # TODO: 2‑Up layout transformation here if layout == "2‑Up"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    with open(tmp.name, "wb") as f:
        writer.write(f)
    return tmp.name

with gr.Blocks(title="PDF Extract & Merge") as demo:
    gr.Markdown("## Upload PDFs and define pages →")

    with gr.Row():
        pdf_a = gr.File(label="PDF A", file_types=[".pdf"])
        pdf_b = gr.File(label="PDF B", file_types=[".pdf"])

    with gr.Row():
        pages_a = gr.Textbox(label="Pages from A (e.g. 1,3‑5)")
        pages_b = gr.Textbox(label="Pages from B (e.g. 2,4)")

    final_order = gr.Textbox(label="Final Order (e.g. A1‑3,B5,A10) – leave blank for default")
    layout      = gr.Radio(["Sequential", "2‑Up"], value="Sequential", label="Layout")

    generate = gr.Button("Generate PDF")
    result   = gr.File(label="Merged PDF")

    generate.click(build_pdf,
                   inputs=[pdf_a, pages_a, pdf_b, pages_b, final_order, layout],
                   outputs=result)

if __name__ == "__main__":
    demo.launch()
```

> **Tip**\
> If you need thumbnail previews or drag‑and‑drop re‑ordering, swap the `final_order` textbox for a custom JavaScript component or Gradio Gallery once the MVP is stable.

---

## `requirements.txt`

```
gradio>=4.19.0
pypdf>=4.0.0
```

---

## README Snippet

```bash
# 1. Install
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Run
python app.py
```

Then open the local link, upload PDFs, enter ranges and an optional order like:

```
A1-2, B5, A10, B2-3
```

Finally click **Generate PDF** to download the merged file.

---

## Gemini CLI Prompt Template

```
You are an AI coding assistant.
Generate a Python Gradio app named app.py that:
1. Lets users upload two PDF files.
2. Input page ranges for each PDF.
3. Accept a final mixed order string (e.g. A1‑3,B5,A10).
4. Optional layout Sequential / 2‑Up.
5. Returns the merged PDF.
Use only pypdf. Include helper functions to parse ranges & order.
Provide runnable code + brief README.
```

---

## Future Enhancements

- **Drag‑and‑Drop Thumbnails** for WYSIWYG ordering
- **N‑Up & Booklet Layouts**
- **Multiple PDFs (>2)** dynamically
- **Robust Error Messages & Validation**

