from fastapi import APIRouter, HTTPException, status, Request
from app.services.chatbot.llm_client import generate_financial_answer
from app.schemas import LLMRequest, LLMResponse
from app.routes.transactions import get_current_user_id

router = APIRouter()


@router.post("/generate", response_model=LLMResponse)
async def generate_chat_response(request: LLMRequest, req: Request):
    try:
        user_id = get_current_user_id(req)
        response_text = generate_financial_answer(request.prompt, user_id)
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
            debug_info=f"Type: {error_type}"
        )
