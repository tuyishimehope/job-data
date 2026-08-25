import json
from openai import OpenAI
import requests
from app.core.settings import settings
from app.service.job_board.schema import JobAIExtraction, NormalizedJob

class LLMService:

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-type": "application/json"
        }

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
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                data=json.dumps({
                    "model": "inclusionai/ling-3.0-flash-sante:free",
                    "messages": [
                        {
                                "role": "user",
                                "content": content
                                }
                    ],
                }),
                timeout=(10, 120)
            )

            data = response.json()
            print("data: ", data)
            result = data["choices"][0]["message"]["content"]

            parsed = self.parse_llm_json(result)

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


    def parse_llm_json(self, result: str) -> dict:
        result = result.strip()

        if result.startswith("```json"):
            result = result[len("```json"):]

        elif result.startswith("```"):
            result = result[len("```"):]

        if result.endswith("```"):
            result = result[:-3]

        result = result.strip()

        return json.loads(result)
llm_service = LLMService()
