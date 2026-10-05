from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import EvaluationResult
from app.schemas.evaluations import (
    EvaluationDatasetCreateRequest,
    EvaluationDatasetResponse,
    EvaluationDatasetRunRequest,
    EvaluationQuestion,
    EvaluationResultResponse,
    EvaluationRunComparisonResponse,
    EvaluationRunReportResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
)
from app.services.evaluation_dataset_service import EvaluationDatasetService
from app.services.evaluation_reporting_service import EvaluationReportingService
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/run", response_model=EvaluationRunResponse)
def run_evaluation(
    request: EvaluationRunRequest,
    db: Session = Depends(get_db),
) -> EvaluationRunResponse:
    service = EvaluationService(db)

    try:
        run = service.run_evaluation(
            run_name=request.run_name,
            questions=request.questions,
            retrieval_mode=request.retrieval_mode,
            top_k=request.top_k,
            answer_strategy=request.answer_strategy,
            answer_provider=request.answer_provider,
            answer_providers=request.answer_providers,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    return _to_run_response(run=run, db=db)


@router.get("/runs/compare", response_model=EvaluationRunComparisonResponse)
def compare_evaluation_runs(
    run_ids: list[UUID] = Query(...),
    db: Session = Depends(get_db),
) -> EvaluationRunComparisonResponse:
    service = EvaluationReportingService(db)

    try:
        return service.compare_runs(run_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs/{run_id}/report", response_model=EvaluationRunReportResponse)
def get_evaluation_run_report(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> EvaluationRunReportResponse:
    service = EvaluationReportingService(db)
    report = service.get_run_report(run_id)

    if report is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")

    return report


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
def get_evaluation_run(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> EvaluationRunResponse:
    service = EvaluationService(db)
    run = service.get_run(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")

    return _to_run_response(run=run, db=db)


@router.post("/datasets", response_model=EvaluationDatasetResponse)
def create_evaluation_dataset(
    request: EvaluationDatasetCreateRequest,
    db: Session = Depends(get_db),
) -> EvaluationDatasetResponse:
    service = EvaluationDatasetService(db)

    try:
        dataset = service.create_dataset(
            name=request.name,
            description=request.description,
            questions=[
                question.model_dump(mode="json")
                for question in request.questions
            ],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _to_dataset_response(dataset)


@router.get("/datasets", response_model=list[EvaluationDatasetResponse])
def list_evaluation_datasets(
    db: Session = Depends(get_db),
) -> list[EvaluationDatasetResponse]:
    service = EvaluationDatasetService(db)
    datasets = service.list_datasets()

    return [_to_dataset_response(dataset) for dataset in datasets]


@router.get("/datasets/{dataset_id}", response_model=EvaluationDatasetResponse)
def get_evaluation_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
) -> EvaluationDatasetResponse:
    service = EvaluationDatasetService(db)
    dataset = service.get_dataset(dataset_id)

    if dataset is None:
        raise HTTPException(status_code=404, detail="Evaluation dataset not found.")

    return _to_dataset_response(dataset)


@router.post("/datasets/{dataset_id}/run", response_model=EvaluationRunResponse)
def run_evaluation_dataset(
    dataset_id: UUID,
    request: EvaluationDatasetRunRequest,
    db: Session = Depends(get_db),
) -> EvaluationRunResponse:
    dataset_service = EvaluationDatasetService(db)
    evaluation_service = EvaluationService(db)

    dataset = dataset_service.get_dataset(dataset_id)

    if dataset is None:
        raise HTTPException(status_code=404, detail="Evaluation dataset not found.")

    try:
        question_dicts = dataset_service.extract_questions(dataset)
        questions = [
            EvaluationQuestion.model_validate(question)
            for question in question_dicts
        ]

        run = evaluation_service.run_evaluation(
            run_name=request.run_name or f"{dataset.name}_run",
            questions=questions,
            retrieval_mode=request.retrieval_mode,
            top_k=request.top_k,
            answer_strategy=request.answer_strategy,
            answer_provider=request.answer_provider,
            answer_providers=request.answer_providers,
        )

        run.run_metadata = {
            **(run.run_metadata or {}),
            "dataset_id": str(dataset.id),
            "dataset_name": dataset.name,
            "dataset_question_count": len(questions),
            "run_source": "evaluation_dataset",
        }
        db.commit()
        db.refresh(run)

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    return _to_run_response(run=run, db=db)


def _to_dataset_response(dataset) -> EvaluationDatasetResponse:
    dataset_json = dataset.dataset_json or {}
    questions = dataset_json.get("questions", [])

    return EvaluationDatasetResponse(
        dataset_id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        question_count=len(questions) if isinstance(questions, list) else 0,
        dataset_json=dataset_json,
        created_at=dataset.created_at,
    )


def _to_run_response(run, db: Session) -> EvaluationRunResponse:
    results = (
        db.query(EvaluationResult)
        .filter(EvaluationResult.run_id == run.id)
        .order_by(EvaluationResult.created_at.asc())
        .all()
    )

    return EvaluationRunResponse(
        run_id=run.id,
        run_name=run.run_name,
        retrieval_mode=run.retrieval_mode,
        answer_strategy=run.answer_strategy,
        answer_provider=run.answer_provider,
        answer_providers=run.answer_providers,
        total_questions=run.total_questions,
        average_score=run.average_score,
        status=run.status,
        created_at=run.created_at,
        results=[
            EvaluationResultResponse(
                question=result.question,
                expected_answer=result.expected_answer,
                actual_answer=result.actual_answer,
                request_id=result.request_id,
                score=result.score,
                retrieved_chunks_count=result.retrieved_chunks_count,
                citations_count=result.citations_count,
                evaluation_details=result.evaluation_details,
            )
            for result in results
        ],
    )
