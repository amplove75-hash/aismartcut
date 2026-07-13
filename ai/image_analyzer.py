"""OpenAI Vision API를 이용한 이미지 분석(설명/키워드/추천 검색어) 모듈."""
from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass, field

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QPixmap

_DEFAULT_MODEL = "gpt-4o-mini"

# 1백만 토큰당 가격(USD). OpenAI가 가격을 바꿀 수 있으니 참고용 추정치이며,
# 정확한 최신 가격은 https://platform.openai.com/docs/pricing 에서 확인해야 한다.
_PRICING_PER_MILLION_TOKENS = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}

_SYSTEM_PROMPT = (
    "당신은 캡처된 화면 이미지를 분석하는 도우미입니다. "
    "이미지 속 사물, 장소, 제품, 문서 유형 등을 한국어로 간단히 설명하고, "
    "핵심 키워드와 이미지 검색에 쓸 수 있는 추천 검색어를 뽑아주세요. "
    "반드시 다음 JSON 형식으로만 답하세요(다른 설명 문장 없이): "
    '{"description": "이미지에 대한 한두 문장 설명", '
    '"keywords": ["키워드1", "키워드2", "키워드3"], '
    '"search_terms": ["추천 검색어1", "추천 검색어2"]}'
)


class AiNotConfiguredError(Exception):
    """OpenAI API 키가 설정되지 않았거나 openai 패키지가 없을 때 발생한다."""


@dataclass
class ImageAnalysisResult:
    """AI 이미지 분석 결과."""

    description: str
    keywords: list[str] = field(default_factory=list)
    search_terms: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float | None = None


class ImageAnalyzer:
    """OpenAI Vision API(gpt-4o-mini 등)를 호출해 이미지를 분석하는 래퍼.

    API 키/클라이언트는 실제로 분석을 처음 실행할 때 지연 로딩한다.
    """

    def __init__(self, model: str | None = None) -> None:
        self._model = model or os.environ.get("OPENAI_MODEL", _DEFAULT_MODEL)
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return self._client

        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass  # python-dotenv가 없으면 시스템 환경변수만 사용한다.

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise AiNotConfiguredError(
                "OPENAI_API_KEY가 설정되어 있지 않습니다. "
                "프로젝트 폴더의 .env.example을 .env로 복사한 뒤, "
                "OPENAI_API_KEY=발급받은키 형식으로 채워주세요."
            )

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise AiNotConfiguredError(
                "openai 패키지가 설치되어 있지 않습니다. 'pip install openai'로 설치해주세요."
            ) from exc

        self._client = OpenAI(api_key=api_key)
        return self._client

    def analyze(self, pixmap: QPixmap) -> ImageAnalysisResult:
        """캡처 이미지를 분석해 설명/키워드/추천 검색어를 반환한다."""
        client = self._ensure_client()
        data_uri = _pixmap_to_data_uri(pixmap)

        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                },
            ],
            max_tokens=500,
        )

        raw_text = response.choices[0].message.content or ""
        result = _parse_result(raw_text)

        usage = getattr(response, "usage", None)
        if usage is not None:
            result.input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            result.output_tokens = getattr(usage, "completion_tokens", 0) or 0
            result.total_tokens = getattr(usage, "total_tokens", 0) or 0
            result.estimated_cost_usd = _estimate_cost(
                self._model, result.input_tokens, result.output_tokens
            )

        return result


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """토큰 사용량으로 예상 비용(USD)을 계산한다. 가격표에 없는 모델이면 None을 반환한다."""
    pricing = _PRICING_PER_MILLION_TOKENS.get(model)
    if pricing is None:
        return None
    return (input_tokens / 1_000_000) * pricing["input"] + (
        output_tokens / 1_000_000
    ) * pricing["output"]


def _parse_result(raw_text: str) -> ImageAnalysisResult:
    """모델 응답(JSON 문자열)을 파싱한다. 형식이 깨져 있으면 응답 전체를 설명으로 취급한다."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # 코드블록(```json ... ```)으로 감싸서 응답하는 경우 이를 제거한다.
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        return ImageAnalysisResult(
            description=str(data.get("description", "")).strip(),
            keywords=[str(k).strip() for k in data.get("keywords", [])],
            search_terms=[str(s).strip() for s in data.get("search_terms", [])],
        )
    except (json.JSONDecodeError, AttributeError):
        return ImageAnalysisResult(description=raw_text.strip())


def _pixmap_to_data_uri(pixmap: QPixmap) -> str:
    """QPixmap을 OpenAI Vision API가 요구하는 base64 data URI(PNG)로 변환한다."""
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.ReadWrite)
    pixmap.save(buffer, "PNG")
    data = bytes(buffer.data())
    buffer.close()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{encoded}"
