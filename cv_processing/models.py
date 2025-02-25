from django.db import models

class CV(models.Model):
    filename = models.CharField(max_length=255)  # Store the original filename, not unique
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='cvs/')

    def __str__(self):
        return f"CV {self.id} - {self.filename}"

class CVData(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE)
    personal_info = models.JSONField(default=dict)
    education = models.JSONField(default=list)
    work_experience = models.JSONField(default=list)
    skills = models.JSONField(default=list)
    projects = models.JSONField(default=list)
    certifications = models.JSONField(default=list)

    def __str__(self):
        return f"Data for CV {self.cv.id}"