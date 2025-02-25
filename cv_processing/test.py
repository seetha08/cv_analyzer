from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import CV, CVData
from .cv_processor import CVProcessor

class CVProcessingTests(TestCase):
    def setUp(self):
        self.processor = CVProcessor()

    def test_pdf_upload(self):
        pdf_content = b"Name: Test\nEducation\n- BS Computer Science\nExperience\n- Developer, 2020-2022"
        pdf_file = SimpleUploadedFile("test_cv.pdf", pdf_content, content_type="application/pdf")
        cv = CV.objects.create(filename="test_cv.pdf", file=pdf_file)
        cv_data = self.processor.process_file(cv.file.path)
        CVData.objects.create(cv=cv, **cv_data)
        self.assertEqual(CV.objects.count(), 1)
        self.assertEqual(CVData.objects.count(), 1)
        self.assertIn("Test", cv_data['personal_info']['Name'])

    def test_chatbot_query(self):
        cv = CV.objects.create(filename="test_cv.pdf")
        CVData.objects.create(
            cv=cv,
            personal_info={"Name": "Test"},
            education=["BS Computer Science"],
            work_experience=["Developer, 2020-2022"],
            skills=["Python"],
            projects=[],
            certifications=[]
        )
        response = self.client.post('/chatbot/', {'query': 'Find candidates with skill Python'})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Found 1 candidates with skill Python", response.json()['response'])