import requests
import json
import time
import re
from cv_analyzer.settings import HUGGINGFACE_API_KEY
from datetime import datetime

class LLMInterface:
    def __init__(self):
        # Hugging Face API setup 
        self.api_url = "https://api-inference.huggingface.co/models/gpt2"
        self.headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        self.max_retries = 5
        self.initial_delay = 2

    def calculate_experience(self, cv_data):
        """Local calculation of years of experience"""
        experience_summary = {}
        current_year = datetime.now().year
        
        for cv_id, data in cv_data['database'].items():
            name = data['personal_info'].get('Name', f'Candidate {cv_id}')
            years = 0
            details = []
            for exp in data['work_experience']:
                match = re.search(r'(\d{4})\s*-\s*(current|\d{4})', exp, re.IGNORECASE)
                if match:
                    start = int(match.group(1))
                    end = current_year if match.group(2).lower() == 'current' else int(match.group(2))
                    years += end - start
                    details.append(exp)
            experience_summary[name] = {"years": years, "details": details}
        
        return experience_summary

    def compare_education(self, cv_data):
        """Local comparison of education levels"""
        education_summary = {}
        
        for cv_id, data in cv_data['database'].items():
            name = data['personal_info'].get('Name', f'Candidate {cv_id}')
            highest_degree = "Unknown"
            details = []
            for edu in data['education']:
                if "master" in edu.lower():
                    highest_degree = "Master’s"
                elif "bachelor" in edu.lower() and highest_degree != "Master’s":
                    highest_degree = "Bachelor’s"
                details.append(edu)
            education_summary[name] = {"highest_degree": highest_degree, "details": details}
        
        return education_summary

    def compare_skills(self, cv_data):
        """Local comparison of skills"""
        skills_summary = {}
        
        for cv_id, data in cv_data['database'].items():
            name = data['personal_info'].get('Name', f'Candidate {cv_id}')
            skills = [skill.lower() for skill in data['skills']]
            skills_summary[name] = {"count": len(skills), "skills": skills}
        
        return skills_summary

    def analyze_cv(self, cv_data):
        query = cv_data.get('query', '').lower()
        cv_data_str = json.dumps(cv_data, indent=2)[:2000]  
        prompt = f"""
        Given this CV data, analyze and {query}. Return a JSON object with 'summary', 'strengths', and 'recommendations' sections:\n{cv_data_str}
        """
        payload = {"inputs": prompt, "max_length": 400}
        
        retries = 0
        delay = self.initial_delay
        
        # Try Hugging Face API
        while retries < self.max_retries:
            try:
                print("Request URL:", self.api_url)
                print("Request Headers:", self.headers)
                print("Request Payload (sample):", prompt[:200])
                response = requests.post(self.api_url, headers=self.headers, json=payload)
                print("Response Status:", response.status_code)
                print("Response Text:", response.text)
                response.raise_for_status()
                result = response.json()
                if isinstance(result, list) and "generated_text" in result[0]:
                    text = result[0]["generated_text"].strip()
                    
                    try:
                        parsed = json.loads(text)
                        if all(key in parsed for key in ["summary", "strengths", "recommendations"]):
                            return parsed
                    except json.JSONDecodeError:
                       
                        if any(keyword in text.lower() for keyword in ["years", "education", "skills"]):
                            return {
                                "summary": text,
                                "strengths": "Extracted from LLM response",
                                "recommendations": "Further analysis may refine results"
                            }
                break  # Exit on success
            except requests.exceptions.RequestException as e:
                print(f"API Error: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                retries += 1
                delay *= 2
        
        # Local fallback if API fails or returns invalid response
        print(f"Max retries ({self.max_retries}) reached or invalid response. Using local logic.")
        
        if "compare their years of experience" in query:
            exp_summary = self.calculate_experience(cv_data)
            names = list(exp_summary.keys())
            if len(names) >= 2:
                cand1 = exp_summary[names[0]]
                cand2 = exp_summary[names[1]]
                summary = f"{names[0]} has approximately {cand1['years']} years of experience ({'; '.join(cand1['details'])}). {names[1]} has approximately {cand2['years']} years of experience ({'; '.join(cand2['details'])}). {names[1] if cand2['years'] > cand1['years'] else names[0]} has significantly more years of experience."
                return {
                    "summary": summary,
                    "strengths": f"{names[1]}’s extended tenure suggests deeper expertise; {names[0]}’s shorter roles show versatility." if cand2['years'] > cand1['years'] else f"{names[0]}’s extended tenure suggests deeper expertise; {names[1]}’s shorter roles show versatility.",
                    "recommendations": f"Consider {names[1]} for roles needing long-term stability, {names[0]} for adaptability." if cand2['years'] > cand1['years'] else f"Consider {names[0]} for roles needing long-term stability, {names[1]} for adaptability."
                }
            elif len(names) == 1:
                cand = exp_summary[names[0]]
                return {
                    "summary": f"{names[0]} has approximately {cand['years']} years of experience ({'; '.join(cand['details'])}). No other CVs available for comparison.",
                    "strengths": "Limited data for full analysis",
                    "recommendations": "Upload another CV for comparison"
                }
            else:
                return {
                    "summary": "No CVs available to compare years of experience.",
                    "strengths": "N/A",
                    "recommendations": "Upload at least two CVs."
                }
        
        elif "compare their education levels" in query or "compare education" in query:
            edu_summary = self.compare_education(cv_data)
            names = list(edu_summary.keys())
            if len(names) >= 2:
                cand1 = edu_summary[names[0]]
                cand2 = edu_summary[names[1]]
                summary = f"{names[0]}’s highest education is a {cand1['highest_degree']} ({'; '.join(cand1['details'])}). {names[1]}’s highest education is a {cand2['highest_degree']} ({'; '.join(cand2['details'])}). Both have advanced degrees, with differences in institutions and timelines."
                strengths = f"{names[0]}: Strong academic background; {names[1]}: Comparable qualifications."
                recommendations = "Both suitable for roles requiring higher education; consider specific fields of study for specialization."
                if cand1['highest_degree'] == cand2['highest_degree']:
                    summary += " Their education levels are equivalent."
                return {
                    "summary": summary,
                    "strengths": strengths,
                    "recommendations": recommendations
                }
            elif len(names) == 1:
                cand = edu_summary[names[0]]
                return {
                    "summary": f"{names[0]}’s highest education is a {cand['highest_degree']} ({'; '.join(cand['details'])}). No other CVs available for comparison.",
                    "strengths": "Limited data for full analysis",
                    "recommendations": "Upload another CV for comparison"
                }
            else:
                return {
                    "summary": "No CVs available to compare education levels.",
                    "strengths": "N/A",
                    "recommendations": "Upload at least two CVs."
                }
        
        elif "compare their skills" in query:
            skills_summary = self.compare_skills(cv_data)
            names = list(skills_summary.keys())
            if len(names) >= 2:
                cand1 = skills_summary[names[0]]
                cand2 = skills_summary[names[1]]
                common_skills = set(cand1['skills']) & set(cand2['skills'])
                unique_cand1 = set(cand1['skills']) - set(cand2['skills'])
                unique_cand2 = set(cand2['skills']) - set(cand1['skills'])
                summary = f"{names[0]} has {cand1['count']} skills ({'; '.join(cand1['skills'])}). {names[1]} has {cand2['count']} skills ({'; '.join(cand2['skills'])}). They share {len(common_skills)} common skills ({', '.join(common_skills)})."
                strengths = f"{names[0]}: Unique skills ({', '.join(unique_cand1)}); {names[1]}: Unique skills ({', '.join(unique_cand2)})."
                recommendations = f"Choose {names[0]} for {', '.join(unique_cand1)} expertise, {names[1]} for {', '.join(unique_cand2)}."
                return {
                    "summary": summary,
                    "strengths": strengths,
                    "recommendations": recommendations
                }
            elif len(names) == 1:
                cand = skills_summary[names[0]]
                return {
                    "summary": f"{names[0]} has {cand['count']} skills ({'; '.join(cand['skills'])}). No other CVs available for comparison.",
                    "strengths": "Limited data for full analysis",
                    "recommendations": "Upload another CV for comparison"
                }
            else:
                return {
                    "summary": "No CVs available to compare skills.",
                    "strengths": "N/A",
                    "recommendations": "Upload at least two CVs."
                }
        
        # Default for unsupported queries
        names = [cv['personal_info'].get('Name', f'Candidate {cv_id}') for cv_id, cv in cv_data['database'].items()]
        return {
            "summary": f"Query '{query}' not supported yet. CVs include: {', '.join(names)}",
            "strengths": "N/A",
            "recommendations": "Supported queries: 'Compare their years of experience', 'Compare their education levels', 'Compare their skills'"
        }