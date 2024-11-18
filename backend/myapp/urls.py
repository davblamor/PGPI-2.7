from django.urls import path
from django.contrib import admin
from . import views
from .views import registro, CustomLoginView
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('categoria/<int:categoria_id>/', views.filtrar_por_categoria, name='filtrar_por_categoria'),
    path('fabricante/<int:fabricante_id>/', views.filtrar_por_fabricante, name='filtrar_por_fabricante'),
    path('admin/', admin.site.urls),
    path('registro/', registro, name='registro'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('accounts/profile/', views.profile, name='profile'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
