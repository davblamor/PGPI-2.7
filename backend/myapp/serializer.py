from rest_framework import serializers
from myapp.models import BlobImage,Category,Manufacturer,Product,Cart,CartItem,Order,OrderItem
from base64 import b64encode
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth.models import User

class BlobImageSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = BlobImage
        fields = ('data',)

    @extend_schema_field(OpenApiTypes.STR)
    def get_data(self, obj):
        return 'data:' + obj.mime_type + ';charset=utf-8;base64,' + b64encode(obj.content).decode('utf-8')
    
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    image = BlobImageSerializer()
    category = CategorySerializer()
    manufacturer = ManufacturerSerializer()

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price', 'stock', 'image', 'category', 'manufacturer')

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity')

class CartSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Muestra el nombre de usuario en lugar de todos sus detalles
    items = CartItemSerializer(source='item', many=True)  # Relación inversa con `related_name="item"` en CartItem

    class Meta:
        model = Cart
        fields = ('id', 'user', 'created_at', 'items')

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'quantity', 'price')

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    order_items = OrderItemSerializer(many=True)  # Relación inversa con `related_name="order_items"` en OrderItem

    class Meta:
        model = Order
        fields = ('id', 'user', 'created_at', 'total', 'delivery_address', 'order_items')

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Fields:
    - `id` (int): The ID of the user.
    - `username` (string): The username of the user.
    - `email` (string): The email of the user.
    - `password` (string): The password of the user.

    Note:
    - The `password` field is write-only, and it should be sent during user registration.
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    Fields:
    - `username` (string): The username of the user.
    - `password` (string): The password of the user.
    """

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)