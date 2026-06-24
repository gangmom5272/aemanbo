import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

import sys

from .services import (
    LLMError,
    MissingApiKeyError,
    ask_llm,
    match_recommendations,
    search_picks_from_catalog,
    trim_history,
)


class ChatMessageAPIView(APIView):
    # 비로그인도 사용 가능 (대화는 세션에 저장)
    permission_classes = []

    def post(self, request):
        message = (request.data.get("message") or "").strip()
        if not message:
            return Response(
                {"detail": "메시지를 입력해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        history = request.session.get("chat_history", [])
        try:
            reply, titles = ask_llm(history, message)
        except MissingApiKeyError:
            return Response(
                {"detail": "AI 키가 설정되지 않았어요. (.env의 OPENAI_API_KEY)"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except LLMError as exc:
            print("[chat] LLM error:", exc, file=sys.stderr)
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except (requests.RequestException, ValueError, KeyError) as exc:
            print("[chat] error:", repr(exc), file=sys.stderr)
            return Response(
                {"detail": f"AI 응답 처리 오류: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        history = trim_history(
            history
            + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": reply},
            ]
        )
        request.session["chat_history"] = history
        request.session.modified = True

        return Response(
            {
                "reply": reply,
                "recommendations": match_recommendations(titles),
            }
        )


class ChatSessionAPIView(APIView):
    permission_classes = []

    def delete(self, request):
        request.session.pop("chat_history", None)
        request.session.modified = True
        return Response(status=status.HTTP_204_NO_CONTENT)


class SearchFallbackAPIView(APIView):
    # 일반 검색(제목) 0건일 때만 프론트가 호출
    # 1) 줄거리/장르 DB 검색  →  2) 그래도 없으면 LLM 추측
    permission_classes = []

    def post(self, request):
        from apps.works.models import Anime, Manga
        from apps.works.serializers import AnimeListSerializer, MangaListSerializer
        from apps.works.services import search_by_content

        keyword = (request.data.get("keyword") or "").strip()
        if not keyword:
            return Response({"keyword": "", "recommendations": [], "source": ""})

        # 1) 줄거리/장르 기반 DB 검색 (정확·저비용)
        content = search_by_content(keyword)
        recs = [{"type": "anime", **AnimeListSerializer(a).data} for a in content["animes"]]
        recs += [{"type": "manga", **MangaListSerializer(m).data} for m in content["mangas"]]
        if recs:
            return Response({"keyword": keyword, "recommendations": recs[:12], "source": "content"})

        # 2) LLM이 DB 작품목록에서 직접 선택 (의미 기반, 실재 작품만)
        try:
            picks = search_picks_from_catalog(keyword)
            recs = []
            for typ, obj_id, _ in picks:
                if typ == "anime":
                    a = Anime.objects.filter(id=obj_id).first()
                    if a:
                        recs.append({"type": "anime", **AnimeListSerializer(a).data})
                else:
                    m = Manga.objects.filter(id=obj_id).first()
                    if m:
                        recs.append({"type": "manga", **MangaListSerializer(m).data})
        except (MissingApiKeyError, LLMError, requests.RequestException, ValueError, KeyError) as exc:
            print("[search-ai] error:", repr(exc), file=sys.stderr)
            recs = []
        return Response({"keyword": keyword, "recommendations": recs, "source": "ai"})
