from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import authenticate, login, get_user_model
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
from decimal import Decimal
from django.contrib.admin.views.decorators import staff_member_required


from myapp.models import Product, Category, Manufacturer, Cart, CartItem, Order, OrderItem, CustomUser
from myapp.serializer import ProductSerializer
from .forms import RegistrationForm, LoginForm
from django.contrib import messages
from .forms import ProductForm

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
        YOUR_DOMAIN = "https://pgpi-2-7.onrender.com"  # Replace with your deployed domain

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

        # Calculate the subtotal
        subtotal = sum(item.product.price * item.quantity for item in cart_items)

        # Determine shipping options
        shipping_options = [
            {
                'shipping_rate_data': {
                    'type': 'fixed_amount',
                    'fixed_amount': {'amount': 500, 'currency': 'eur'},
                    'display_name': 'Standard shipping (€5.00, 5-7 business days)',
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
                    'display_name': 'Express shipping (€15.00, 1-3 business days)',
                    'delivery_estimate': {
                        'minimum': {'unit': 'business_day', 'value': 1},
                        'maximum': {'unit': 'business_day', 'value': 3},
                    },
                },
            },
        ]

        # Add free shipping option if subtotal >= €1500
        if subtotal >= 1500:
            shipping_options.append({
                'shipping_rate_data': {
                    'type': 'fixed_amount',
                    'fixed_amount': {'amount': 0, 'currency': 'eur'},
                    'display_name': 'Free shipping (Subtotal ≥ €1500)',
                    'delivery_estimate': {
                        'minimum': {'unit': 'business_day', 'value': 5},
                        'maximum': {'unit': 'business_day', 'value': 7},
                    },
                },
            })

        # Create line items for Stripe
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
                shipping_options=shipping_options,
            )
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        
@login_required
def initiate_checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.item.exists():
        return redirect('cart')

    cart_items = cart.item.all()
    subtotal = sum(item.product.price * item.quantity for item in cart_items)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    YOUR_DOMAIN = "https://pgpi-2-7.onrender.com"

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

    # Determine shipping options
    shipping_options = [
        {
            'shipping_rate_data': {
                'type': 'fixed_amount',
                'fixed_amount': {'amount': 500, 'currency': 'eur'},
                'display_name': 'Envío Estándar (€5.00, 5-7 días hábiles)',
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
                'display_name': 'Envío Exprés (€15.00, 1-3 días hábiles)',
                'delivery_estimate': {
                    'minimum': {'unit': 'business_day', 'value': 1},
                    'maximum': {'unit': 'business_day', 'value': 3},
                },
            },
        },
    ]

    if subtotal >= 1500:
        shipping_options.append({
            'shipping_rate_data': {
                'type': 'fixed_amount',
                'fixed_amount': {'amount': 0, 'currency': 'eur'},
                'display_name': 'Envío Gratuito (Pedido superior a €1500)',
                'delivery_estimate': {
                    'minimum': {'unit': 'business_day', 'value': 1},
                    'maximum': {'unit': 'business_day', 'value': 3},
                },
            },
        })

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=f"{YOUR_DOMAIN}/success/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{YOUR_DOMAIN}/cart/",
            shipping_address_collection={
                'allowed_countries': ['US', 'CA', 'ES'],
            },
            shipping_options=shipping_options,
        )

        # Generate tracking number
        track_number = f"TRACK-{uuid.uuid4().hex[:10].upper()}"

        # Create order
        order = Order.objects.create(
            user=request.user,
            session_id=checkout_session.id,
            total=subtotal,
            delivery_address="Pendiente de ser completada",
            track_number=track_number,
            status='Recibido',
        )

        # Add order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
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
            Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            productos_no_existentes.append(product_id)
            del cart[product_id]

    request.session['cart'] = cart

    if productos_no_existentes:
        productos_ids = ', '.join(str(pid) for pid in productos_no_existentes)
        return render(request, 'checkout_error.html', {
            'error': f'Los siguientes productos se eliminaron del carrito porque no existen: {productos_ids}. Por favor, actualiza tu carrito.'
        })

    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())

    stripe.api_key = settings.STRIPE_SECRET_KEY
    YOUR_DOMAIN = "https://pgpi-2-7.onrender.com"

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

    # Determine shipping options
    shipping_options = [
        {
            'shipping_rate_data': {
                'type': 'fixed_amount',
                'fixed_amount': {'amount': 500, 'currency': 'eur'},
                'display_name': 'Envío Estándar (€5.00, 5-7 días hábiles)',
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
                'display_name': 'Envío Exprés (€15.00, 1-3 días hábiles)',
                'delivery_estimate': {
                    'minimum': {'unit': 'business_day', 'value': 1},
                    'maximum': {'unit': 'business_day', 'value': 3},
                },
            },
        },
    ]

    if subtotal >= 1500:
        shipping_options.append({
            'shipping_rate_data': {
                'type': 'fixed_amount',
                'fixed_amount': {'amount': 0, 'currency': 'eur'},
                'display_name': 'Envío Gratuito (Pedido superior a €1500)',
                'delivery_estimate': {
                    'minimum': {'unit': 'business_day', 'value': 1},
                    'maximum': {'unit': 'business_day', 'value': 3},
                },
            },
        })

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=f"{YOUR_DOMAIN}/success_guest/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{YOUR_DOMAIN}/cart_guest/",
            shipping_address_collection={
                'allowed_countries': ['US', 'CA', 'ES'],
            },
            shipping_options=shipping_options,
        )

        # Generate tracking number
        track_number = f"TRACK-{uuid.uuid4().hex[:10].upper()}"

        # Create order
        order = Order.objects.create(
            session_id=checkout_session.id,
            total=subtotal,
            delivery_address="Pendiente de ser completada",
            track_number=track_number,
            status='Recibido',
        )

        # Add order items
        for product_id, item in cart.items():
            OrderItem.objects.create(
                order=order,
                product=Product.objects.get(id=product_id),
                quantity=item['quantity'],
                price=item['price'],
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
    
@login_required
def cash_on_delivery_form(request):
    if request.method == 'GET':
        return render(request, 'cash_on_delivery_form.html')
    

from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal

@login_required
def finalize_cash_on_delivery(request):
    if request.method == 'POST':
        print("Formulario enviado correctamente")
        print("Datos del POST:", request.POST)

        name = request.POST.get('name')
        email = request.POST.get('email')
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2', '')
        city = request.POST.get('city')
        province = request.POST.get('province', '')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country')
        shipping_method = request.POST.get('shipping_method')

        if not all([name, email, address_line_1, city, postal_code, country, shipping_method]):
            messages.error(request, 'Por favor, complete todos los campos obligatorios.')
            return redirect('cash_on_delivery_form')

        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.item.exists():
            messages.error(request, 'Tu carrito está vacío.')
            return redirect('cash_on_delivery_form')

        cart_items = cart.item.all()
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        shipping_cost = Decimal('5.00') if shipping_method == 'standard' else Decimal('15.00')
        total_price = subtotal + shipping_cost

        order = Order.objects.create(
            user=request.user,
            total=total_price,
            delivery_address=f"{address_line_1}, {address_line_2}, {city}, {province}, {postal_code}, {country}",
            track_number=f"TRACK-{uuid.uuid4().hex[:10].upper()}",
            status='Received',
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )

        cart_items.delete()

        return render(request, 'success.html', {
            'track_number': order.track_number,
            'name': name,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'total': total_price,
        })

    messages.error(request, 'Método de solicitud inválido.')
    return redirect('cash_on_delivery_form')



@login_required
def cash_on_delivery_form(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.item.exists():
        return render(request, 'checkout_error.html', {
            'error': 'Tu carrito está vacío. Añade productos antes de finalizar la compra.'
        })

    cart_items = cart.item.all()
    subtotal = sum(item.product.price * item.quantity for item in cart_items)

    return render(request, 'cash_on_delivery_form.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
    })
    
def guest_cash_on_delivery_form(request):
    cart = request.session.get('cart', {})
    if not cart:
        return render(request, 'checkout_error.html', {
            'error': 'Your cart is empty. Add products before completing the purchase.'
        })

    cart_items = [
        {
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'total': item['price'] * item['quantity']
        }
        for item in cart.values()
    ]
    subtotal = sum(item['total'] for item in cart_items)

    return render(request, 'guest_cash_on_delivery_form.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
    })


