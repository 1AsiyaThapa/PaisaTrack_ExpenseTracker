from fastapi import APIRouter, HTTPException, status
from app.services.chatbot.llm_client import generate_text
from app.schemas import LLMRequest, LLMResponse

router = APIRouter()

@router.post("/generate", response_model=LLMResponse)
async def generate_chat_response(request: LLMRequest):
    """
    Generate a response from the LLM based on the user's prompt.
    """
    try:
        response_text = generate_text(request.prompt)
        return LLMResponse(response=response_text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request."
        )
