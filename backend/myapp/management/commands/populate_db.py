from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from myapp.models import BlobImage,Category,Manufacturer,Product,Cart,CartItem,Order,OrderItem


class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def handle(self, *args, **kwargs):
        User = get_user_model() 

        #Create categories
        electronics = Category.objects.create(name="Electronica", description="Dispositivos electrónicos")
        furniture = Category.objects.create(name="Muebles", description="Muebles para hogar y oficina")

        #Create manufacturers
        samsung = Manufacturer.objects.create(name="Samsung", description="Fabricante de electrodomésticos")
        ikea = Manufacturer.objects.create(name="Ikea", description="Fabricante de muebles")


        #Imágenes
        image_product1 = BlobImage.objects.create()
        image_product1.save_image('../assets/alingsas-frigorifico-congelador-ikea-500-independiente-ac-inox__1218105_pe913139_s5.avif')
        image_product2 = BlobImage.objects.create()
        image_product2.save_image('../assets/micke-escritorio-blanco__0736018_pe740345_s5.avif')
        image_product3 = BlobImage.objects.create()
        image_product3.save_image('../assets/millberget-silla-giratoria-murum-negro__1020142_pe831799_s5.avif')


        #Create products
        fridge = Product.objects.create(
            name="Nevera",
            description="No frost nevera",
            price=999.99,
            stock=10,
            image=image_product1,
            category=electronics,
            manufacturer=samsung
        )
        desk = Product.objects.create(
            name="Escritorio",
            description="Office desk",
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


