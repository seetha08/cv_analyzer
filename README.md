# CV Analysis System

A Django-based web application designed to process multiple CV documents (PDF and Word formats), extract structured information using OCR, and provide a chatbot interface for querying the extracted data with LLM integration. This system supports analyzing candidate profiles, comparing qualifications, and matching job requirements.

## Features
- **Document Processing**: Handles PDF and Word CVs with OCR for scanned documents.
- **Information Extraction**: Extracts Personal Information, Education History, Work Experience, Skills, Projects, and Certifications.
- **LLM Integration**: Integrates with Hugging Face `gpt2` API with fallback logic for robust query handling.
- **Chatbot Interface**: Web-based chatbot for natural language queries with context management using Django sessions.
- **Query Types**: 
  - Find candidates by specific skills.
  - Compare education levels and years of experience.
  - Search for experience in specific industries.
  - Identify candidates matching job requirements.

## Prerequisites
- **Python**: Version 3.8 or higher
- **Git**: For cloning the repository
- **Tesseract OCR**: Required for processing scanned PDFs (`brew install tesseract` on macOS)
- **Poppler**: For converting PDFs to images for OCR (`brew install poppler` on macOS)
- **GitHub Account**: To access or contribute to the repository

## Setup Instructions

### 1. Clone the Repository
Clone the project from GitHub and navigate to the project directory:
```bash
git clone https://github.com/seetha08/cv_analyzer.git
cd cv_analyzer