def finalize_guest_cash_on_delivery(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', None)  # Optional
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2', '')  # Optional
        city = request.POST.get('city')
        province = request.POST.get('province')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country')
        shipping_method = request.POST.get('shipping_method')

        address = f"{address_line_1}, {address_line_2}, {city}, {province}, {postal_code}, {country}"

        # Validate required fields
        if not all([name, email, address_line_1, city, province, postal_code, country, shipping_method]):
            return render(request, 'checkout_error.html', {
                'error': 'Please fill in all required fields.'
            })

        # Validate cart
        cart = request.session.get('cart', {})
        if not cart:
            return render(request, 'checkout_error.html', {
                'error': 'Your cart is empty. Add products before completing the purchase.'
            })

        # Calculate prices
        cart_items = []
        for product_id, item in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                cart_items.append({
                    'product': product,
                    'name': item['name'],
                    'price': Decimal(item['price']),
                    'quantity': item['quantity'],
                    'total': Decimal(item['price']) * item['quantity'],
                })
            except Product.DoesNotExist:
                # Handle invalid product references
                continue

        subtotal = sum(item['total'] for item in cart_items)
        shipping_cost = Decimal('5.00') if shipping_method == 'standard' else Decimal('15.00')
        total_price = subtotal + shipping_cost

        # Generate tracking number
        track_number = f"TRACK-{uuid.uuid4().hex[:10].upper()}"

        # Create order (without linking to a user)
        order = Order.objects.create(
            user=None,  # No user linked
            total=total_price,
            delivery_address=address,
            track_number=track_number,
            status='Received',
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],  # Pass the actual Product instance
                quantity=item['quantity'],
                price=item['price'],
            )

        # Clear the session cart
        del request.session['cart']

        # Render success page
        return render(request, 'success_guest.html', {
            'track_number': track_number,
            'name': name,
            'address': {
                "line1": address_line_1,
                "line2": address_line_2,
                "city": city,
                "state": province,
                "postal_code": postal_code,
                "country": country,
            },
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'total': total_price,
        })

    return render(request, 'checkout_error.html', {
        'error': 'Request method not allowed.'
    })

