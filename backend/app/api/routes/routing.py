from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.routing import AnswerRoutingPlanRequest, AnswerRoutingPlanResponse
from app.services.model_routing_service import ModelRoutingService

router = APIRouter(prefix="/routing", tags=["routing"])


@router.post("/answer-plan", response_model=AnswerRoutingPlanResponse)
def build_answer_routing_plan(
    request: AnswerRoutingPlanRequest,
) -> AnswerRoutingPlanResponse:
    settings = get_settings()
    service = ModelRoutingService()

    openai_configured = bool(settings.openai_api_key)

    return service.build_answer_plan(
        request=request,
        openai_configured=openai_configured,
    )
