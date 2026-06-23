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
