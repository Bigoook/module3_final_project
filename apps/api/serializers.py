"""DRF serializers. Mutating serializers delegate to the services layer."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.services import register_user
from apps.catalog.selectors import can_submit_review, get_related_products
from apps.core.emailing import send_order_confirmation
from apps.orders.cart import Cart
from apps.orders.models import Order, OrderItem
from apps.orders.selectors import get_cart_lines
from apps.orders.services import OutOfStockError, create_order
from apps.reviews.models import Review
from apps.reviews.services import ReviewNotAllowedError, create_review


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    description = serializers.CharField(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)
    category = serializers.SerializerMethodField()
    stock = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    rating_avg = serializers.SerializerMethodField()
    rating_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_category(self, product) -> dict | None:
        if product.category_id is None:
            return None
        return {
            'id': product.category_id,
            'name': product.category.name,
            'slug': product.category.slug,
        }

    def get_rating_avg(self, product) -> float:
        return round(product.rating_avg, 2)


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'user', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

    def create(self, validated_data):
        request = self.context['request']
        product = self.context['product']
        try:
            return create_review(
                user=request.user,
                product=product,
                rating=validated_data['rating'],
                comment=validated_data['comment'],
            )
        except ReviewNotAllowedError as exc:
            raise serializers.ValidationError({'detail': str(exc)}) from exc


class ProductDetailSerializer(ProductSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    related_products = serializers.SerializerMethodField()
    can_review = serializers.SerializerMethodField()

    def get_related_products(self, product) -> list[dict]:
        return list(ProductSerializer(get_related_products(product), many=True).data)

    def get_can_review(self, product) -> bool:
        request = self.context.get('request')
        return can_submit_review(request.user if request else None, product)


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.IntegerField(source='product_id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'quantity', 'price', 'subtotal')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices, required=False)

    class Meta:
        model = Order
        fields = (
            'id',
            'order_number',
            'status',
            'payment_method',
            'total_price',
            'full_name',
            'email',
            'phone',
            'shipping_address',
            'created_at',
            'items',
        )
        read_only_fields = ('id', 'order_number', 'status', 'total_price', 'created_at', 'items')

    def create(self, validated_data):
        request = self.context['request']
        cart = Cart(request.session)
        lines = get_cart_lines(cart)
        if not lines:
            raise serializers.ValidationError({'detail': 'Your cart is empty.'})
        items = [(line['product'], line['quantity']) for line in lines]
        try:
            order = create_order(user=request.user, items=items, **validated_data)
        except OutOfStockError as exc:
            raise serializers.ValidationError({'detail': str(exc)}) from exc
        cart.clear()
        send_order_confirmation(order)
        return order


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=32)
    default_address = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value: str) -> str:
        if get_user_model().objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return value

    def validate_email(self, value: str) -> str:
        lowered = value.lower()
        if get_user_model().objects.filter(email=lowered).exists():
            raise serializers.ValidationError('A user with that email already exists.')
        return lowered

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data):
        return register_user(**validated_data)


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    default_address = serializers.CharField(read_only=True)


class CartLineSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)
    product = serializers.SerializerMethodField()

    def get_product(self, line) -> dict:
        return ProductSerializer(line['product']).data


class CartReadSerializer(serializers.Serializer):
    lines = CartLineSerializer(many=True, read_only=True)
    total = serializers.CharField(read_only=True)
    is_empty = serializers.BooleanField(read_only=True)
