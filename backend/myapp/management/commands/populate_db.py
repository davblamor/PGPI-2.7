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
        electronics = Category.objects.create(name="Electronica", description="Dispositivos electrónicos")
        furniture = Category.objects.create(name="Muebles", description="Muebles para hogar y oficina")

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
        image_product2.save_image('static/images/products/micke-escritorio-blanco__0736018_pe740345_s5.avif')
        image_product3 = BlobImage.objects.create()
        image_product3.save_image('static/images/products/millberget-silla-giratoria-murum-negro__1020142_pe831799_s5.avif')
        image_product4 = BlobImage.objects.create()
        image_product4.save_image('static/images/products/lavavajillas_Siemens.jpg')
        image_product5 = BlobImage.objects.create()
        image_product5.save_image('static/images/products/televisor_Samsung.jpeg')
        image_product6 = BlobImage.objects.create()
        image_product6.save_image('static/images/products/lavavadora_lg.avif')
        image_product7 = BlobImage.objects.create()
        image_product7.save_image('static/images/products/escritorio_leroy.webp')

        #Create products
        fridge = Product.objects.create(
            name="Nevera",
            description="Nevera sin escarcha",
            price=999.99,
            stock=10,
            image=image_product1,
            category=electronics,
            manufacturer=samsung
        )
        desk = Product.objects.create(
            name="Escritorio",
            description="Mesa de escritorio",
            price=150.00,
            stock=5,
            image=image_product2,
            category=furniture,
            manufacturer=ikea
        )
        chair = Product.objects.create(
            name="Silla",
            description="Silla de escritorio",
            price=100.00,
            stock=10,
            image=image_product3,
            category=furniture,
            manufacturer=ikea
        )
        dishwasher = Product.objects.create(
            name="Lavavajillas",
            description="Lavavajillas multifuncional",
            price=649.00,
            stock=8,
            image=image_product4,
            category=electronics,
            manufacturer=siemens
        )
        tv = Product.objects.create(
            name="Televisor",
            description="Televisor Samsung QLED 4K/55 pulgadas",
            price=1150.00,
            stock=1,
            image=image_product5,
            category=electronics,
            manufacturer=samsung
        )
        washing_machine = Product.objects.create(
            name="Lavadora",
            description="Lavadora 10% más eficiente",
            price=531.45,
            stock=0,
            image=image_product6,
            category=electronics,
            manufacturer=lg
        )
        desk_2 = Product.objects.create(
            name="Escritorio",
            description="Mesa de escritorio",
            price=110.00,
            stock=4,
            image=image_product7,
            category=furniture,
            manufacturer=leroy
        )

        self.stdout.write(self.style.SUCCESS('Nuevos productos añadidos con éxito'))

        #Creación usuario de prueba
        user1 = User.objects.create_user(email='testuser@django.com', password='test')

        #Crear una cesta y agregar items
        cart = Cart.objects.create(user=user1)
        CartItem.objects.create(cart=cart,product=fridge,quantity=1)
        CartItem.objects.create(cart=cart,product=chair,quantity=2)

        #Crear un pedido con items
        order = Order.objects.create(user=user1, total=1300.00, delivery_address="123 Main St")
        OrderItem.objects.create(order=order, product=fridge, quantity=1, price=999.99)
        OrderItem.objects.create(order=order, product=desk, quantity=2, price=300.00)

        self.stdout.write(self.style.SUCCESS('Base de datos poblada con éxito'))


