import pyttsx3

# voices = engine.getProperty('voices')
# for i, v in enumerate(voices):
#     print(f"{i}: ID={v.id}, Name={v.name}, Lang={getattr(v, 'languages', 'N/A')}")

engine = pyttsx3.init()

# Получаем список голосов
voices = engine.getProperty('voices')

# Ищем русский голос по языку или имени
russian_voice = None
for voice in voices:
    if 'ru' in str(voice.languages).lower() or 'irina' in voice.name.lower():
        russian_voice = voice
        break

if russian_voice:
    engine.setProperty('voice', russian_voice.id)
    print(f"✅ Используется голос: {russian_voice.name}")
else:
    print("⚠️ Русский голос не найден")

engine.say("Первая фраза!")
engine.runAndWait()

engine.say("Вторая фраза!")
engine.runAndWait()

engine.say("Третья фраза!")
engine.runAndWait()

