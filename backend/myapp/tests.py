from django.test import TestCase
from django.urls import reverse
from myapp.models import Product, Category, Manufacturer, Cart, CartItem, Order, OrderItem
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

class CatalogIntegrationTests(TestCase):
    def setUp(self):
        self.category_living_room = Category.objects.create(name="Salón", description="Electrodomésticos de salón")
        self.category_kitchen = Category.objects.create(name="Cocina", description="Electrodomésticos de cocina")
        self.manufacturer_samsung = Manufacturer.objects.create(name="Samsung", description="Fabricante de electrodomésticos")
        self.manufacturer_lg = Manufacturer.objects.create(name="LG", description="Fabricante de electrodomésticos")

        self.product_tv = Product.objects.create(
            name="Televisor",
            description="Televisor Samsung QLED 4K/55 pulgadas",
            price=1150.00,
            stock=1,
            category=self.category_living_room,
            manufacturer=self.manufacturer_samsung
        )
        self.product_fridge = Product.objects.create(
            name="Nevera",
            description="Nevera sin escarcha",
            price=999.99,
            stock=10,
            category=self.category_kitchen,
            manufacturer=self.manufacturer_samsung
        )
        self.product_washing_machine = Product.objects.create(
            name="Lavadora",
            description="Lavadora eficiente",
            price=531.45,
            stock=5,
            category=self.category_kitchen,
            manufacturer=self.manufacturer_lg
        )
        User = get_user_model()
        self.user = User.objects.create_user(email="testuser@django.com", password="test123")

    def test_catalog_page_loads_and_displays_products(self):
        response = self.client.get(reverse('catalogo'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalogo.html')
        self.assertContains(response, 'Televisor')
        self.assertContains(response, 'Nevera')
        self.assertContains(response, 'Lavadora')

    def test_navigation_by_category(self):
        response = self.client.get(reverse('filtrar_por_categoria', args=[self.category_living_room.id]))
        self.assertContains(response, "Televisor")
        self.assertNotContains(response, "Nevera")
        self.assertNotContains(response, "Lavadora")

        response = self.client.get(reverse('filtrar_por_categoria', args=[self.category_kitchen.id]))
        self.assertNotContains(response, "Televisor")
        self.assertContains(response, "Nevera")
        self.assertContains(response, "Lavadora")

    def test_navigation_by_manufacturer(self):
        response = self.client.get(reverse('filtrar_por_fabricante', args=[self.manufacturer_samsung.id]))
        self.assertContains(response, "Televisor")
        self.assertContains(response, "Nevera")
        self.assertNotContains(response, "Lavadora")

        response = self.client.get(reverse('filtrar_por_fabricante', args=[self.manufacturer_lg.id]))
        self.assertNotContains(response, "Televisor")
        self.assertNotContains(response, "Nevera")
        self.assertContains(response, "Lavadora")

    def test_search_functionality(self):
        response = self.client.get(reverse('catalogo') + '?q=Nevera')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nevera')

        response = self.client.get(reverse('catalogo') + '?q=Lavadora')
        self.assertContains(response, 'Lavadora')

class CartIntegrationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electrodomésticos", description="Categoría general")
        self.manufacturer = Manufacturer.objects.create(name="Samsung", description="Fabricante")
        self.product = Product.objects.create(
            name="Aspiradora",
            description="Aspiradora potente",
            price=200.00,
            stock=5,
            category=self.category,
            manufacturer=self.manufacturer
        )
        User = get_user_model()
        self.user = User.objects.create_user(email="buyer@django.com", password="password123")

    def test_authenticated_user_can_add_to_cart(self):
        self.client.login(email=self.user.email, password="password123")
        response = self.client.post(reverse('add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        cart_item = CartItem.objects.filter(product=self.product, cart__user=self.user).first()
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.quantity, 1)

    def test_guest_can_add_to_cart_and_initiate_checkout(self):
        session = self.client.session
        response = self.client.post(reverse('add_to_cart_guest', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)

class CatalogIntegrationTests(TestCase):
    def setUp(self):
        self.category_living_room = Category.objects.create(name="Salón", description="Electrodomésticos de salón")
        self.category_kitchen = Category.objects.create(name="Cocina", description="Electrodomésticos de cocina")
        self.manufacturer_samsung = Manufacturer.objects.create(name="Samsung", description="Fabricante de electrodomésticos")
        self.manufacturer_lg = Manufacturer.objects.create(name="LG", description="Fabricante de electrodomésticos")

        self.product_tv = Product.objects.create(
            name="Televisor",
            description="Televisor Samsung QLED 4K/55 pulgadas",
            price=1150.00,
            stock=1,
            category=self.category_living_room,
            manufacturer=self.manufacturer_samsung
        )
        self.product_fridge = Product.objects.create(
            name="Nevera",
            description="Nevera sin escarcha",
            price=999.99,
            stock=10,
            category=self.category_kitchen,
            manufacturer=self.manufacturer_samsung
        )
        self.product_washing_machine = Product.objects.create(
            name="Lavadora",
            description="Lavadora eficiente",
            price=531.45,
            stock=5,
            category=self.category_kitchen,
            manufacturer=self.manufacturer_lg
        )
        User = get_user_model()
        self.user = User.objects.create_user(email="testuser@django.com", password="test123")

    def test_catalog_page_loads_and_displays_products(self):
        response = self.client.get(reverse('catalogo'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalogo.html')
        self.assertContains(response, 'Televisor')
        self.assertContains(response, 'Nevera')
        self.assertContains(response, 'Lavadora')

    def test_navigation_by_category(self):
        response = self.client.get(reverse('filtrar_por_categoria', args=[self.category_living_room.id]))
        self.assertContains(response, "Televisor")
        self.assertNotContains(response, "Nevera")
        self.assertNotContains(response, "Lavadora")

        response = self.client.get(reverse('filtrar_por_categoria', args=[self.category_kitchen.id]))
        self.assertNotContains(response, "Televisor")
        self.assertContains(response, "Nevera")
        self.assertContains(response, "Lavadora")

    def test_navigation_by_manufacturer(self):
        response = self.client.get(reverse('filtrar_por_fabricante', args=[self.manufacturer_samsung.id]))
        self.assertContains(response, "Televisor")
        self.assertContains(response, "Nevera")
        self.assertNotContains(response, "Lavadora")

        response = self.client.get(reverse('filtrar_por_fabricante', args=[self.manufacturer_lg.id]))
        self.assertNotContains(response, "Televisor")
        self.assertNotContains(response, "Nevera")
        self.assertContains(response, "Lavadora")

    def test_search_functionality(self):
        response = self.client.get(reverse('catalogo') + '?q=Nevera')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nevera')

        response = self.client.get(reverse('catalogo') + '?q=Lavadora')
        self.assertContains(response, 'Lavadora')

class CartIntegrationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electrodomésticos", description="Categoría general")
        self.manufacturer = Manufacturer.objects.create(name="Samsung", description="Fabricante")
        self.product = Product.objects.create(
            name="Aspiradora",
            description="Aspiradora potente",
            price=200.00,
            stock=5,
            category=self.category,
            manufacturer=self.manufacturer
        )
        User = get_user_model()
        self.user = User.objects.create_user(email="buyer@django.com", password="password123")

    def test_authenticated_user_can_add_to_cart(self):
        self.client.login(email=self.user.email, password="password123")
        response = self.client.post(reverse('add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        cart_item = CartItem.objects.filter(product=self.product, cart__user=self.user).first()
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.quantity, 1)

    def test_guest_can_add_to_cart_and_initiate_checkout(self):
        session = self.client.session
        response = self.client.post(reverse('add_to_cart_guest', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)

        session_cart = self.client.session['cart']
        self.assertIn(str(self.product.id), session_cart)
        self.assertEqual(session_cart[str(self.product.id)]['quantity'], 1)

        # Simula iniciar checkout como invitado
        response = self.client.post(reverse('initiate_checkout_guest'))
        self.assertEqual(response.status_code, 302)

    def test_cannot_add_out_of_stock_product(self):
        product_out_of_stock = Product.objects.create(
            name="PlayStation 5", price=499.99, stock=0, category=self.category, manufacturer=self.manufacturer
        )
        self.client.login(email=self.user.email, password="password123")
        response = self.client.post(reverse('add_to_cart', args=[product_out_of_stock.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No hay suficiente stock disponible")

    def test_guest_cannot_add_out_of_stock_product(self):
            product_out_of_stock = Product.objects.create(
                name="PlayStation 5",
                price=499.99,
                stock=0,
                category=self.category,
                manufacturer=self.manufacturer
            )
            response = self.client.post(reverse('add_to_cart_guest', args=[product_out_of_stock.id]))
            
            # Verificar que se redirige al catálogo
            self.assertRedirects(response, reverse('catalogo'))

            # Obtener mensajes de la respuesta
            messages = list(get_messages(response.wsgi_request))
            
            # Verificar que hay un mensaje de error
            self.assertEqual(len(messages), 1)
            self.assertEqual(str(messages[0]), "No hay suficiente stock disponible")

            # Verificar que el producto no está en el carrito de la sesión
            cart = self.client.session.get('cart', {})
            self.assertNotIn(str(product_out_of_stock.id), cart)

    def test_successful_checkout_creates_order(self):
        self.client.login(email=self.user.email, password="password123")
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        response = self.client.get(reverse('initiate_checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(user=self.user, total=self.product.price * 2).exists())

    def test_increase_cart_quantity(self):
        self.client.login(email=self.user.email, password="password123")
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)

        response = self.client.post(reverse('increase_quantity', args=[cart_item.id]))
        self.assertEqual(response.status_code, 302)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 2)

    def test_decrease_cart_quantity(self):
        self.client.login(email=self.user.email, password="password123")
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        response = self.client.post(reverse('decrease_quantity', args=[cart_item.id]))
        self.assertEqual(response.status_code, 302)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 1)

        response = self.client.post(reverse('decrease_quantity', args=[cart_item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())

    def test_increase_cart_quantity_guest(self):
        session = self.client.session
        session['cart'] = {str(self.product.id): {'quantity': 1, 'price': self.product.price}}
        session.save()

        response = self.client.post(reverse('increase_quantity_guest', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['cart'][str(self.product.id)]['quantity'], 2)

    def test_decrease_cart_quantity_guest(self):
        session = self.client.session
        session['cart'] = {str(self.product.id): {'quantity': 2, 'price': self.product.price}}
        session.save()

        response = self.client.post(reverse('decrease_quantity_guest', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['cart'][str(self.product.id)]['quantity'], 1)

        response = self.client.post(reverse('decrease_quantity_guest', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(str(self.product.id), self.client.session['cart'])

    def test_track_order_valid_code(self):
        order = Order.objects.create(user=self.user, session_id="test_session", total=100, track_number="TRACK-12345")
        self.client.login(email=self.user.email, password="password123")

        response = self.client.post(reverse('track_order_guest'), {'track_number': 'TRACK-12345'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TRACK-12345')

    def test_track_order_invalid_code(self):
        self.client.login(email=self.user.email, password="password123")

        response = self.client.post(reverse('track_order_guest'), {'track_number': 'INVALID-12345'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se encontró ningún pedido con ese código de seguimiento')

    def test_track_order_guest_valid_code(self):
        order = Order.objects.create(session_id="test_session", total=100, track_number="TRACK-12345")
        response = self.client.post(reverse('track_order_guest'), {'track_number': 'TRACK-12345'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TRACK-12345')

    def test_track_order_guest_invalid_code(self):
        response = self.client.post(reverse('track_order_guest'), {'track_number': 'INVALID-12345'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se encontró ningún pedido con ese código de seguimiento')