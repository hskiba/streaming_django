from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("keepalive.urls")),
    path("health_check/", include('health_check.urls')),
    path("admin/", admin.site.urls),
]
