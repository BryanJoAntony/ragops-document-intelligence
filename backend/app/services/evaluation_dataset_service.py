from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import EvaluationDataset


class EvaluationDatasetService:
    def __init__(self, db: Session):
        self.db = db

    def create_dataset(
        self,
        name: str,
        description: str | None,
        questions: list[dict],
    ) -> EvaluationDataset:
        existing = (
            self.db.query(EvaluationDataset)
            .filter(EvaluationDataset.name == name)
            .first()
        )

        if existing is not None:
            raise ValueError(f"Evaluation dataset already exists with name: {name}")

        dataset = EvaluationDataset(
            name=name,
            description=description,
            dataset_json={
                "questions": questions,
                "question_count": len(questions),
                "schema_version": "evaluation_dataset_v1",
            },
        )

        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)

        return dataset

    def list_datasets(self) -> list[EvaluationDataset]:
        return (
            self.db.query(EvaluationDataset)
            .order_by(EvaluationDataset.created_at.desc())
            .all()
        )

    def get_dataset(self, dataset_id: UUID) -> EvaluationDataset | None:
        return self.db.get(EvaluationDataset, dataset_id)

    @staticmethod
    def extract_questions(dataset: EvaluationDataset) -> list[dict]:
        dataset_json = dataset.dataset_json or {}
        questions = dataset_json.get("questions", [])

        if not isinstance(questions, list):
            raise ValueError("Evaluation dataset has invalid questions format.")

        return questions
