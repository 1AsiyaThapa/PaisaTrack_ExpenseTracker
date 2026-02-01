from fastapi import APIRouter, HTTPException, status, Depends
from app.core.security import get_current_user_id
from .schemas import LLMRequest, LLMResponse
from .service import ChatbotService

router = APIRouter()


def get_chatbot_service() -> ChatbotService:
    return ChatbotService()


@router.post("/generate", response_model=LLMResponse)
def generate_chat_response(
    request: LLMRequest,
    user_id: str = Depends(get_current_user_id),
    service: ChatbotService = Depends(get_chatbot_service),
):
    try:
        response_text = service.generate_financial_answer(
            request.prompt, user_id, request.history
        )
        return LLMResponse(response=response_text)

    except HTTPException as he:
        raise he
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"Error in chatbot [{error_type}]: {error_msg}")
        import traceback

        traceback.print_exc()

        return LLMResponse(
            response=f"Error: {error_msg}",
            error=error_msg,
            debug_info=f"Type: {error_type}",
        )
