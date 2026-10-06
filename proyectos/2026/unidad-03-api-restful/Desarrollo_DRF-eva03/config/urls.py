from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from adopciones.views import SolicitudViewSet
from animales.views import AnimalViewSet
from cuentas.views import UsuarioViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuario")
router.register("animales", AnimalViewSet, basename="animal")
router.register("solicitudes", SolicitudViewSet, basename="solicitud")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("cuentas.urls")),
    path("api/v1/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # solo sirve con DEBUG=1
