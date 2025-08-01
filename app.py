import gradio as gr, tempfile, os, json, re
from pypdf import PdfReader, PdfWriter, PageObject
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

def build_pdf_from_order(pdf_a_obj, pdf_b_obj, order_str, layout, output_filename):
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
        new_writer = PdfWriter()
        # Collect all pages first
        all_pages = []
        for src, page_num in page_spec:
            pdf_path = pdf_paths.get(src)
            if not pdf_path:
                raise gr.Error(f"PDF for source '{src}' is missing. Please upload it again.")
            if src not in readers:
                readers[src] = PdfReader(pdf_path)
            if not 0 < page_num <= len(readers[src].pages):
                raise gr.Error(f"Page number {page_num} for PDF {src} is out of range.")
            all_pages.append(readers[src].pages[page_num - 1])

        for i in range(0, len(all_pages), 2):
            p1 = all_pages[i]

            if i + 1 < len(all_pages):
                p2 = all_pages[i+1]

                # Get the dimensions of the pages
                p1_width = float(p1.mediabox.width)
                p1_height = float(p1.mediabox.height)
                p2_width = float(p2.mediabox.width)
                p2_height = float(p2.mediabox.height)

                # Determine the dimensions for the new combined page
                # Max height of the two pages
                combined_height = max(p1_height, p2_height)
                # Sum of widths of the two pages
                combined_width = p1_width + p2_width

                # Create a new blank page with the calculated dimensions
                new_page = PageObject.create_blank_page(width=combined_width, height=combined_height)

                # Add the first page to the left half
                new_page.merge_page(p1)
                # Add the second page to the right half, shifted by the width of the first page
                new_page.merge_page(p2, (p1_width, 0))
                new_writer.add_page(new_page)
            else:
                # Odd number of pages, add the last one alone
                new_writer.add_page(p1)
        writer = new_writer

    if not output_filename.lower().endswith(".pdf"):
        output_filename += ".pdf"
    
    # Create a temporary file with the desired filename in the system's temp directory
    tmp_filepath = os.path.join(tempfile.gettempdir(), output_filename)
    with open(tmp_filepath, "wb") as f:
        writer.write(f)
    return tmp_filepath

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
    output_filename = gr.Textbox(label="Output Filename (e.g., merged.pdf)", value="merged.pdf")
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
        inputs=[pdf_a, pdf_b, final_order, layout, output_filename],
        outputs=result
    )

if __name__ == "__main__":
    demo.launch()