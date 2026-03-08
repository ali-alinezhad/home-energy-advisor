import json
import re
from datetime import datetime

from app.core.logging import logger
from app.llm.client import generate_advice
from app.schemas.advice import AdviceResponse


def build_prompt(home) -> str:
    current_year = datetime.now().year
    home_age_years = current_year - home.year_built

    return f"""
You are a senior home energy advisor.

Your job is to review a single home's characteristics and return
the three most valuable energy-saving improvements for that home.

Home details:
- Size: {home.size} sqm
- Year built: {home.year_built}
- Approximate home age: {home_age_years} years
  (derived from current year {current_year})
- Heating type: {home.heating_type}
- Insulation level: {home.insulation_level}

Ranking rules:
- Rank recommendations by expected energy-saving impact first
- Prefer practical actions a homeowner can realistically take
- Consider the current heating system and insulation level
  before suggesting upgrades
- Consider the home's construction era when suggesting envelope upgrades
- Avoid repeating the same idea in different words

Output rules:
- Return exactly 3 recommendations
- Each recommendation must be specific and actionable
- Each description must be one short sentence under 30 words
- Use only these priority values: high, medium, low
- Return only valid JSON
- Do not include markdown or commentary

Required JSON format:
{{
  "recommendations": [
    {{"title": "string", "description": "string", "priority": "high"}},
    {{"title": "string", "description": "string", "priority": "medium"}},
    {{"title": "string", "description": "string", "priority": "low"}}
  ]
}}
""".strip()


def parse_and_validate_advice(raw_response: str) -> AdviceResponse:
    try:
        data = json.loads(raw_response)
        return AdviceResponse.model_validate(data)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if not match:
            logger.error(
                "No JSON object found in LLM response: %s", raw_response
            )
            raise RuntimeError("LLM returned invalid JSON")

        try:
            data = json.loads(match.group())
            return AdviceResponse.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse extracted JSON: %s", raw_response)
            raise RuntimeError("LLM returned invalid JSON") from e
    except Exception as e:
        logger.error("LLM response schema validation failed: %s", raw_response)
        raise RuntimeError("LLM returned invalid structured advice") from e


def get_advice(home, db):
    prompt = build_prompt(home)
    raw_response = generate_advice(prompt)
    validated_response = parse_and_validate_advice(raw_response)

    home.latest_advice = validated_response.model_dump_json()
    home.advice_generated_at = datetime.utcnow()
    db.add(home)
    db.commit()
    db.refresh(home)

    logger.info("Fresh advice generated and saved for home_id=%s", home.id)
    return validated_response
