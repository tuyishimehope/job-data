import json
from openai import OpenAI
import requests
from app.core.settings import settings
from app.service.job_board.schema import JobAIExtraction, NormalizedJob

invoke_url = settings.llm_api_url
stream = True
NVIDIA_API_KEY = settings.nvidia_api_key


class LLMService:

    def __init__(self):
        self.API_URL = settings.hf_url
        self.headers = {
            "Authorization": f"Bearer {settings.hf_token}",
        }
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def extract_fields(
        self,
        job: NormalizedJob,
    ) -> JobAIExtraction | None:

        job_context = {
            "title": job.title,
            "company_name": job.company_name,
            "location": (
                job.location.model_dump()
                if job.location
                else None
            ),
            "content": job.content,
        }

        # payload = {
        #     "messages": [
        #         {
        #             "role": "user",
        #             "content": (
        #                 "Extract structured information from this job posting.\n\n"
        #                 "Return ONLY valid JSON.\n"
        #                 "Do not include markdown or explanations.\n\n"
        #                 "Fields:\n"
        #                 "- application_deadline\n"
        #                 "- visa_sponsorship\n"
        #                 "- visa_sponsorship_details\n"
        #                 "- relocation_support\n"
        #                 "- min_years_experience\n"
        #                 "- max_years_experience\n"
        #                 "- experience_level\n"
        #                 "- skills\n"
        #                 "- technologies\n"
        #                 "- required_languages\n\n"
        #                 f"Job:\n{json.dumps(job_context)}"
        #             ),
        #         }
        #     ],
        #     "model": "zai-org/GLM-5.3:novita",
        # }
        
        content = (
            "Extract structured information from this job posting.\n\n"
            "Return ONLY valid JSON.\n"
            "Do not include markdown or explanations.\n\n"
            "Fields:\n"
            "- application_deadline\n"
            "- visa_sponsorship\n"
            "- visa_sponsorship_details\n"
            "- relocation_support\n"
            "- min_years_experience\n"
            "- max_years_experience\n"
            "- experience_level\n"
            "- skills\n"
            "- technologies\n"
            "- required_languages\n\n"
            f"Job:\n{json.dumps(job_context)}"
        )
        try:
            # response = requests.post(
            #     self.API_URL,
            #     headers=self.headers,
            #     json=payload,
            #     timeout=(10, 120),
            # )

            # response.raise_for_status()

            # content = response.json()["choices"][0]["message"]["content"]

            response = self.client.responses.create(
                model="gpt-5.5",
                # instructions=instructions,
                input=content
            )
            content = response.output_text

            parsed = json.loads(content)

            return JobAIExtraction.model_validate(parsed)

        except requests.exceptions.ReadTimeout:
            print(f"LLM timeout: {job.title}")
            return None

        except requests.exceptions.RequestException as exc:
            print(f"LLM request failed: {exc}")
            return None

        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            print(f"Invalid LLM response: {exc}")
            return None


llm_service = LLMService()
