import os
import time
import json
import requests
import fitz  # PyMuPDF
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util



def safe_post_request(endpoint, data, headers, retries=3):
    for i in range(retries):
        response = requests.post(endpoint, json=data, headers=headers)
        if response.status_code == 429:
            wait_time = 2 ** i
            print(f"Rate limited. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            response.raise_for_status()
            return response
    raise Exception("Failed after retries.")

class GroqResumeExtractor:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GROQ_KEY")
        self.model = "llama3-70b-8192"
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def extract_text_from_pdf(self, pdf_path):
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text.strip()

    def extract_info(self, resume_text):
        prompt = f"""
Extract resume information as strict minified JSON (one line, no line breaks, no extra text).

Expected structure:
{{"name":"", "email":"", "phone":"", "skills":["", "", ""], "experience":["", "", ""]}}

Only return this JSON. No explanations. No markdown.
Resume:
{resume_text}
"""


        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
            
        }
        
        time.sleep(10)
        response = safe_post_request(self.endpoint, data, headers)
        try:
            reply = response.json()["choices"][0]["message"]["content"]
            return json.loads(reply)
        except Exception as e:
            print("Error parsing JSON:", e)
            return {"error": str(e), "raw_response": response.text}

    def process_resume_folder(self, folder_path):
        results = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(folder_path, filename)
                print(f"\n📄 Processing: {filename}")
                text = self.extract_text_from_pdf(file_path)
                info = self.extract_info(text)
                results.append({"file": filename, "info": info})
        return results

# 🧪 Test
# if __name__ == "__main__":
#     folder = "./resumes"  # your folder of PDFs
#     extractor = GroqResumeExtractor()
#     extracted = extractor.process_resume_folder(folder)

#     print("\n✅ Final Extracted Info:")
#     print(json.dumps(extracted, indent=2))


class ResumeRanker:
    def __init__(self, job_description):
        self.job_desc = job_description
        self.model = SentenceTransformer("all-MiniLM-L6-v2")  # fast, lightweight

    def rank_resumes(self, resume_texts):
        job_embedding = self.model.encode(self.job_desc, convert_to_tensor=True)
        scores = []
        for resume_text in resume_texts:
            resume_embedding = self.model.encode(resume_text, convert_to_tensor=True)
            score = util.cos_sim(job_embedding, resume_embedding).item()
            scores.append(score)
        return scores


def process_resumes(folder_path, job_description):
    extractor = GroqResumeExtractor()
    ranker = ResumeRanker(job_description)

    resume_texts = []
    detailed_results = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            print(f"📄 Processing: {filename}")
            file_path = os.path.join(folder_path, filename)
            text = extractor.extract_text_from_pdf(file_path)
            info = extractor.extract_info(text)
            resume_texts.append(text)
            detailed_results.append({
                "file": filename,
                "info": info,
                "text": text  # keep for ranking
            })
            
            print(info)

    scores = ranker.rank_resumes([res["text"] for res in detailed_results])

    for i, result in enumerate(detailed_results):
        result["relevance_score"] = round(scores[i], 4)
        del result["text"]  # remove raw text from final output

    return sorted(detailed_results, key=lambda x: x["relevance_score"], reverse=True)


# 🧪 Run test
if __name__ == "__main__":
    folder = "./resumes"
    job_desc = """
    We are seeking a Python developer with experience in web scraping, API integration, and working with machine learning pipelines. 
    Familiarity with AWS, Docker, and CI/CD is a bonus.
    """
    ranked = process_resumes(folder, job_desc)

    print("\n✅ Ranked Resumes:")
    print(json.dumps(ranked, indent=2))
