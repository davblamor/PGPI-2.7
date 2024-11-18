from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Q
from django.views import View
import stripe
from django.conf import settings

from myapp.models import Product, Category, Manufacturer, Cart, CartItem
from myapp.serializer import ProductSerializer
from .forms import RegistrationForm, LoginForm
from django.contrib import messages


# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# Vista principal
def index(request: HttpRequest) -> HttpResponse:
    return HttpResponse("PGPI Grupo 2.7")


# Vista home
def home(request):
    return render(request, 'home.html')


# Vista del catálogo de productos
def catalogo(request):
    query = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria')
    fabricante_id = request.GET.get('fabricante')
    total_items = 0

    productos = Product.objects.all()
    categorias = Category.objects.all()
    fabricantes = Manufacturer.objects.all()

    if query:
        productos = productos.filter(
            Q(name__icontains=query) |
            Q(category__name__icontains=query) |
            Q(manufacturer__name__icontains=query)
        )

    if categoria_id:
        productos = productos.filter(category_id=categoria_id)
        filtro = f"Categoría: {Category.objects.get(id=categoria_id).name}"
    elif fabricante_id:
        productos = productos.filter(manufacturer_id=fabricante_id)
        filtro = f"Fabricante: {Manufacturer.objects.get(id=fabricante_id).name}"
    else:
        filtro = None

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            total_items = sum(item.quantity for item in cart.item.all())

    return render(request, 'catalogo.html', {
        'productos': productos,
        'categorias': categorias,
        'fabricantes': fabricantes,
        'query': query,
        'filtro': filtro,
        'total_items': total_items,
    })


# Filtrar por categoría
def filtrar_por_categoria(request, categoria_id):
    categoria = get_object_or_404(Category, id=categoria_id)
    productos = Product.objects.filter(category=categoria)
    categorias = Category.objects.all()
    fabricantes = Manufacturer.objects.all()

    return render(request, 'catalogo.html', {
        'productos': productos,
        'categorias': categorias,
        'fabricantes': fabricantes,
        'filtro': f"Categoría: {categoria.name}",
    })


# Filtrar por fabricante
def filtrar_por_fabricante(request, fabricante_id):
    fabricante = get_object_or_404(Manufacturer, id=fabricante_id)
    productos = Product.objects.filter(manufacturer=fabricante)
    categorias = Category.objects.all()
    fabricantes = Manufacturer.objects.all()

    return render(request, 'catalogo.html', {
        'productos': productos,
        'categorias': categorias,
        'fabricantes': fabricantes,
        'filtro': f"Fabricante: {fabricante.name}",
    })


# Registro de usuarios
def registro(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("catalogo")
    else:
        form = RegistrationForm()
    return render(request, 'registro.html', {'form': form})


# Vista de inicio de sesión personalizado
class CustomLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "registration/login.html"

    def get_success_url(self):
        return reverse('catalogo')


# Vista de perfil de usuario
@login_required
def profile(request: HttpRequest) -> HttpResponse:
    return render(request, 'profile.html', {'user': request.user})


# Añadir productos al carrito
@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('catalogo')


# Vista del carrito de compras
@login_required
def cart(request):
    # Get or create the cart for the current user
    cart_obj, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart_obj.item.all()

    # Calculate total items and total price
    total_items = sum(item.quantity for item in cart_items)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    cart_items_with_totals = [
        {
            'item': item,
            'total_price': item.product.price * item.quantity
        }
        for item in cart_items
    ]

    # Check if the cart is empty
    if cart_items:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        YOUR_DOMAIN = "http://127.0.0.1:8000"  # Replace with your deployed domain

        # Create line items for Stripe Checkout
        line_items = []
        for item in cart_items:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.name,
                    },
                    'unit_amount': int(item.product.price * 100),  # Convert price to cents
                },
                'quantity': item.quantity,
            })

        # Create the Stripe Checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success/',
            cancel_url=YOUR_DOMAIN + '/cart/',
        )
        checkout_session_id = checkout_session.id
    else:
        # If the cart is empty, no Checkout session is created
        checkout_session_id = None

    return render(request, 'cart.html', {
        'cart_items_with_totals': cart_items_with_totals,
        'total_items': total_items,
        'total_price': total_price,
        'checkout_session_id': checkout_session_id,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    })


# Stripe Checkout Session View
class StripeCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        YOUR_DOMAIN = f"http://{request.get_host()}"
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.item.all()

        line_items = [
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.name,
                    },
                    'unit_amount': int(item.product.price * 100),
                },
                'quantity': item.quantity,
            }
            for item in cart_items
        ]

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=YOUR_DOMAIN + '/success/',
                cancel_url=YOUR_DOMAIN + '/cart/',
            )
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# Success view
@login_required
def success_view(request):
    
    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        # Delete all items in the cart
        cart.item.all().delete()

    return render(request, 'success.html')


# Incrementar la cantidad de un producto en el carrito
@login_required
def increase_cart_quantity(request, cart_item_id):
    cart_item = CartItem.objects.get(id=cart_item_id)
    cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')


# Disminuir la cantidad de un producto en el carrito
@login_required
def decrease_cart_quantity(request, cart_item_id):
    cart_item = CartItem.objects.get(id=cart_item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')


# API para obtener el listado de productos
class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    @extend_schema(
        description="Obtiene un listado completo de todos los productos.",
        responses={
            200: ProductSerializer(many=True),
            400: OpenApiResponse(response=None, description="Error en la solicitud")
        }
    )
    def get(self, request, *args, **kwargs):
        products = self.get_queryset()
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# API para obtener detalles de un producto específico
class ProductDetailView(APIView):
    @extend_schema(
        description="Obtiene los detalles de un producto específico según el ID.",
        responses={200: ProductSerializer, 404: OpenApiResponse(response=None, description="Producto no encontrado")}
    )
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)