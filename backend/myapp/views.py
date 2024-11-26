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
import uuid

from myapp.models import Product, Category, Manufacturer, Cart, CartItem, Order, OrderItem
from myapp.serializer import ProductSerializer
from .forms import RegistrationForm, LoginForm
from django.contrib import messages

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from PGPIProject import settings

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
    else:
        cart = request.session.get('cart', {})
        total_items = sum(item['quantity'] for item in cart.values())

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
    product = get_object_or_404(Product, id=product_id)
    if product.stock > 0:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    else:
        messages.error(request, "No hay suficiente stock disponible")
        return HttpResponse("No hay suficiente stock disponible", status=200)
    return redirect('catalogo')


# Vista del carrito de compras
@login_required
def cart(request):
    cart_obj, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart_obj.item.all()

    total_items = sum(item.quantity for item in cart_items)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    cart_items_with_totals = [
        {
            'item': item,
            'total_price': item.product.price * item.quantity
        }
        for item in cart_items
    ]

    if cart_items:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        YOUR_DOMAIN = "http://127.0.0.1:8000"  # Replace with your deployed domain

        line_items = [
            {
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': item.product.name,
                    },
                    'unit_amount': int(item.product.price * 100),
                },
                'quantity': item.quantity,
            }
            for item in cart_items
        ]

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success/?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=YOUR_DOMAIN + '/cart/',
            shipping_address_collection={
                'allowed_countries': ['US', 'CA', 'ES']
            },
            shipping_options=[
                {
                    'shipping_rate_data': {
                        'type': 'fixed_amount',
                        'fixed_amount': {'amount': 500, 'currency': 'eur'},
                        'display_name': 'Standard shipping',
                        'delivery_estimate': {
                            'minimum': {'unit': 'business_day', 'value': 5},
                            'maximum': {'unit': 'business_day', 'value': 7},
                        },
                    },
                },
                {
                    'shipping_rate_data': {
                        'type': 'fixed_amount',
                        'fixed_amount': {'amount': 1500, 'currency': 'eur'},
                        'display_name': 'Express shipping',
                        'delivery_estimate': {
                            'minimum': {'unit': 'business_day', 'value': 1},
                            'maximum': {'unit': 'business_day', 'value': 3},
                        },
                    },
                },
            ]
        )
        checkout_session_id = checkout_session.id
    else:
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
                    'currency': 'eur',
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
                success_url=YOUR_DOMAIN + '/success/?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=YOUR_DOMAIN + '/cart/',
                shipping_address_collection={
                    'allowed_countries': ['US', 'CA', 'ES'], 
                },
                shipping_options=[
                    {
                        'shipping_rate_data': {
                            'type': 'fixed_amount',
                            'fixed_amount': {'amount': 500, 'currency': 'eur'},
                            'display_name': 'Standard shipping',
                            'delivery_estimate': {
                                'minimum': {'unit': 'business_day', 'value': 5},
                                'maximum': {'unit': 'business_day', 'value': 7},
                            },
                        },
                    },
                    {
                        'shipping_rate_data': {
                            'type': 'fixed_amount',
                            'fixed_amount': {'amount': 1500, 'currency': 'eur'},
                            'display_name': 'Express shipping',
                            'delivery_estimate': {
                                'minimum': {'unit': 'business_day', 'value': 1},
                                'maximum': {'unit': 'business_day', 'value': 3},
                            },
                        },
                    },
                ],
            )
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
@login_required
def initiate_checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.item.exists():
        return redirect('cart')

    productos_no_existentes = []
    for item in cart.item.all():
        if item.product.stock < item.quantity:
            productos_no_existentes.append(item.product.name)

    if productos_no_existentes:
        return render(request, 'checkout_error.html', {
            'error': f'Los siguientes productos no tienen suficiente stock: {", ".join(productos_no_existentes)}. Por favor, actualiza tu carrito.'
        })

    total = sum(item.product.price * item.quantity for item in cart.item.all())

    stripe.api_key = settings.STRIPE_SECRET_KEY
    YOUR_DOMAIN = "http://127.0.0.1:8000"  # Reemplaza con tu dominio

    line_items = [
        {
            'price_data': {
                'currency': 'eur',
                'product_data': {
                    'name': item.product.name,
                },
                'unit_amount': int(item.product.price * 100),  # Convertir a centavos
            },
            'quantity': item.quantity,
        }
        for item in cart.item.all()
    ]

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success/?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=YOUR_DOMAIN + '/cart/',
            shipping_address_collection={
                'allowed_countries': ['US', 'CA', 'ES']
            },
            shipping_options=[
                {
                    'shipping_rate_data': {
                        'type': 'fixed_amount',
                        'fixed_amount': {'amount': 500, 'currency': 'eur'},
                        'display_name': 'Standard shipping',
                        'delivery_estimate': {
                            'minimum': {'unit': 'business_day', 'value': 5},
                            'maximum': {'unit': 'business_day', 'value': 7},
                        },
                    },
                },
                {
                    'shipping_rate_data': {
                        'type': 'fixed_amount',
                        'fixed_amount': {'amount': 1500, 'currency': 'eur'},
                        'display_name': 'Express shipping',
                        'delivery_estimate': {
                            'minimum': {'unit': 'business_day', 'value': 1},
                            'maximum': {'unit': 'business_day', 'value': 3},
                        },
                    },
                },
            ],
        )

        track_number = f"TRACK-{uuid.uuid4().hex[:10].upper()}"

        order = Order.objects.create(
            user=request.user,
            session_id=checkout_session.id,
            total=total,
            delivery_address="Pendiente de ser completada",
            track_number=track_number,
            status='Recibido'
        )

        for item in cart.item.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        return redirect(checkout_session.url, code=303)

    except stripe.error.StripeError as e:
        return render(request, 'checkout_error.html', {'error': str(e)})


