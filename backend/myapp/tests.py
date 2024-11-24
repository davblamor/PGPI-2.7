from django.test import TestCase
from django.urls import reverse
from myapp.models import Product, Category, Manufacturer, Cart, CartItem, Order, OrderItem
from django.contrib.auth import get_user_model


class CatalogoTests(TestCase):
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

    def test_catalogo_page_loads(self):
        response = self.client.get(reverse('catalogo'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalogo.html')
        self.assertContains(response, 'Catálogo de Productos')

    def test_product_display(self):
        response = self.client.get(reverse('catalogo'))
        self.assertContains(response, "Televisor")
        self.assertContains(response, "Nevera")
        self.assertContains(response, "Lavadora")

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

    def test_add_to_cart(self):
        self.client.login(email="testuser@django.com", password="test123")
        response = self.client.post(reverse('add_to_cart', args=[self.product_fridge.id]), {'quantity': 1})
        self.assertEqual(response.status_code, 302)  # Redirige después de añadir
        self.assertTrue(CartItem.objects.filter(product=self.product_fridge).exists())

    
    def test_user_registration(self):
        User = get_user_model()
        User.objects.all().delete() 
        response = self.client.post(reverse('registro'), {
            'email': 'newuser@django.com',
            'password': 'validpassword123',
            'password_confirm': 'validpassword123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('catalogo'))

        self.assertTrue(User.objects.filter(email='newuser@django.com').exists())

    def test_user_login(self):
        User = get_user_model()
        user_email = 'testuser+1@django.com'  # Asegura un correo único
        user = User.objects.create_user(email=user_email, password='test123')

        response = self.client.post(reverse('login'), {
            'username': user_email,  # Django usa "username" en el backend
            'password': 'test123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('catalogo'))

        self.assertTrue('_auth_user_id' in self.client.session)

    def test_user_profile(self):
        self.client.login(email="testuser@django.com", password="test123")
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertContains(response, "testuser@django.com")

    def test_user_logout(self):
        self.client.login(email='testuser@django.com', password='test123')
        response = self.client.post(reverse('logout'))  # POST es más seguro para logout

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('catalogo'))

        self.assertFalse('_auth_user_id' in self.client.session)

