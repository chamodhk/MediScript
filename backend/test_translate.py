from services.translate_service import TranslationService

translator = TranslationService()

doctor_name = "Dr. Perera"
session_datetime = "2026-04-02 10:45 AM"

heading_en = "Manage fever, body pain, and sore throat at home with medicine and rest"

instructions_en = [
    "Take paracetamol 500 milligrams every six hours after meals for three days.",
    "Drink plenty of water.",
    "Get enough rest.",
]

follow_up_en = [
    "Clinic visit next Monday at 9 AM."
]

translated_heading = translator.translate_to_sinhala(heading_en)
translated_instructions = [
    translator.translate_to_sinhala(item) for item in instructions_en
]
translated_follow_up = [
    translator.translate_to_sinhala(item) for item in follow_up_en
]

lines = []
lines.append("🏥 වෛද්‍ය උපදෙස් සාරාංශය")
lines.append("")
lines.append(f"වෛද්‍යවරයා: {doctor_name}")
lines.append(f"දිනය හා වේලාව: {session_datetime}")
lines.append("")
lines.append(translated_heading)
lines.append("")
lines.append("උපදෙස්:")

for item in translated_instructions:
    lines.append(f"- {item}")

lines.append("")
lines.append("නැවත පරීක්ෂාව:")

for item in translated_follow_up:
    lines.append(f"- {item}")

lines.append("")
lines.append("අමතර පැහැදිලි කිරීමක් අවශ්‍ය නම් රෝහල අමතන්න.")

message = "\n".join(lines)

print(message)