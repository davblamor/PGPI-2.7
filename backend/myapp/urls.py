from django.urls import path
from django.contrib import admin
from . import views
from .views import registro, CustomLoginView
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from .views import StripeCheckoutSessionView
from .views import success_view




urlpatterns = [
    path('', views.home, name='home'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('categoria/<int:categoria_id>/', views.filtrar_por_categoria, name='filtrar_por_categoria'),
    path('fabricante/<int:fabricante_id>/', views.filtrar_por_fabricante, name='filtrar_por_fabricante'),
    path('admin/', admin.site.urls),
    path('registro/', registro, name='registro'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('profile/', views.profile, name='profile'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('logout/', LogoutView.as_view(next_page='catalogo'), name='logout'),
    path('cart/', views.cart, name='cart'),
    path('increase_quantity/<int:cart_item_id>/', views.increase_cart_quantity, name='increase_quantity'),
    path('create-checkout-session/', StripeCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('success/', success_view, name='success'),
    path('decrease_quantity/<int:cart_item_id>/', views.decrease_cart_quantity, name='decrease_quantity'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
