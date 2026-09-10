"""
Evaluator factory — selects the right evaluator based on config.

This is the only place that knows about all evaluator implementations.
The service layer just calls get_evaluator() and uses BaseEvaluator.
"""
from __future__ import annotations

import logging

from app.evaluators.base import BaseEvaluator
from app.evaluators.mock_evaluator import MockEvaluator
from app.evaluators.rule_based_evaluator import RuleBasedEvaluator

logger = logging.getLogger(__name__)


def get_evaluator(config) -> BaseEvaluator:
    """
    Return the appropriate evaluator based on EVALUATOR_TYPE config.
    Falls back to RuleBasedEvaluator if AI is requested but key is missing.
    """
    evaluator_type = getattr(config, "EVALUATOR_TYPE", "rule_based")

    if evaluator_type == "mock":
        logger.info("Using MockEvaluator")
        return MockEvaluator()

    if evaluator_type == "ai":
        api_key = getattr(config, "OPENAI_API_KEY", "")
        if not api_key:
            logger.warning(
                "EVALUATOR_TYPE=ai but OPENAI_API_KEY is missing — falling back to RuleBasedEvaluator"
            )
            return RuleBasedEvaluator()
        try:
            from app.evaluators.ai_evaluator import AIEvaluator
            model = getattr(config, "OPENAI_MODEL", "gpt-4o")
            timeout = getattr(config, "AI_TIMEOUT", 30)
            logger.info("Using AIEvaluator with model=%s", model)
            return AIEvaluator(api_key=api_key, model=model, timeout=timeout)
        except Exception as e:
            logger.error("Failed to create AIEvaluator: %s — falling back", e)
            return RuleBasedEvaluator()

    # Default: rule_based
    logger.info("Using RuleBasedEvaluator")
    return RuleBasedEvaluator()
