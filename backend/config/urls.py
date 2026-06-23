from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.works.urls")),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/", include("apps.interactions.urls")),
    path("api/v1/", include("apps.chat.urls")),
    path("api/v1/auth/", include("apps.users.auth_urls")),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
