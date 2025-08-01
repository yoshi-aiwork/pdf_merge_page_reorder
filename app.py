import gradio as gr, tempfile, os, json, re
from pypdf import PdfReader, PdfWriter
from helpers import parse_ranges, parse_final_order, pdf_page_to_thumbnail

# --- Helpers ---
def get_file_path(file_obj):
    """Normalize file path from Gradio File object."""
    return file_obj.name if hasattr(file_obj, 'name') else file_obj

# --- Core Functions ---
def build_pdf_manual(pdf_a_obj, pdf_b_obj, order, lay):
    writer = PdfWriter()
    readers = {}
    
    pdf_paths = {"A": get_file_path(pdf_a_obj), "B": get_file_path(pdf_b_obj)}

    try:
        page_spec = parse_final_order(order)
    except ValueError as e:
        raise gr.Error(f"Invalid Final Order string: {e}")

    for src, page in page_spec:
        if src not in readers:
            pdf_path = pdf_paths.get(src)
            if not pdf_path:
                raise gr.Error(f"PDF for source '{src}' is missing. Please upload it again.")
            readers[src] = PdfReader(pdf_path)
        
        if not 0 < page <= len(readers[src].pages):
            raise gr.Error(f"Page number {page} for PDF {src} is out of range.")
            
        writer.add_page(readers[src].pages[page - 1])

    if not writer.pages:
        gr.Warning("No pages were added to the PDF.")
        return None
    # TODO 2‑Up layout if requested
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    with open(tmp.name, "wb") as f:
        writer.write(f)
    return tmp.name

def build_gallery(pdf_a_obj, rng_a, pdf_b_obj, rng_b):
    gallery_items = []
    pdf_a_path = get_file_path(pdf_a_obj)
    pdf_b_path = get_file_path(pdf_b_obj)

    if not pdf_a_path and not pdf_b_path:
        return []

    mapping = {}
    if pdf_a_path:
        try:
            mapping["A"] = (pdf_a_path, parse_ranges(rng_a))
        except ValueError as e:
            raise gr.Error(f"Invalid page range for PDF A: {e}")
    if pdf_b_path:
        try:
            mapping["B"] = (pdf_b_path, parse_ranges(rng_b))
        except ValueError as e:
            raise gr.Error(f"Invalid page range for PDF B: {e}")

    for src, (path, pages) in mapping.items():
        for p in pages:
            thumb = pdf_page_to_thumbnail(path, p)
            if thumb:
                caption = f"{src}{p}"
                gallery_items.append((thumb, caption))

    if not gallery_items and (pdf_a_path or pdf_b_path):
        gr.Warning("No pages selected or an error occurred in thumbnail generation.")
    
    return gallery_items

with gr.Blocks(title="PDF Extract & Merge") as demo:
    gr.Markdown("## Upload PDFs, pick pages, and reorder them →")

    pdf_a = gr.File(label="PDF A", file_types=[".pdf"])
    pdf_b = gr.File(label="PDF B", file_types=[".pdf"])
    pages_a = gr.Textbox(label="Pages from A (e.g. 1,3‑5)")
    pages_b = gr.Textbox(label="Pages from B (e.g. 2,4)")

    gallery       = gr.Gallery(label="Page Preview", interactive=False, visible=True, columns=[5]) # Made non-interactive

    final_order   = gr.Textbox(label="Final Order (A1‑3,B5,A10)", visible=True) # Always visible
    layout        = gr.Radio(["Sequential", "2‑Up"], value="Sequential", label="Layout")
    generate      = gr.Button("Generate PDF")
    result        = gr.File(label="Merged PDF")

    # Build thumbnails when ranges are entered / files uploaded
    build_btn = gr.Button("Build Thumbnails")
    build_btn.click(build_gallery, inputs=[pdf_a, pages_a, pdf_b, pages_b],
                    outputs=[gallery])

    # Generate PDF always using build_pdf_manual
    generate.click(
        fn=build_pdf_manual,
        inputs=[pdf_a, pdf_b, final_order, layout],
        outputs=result)

if __name__ == "__main__":
    demo.launch()