import gradio as gr, tempfile, os, json, re
from pypdf import PdfReader, PdfWriter
from helpers import parse_ranges, parse_final_order, pdf_page_to_thumbnail

# --- Helpers ---
def get_file_path(file_obj):
    """Normalize file path from Gradio File object."""
    return file_obj.name if hasattr(file_obj, 'name') else file_obj

# --- Core Functions ---
def generate_single_pdf_preview(pdf_obj, range_str):
    """Generates a gallery for a single PDF's selected pages."""
    preview_items = []
    pdf_path = get_file_path(pdf_obj)

    if not pdf_path:
        raise gr.Error("Please upload a PDF file first.")

    try:
        pages = parse_ranges(range_str)
    except ValueError as e:
        raise gr.Error(f"Invalid page range: {e}")

    for p in pages:
        thumb = pdf_page_to_thumbnail(pdf_path, p)
        if thumb:
            preview_items.append((thumb, f"Page {p}"))
        else:
            gr.Warning(f"Could not generate thumbnail for page {p}.")

    return preview_items

def generate_final_preview_gallery(pdf_a_obj, pdf_b_obj, order_str):
    """Generates a gallery that reflects the sequence in the final_order textbox."""
    preview_items = []
    pdf_paths = {"A": get_file_path(pdf_a_obj), "B": get_file_path(pdf_b_obj)}

    if not order_str.strip():
        raise gr.Error("The 'Final Order' text field is empty. Cannot generate a preview.")

    try:
        page_spec = parse_final_order(order_str)
    except ValueError as e:
        raise gr.Error(f"Invalid Final Order string: {e}")

    for src, page in page_spec:
        pdf_path = pdf_paths.get(src)
        if not pdf_path:
            raise gr.Error(f"PDF for source '{src}' is missing. Please upload it again.")
        
        thumb = pdf_page_to_thumbnail(pdf_path, page)
        if thumb:
            preview_items.append((thumb, f"{src}{page}"))
        else:
            gr.Warning(f"Could not generate thumbnail for {src}{page}.")

    return preview_items

def build_pdf_from_order(pdf_a_obj, pdf_b_obj, order_str, layout):
    """Builds the final PDF based on the final_order string."""
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
    gr.Markdown("## 1. Upload PDFs and Select Pages")
    with gr.Row():
        with gr.Column():
            pdf_a = gr.File(label="PDF A", file_types=[".pdf"])
            pages_a = gr.Textbox(label="Pages from A (e.g. 1, 3-5)")
            preview_a_btn = gr.Button("Preview PDF A")
            gallery_a = gr.Gallery(label="PDF A Preview", interactive=False, visible=True, columns=4, height="auto")
        with gr.Column():
            pdf_b = gr.File(label="PDF B", file_types=[".pdf"])
            pages_b = gr.Textbox(label="Pages from B (e.g. 2, 4)")
            preview_b_btn = gr.Button("Preview PDF B")
            gallery_b = gr.Gallery(label="PDF B Preview", interactive=False, visible=True, columns=4, height="auto")

    gr.Markdown("## 2. Specify Final Page Order and Preview")
    final_order = gr.Textbox(
        label="Final Page Order", info="Example: A1-3, B5, A10", visible=True
    )
    preview_final_btn = gr.Button("Preview Final Order")
    final_gallery = gr.Gallery(
        label="Final Order Preview", interactive=False, visible=True, columns=8, height="auto"
    )

    gr.Markdown("## 3. Generate Final PDF")
    layout = gr.Radio(["Sequential", "2-Up"], value="Sequential", label="Layout")
    generate_btn = gr.Button("Generate PDF", variant="primary")
    result = gr.File(label="Merged PDF")

    # --- Event Handlers ---
    preview_a_btn.click(
        fn=generate_single_pdf_preview,
        inputs=[pdf_a, pages_a],
        outputs=[gallery_a]
    )

    preview_b_btn.click(
        fn=generate_single_pdf_preview,
        inputs=[pdf_b, pages_b],
        outputs=[gallery_b]
    )

    preview_final_btn.click(
        fn=generate_final_preview_gallery,
        inputs=[pdf_a, pdf_b, final_order],
        outputs=[final_gallery]
    )

    generate_btn.click(
        fn=build_pdf_from_order,
        inputs=[pdf_a, pdf_b, final_order, layout],
        outputs=result
    )

if __name__ == "__main__":
    demo.launch()