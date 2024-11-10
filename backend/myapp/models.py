from django.db import models
from django.contrib.auth.models import User
from base64 import urlsafe_b64encode
#Imagenes
class BlobImage(models.Model):
    content = models.BinaryField()
    mime_type = models.TextField()

    def save_image(self, ruta_archivo):
        from mimetypes import guess_type

        with open(ruta_archivo, 'rb') as f:
            datos = f.read()
            self.content = datos
            self.mime_type = guess_type(ruta_archivo)[0]
            self.save()

    def get_image(self):
        return urlsafe_b64encode(self.content).decode('utf-8')

#Categorías de Productos
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

#Fabricantes
class Manufacturer(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

#Productos
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ForeignKey(BlobImage,on_delete=models.CASCADE,null=True,blank=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

#Cesta de Compra
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart ({self.user})" if self.user else "Guest Cart"

#Elementos en la Cesta
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="item")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"

#Pedido
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField()

    def __str__(self):
        return f"Order ({self.id}) - {self.user.username}"

#Detalles de Pedido
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in Order {self.order.id}"

