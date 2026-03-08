import json
import time

from openai import OpenAI

from app.core.logging import logger
from app.core.settings import settings

MAX_LLM_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 1


def _mock_response() -> str:
    return json.dumps(
        {
            "recommendations": [
                {
                    "title": "Seal air leaks",
                    "description": (
                        "Seal drafty doors, windows, and loft penetrations "
                        "to reduce avoidable heat loss."
                    ),
                    "priority": "high",
                },
                {
                    "title": "Upgrade attic insulation",
                    "description": (
                        "Increase attic insulation depth to improve comfort "
                        "and cut heating demand."
                    ),
                    "priority": "medium",
                },
                {
                    "title": "Install smart heating controls",
                    "description": (
                        "Add programmable controls to reduce heating runtime "
                        "when rooms are unused."
                    ),
                    "priority": "low",
                },
            ]
        }
    )


def _get_client() -> OpenAI:
    if not settings.llm_api_key:
        raise RuntimeError(
            "LLM_API_KEY is not set. "
            "Add it to .env or run with MOCK_LLM=true."
        )

    return OpenAI(api_key=settings.llm_api_key)


def generate_advice(prompt: str) -> str:
    if settings.mock_llm:
        logger.info(
            "MOCK_LLM=true, returning deterministic mock advice"
        )
        return _mock_response()

    client = _get_client()

    for attempt in range(1, MAX_LLM_ATTEMPTS + 1):
        try:
            logger.info(
                "Sending prompt to LLM (attempt %s/%s)",
                attempt,
                MAX_LLM_ATTEMPTS,
            )

            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert home energy advisor. "
                            "Return only valid JSON with no markdown "
                            "and no extra text."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                timeout=settings.llm_timeout,
            )

            content = response.choices[0].message.content

            if not content:
                logger.error("LLM returned empty response")
                raise RuntimeError("LLM returned empty response")

            logger.info("LLM response received successfully")
            return content
        except Exception as e:
            logger.exception(
                "LLM request failed on attempt %s/%s",
                attempt,
                MAX_LLM_ATTEMPTS,
            )
            if attempt == MAX_LLM_ATTEMPTS:
                raise RuntimeError(
                    "Failed to generate advice from LLM. Please try again."
                ) from e
            time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError("Failed to generate advice from LLM. Please try again.")
