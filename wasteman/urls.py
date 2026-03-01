from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.conf.urls.static import static

from .views import home, register, logout, login, profile, poster, posters, cart, checkout, paintings, painting, webhook, address

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home, name="home"),

    path("profile", profile, name="profile"),
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("logout/", logout, name="logout"),

    path("terms-of-service/", TemplateView.as_view(template_name="terms.html"), name="terms"),

    path("paintings/", paintings, name="paintings"),
    path("painting/<int:id>", painting, name="painting"),

    path("posters/", posters, name="posters"),
    path("poster/<int:id>", poster, name="poster"),

    path("cart/", cart, name="cart"),
    path("address/", address, name="address"),
    path("checkout/", checkout, name="checkout"),
    path("success/", TemplateView.as_view(template_name="success.html"), name="success"),
    path("cancel/", TemplateView.as_view(template_name="cancel.html"), name="cancel"),

    path("webhook/", webhook, name="webhook")
]

if settings.DEBUG == False:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
