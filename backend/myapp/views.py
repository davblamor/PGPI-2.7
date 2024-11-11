from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from rest_framework.response import Response  # Solo una vez
from myapp.models import Product
from rest_framework.viewsets import ModelViewSet
from myapp.serializer import *
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics


def index(request: HttpRequest) -> HttpResponse:
    return HttpResponse("PGPI Grupo 2.7")

def home(request):
    return render(request, 'home.html')

def catalogue(request):
    return render(request, 'catalogue.html')

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
