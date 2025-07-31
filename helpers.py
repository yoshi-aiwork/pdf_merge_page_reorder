import re, io, base64
from typing import List, Tuple
import fitz                         # PyMuPDF
from PIL import Image

PAGE_RE  = re.compile(r"([AB])[:]?([0-9]+(?:-[0-9]+)?)", re.I)
SEP_RE   = re.compile(r"[ ,;]+")
RANGE_RE = re.compile(r"(\d+)-(\d+)")

def parse_ranges(rng: str) -> List[int]:
    pages: List[int] = []
    if not rng:
        return pages
    for part in SEP_RE.split(rng.strip()):
        if not part:
            continue
        m = RANGE_RE.fullmatch(part)
        if m:
            s, e = map(int, m.groups())
            if s > e:
                s, e = e, s # Swap if order is reversed
            pages.extend(range(s, e + 1))
        elif part.isdigit():
            pages.append(int(part))
        else:
            raise ValueError(f"Invalid token '{part}'.")
    return sorted(list(set(pages)))

def parse_final_order(order_str: str) -> List[Tuple[str, int]]:
    out: List[Tuple[str, int]] = []
    for token in SEP_RE.split(order_str.strip()):
        if not token:
            continue
        m = PAGE_RE.fullmatch(token)
        if not m:
            raise ValueError(f"Invalid order token '{token}'. Use e.g. A1 or B5-7.")
        src, spec = m.groups()
        src = src.upper()
        if "-" in spec:
            s, e = map(int, spec.split("-"))
            if s > e:
                s, e = e, s # Swap if order is reversed
            out.extend([(src, p) for p in range(s, e + 1)])
        else:
            out.append((src, int(spec)))
    return out

def pdf_page_to_thumbnail(pdf_path: str, page_num: int, thumb_w: int = 160) -> str:
    """Return base64 PNG Data-URI for page thumbnail (~10-20 KB)."""
    try:
        doc  = fitz.open(pdf_path)
    except fitz.fitz.FitzError as e:
        print(f"Error opening PDF {pdf_path}: {e}")
        return ""

    if not (0 < page_num <= len(doc)):
        print(f"Page number {page_num} is out of range for PDF {pdf_path}.")
        return ""
        
    page = doc[page_num - 1]

    # Calculate the appropriate scaling factor
    if page.rect.width == 0:
        return "" # Avoid division by zero for empty pages
    zoom = thumb_w / page.rect.width  # Zoom factor to make the width approx. thumb_w pixels
    mat  = fitz.Matrix(zoom, zoom)

    try:
        pix  = page.get_pixmap(matrix=mat, alpha=False)
        img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    except (RuntimeError, ValueError) as e:
        print(f"Error generating thumbnail for page {page_num} of {pdf_path}: {e}")
        return ""

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    doc.close()
    data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    return data_uri