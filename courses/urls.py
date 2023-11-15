from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path("unicorn/", include("django_unicorn.urls")),
    path("accounts/", include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path("classroom/", include('classroom.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path("", include('app.urls')),
    path("api/", include('app.api.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
