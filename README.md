# Gradio PDF Extract & Merge Tool (Enhanced)

This Gradio app lets you upload **two PDF files**, pick page ranges from each, and arrange pages **visually** with drag‑and‑drop thumbnails (*default*). Power users can still switch to the original textbox‑based sequence (e.g. `A1‑3, B5, A10`). Finally choose a layout (sequential or 2‑up) and download a single merged PDF.

## Install

```bash
# 1. Install dependencies (Poppler *not* required)
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
# 2. Run the app
python app.py
```

1. Upload *PDF A* & *PDF B*.
2. Enter page ranges (`1,3‑5`).
3. Click **Build Thumbnails**.
4. Drag pages in the gallery **or** switch to **Manual Text** and enter `A1‑3,B5,A10`.
5. Choose layout & hit **Generate PDF**.