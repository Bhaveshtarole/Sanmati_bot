import PyPDF2
from pathlib import Path

pdf_path = Path("Sanmati_Engineering_College_Washim_2025_Brochure.pdf")
knowledge_override = Path("knowledge.txt")

extracted_text = "\n\n=== CONTENT FROM 2025 BROCHURE ===\n"

# Open the PDF file
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"

# Append to knowledge.txt
with open(knowledge_override, 'a', encoding='utf-8') as kf:
    kf.write(extracted_text)

print("Text successfully extracted and appended to knowledge.txt!")
