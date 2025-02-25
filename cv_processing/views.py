from datetime import datetime
import json
import re
from django.shortcuts import render
from django.http import JsonResponse
from .models import CV, CVData
from .cv_processor import CVProcessor
from .llm_interface import LLMInterface
import os

def upload_cv(request):
   
    if request.method == 'POST':
        cv_files = request.FILES.getlist('cv_files')
        if not cv_files:
            return JsonResponse({'message': 'Please select at least one CV to upload'})
        
        processor = CVProcessor()
        processed_count = 0
        errors = []
        
        for cv_file in cv_files:
            try:
                cv = CV.objects.create(filename=cv_file.name, file=cv_file)
                file_path = cv.file.path
                cv_data = processor.process_file(file_path)
                CVData.objects.create(cv=cv, **cv_data)
                processed_count += 1
            except Exception as e:
                errors.append(f"Error processing '{cv_file.name}': {str(e)}")
        
        if processed_count > 0 and not errors:
            return JsonResponse({'message': f"{processed_count} CV(s) processed successfully"})
        elif processed_count > 0:
            return JsonResponse({'message': f"{processed_count} CV(s) processed successfully, but: {', '.join(errors)}"})
        else:
            return JsonResponse({'message': ', '.join(errors)})
    return render(request, 'upload.html')

def chatbot(request):
    if request.method == 'POST':
        if not CV.objects.exists():
            return JsonResponse({'response': 'You should upload a CV'})
        
        query = request.POST.get('query').lower().strip()
        llm = LLMInterface()
        
        # Initialize session context if not present
        if 'cv_ids' not in request.session:
            request.session['cv_ids'] = []
        
        # Build full CV data
        full_cv_data = {
            "query": query,
            "database": {
                str(cv.id): {
                    "personal_info": cv.cvdata_set.first().personal_info if cv.cvdata_set.exists() else {},
                    "education": cv.cvdata_set.first().education if cv.cvdata_set.exists() else [],
                    "work_experience": cv.cvdata_set.first().work_experience if cv.cvdata_set.exists() else [],
                    "skills": cv.cvdata_set.first().skills if cv.cvdata_set.exists() else [],
                    "projects": cv.cvdata_set.first().projects if cv.cvdata_set.exists() else [],
                    "certifications": cv.cvdata_set.first().certifications if cv.cvdata_set.exists() else []
                } for cv in CV.objects.all()
            }
        }
        
        # Use context if cv_ids exist and query is a follow-up
        if request.session['cv_ids'] and any(phrase in query for phrase in ["what about", "their experience", "their skills", "their education"]):
            cv_data = {
                "query": query,
                "database": {
                    cv_id: data for cv_id, data in full_cv_data['database'].items() 
                    if cv_id in request.session['cv_ids']
                }
            }
        else:
            cv_data = full_cv_data  

        print("CV Data Sent to LLM:", json.dumps(cv_data, indent=2))  
        
        # Direct queries
        if query == "skills":
            all_skills = [data['skills'] for data in cv_data['database'].values()]
            response = "Skills: " + ", ".join([skill for sublist in all_skills for skill in sublist])
            request.session['cv_ids'] = list(cv_data['database'].keys())  
            return JsonResponse({'response': response})
        
        elif query == "experience":
            all_experience = [data['work_experience'] for data in cv_data['database'].values()]
            response = "Experience: " + "; ".join([exp for sublist in all_experience for exp in sublist])
            request.session['cv_ids'] = list(cv_data['database'].keys())  
            return JsonResponse({'response': response})
        
        elif query == "education":
            all_education = [data['education'] for data in cv_data['database'].values()]
            response = "Education: " + "; ".join([edu for sublist in all_education for edu in sublist])
            request.session['cv_ids'] = list(cv_data['database'].keys())  
            return JsonResponse({'response': response})
        
        elif "skill" in query:
            skill = query.split("skill")[-1].strip()
            results = [cv_id for cv_id, data in cv_data['database'].items() if skill.lower() in str(data['skills']).lower()]
            request.session['cv_ids'] = results  
            return JsonResponse({'response': f"Found {len(results)} candidates with skill {skill}"})
        
        elif "experience in" in query:
            industry = query.split("experience in")[-1].strip()
            results = [cv_id for cv_id, data in cv_data['database'].items() if industry.lower() in str(data['work_experience']).lower()]
            request.session['cv_ids'] = results  
            return JsonResponse({'response': f"Found {len(results)} candidates with experience in {industry}"})
        
        elif "identify matching candidates for job requirements" in query:
            requirements = query.split("job requirements:")[-1].strip().split(" and ")
            matches = {}
            current_year = datetime.now().year
            for cv_id, data in cv_data['database'].items():
                name = data['personal_info'].get('Name', f'Candidate {cv_id}')
                skills_match = all(req.lower() in " ".join(data['skills']).lower() for req in requirements if "years" not in req.lower())
                years_match = False
                for exp in data['work_experience']:
                    match = re.search(r'(\d{4})\s*-\s*(current|\d{4})', exp, re.IGNORECASE)
                    if match:
                        start = int(match.group(1))
                        end = current_year if match.group(2).lower() == 'current' else int(match.group(2))
                        years = end - start
                        for req in requirements:
                            if "years" in req.lower() and years >= int(re.search(r'\d+', req).group()):
                                years_match = True
                matches[name] = skills_match and years_match
            matched_names = [name for name, match in matches.items() if match]
            request.session['cv_ids'] = [cv_id for cv_id, data in cv_data['database'].items() if data['personal_info'].get('Name', f'Candidate {cv_id}') in matched_names]
            return JsonResponse({'response': f"Matched {len(matched_names)} candidates: {', '.join(matched_names)}"})
        
        # LLM queries with context
        else:
            analysis = llm.analyze_cv(cv_data)
            if analysis and 'summary' in analysis:
                return JsonResponse({'response': json.dumps(analysis)})
            return JsonResponse({'response': 'Could not process query due to service issues'})
    return render(request, 'chatbot.html')