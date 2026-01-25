import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
chat = client.chats.create(model="gemini-2.5-flash")


def send_and_trim(user_text):
    global chat
    chat.send_message(user_text)

    current_history = chat.get_history()
    if len(current_history) > 10:
        trimmed_history = current_history[-10:]
        chat = client.chats.create(model="gemini-2.5-flash", history=trimmed_history)


send_and_trim("my name is Asiya")
send_and_trim("what is my name?")

for message in chat.get_history():
    print(f"{message.role}: {message.parts[0].text}")
    print("-" * 20)
