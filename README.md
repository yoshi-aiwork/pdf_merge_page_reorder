# Gradio PDF Extract & Merge Tool

This Gradio app lets you upload **two PDF files**, pick page ranges from each, arrange pages in *any* order you like (e.g. `A1‑3, B5, A10`), choose a layout (sequential or 2‑up), and download a single merged PDF.

## Install

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Then open the local link, upload PDFs, enter ranges and an optional order like:

```
A1-2, B5, A10, B2-3
```

Finally click **Generate PDF** to download the merged file.