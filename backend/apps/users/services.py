from urllib.parse import urlencode

from django.conf import settings


class UnsupportedOAuthProviderError(ValueError):
    pass


class MissingOAuthClientIDError(ValueError):
    pass


def build_oauth_authorization_url(provider):
    provider_key = provider.lower()
    provider_config = settings.OAUTH_PROVIDERS.get(provider_key)

    if provider_config is None:
        raise UnsupportedOAuthProviderError("Unsupported OAuth provider.")

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
    