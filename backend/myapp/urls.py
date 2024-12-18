from django.urls import path
from django.contrib import admin
from . import views
from .views import registro, CustomLoginView
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from .views import StripeCheckoutSessionView
from .views import success_view, add_product

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
    path('cart_guest/', views.cart_guest, name='cart_guest'),
    path('add_to_cart_guest/<int:product_id>/', views.add_to_cart_guest, name='add_to_cart_guest'),
    path('increase_quantity_guest/<int:product_id>/', views.increase_cart_quantity_guest, name='increase_quantity_guest'),
    path('decrease_quantity_guest/<int:product_id>/', views.decrease_cart_quantity_guest, name='decrease_quantity_guest'),
    path('initiate_checkout_guest/', views.initiate_checkout_guest, name='initiate_checkout_guest'),
    path('track_order_guest/', views.track_order_guest, name='track_order_guest'),
    path('success_guest/', views.success_guest_view, name='success_guest'),
    path('track_order/', views.track_order, name='track_order'),
    path('edit_order/<int:order_id>/', views.edit_order, name='edit_order'),
    path('initiate_checkout/', views.initiate_checkout, name='initiate_checkout'),
    path('cash-on-delivery-form/', views.cash_on_delivery_form, name='cash_on_delivery_form'),
    path('guest-checkout/', views.guest_cash_on_delivery_form, name='guest_cash_on_delivery_form'),
    path('finalize-guest-checkout/', views.finalize_guest_cash_on_delivery, name='finalize_guest_cash_on_delivery'),
    path('finalize-cash-on-delivery/', views.finalize_cash_on_delivery, name='finalize_cash_on_delivery'),
    path('staff/orders/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
    path('staff/orders/', views.order_list, name='order_list'),
    path('staff/add-product/', views.add_product, name='add_product'),
    path('staff/delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('staff/update-product/<int:product_id>/', views.update_product, name='update_product'),
    path('staff/update-order/<int:order_id>/', views.update_order, name='update_order'),
    path('staff/users/', views.user_list, name='user_list'),
    path('staff/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
]
