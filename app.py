import gradio as gr, tempfile, os, json, re
from pypdf import PdfReader, PdfWriter
from helpers import parse_ranges, parse_final_order, pdf_page_to_thumbnail

# --- Helpers ---
def get_file_path(file_obj):
    """Normalize file path from Gradio File object."""
    return file_obj.name if hasattr(file_obj, 'name') else file_obj

# --- Core Functions ---
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

def build_pdf_from_gallery(pdf_a_obj, pdf_b_obj, gallery_items, layout):
    writer = PdfWriter()
    readers = {}
    pdf_paths = {"A": get_file_path(pdf_a_obj), "B": get_file_path(pdf_b_obj)}

    if not gallery_items:
        raise gr.Error("There are no pages in the gallery to build a PDF.")

    for _thumb, caption in gallery_items:
        match = re.match(r"([AB])(\d+)", caption)
        if not match:
            continue
        src, page_str = match.groups()
        page = int(page_str)
        
        if src not in readers:
            pdf_path = pdf_paths.get(src)
            if not pdf_path:
                raise gr.Error(f"PDF for source '{src}' is missing. Please upload it again.")
            readers[src] = PdfReader(pdf_path)
        
        if not 0 < page <= len(readers[src].pages):
            raise gr.Error(f"Page {page} for PDF {src} is out of range.")
            
        writer.add_page(readers[src].pages[page - 1])

    if not writer.pages:
        gr.Warning("No pages were added to the PDF.")
        return None

    if layout == "2-Up":
        gr.Warning("2-Up layout is not yet implemented. Generating a sequential PDF.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        writer.write(tmp)
        return tmp.name

def build_pdf_manual(pdf_a_obj, pdf_b_obj, order_str, layout):
    writer = PdfWriter()
    readers = {}
    pdf_paths = {"A": get_file_path(pdf_a_obj), "B": get_file_path(pdf_b_obj)}

    if not order_str.strip():
        raise gr.Error("The 'Final Order' text field is empty.")

    try:
        page_spec = parse_final_order(order_str)
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

    if layout == "2-Up":
        gr.Warning("2-Up layout is not yet implemented. Generating a sequential PDF.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        writer.write(tmp)
        return tmp.name

# --- Gradio UI ---
with gr.Blocks(title="PDF Extract & Merge") as demo:
    gr.Markdown("## 1. Upload PDFs and Select Page Ranges")
    with gr.Row():
        pdf_a = gr.File(label="PDF A", file_types=[".pdf"])
        pdf_b = gr.File(label="PDF B", file_types=[".pdf"])
    with gr.Row():
        pages_a = gr.Textbox(label="Pages from A (e.g. 1, 3-5)")
        pages_b = gr.Textbox(label="Pages from B (e.g. 2, 4)")

    gr.Markdown("## 2. Choose How to Order Pages")
    ordering_mode = gr.Radio(
        ["Drag-and-Drop", "Manual Text"], value="Drag-and-Drop", label="Ordering Mode"
    )
    build_btn = gr.Button("Build Thumbnails")

    gr.Markdown("## 3. Arrange Pages")
    gallery = gr.Gallery(
        label="Reorder Pages (drag to arrange)", interactive=True, visible=True, columns=8, height="auto"
    )
    final_order = gr.Textbox(
        label="Final Page Order (e.g., A1-3, B5, A10)", visible=False
    )

    gr.Markdown("## 4. Generate Final PDF")
    layout = gr.Radio(["Sequential", "2-Up"], value="Sequential", label="Layout")
    generate_btn = gr.Button("Generate PDF", variant="primary")
    result = gr.File(label="Merged PDF")

    # --- Event Handlers ---
    build_btn.click(
        fn=build_gallery,
        inputs=[pdf_a, pages_a, pdf_b, pages_b],
        outputs=[gallery]
    )

    def toggle_ordering_mode(mode):
        is_dnd = mode == "Drag-and-Drop"
        return {
            gallery: gr.update(visible=is_dnd),
            final_order: gr.update(visible=not is_dnd),
            build_btn: gr.update(visible=is_dnd),
        }

    ordering_mode.change(
        fn=toggle_ordering_mode,
        inputs=ordering_mode,
        outputs=[gallery, final_order, build_btn]
    )

    def generate_pdf_dispatcher(mode, p_a, p_b, gallery_val, order_str, lay):
        if mode == "Drag-and-Drop":
            return build_pdf_from_gallery(p_a, p_b, gallery_val, lay)
        else:
            return build_pdf_manual(p_a, p_b, order_str, lay)

    generate_btn.click(
        fn=generate_pdf_dispatcher,
        inputs=[ordering_mode, pdf_a, pdf_b, gallery, final_order, layout],
        outputs=result
    )

if __name__ == "__main__":
    demo.launch()