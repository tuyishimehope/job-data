import requests
import json
from app.core.settings import settings
from app.service.job_board.schema import GreenhouseJob

invoke_url = settings.llm_api_url
stream = True
NVIDIA_API_KEY = settings.nvidia_api_key


class LLMService():
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "text/event-stream" if stream else "application/json",
        }

    def extract_fields(self, job: GreenhouseJob):
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "content": (
                                "Analyze the following job data and extract/complete "
                                "the required fields, focus on deadline, visa, relocation, years, skills because they are hard to extract other fields come from api.\n\n"
                                "Return ONLY valid JSON.\n"
                                "Do not include markdown or explanations.\n\n"
                                "Required fields:\n"
                                "id, internal_job_id, company_name, title, updated_at, "
                                "requisition_id, location, absolute_url, language, content, "
                                "application_deadline, visa_sponsorship, years, skills(a list of string).\n\n"
                                f"Job:\n{job.model_dump_json()}"
                            ), }
                    ]
                }
            ],
            "model": "moonshotai/kimi-k3",
            "max_tokens": 16384,
            "seed": 0,
            "stream": stream,
            "temperature": 1,
            "reasoning_effort": "max"
        }

        response = requests.post(
            invoke_url, headers=self.headers, json=payload, stream=stream)
        print("Status", response.status_code)
        result = ""

        for line in response.iter_lines():
            if not line:
                continue

            decoded_line = line.decode("utf-8")

            if not decoded_line.startswith("data: "):
                continue

            data = decoded_line.removeprefix("data: ")

            if data == "[DONE]":
                break

            chunk = json.loads(data)

            content = chunk["choices"][0]["delta"].get("content")

            if content:
                result += content
                print(f"content: {content}")

        return result


llm_service = LLMService()
