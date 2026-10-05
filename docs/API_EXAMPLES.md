# API Examples

Base URL:

~~~text
http://localhost:8000
~~~

## Health

~~~powershell
curl.exe http://localhost:8000/health/deps
~~~

## Ask with hybrid retrieval

Create `ask.json`:

~~~json
{
  "question": "Where should audit history be stored?",
  "top_k": 5,
  "retrieval_mode": "hybrid",
  "answer_strategy": "single",
  "answer_provider": "local_extractive"
}
~~~

Run:

~~~powershell
curl.exe -X POST http://localhost:8000/query/ask `
  -H "Content-Type: application/json" `
  --data-binary "@./ask.json"
~~~

## Ask with metadata filter

Create `ask_filtered.json`:

~~~json
{
  "question": "Where should audit history be stored?",
  "top_k": 5,
  "retrieval_mode": "hybrid",
  "filters": {
    "filename": "sample_policy_milestone3.txt"
  },
  "answer_strategy": "single",
  "answer_provider": "local_extractive"
}
~~~

Run:

~~~powershell
curl.exe -X POST http://localhost:8000/query/ask `
  -H "Content-Type: application/json" `
  --data-binary "@./ask_filtered.json"
~~~

## Compare answer providers

Create `ask_compare.json`:

~~~json
{
  "question": "Where should audit history be stored?",
  "top_k": 5,
  "retrieval_mode": "hybrid",
  "answer_strategy": "compare",
  "answer_providers": ["local_extractive", "local_summary"]
}
~~~

Run:

~~~powershell
curl.exe -X POST http://localhost:8000/query/ask `
  -H "Content-Type: application/json" `
  --data-binary "@./ask_compare.json"
~~~

## Validate citations

Create `citation_validate.json`:

~~~json
{
  "question": "Where should audit history be stored?",
  "top_k": 5,
  "retrieval_mode": "hybrid",
  "answer_strategy": "single",
  "answer_provider": "local_extractive"
}
~~~

Run:

~~~powershell
curl.exe -X POST http://localhost:8000/citations/validate-rag `
  -H "Content-Type: application/json" `
  --data-binary "@./citation_validate.json"
~~~

## Run evaluation

Create `eval_run.json`:

~~~json
{
  "run_name": "local_eval_smoke_test",
  "retrieval_mode": "hybrid",
  "top_k": 5,
  "answer_strategy": "compare",
  "answer_providers": ["local_extractive", "local_summary"],
  "questions": [
    {
      "question": "Where should audit history be stored?",
      "expected_answer": "Audit history should be stored in PostgreSQL."
    },
    {
      "question": "What should Qdrant store?",
      "expected_answer": "Qdrant should store vector embeddings."
    }
  ]
}
~~~

Run:

~~~powershell
curl.exe -X POST http://localhost:8000/evaluations/run `
  -H "Content-Type: application/json" `
  --data-binary "@./eval_run.json"
~~~

## Create evaluation dataset

Create `dataset.json`:

~~~json
{
  "name": "core_storage_benchmark_v1",
  "description": "Small benchmark for RAGOps storage/retrieval behavior.",
  "questions": [
    {
      "question": "Where should audit history be stored?",
      "expected_answer": "Audit history should be stored in PostgreSQL.",
      "tags": ["audit", "postgresql"]
    },
    {
      "question": "What should Qdrant store?",
      "expected_answer": "Qdrant should store vector embeddings.",
      "tags": ["qdrant", "vector-search"]
    }
  ]
}
~~~

Run:

~~~powershell
curl.exe -X POST http://localhost:8000/evaluations/datasets `
  -H "Content-Type: application/json" `
  --data-binary "@./dataset.json"
~~~

## Run saved dataset

Create `dataset_run.json`:

~~~json
{
  "run_name": "dataset_run_smoke_test",
  "retrieval_mode": "hybrid",
  "top_k": 5,
  "answer_strategy": "compare",
  "answer_providers": ["local_extractive", "local_summary"]
}
~~~

Run:

~~~powershell
curl.exe -X POST http://localhost:8000/evaluations/datasets/<DATASET_ID>/run `
  -H "Content-Type: application/json" `
  --data-binary "@./dataset_run.json"
~~~

## Run async evaluation job

Create `async_eval.json`:

~~~json
{
  "run_name": "async_eval_smoke_test",
  "retrieval_mode": "hybrid",
  "top_k": 5,
  "answer_strategy": "compare",
  "answer_providers": ["local_extractive", "local_summary"],
  "questions": [
    {
      "question": "Where should audit history be stored?",
      "expected_answer": "Audit history should be stored in PostgreSQL."
    },
    {
      "question": "What should Qdrant store?",
      "expected_answer": "Qdrant should store vector embeddings."
    }
  ]
}
~~~

Run:

~~~powershell
curl.exe -X POST http://localhost:8000/jobs/evaluations/run `
  -H "Content-Type: application/json" `
  --data-binary "@./async_eval.json"
~~~

## Check async job

~~~powershell
curl.exe http://localhost:8000/jobs/<JOB_ID>
~~~

## Dashboard

~~~powershell
curl.exe http://localhost:8000/dashboard/overview
curl.exe http://localhost:8000/dashboard/evaluations
curl.exe http://localhost:8000/dashboard/retrieval
curl.exe http://localhost:8000/dashboard/jobs
~~~

## Routing plan

Create `routing_plan.json`:

~~~json
{
  "question": "Where should audit history be stored?",
  "retrieval_mode": "hybrid",
  "top_k": 5,
  "task_type": "qa",
  "priority": "cost",
  "allow_paid_providers": false,
  "max_estimated_cost_usd": 0.0
}
~~~

Run:

~~~powershell
curl.exe -X POST http://localhost:8000/routing/answer-plan `
  -H "Content-Type: application/json" `
  --data-binary "@./routing_plan.json"
~~~

## Frontend

~~~text
http://localhost:5173
~~~
