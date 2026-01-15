import json
from typing import Optional

import httpx

from server.core.config import settings
from server.schemas.extract import ExtractRequest, ExtractResponse


def _is_configured() -> bool:
    return bool(settings.llm_base_url and settings.llm_api_key and settings.llm_model)


async def extract_entities(payload: ExtractRequest) -> Optional[ExtractResponse]:
    if not _is_configured():
        return None

    prompt = (
        "Extract entities and relationships as JSON with keys entities and relationships. "
        "Each entity must include type and name, relationships must include from_entity_name, "
        "to_entity_name, and type."
    )

    request_body = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": payload.content},
        ],
        "temperature": 0,
    }

    async with httpx.AsyncClient(base_url=settings.llm_base_url) as client:
        response = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json=request_body,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    payload_json = json.loads(content)
    return ExtractResponse(**payload_json)
