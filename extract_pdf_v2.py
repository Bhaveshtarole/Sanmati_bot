import fitz
from pathlib import Path

pdf_path = "Sanmati_Engineering_College_Washim_2025_Brochure.pdf"
out_path = Path("raw_extracted_text.txt")

try:
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n\n--- PAGE BREAK ---\n\n"
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print("PyMuPDF Extraction Complete! Written to:", out_path)
except Exception as e:
    print(f"Error: {e}")