@login_required
def track_order(request):
    if request.method == 'POST':
        track_number = request.POST.get('track_number')

        try:
            order = Order.objects.get(user=request.user, track_number=track_number)
            return render(request, 'track_order.html', {'order': order})
        except Order.DoesNotExist:
            return render(request, 'track_order.html', {'error': 'No se encontró ningún pedido con ese código de seguimiento.'})

    return render(request, 'track_order.html')



@login_required
def success_view(request):
    session_id = request.GET.get('session_id')

    name = "Cliente"
    address = {
        "line1": "No disponible",
        "line2": "",
        "city": "No disponible",
        "state": "No disponible",
        "postal_code": "No disponible",
        "country": "No disponible",
    }
    track_number = "No disponible"

    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id, expand=['shipping_details', 'customer_details'])
            shipping_details = session.get('shipping_details', {})
            email = session.customer_details.email  # Correo del cliente desde Stripe
            name = shipping_details.get('name', "Cliente")
            address_obj = shipping_details.get('address', {})
            address = {
                "line1": address_obj.get('line1', "No disponible"),
                "line2": address_obj.get('line2', ""),
                "city": address_obj.get('city', "No disponible"),
                "state": address_obj.get('state', "No disponible"),
                "postal_code": address_obj.get('postal_code', "No disponible"),
                "country": address_obj.get('country', "No disponible"),
            }

            # Obtener la orden vinculada al session_id
            order = Order.objects.get(session_id=session_id, user=request.user)
            track_number = order.track_number

            # Enviar correo de confirmación
            enviar_correo_confirmacion(order, email, name, address)

        except Exception as e:
            print(f"Error: {e}")

    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        for item in cart.item.all():
            product = item.product
            product.stock -= item.quantity
            product.save()
        cart.item.all().delete()

    return render(request, 'success.html', {
        'name': name,
        'address': address,
        'track_number': track_number,
    })

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

def add_to_cart_guest(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    # Verificar stock antes de añadir al carrito
    if product.stock > 0:
        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] += 1
        else:
            cart[str(product_id)] = {
                'name': product.name,
                'price': float(product.price),
                'quantity': 1,
            }
        request.session['cart'] = cart
    else:
        messages.error(request, "No hay suficiente stock disponible")
        return redirect('catalogo')

    return redirect('catalogo')

def cart_guest(request):
    cart = request.session.get('cart', {})
    total_items = sum(item['quantity'] for item in cart.values())
    total_price = sum(item['price'] * item['quantity'] for item in cart.values())

    cart_items_with_totals = [
        {
            'product_id': key,
            'name': item['name'],
            'quantity': item['quantity'],
            'price': item['price'],
            'total_price': item['price'] * item['quantity'],
        }
        for key, item in cart.items()
    ]

    return render(request, 'cart_guest.html', {
        'cart_items_with_totals': cart_items_with_totals,
        'total_items': total_items,
        'total_price': total_price,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    })

