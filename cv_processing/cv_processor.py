import PyPDF2
import docx
import pytesseract
from PIL import Image
import io
import os
from pdf2image import convert_from_path
import re

class CVProcessor:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

    def read_pdf(self, file_path):
        text = ""
        # Try PyPDF2 first
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            print("PyPDF2 Extracted Text:", text if text.strip() else "None")
        except Exception as e:
            print(f"PyPDF2 Error: {e}")

        # Fallback to OCR if no text or minimal
        
        if not text.strip() or len(text) < 50:
            print("Falling back to OCR with Tesseract")
            try:
                images = convert_from_path(file_path)
                for image in images:
                    ocr_text = pytesseract.image_to_string(image)
                    text += ocr_text + "\n"
                print("OCR Extracted Text:", text)
            except Exception as e:
                print(f"OCR Error: {e}. Check Poppler and Tesseract installation.")
                return ""  
        return text

    def read_docx(self, file_path):
        try:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            print("DOCX Extracted Text:", text)
            return text
        except Exception as e:
            print(f"DOCX Error: {e}")
            return ""

    def process_file(self, file_path):
        if file_path.endswith('.pdf'):
            text = self.read_pdf(file_path)
        elif file_path.endswith('.docx'):
            text = self.read_docx(file_path)
        else:
            raise ValueError("Unsupported file format")

        print("Final Extracted Text:", text)
        lines = text.split('\n')
        cv_data = {
            'personal_info': {},
            'education': [],
            'work_experience': [],
            'skills': [],
            'projects': [],
            'certifications': []
        }
        current_section = None

        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        phone_pattern = re.compile(r'\(\d{3}\)\s*\d{3}-\d{4}')

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if 'education' in line.lower():
                current_section = 'education'
            elif 'experience' in line.lower():
                current_section = 'work_experience'
            elif 'skills' in line.lower():
                current_section = 'skills'
            elif 'projects' in line.lower():
                current_section = 'projects'
            elif 'certifications' in line.lower():
                current_section = 'certifications'
            elif email_pattern.search(line):
                cv_data['personal_info']['Email'] = line.split('$')[0].strip()
            elif phone_pattern.search(line):
                cv_data['personal_info']['Phone'] = line.split('$')[0].strip()
            elif not current_section and len(line.split()) <= 3 and not any(c.isdigit() for c in line):
                cv_data['personal_info']['Name'] = line
            elif current_section:
                cv_data[current_section].append(line)

        print("Parsed CV Data:", cv_data)
        return cv_data