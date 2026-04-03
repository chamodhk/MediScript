import ollama
import json
import gc


class StructureService:

    def structure(self, raw_text: str) -> dict:
        try:
            print("Structuring text...")

            prompt = f"""
Extract patient instructions and follow-up actions from this doctor transcript.
Return ONLY valid JSON with no markdown or extra text.

Transcript:
\"\"\"{raw_text}\"\"\"

JSON format:
{{
  "instructions": [
    "short clear instruction for the patient"
  ],
  "follow_up": [
    {{
      "instruction_type": "lab_test | scan | clinic_visit | review | follow_up",
      "doctor_instruction": "clear follow-up instruction for the patient",
      "medical_time_reference": "time phrase as spoken, or null",
      "exact_medical_datetime": null,
      "reminder_mode": "absolute | relative | window | conditional",
      "source_text": "source sentence from the transcript"
    }}
  ]
}}

Rules:
- Put medicine and general care advice in "instructions"
- Put tests, scans, reviews, return visits, and urgent return advice in "follow_up"
- Keep phrases like "tomorrow", "next Monday", "within one week", "after three days", or "after test results" in "medical_time_reference"
- Do not invent exact dates or times
- Use "exact_medical_datetime" only if the doctor explicitly gives an exact real date and time
- Use reminder_mode:
  - "absolute" for exact date/time
  - "relative" for tomorrow / after 3 days / next Monday
  - "window" for within a time range
  - "conditional" for if symptoms worsen / after test results
- Split advice into short items
- If none found, return empty arrays
"""
            response = ollama.chat(
                model="gpt-oss:120b-cloud",
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
