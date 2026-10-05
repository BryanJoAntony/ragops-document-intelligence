from app.schemas.routing import AnswerRoutingPlanRequest


class ModelRoutingService:
    # Placeholder pricing values for local planning only.
    # Keep these configurable later if real billing accuracy is needed.
    PROVIDER_PRICING = {
        "local_extractive": {
            "input_per_token": 0.0,
            "output_per_token": 0.0,
            "available_without_key": True,
        },
        "local_summary": {
            "input_per_token": 0.0,
            "output_per_token": 0.0,
            "available_without_key": True,
        },
        "openai": {
            "input_per_token": 0.00000015,
            "output_per_token": 0.00000060,
            "available_without_key": False,
        },
    }

    def build_answer_plan(
        self,
        request: AnswerRoutingPlanRequest,
        openai_configured: bool = False,
    ) -> dict:
        estimated_context_tokens = self.estimate_context_tokens(
            question=request.question,
            top_k=request.top_k,
        )
        estimated_output_tokens = self.estimate_output_tokens(
            task_type=request.task_type,
            question=request.question,
        )

        provider_estimates = [
            self.estimate_provider_cost(
                provider=provider,
                input_token_estimate=estimated_context_tokens,
                output_token_estimate=estimated_output_tokens,
                allow_paid_providers=request.allow_paid_providers,
                max_estimated_cost_usd=request.max_estimated_cost_usd,
                openai_configured=openai_configured,
            )
            for provider in request.candidate_providers
        ]

        available_estimates = [
            estimate
            for estimate in provider_estimates
            if estimate["available"] and estimate["within_budget"]
        ]

        warnings: list[str] = []
        reasons: list[str] = []

        if not available_estimates:
            warnings.append("No candidate provider was both available and within budget.")
            fallback = self.estimate_provider_cost(
                provider="local_extractive",
                input_token_estimate=estimated_context_tokens,
                output_token_estimate=estimated_output_tokens,
                allow_paid_providers=False,
                max_estimated_cost_usd=0.0,
                openai_configured=openai_configured,
            )
            available_estimates = [fallback]

        if request.require_compare:
            compare_providers = [
                estimate["provider"]
                for estimate in available_estimates
                if estimate["provider"] in {"local_extractive", "local_summary", "openai"}
            ]

            if len(compare_providers) >= 2:
                reasons.append("Compare strategy selected because require_compare=true.")
                return {
                    "recommended_answer_provider": None,
                    "recommended_answer_strategy": "compare",
                    "recommended_answer_providers": compare_providers[:2],
                    "priority": request.priority,
                    "task_type": request.task_type,
                    "estimated_context_tokens": estimated_context_tokens,
                    "estimated_output_tokens": estimated_output_tokens,
                    "provider_estimates": provider_estimates,
                    "reasons": reasons,
                    "warnings": warnings,
                }

            warnings.append("Compare requested but fewer than two providers are available within budget.")

        recommended = self._choose_provider(
            available_estimates=available_estimates,
            task_type=request.task_type,
            priority=request.priority,
            allow_paid_providers=request.allow_paid_providers,
        )

        reasons.append(
            self._build_recommendation_reason(
                provider=recommended["provider"],
                task_type=request.task_type,
                priority=request.priority,
            )
        )

        return {
            "recommended_answer_provider": recommended["provider"],
            "recommended_answer_strategy": "single",
            "recommended_answer_providers": None,
            "priority": request.priority,
            "task_type": request.task_type,
            "estimated_context_tokens": estimated_context_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "provider_estimates": provider_estimates,
            "reasons": reasons,
            "warnings": warnings,
        }

    @staticmethod
    def estimate_context_tokens(question: str, top_k: int) -> int:
        question_tokens = max(len(question.split()), 1)
        estimated_chunk_tokens = top_k * 180
        return question_tokens + estimated_chunk_tokens

    @staticmethod
    def estimate_output_tokens(task_type: str, question: str) -> int:
        if task_type == "summary":
            return 220

        if task_type == "comparison":
            return 260

        if task_type == "evaluation":
            return 180

        if len(question.split()) > 25:
            return 180

        return 120

    def estimate_provider_cost(
        self,
        provider: str,
        input_token_estimate: int,
        output_token_estimate: int,
        allow_paid_providers: bool,
        max_estimated_cost_usd: float,
        openai_configured: bool,
    ) -> dict:
        pricing = self.PROVIDER_PRICING.get(provider)

        if pricing is None:
            return {
                "provider": provider,
                "input_token_estimate": input_token_estimate,
                "output_token_estimate": output_token_estimate,
                "total_token_estimate": input_token_estimate + output_token_estimate,
                "estimated_cost_usd": 0.0,
                "within_budget": False,
                "available": False,
                "reason": "Unknown provider.",
            }

        estimated_cost = round(
            (input_token_estimate * pricing["input_per_token"])
            + (output_token_estimate * pricing["output_per_token"]),
            8,
        )

        is_paid_provider = estimated_cost > 0
        available = True

        if provider == "openai" and not openai_configured:
            available = False

        if is_paid_provider and not allow_paid_providers:
            within_budget = False
            reason = "Paid provider is disabled by request."
        elif is_paid_provider and estimated_cost > max_estimated_cost_usd:
            within_budget = False
            reason = "Estimated cost exceeds max_estimated_cost_usd."
        elif not available:
            within_budget = False
            reason = "Provider is not configured."
        else:
            within_budget = True
            reason = "Provider is available within budget."

        return {
            "provider": provider,
            "input_token_estimate": input_token_estimate,
            "output_token_estimate": output_token_estimate,
            "total_token_estimate": input_token_estimate + output_token_estimate,
            "estimated_cost_usd": estimated_cost,
            "within_budget": within_budget,
            "available": available,
            "reason": reason,
        }

    @staticmethod
    def _choose_provider(
        available_estimates: list[dict],
        task_type: str,
        priority: str,
        allow_paid_providers: bool,
    ) -> dict:
        provider_names = {estimate["provider"]: estimate for estimate in available_estimates}

        if priority == "cost":
            return min(
                available_estimates,
                key=lambda estimate: estimate["estimated_cost_usd"],
            )

        if priority == "latency":
            if "local_extractive" in provider_names:
                return provider_names["local_extractive"]

        if task_type == "summary" and "local_summary" in provider_names:
            return provider_names["local_summary"]

        if priority == "quality" and allow_paid_providers and "openai" in provider_names:
            return provider_names["openai"]

        if "local_extractive" in provider_names:
            return provider_names["local_extractive"]

        return available_estimates[0]

    @staticmethod
    def _build_recommendation_reason(
        provider: str,
        task_type: str,
        priority: str,
    ) -> str:
        if provider == "local_extractive":
            return "local_extractive selected as the safe default for grounded cited answers."

        if provider == "local_summary":
            return "local_summary selected because the task is summary-oriented or suited for concise local output."

        if provider == "openai":
            return "openai selected because quality priority and budget/configuration allow a paid provider."

        return f"{provider} selected based on routing priority={priority} and task_type={task_type}."
