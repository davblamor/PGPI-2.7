from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from base64 import urlsafe_b64encode
from django.contrib.auth.base_user import BaseUserManager
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import mimetypes

#Imagenes
class BlobImage(models.Model):
    content = models.BinaryField()
    mime_type = models.TextField()
    file_name = models.TextField(blank=True, null=True)

    def save_image(self, ruta_archivo):
        from mimetypes import guess_type
        import os

        with open(ruta_archivo, 'rb') as f:
            datos = f.read()
            self.content = datos
            self.mime_type = mimetypes.guess_type(ruta_archivo)[0] or "application/octet-stream"
            self.file_name = os.path.basename(ruta_archivo)
            self.save()

    def get_image_url(self):
        return f"/static/images/products/{self.file_name}"

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
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart ({self.user})" if self.user else "Guest Cart"

    def total_items(self):
        return sum(item.quantity for item in self.item.all())

#Elementos en la Cesta
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="item")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"

#Pedido
class Order(models.Model):
    # Definición de los posibles estados
    STATUS_CHOICES = [
        ('Recibido', 'Recibido'),
        ('En Proceso', 'En Proceso'),
        ('Enviado', 'Enviado'),
        ('Entregado', 'Entregado'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField()
    track_number = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Recibido')

    def __str__(self):
        return f"Order {self.track_number} - Estado: {self.estado}"
    
#Detalles de Pedido
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in Order {self.order.id}"

#User
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        Group,
        related_name="customuser_groups",  # Cambia el related_name aquí
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_user_permissions",  # Cambia el related_name aquí
        blank=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email