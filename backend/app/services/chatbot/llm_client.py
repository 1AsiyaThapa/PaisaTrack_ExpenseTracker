from google import genai
from dotenv import load_dotenv
from sqlalchemy import text
from app.models import engine
from app.schemas import ChatRouting
from app.services.chatbot.prompts import get_routing_system_prompt, get_summary_prompt
from app.services.chatbot.helper import check_and_raise_api_error
import os

load_dotenv()

model_id = "gemini-2.5-flash-lite"
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
chat = client.chats.create(model=model_id)


def send_and_trim(user_text: str) -> str:
    global chat

    if not user_text.strip():
        raise ValueError("Prompt cannot be empty")

    response = chat.send_message(user_text)
    response_text = response.text.strip()

    current_history = chat.get_history()
    if len(current_history) > 10:
        trimmed_history = current_history[-10:]
        chat = client.chats.create(model=model_id, history=trimmed_history)

    return response_text


def generate_text(prompt: str) -> str:
    return send_and_trim(prompt)


def generate_financial_answer(user_question: str, current_user_id: str):
    system_prompt = get_routing_system_prompt(current_user_id)

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=user_question,
            config={
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
                "response_json_schema": ChatRouting.model_json_schema(),
            },
        )

        routing = ChatRouting.model_validate_json(response.text)

    except Exception as e:
        error_str = str(e)
        print(f"Error in structured output parsing: {e}")
        check_and_raise_api_error(error_str)
        
        try:
            return send_and_trim(user_question)
        except Exception as fallback_error:
            check_and_raise_api_error(str(fallback_error))
            return "I'm having trouble understanding your request. As your PaisaTrack Financial Assistant, I'm here to help you track expenses and manage your finances. Could you try rephrasing?"

    if routing.intent == "chat":
        if routing.chat_response:
            return routing.chat_response
        try:
            return send_and_trim(user_question)
        except Exception as e:
            check_and_raise_api_error(str(e))
            return "Hello! I'm your PaisaTrack Financial Assistant AI. I'm here to help you track expenses, analyze spending patterns, and manage your finances. How can I assist you today?"

    if routing.intent == "query":
        if not routing.sql:
            return "I understand you're asking about your finances, but I couldn't generate a query for that. Could you try rephrasing your question?"

        forbidden = ["DELETE", "UPDATE", "DROP", "ALTER", "INSERT", "TRUNCATE"]
        if any(word in routing.sql.upper() for word in forbidden):
            return "I'm sorry, I can't perform that action on your data."

        try:
            print(f"DEBUG SQL: {routing.sql}")

            with engine.connect() as conn:
                result = conn.execute(text(routing.sql))
                data = [dict(row._mapping) for row in result]

            summary_prompt = get_summary_prompt(user_question, data)

            try:
                summary_response = client.models.generate_content(
                    model=model_id, contents=summary_prompt
                )
                return summary_response.text.strip()
            except Exception as summary_error:
                check_and_raise_api_error(str(summary_error))
                try:
                    return send_and_trim(summary_prompt)
                except Exception as fallback_error:
                    check_and_raise_api_error(str(fallback_error))
                    raise summary_error

        except Exception as e:
            error_msg = str(e)
            print(f"SQL ERROR: {error_msg}")
            print(f"SQL that failed: {routing.sql}")
            raise Exception(f"SQL Error: {error_msg} | SQL: {routing.sql}")

    return "I'm your PaisaTrack Financial Assistant AI! I can help you track expenses, analyze spending patterns, and answer questions about your finances. What would you like to know?"
