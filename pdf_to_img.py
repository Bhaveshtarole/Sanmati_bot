import fitz
from pathlib import Path

pdf_path = "Sanmati_Engineering_College_Washim_2025_Brochure.pdf"
doc = fitz.open(pdf_path)

out_dir = Path("pdf_images")
out_dir.mkdir(exist_ok=True)

# Convert first 8 pages (or all if < 8)
num_pages = min(len(doc), 15)

for i in range(num_pages):
    page = doc.load_page(i)
    pix = page.get_pixmap(dpi=150)
    out_file = out_dir / f"page_{i}.png"
    pix.save(str(out_file))

print(f"Extracted {num_pages} pages to images in {out_dir}")
