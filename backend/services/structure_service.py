import ollama
import json
import gc


class StructureService:

    def structure(self, raw_text: str) -> dict:
        try:
            print("Structuring text...")

            prompt = f"""
You are a medical assistant AI.

Your task is to convert a doctor's spoken instructions into STRICT JSON format.

IMPORTANT RULES:
- Output ONLY valid JSON
- Do NOT include explanations, notes, or extra text
- Do NOT include markdown (no ```json)
- Ensure JSON is properly formatted and parsable
- If data is missing, use null or empty arrays

INPUT TEXT:
\"\"\"{raw_text}\"\"\"

OUTPUT FORMAT:
{{
  "greetings": "short friendly greeting to patient",
  "heading": "short summary of doctor's advice",

  "instructions": [
    "clear instruction 1",
    "clear instruction 2",
    "clear instruction 3"
  ],

  "follow_up": [
    {{
      "type": "checkup | lab test | clinic visit",
      "when": "time mentioned (e.g., 2 weeks, next month)"
    }}
  ]
}}

GUIDELINES:
- Convert medical advice into simple patient-friendly instructions
- Keep sentences short and clear
- Extract follow-up actions only if mentioned
- Do NOT hallucinate missing medical info

RETURN ONLY JSON.
"""

            response = ollama.chat(
                model="phi3",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            raw_response = response["message"]["content"]

            cleaned = raw_response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0]
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0]

            structured = json.loads(cleaned.strip())
            print("Structuring complete!")

            gc.collect()

            return structured

        except json.JSONDecodeError:
            print("JSON parsing failed, returning fallback")
            return {
                "medicines": [],
                "instructions": [raw_text],
                "follow_up": []
            }

        except Exception as e:
            raise Exception(f"Structuring failed: {str(e)}")