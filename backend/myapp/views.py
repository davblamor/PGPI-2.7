from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from rest_framework.response import Response  # Solo una vez
from myapp.models import Product
from rest_framework.viewsets import ModelViewSet
from myapp.serializer import *
from django.contrib.auth import login
from .forms import RegistrationForm, LoginForm
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework import generics
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.urls import reverse



def index(request: HttpRequest) -> HttpResponse:
    return HttpResponse("PGPI Grupo 2.7")

def home(request):
    return render(request, 'home.html')

def catalogo(request):
    query = request.GET.get('q', '')  
    productos = Product.objects.all() 

    if query:
        productos = productos.filter(
            Q(name__icontains=query) | 
            Q(category__name__icontains=query) | 
            Q(manufacturer__name__icontains=query)  
        )

    return render(request, 'catalogo.html', {'productos': productos})

def registro(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("catalogo")  # Redirige al catálogo
    else:
        form = RegistrationForm()
    return render(request, 'registro.html', {'form': form})

class CustomLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "registration/login.html"

    def get_success_url(self):
        return reverse('catalogo')


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    return render(request, 'profile.html', {'user': request.user})

@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('catalogo')

# Devuelve el listado de productos
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
