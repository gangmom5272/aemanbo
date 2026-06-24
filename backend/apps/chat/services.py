import json
import os

import requests
from django.db.models import Q

from apps.works.models import Anime, Manga
from apps.works.serializers import AnimeListSerializer, MangaListSerializer

OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_URL = OPENAI_BASE_URL + "/chat/completions"
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
MAX_HISTORY = 12  # 최근 메시지만 유지 (user/assistant 합산)

SYSTEM_PROMPT = (
    "너는 애니/만화 추천 서비스 '애만보'의 작품 큐레이터야.\n"
    "[페르소나·말투 — 항상 일관되게]\n"
    "- 따뜻하고 다정한 정중한 존댓말('~해요'체 중심, 가끔 '~예요/~랍니다'로 부드럽게). 안목 있는 큐레이터의 신뢰감은 유지하되 친근하게.\n"
    "- 답변은 2~3문장으로 간결하되 정성스럽게. 호들갑·과장·반말은 금지하지만 너무 딱딱하지 않게.\n"
    "- 추천하는 작품마다 어떤 점이 어울리는지 한 구절로 따뜻하게 짚어줘.\n"
    "- 이모지는 자제하되, 분위기를 살릴 때 답변당 최대 1개까지 허용.\n"
    "- 작품 제목은 한국에서 통용되는 정식 명칭으로 표기해.\n"
    "- 취향이 모호하면 부담스럽지 않게 한 가지만 살짝 여쭤봐.\n"
    "[출력 형식] 다른 텍스트 없이 아래 JSON만: "
    '{"reply": "사용자에게 보여줄 한국어 답변", "titles": ["추천 작품 제목", ...]}. '
    "titles 는 최대 6개, 추천할 작품이 없으면 빈 배열."
)


class MissingApiKeyError(RuntimeError):
    pass


class LLMError(RuntimeError):
    pass


def ask_llm(history, message):
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise MissingApiKeyError("OPENAI_API_KEY is not set")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history
    messages.append({"role": "user", "content": message})

    resp = requests.post(
        OPENAI_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "messages": messages,
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except ValueError:
            detail = resp.text[:300]
        raise LLMError(f"OpenAI {resp.status_code}: {detail}")
    content = resp.json()["choices"][0]["message"]["content"]
    data = json.loads(content)
    reply = (data.get("reply") or "").strip()
    titles = [t for t in (data.get("titles") or []) if isinstance(t, str)]
    return reply, titles


SEARCH_PROMPT = (
    "너는 애니/만화 검색 보정기야. 사용자가 제목을 정확히 모르거나 줄거리·특징을 "
    "설명형으로 검색했을 때, 해당할 가능성이 높은 작품의 '한국 정식 제목'을 추측해.\n"
    "- 확신이 낮아도 그럴듯한 후보를 제시해.\n"
    "- 한국에서 통용되는 정식 명칭으로만 표기(예: '진격의 거인').\n"
    "- 설명만으로 떠오르는 게 없으면 빈 배열.\n"
    '다른 텍스트 없이 JSON만: {"titles": ["제목", ...]} (최대 8개).'
)


def search_titles(query):
    """모호/설명형 검색어 → 추측 작품 제목 리스트."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise MissingApiKeyError("OPENAI_API_KEY is not set")

    resp = requests.post(
        OPENAI_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SEARCH_PROMPT},
                {"role": "user", "content": query},
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        },
        timeout=20,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except ValueError:
            detail = resp.text[:300]
        raise LLMError(f"OpenAI {resp.status_code}: {detail}")
    content = resp.json()["choices"][0]["message"]["content"]
    data = json.loads(content)
    return [t for t in (data.get("titles") or []) if isinstance(t, str)]


CATALOG_PROMPT = (
    "아래 [작품목록]은 우리 서비스 DB에 있는 작품 전체야. "
    "사용자의 [검색어](제목 일부·줄거리 설명·분위기·키워드 등)에 가장 잘 맞는 작품을 "
    "반드시 [작품목록] 안에서만 골라, 각 작품 앞의 번호를 반환해. "
    "목록에 없는 작품은 절대 지어내지 마. 관련 작품이 없으면 빈 배열.\n"
    '다른 텍스트 없이 JSON만: {"picks": [번호, ...]} (최대 8개, 관련도 높은 순).'
)


def search_picks_from_catalog(query):
    """검색어 → DB 작품목록에서 LLM이 직접 고른 (type, id, title) 리스트.
    LLM이 DB에 실재하는 작품만 번호로 선택하므로 글자 매칭 실패가 없다."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise MissingApiKeyError("OPENAI_API_KEY is not set")

    items = [("anime", a_id, title) for a_id, title in Anime.objects.values_list("id", "title")]
    items += [("manga", m_id, title) for m_id, title in Manga.objects.values_list("id", "title")]
    catalog = "\n".join(f"{i + 1}. {it[2]}" for i, it in enumerate(items))
    user_msg = f"[검색어]\n{query}\n\n[작품목록]\n{catalog}"

    resp = requests.post(
        OPENAI_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": CATALOG_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        },
        timeout=40,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except ValueError:
            detail = resp.text[:300]
        raise LLMError(f"OpenAI {resp.status_code}: {detail}")
    content = resp.json()["choices"][0]["message"]["content"]
    data = json.loads(content)
    picks = []
    for p in (data.get("picks") or []):
        try:
            n = int(p)
        except (TypeError, ValueError):
            continue
        if 1 <= n <= len(items):
            picks.append(items[n - 1])
    return picks


def match_recommendations(titles, limit=6):
    recs = []
    seen = set()
    for t in titles:
        t = (t or "").strip()
        if not t:
            continue
        q = Q(title__icontains=t) | Q(original_title__icontains=t)
        anime = Anime.objects.filter(q).first()
        if anime and ("anime", anime.id) not in seen:
            recs.append({"type": "anime", **AnimeListSerializer(anime).data})
            seen.add(("anime", anime.id))
            continue
        manga = Manga.objects.filter(q).first()
        if manga and ("manga", manga.id) not in seen:
            recs.append({"type": "manga", **MangaListSerializer(manga).data})
            seen.add(("manga", manga.id))
        if len(recs) >= limit:
            break
    return recs


def trim_history(history):
    return history[-MAX_HISTORY:]
