import PyPDF2

def pdf_to_text(pdf_file):
    """Convert PDF to text using PyPDF2"""
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text()
    return text