@staff_member_required
def update_order_status(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get("status")
        if new_status:
            order.status = new_status
            order.save()
            return redirect("order_list")
    return HttpResponse("Método no permitido", status=405)

@staff_member_required
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    for order in orders:
        # Añade un atributo personalizado con el correo o "Usuario invitado"
        order.display_email = order.user.email if order.user else "Usuario invitado"
    return render(request, 'order_list.html', {'orders': orders})

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


@staff_member_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto añadido con éxito.')
            return redirect('catalogo')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, 'Producto eliminado con éxito.')
    return redirect('catalogo')

@staff_member_required
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)  # Accept files for image updates
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado con éxito.')
            return redirect('catalogo')
    else:
        form = ProductForm(instance=product)
    return render(request, 'update_product.html', {'form': form, 'product': product})

@staff_member_required
def update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        email = request.POST.get('email')
        address = request.POST.get('delivery_address')
        phone = request.POST.get('phone')

        # Update order details
        order.delivery_address = address
        order.phone = phone
        order.user.email = email
        order.save()
        return redirect('order_list')

    return render(request, 'update_order.html', {'order': order})

@staff_member_required
def user_list(request):
    users = CustomUser.objects.all()
    return render(request, 'user_list.html', {'users': users})

@staff_member_required
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user.is_superuser:
        messages.error(request, "No se puede eliminar un superusuario.")
        return redirect('user_list')
    
    user.delete()
    messages.success(request, "Usuario eliminado con éxito.")
    return redirect('user_list')