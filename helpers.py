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