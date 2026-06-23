from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """세션 로그인은 그대로 인증하되 CSRF 검사는 생략 (SPA + 세션 조합용)."""

    def enforce_csrf(self, request):
        return None
