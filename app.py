import gradio as gr, tempfile, os
from pypdf import PdfReader, PdfWriter
from helpers import parse_ranges, parse_final_order  # assume same dir or inline

def build_pdf(pdf_a, pages_a, pdf_b, pages_b, final_order, layout):
    reader_a, reader_b = PdfReader(pdf_a), PdfReader(pdf_b)
    pages_map = {
        "A": {idx+1: pg for idx, pg in enumerate(reader_a.pages)},
        "B": {idx+1: pg for idx, pg in enumerate(reader_b.pages)},
    }

    # Expand default order if user didn't supply custom sequence
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