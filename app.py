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
            readers[src] = PdfReader(globals()[f"pdf_{src.lower()}_path"])
        writer.add_page(readers[src].pages[page-1])
    # TODO 2‑Up layout if requested
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    with open(tmp.name, "wb") as f:
        writer.write(f)
    return tmp.name

def build_pdf_manual(pdf_a, pages_a, pdf_b, pages_b, final_order, layout):
    reader_a, reader_b = PdfReader(pdf_a), PdfReader(pdf_b)
    pages_map = {
        "A": {idx+1: pg for idx, pg in enumerate(reader_a.pages)},
        "B": {idx+1: pg for idx, pg in enumerate(reader_b.pages)},
    }

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
    gr.Markdown("## Upload PDFs, pick pages, and reorder them →")

    with gr.Row():
        pdf_a = gr.File(label="PDF A", file_types=[".pdf"])
        pdf_b = gr.File(label="PDF B", file_types=[".pdf"])

    with gr.Row():
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
    def build_pdf_combined(mode, meta, order, lay, pdf_a_path, pages_a_str, pdf_b_path, pages_b_str):
        if mode == "Drag‑and‑Drop":
            return build_pdf_drag(meta, lay)
        else:
            return build_pdf_manual(pdf_a_path, pages_a_str, pdf_b_path, pages_b_str, order, lay)

    generate.click(
        fn=build_pdf_combined,
        inputs=[ordering_mode, gallery_meta, final_order, layout, pdf_a, pages_a, pdf_b, pages_b],
        outputs=result)

if __name__ == "__main__":
    demo.launch()
