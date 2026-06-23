import uuid
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import SocialAccount


class UnsupportedOAuthProviderError(ValueError):
    pass


class MissingOAuthClientIDError(ValueError):
    pass


class MissingOAuthClientSecretError(ValueError):
    pass


class OAuthTokenRequestError(ValueError):
    pass


class OAuthUserInfoRequestError(ValueError):
    pass


def get_oauth_provider_config(provider):
    provider_key = provider.lower()
    provider_config = settings.OAUTH_PROVIDERS.get(provider_key)

    if provider_config is None:
        raise UnsupportedOAuthProviderError("Unsupported OAuth provider.")

    return provider_key, provider_config


def build_oauth_authorization_url(provider):
    provider_key, provider_config = get_oauth_provider_config(provider)

    client_id = provider_config["client_id"]
    if not client_id:
        raise MissingOAuthClientIDError("OAuth client_id is not configured.")

    query_params = {
        "client_id": client_id,
        "redirect_uri": provider_config["redirect_uri"],
        "response_type": "code",
    }

    scope = provider_config.get("scope")
    if scope:
        query_params["scope"] = scope

    query_params.update(provider_config.get("extra_params", {}))

    authorization_url = (
        f"{provider_config['authorization_url']}?{urlencode(query_params)}"
    )

    return {
        "provider": provider_key,
        "authorization_url": authorization_url,
    }


def request_oauth_access_token(provider_key, provider_config, code):
    client_id = provider_config["client_id"]
    client_secret = provider_config.get("client_secret", "")

    if not client_id:
        raise MissingOAuthClientIDError("OAuth client_id is not configured.")
    if not client_secret:
        raise MissingOAuthClientSecretError("OAuth client_secret is not configured.")

    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": provider_config["redirect_uri"],
        "code": code,
    }
    # 네이버 등은 토큰 교환 시에도 authorize 때와 동일한 state가 필요
    state = provider_config.get("extra_params", {}).get("state")
    if state:
        data["state"] = state

    response = requests.post(provider_config["token_url"], data=data, timeout=5)
    if response.status_code >= 400:
        raise OAuthTokenRequestError("Failed to request OAuth access token.")

    access_token = response.json().get("access_token")
    if not access_token:
        raise OAuthTokenRequestError("OAuth access token was not returned.")

    return access_token


def request_oauth_user_info(provider_config, access_token):
    response = requests.get(
        provider_config["userinfo_url"],
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=5,
    )
    if response.status_code >= 400:
        raise OAuthUserInfoRequestError("Failed to request OAuth user info.")

    return response.json()


def normalize_oauth_user_info(provider_key, raw_user_info):
    if provider_key == "google":
        return {
            "provider_user_id": str(raw_user_info.get("sub")),
            "email": raw_user_info.get("email", ""),
            "nickname": raw_user_info.get("name") or raw_user_info.get("email") or "",
            "profile_image_url": raw_user_info.get("picture", ""),
        }

    if provider_key == "kakao":
        kakao_account = raw_user_info.get("kakao_account", {})
        profile = kakao_account.get("profile", {})
        return {
            "provider_user_id": str(raw_user_info.get("id")),
            "email": kakao_account.get("email", ""),
            "nickname": profile.get("nickname") or kakao_account.get("email") or "",
            "profile_image_url": profile.get("profile_image_url", ""),
        }

    if provider_key == "naver":
        response = raw_user_info.get("response", {})
        return {
            "provider_user_id": str(response.get("id")),
            "email": response.get("email", ""),
            "nickname": response.get("nickname") or response.get("email") or "",
            "profile_image_url": response.get("profile_image", ""),
        }

    raise UnsupportedOAuthProviderError("Unsupported OAuth provider.")


def make_unique_username(provider_key, provider_user_id):
    return f"{provider_key}_{provider_user_id}"


def make_unique_nickname(base_nickname):
    User = get_user_model()
    fallback = f"user-{uuid.uuid4().hex[:8]}"
    nickname = (base_nickname or fallback)[:50]

    if not User.objects.filter(nickname=nickname).exists():
        return nickname

    for _ in range(10):
        candidate = f"{nickname[:41]}-{uuid.uuid4().hex[:8]}"
        if not User.objects.filter(nickname=candidate).exists():
            return candidate

    return fallback


@transaction.atomic
def get_or_create_oauth_user(provider_key, normalized_user_info):
    User = get_user_model()
    provider_user_id = normalized_user_info["provider_user_id"]

    social_account = (
        SocialAccount.objects.select_related("user")
        .filter(provider=provider_key.upper(), provider_user_id=provider_user_id)
        .first()
    )
    if social_account:
        return social_account.user, False

    email = normalized_user_info.get("email", "")
    user = None
    if email:
        user = User.objects.filter(email=email).first()

    if user is None:
        username = make_unique_username(provider_key, provider_user_id)
        # 기본 닉네임은 이메일 우선 (없으면 소셜 닉네임)
        nickname = make_unique_nickname(email or normalized_user_info.get("nickname", ""))
        user = User.objects.create_user(
            username=username,
            email=email or None,
            nickname=nickname,
            profile_image_url=normalized_user_info.get("profile_image_url", ""),
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])

    SocialAccount.objects.create(
        user=user,
        provider=provider_key.upper(),
        provider_user_id=provider_user_id,
        email=email or None,
    )

    return user, True


def authenticate_oauth_user(provider, code):
    provider_key, provider_config = get_oauth_provider_config(provider)
    access_token = request_oauth_access_token(provider_key, provider_config, code)
    raw_user_info = request_oauth_user_info(provider_config, access_token)
    normalized_user_info = normalize_oauth_user_info(provider_key, raw_user_info)

    if not normalized_user_info["provider_user_id"]:
        raise OAuthUserInfoRequestError("OAuth provider user id was not returned.")

    return get_or_create_oauth_user(provider_key, normalized_user_info)
