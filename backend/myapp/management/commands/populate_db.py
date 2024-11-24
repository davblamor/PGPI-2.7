from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from myapp.models import BlobImage,Category,Manufacturer,Product,Cart,CartItem,Order,OrderItem


class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def handle(self, *args, **kwargs):
        # Limpiamos tablas relacionadas
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        Product.objects.all().delete()
        BlobImage.objects.all().delete()
        Category.objects.all().delete()
        Manufacturer.objects.all().delete()

        User = get_user_model()
        User.objects.filter(email='testuser@django.com').delete()

        #Create categories
        living_room = Category.objects.create(name="Salón", description="Electrodomésticos de salón")
        kitchen = Category.objects.create(name="Cocina", description="Electrodomésticos de cocina")
        bathroom = Category.objects.create(name="Baño", description="Electrodomésticos de baño")


        #Create manufacturers
        samsung = Manufacturer.objects.create(name="Samsung", description="Fabricante de electrodomésticos")
        ikea = Manufacturer.objects.create(name="Ikea", description="Fabricante de muebles")
        siemens = Manufacturer.objects.create(name="Siemens", description="Fabricante de electrodomésticos")
        leroy = Manufacturer.objects.create(name="Leroy Merlin", description="Fabricante de muebles")
        lg = Manufacturer.objects.create(name="LG", description="Fabricante de electrodomésticos")



        #Imágenes
        image_product1 = BlobImage.objects.create()
        image_product1.save_image('static/images/products/alingsas-frigorifico-congelador-ikea-500-independiente-ac-inox__1218105_pe913139_s5.avif')
        image_product2 = BlobImage.objects.create()
        image_product2.save_image('static/images/products/microwave.webp')
        image_product3 = BlobImage.objects.create()
        image_product3.save_image('static/images/products/dishwahser.avif')
        image_product4 = BlobImage.objects.create()
        image_product4.save_image('static/images/products/lavavajillas_Siemens.jpg')
        image_product5 = BlobImage.objects.create()
        image_product5.save_image('static/images/products/televisor_Samsung.jpeg')
        image_product6 = BlobImage.objects.create()
        image_product6.save_image('static/images/products/lavavadora_lg.avif')
        image_product7 = BlobImage.objects.create()
        image_product7.save_image('static/images/products/oven_lagan.avif')
        image_product8 = BlobImage.objects.create()
        image_product8.save_image('static/images/products/tv_samsung.webp')

        #Create products
        fridge = Product.objects.create(
            name="Nevera",
            description="Nevera sin escarcha",
            price=999.99,
            stock=10,
            image=image_product1,
            category=kitchen,
            manufacturer=samsung
        )

        dishwasher = Product.objects.create(
            name="Lavavajillas",
            description="Lavavajillas multifuncional",
            price=649.00,
            stock=8,
            image=image_product4,
            category=kitchen,
            manufacturer=siemens
        )
        tv = Product.objects.create(
            name="Televisor",
            description="Televisor Samsung QLED 4K/55 pulgadas",
            price=1150.00,
            stock=1,
            image=image_product5,
            category=living_room,
            manufacturer=samsung
        )
        washing_machine = Product.objects.create(
            name="Lavadora",
            description="Lavadora 10% más eficiente",
            price=531.45,
            stock=1,
            image=image_product6,
            category=bathroom,
            manufacturer=lg
        )
        microwave = Product.objects.create(
            name="Microondas",
            description="Microondas de cocina",
            price=120.00,
            stock=5,
            image = image_product2,
            category=kitchen,
            manufacturer=ikea

        )
        dishwasher2 = Product.objects.create(
            name="Lavavajillas",
            description="Lavavajillas leroy",
            price=600.00,
            stock=10,
            image = image_product3,
            category=kitchen,
            manufacturer=leroy
        )
        oven = Product.objects.create(
            name="Horno",
            description="Horno de cocina",
            price=400.00,
            stock=6,
            image = image_product7,
            category=kitchen,
            manufacturer=leroy
        )
        tv_samsung = Product.objects.create(
            name="Televisión samsung",
            description="Smart TV",
            price=1000.00,
            stock=3,
            image = image_product8,
            category=living_room,
            manufacturer=leroy
        )


        self.stdout.write(self.style.SUCCESS('Nuevos productos añadidos con éxito'))

        #Creación usuario de prueba
        user1 = User.objects.create_user(email='testuser@django.com', password='test')

        #Crear una cesta y agregar items
        cart = Cart.objects.create(user=user1)
        CartItem.objects.create(cart=cart,product=fridge,quantity=1)
        CartItem.objects.create(cart=cart,product=oven,quantity=2)

        #Crear un pedido con items
        order = Order.objects.create(user=user1, total=1300.00, delivery_address="123 Main St")
        OrderItem.objects.create(order=order, product=fridge, quantity=1, price=999.99)
        OrderItem.objects.create(order=order, product=oven, quantity=2, price=800.00)

        self.stdout.write(self.style.SUCCESS('Base de datos poblada con éxito'))