def initiate_checkout_guest(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart_guest')

    productos_no_existentes = []
    for product_id, item in list(cart.items()):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            productos_no_existentes.append(product_id)
            del cart[product_id]

    request.session['cart'] = cart

    if productos_no_existentes:
        productos_ids = ', '.join(str(pid) for pid in productos_no_existentes)
        return render(request, 'checkout_error.html', {
            'error': f'Los siguientes productos se eliminaron del carrito porque no existen: {productos_ids}. Por favor, actualiza tu carrito.'
        })

    total = sum(item['price'] * item['quantity'] for item in cart.values())

    stripe.api_key = settings.STRIPE_SECRET_KEY
    YOUR_DOMAIN = "http://127.0.0.1:8000"  

    line_items = [
        {
            'price_data': {
                'currency': 'eur',
                'product_data': {
                    'name': item['name'],
                },
                'unit_amount': int(item['price'] * 100),  
            },
            'quantity': item['quantity'],
        }
        for item in cart.values()
    ]

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success_guest/?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=YOUR_DOMAIN + '/cart_guest/',
            shipping_address_collection={
                'allowed_countries': ['US', 'CA', 'ES']
            },
            shipping_options=[
                {
                    'shipping_rate_data': {
                        'type': 'fixed_amount',
                        'fixed_amount': {'amount': 500, 'currency': 'eur'},
                        'display_name': 'Standard shipping',
                        'delivery_estimate': {
                            'minimum': {'unit': 'business_day', 'value': 5},
                            'maximum': {'unit': 'business_day', 'value': 7},
                        },
                    },
                },
                {
                    'shipping_rate_data': {
                        'type': 'fixed_amount',
                        'fixed_amount': {'amount': 1500, 'currency': 'eur'},
                        'display_name': 'Express shipping',
                        'delivery_estimate': {
                            'minimum': {'unit': 'business_day', 'value': 1},
                            'maximum': {'unit': 'business_day', 'value': 3},
                        },
                    },
                },
            ],
        )

        track_number = f"TRACK-{uuid.uuid4().hex[:10].upper()}"

        order = Order.objects.create(
            session_id=checkout_session.id,
            total=total,
            delivery_address="Pendiente de ser completada",
            track_number=track_number 
        )

        for product_id, item in cart.items():
            OrderItem.objects.create(
                order=order,
                product=Product.objects.get(id=product_id),
                quantity=item['quantity'],
                price=item['price']
            )

        return redirect(checkout_session.url, code=303)

    except stripe.error.StripeError as e:
        return render(request, 'checkout_error.html', {'error': str(e)})
    
def track_order_guest(request):
    if request.method == 'POST':
        track_number = request.POST.get('track_number')

        try:
            order = Order.objects.get(track_number=track_number)
            return render(request, 'track_order_guest.html', {'order': order})
        except Order.DoesNotExist:
            return render(request, 'track_order_guest.html', {'error': 'No se encontró ningún pedido con ese código de seguimiento.'})

    return render(request, 'track_order_guest.html')
        
def increase_cart_quantity_guest(request, product_id):
    cart = request.session.get('cart', {})
    
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
        request.session['cart'] = cart

    return redirect('cart_guest')

def decrease_cart_quantity_guest(request, product_id):
    cart = request.session.get('cart', {})
    
    if str(product_id) in cart:
        if cart[str(product_id)]['quantity'] > 1:
            cart[str(product_id)]['quantity'] -= 1
        else:
            del cart[str(product_id)]
        request.session['cart'] = cart

    return redirect('cart_guest')

def success_guest_view(request):
    session_id = request.GET.get('session_id')

    name = "Cliente"
    address = {
        "line1": "No disponible",
        "line2": "",
        "city": "No disponible",
        "state": "No disponible",
        "postal_code": "No disponible",
        "country": "No disponible",
    }
    track_number = "No disponible"

    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id, expand=['shipping_details', 'customer_details'])
            shipping_details = session.get('shipping_details', {})
            email = session.customer_details.email  # Correo del cliente desde Stripe
            name = shipping_details.get('name', "Cliente")
            address_obj = shipping_details.get('address', {})
            address = {
                "line1": address_obj.get('line1', "No disponible"),
                "line2": address_obj.get('line2', ""),
                "city": address_obj.get('city', "No disponible"),
                "state": address_obj.get('state', "No disponible"),
                "postal_code": address_obj.get('postal_code', "No disponible"),
                "country": address_obj.get('country', "No disponible"),
            }

            # Obtener la orden vinculada al session_id
            order = Order.objects.get(session_id=session_id)
            track_number = order.track_number

            # Enviar correo de confirmación
            enviar_correo_confirmacion(order, email, name, address)

        except Exception as e:
            print(f"Error: {e}")

    cart = request.session.get('cart', {})
    for product_id, item in cart.items():
        product = Product.objects.get(id=product_id)
        product.stock -= item['quantity']
        product.save()

    # Vaciar el carrito de la sesión
    if 'cart' in request.session:
        del request.session['cart']

    return render(request, 'success_guest.html', {
        'name': name,
        'address': address,
        'track_number': track_number,
    })


def create_order_guest(session_id, total, delivery_address):
    track_number = f"TRACK-{uuid.uuid4().hex[:10].upper()}"

    order = Order.objects.create(
        session_id=session_id,
        total=total,
        delivery_address=delivery_address,
        track_number=track_number
    )
    return order

def enviar_correo_confirmacion(order, email, name, address):
    # Renderiza la plantilla de correo electrónico
    subject = 'Confirmación de Compra'
    html_message = render_to_string('email_confirmation.html', {
        'name': name,
        'address': address,
        'order': order,
    })
    plain_message = strip_tags(html_message)

    # Envía el correo
    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [email],
        html_message=html_message,
    )

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
        
