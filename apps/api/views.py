"""REST API views. Querying goes through selectors, mutations through services."""

from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import (
    CartLineSerializer,
    OrderSerializer,
    ProductDetailSerializer,
    ProductSerializer,
    RegisterSerializer,
    ReviewSerializer,
    UserSerializer,
)
from apps.catalog.selectors import get_product_detail, get_product_query
from apps.orders.cart import Cart
from apps.orders.models import Order
from apps.orders.selectors import get_cart_lines, get_cart_total, get_user_order, get_user_orders
from apps.orders.services import (
    CartStatus,
    OrderTransitionError,
    add_product_to_cart,
    cancel_order,
    remove_from_cart,
    update_cart_quantity,
)
from apps.reviews.selectors import list_reviews


class ProductListView(generics.ListAPIView):
    """Paginated active products with filtering, search and ordering."""

    serializer_class = ProductSerializer

    def get_queryset(self):
        return get_product_query(self.request.query_params)


class ProductDetailView(generics.RetrieveAPIView):
    """Single active product with its reviews and related products."""

    serializer_class = ProductDetailSerializer

    def get_object(self):
        product = get_product_detail(self.kwargs['pk'])
        if product is None:
            raise NotFound('Product not found.')
        return product


class ReviewListCreateView(APIView):
    """List product reviews (public) or add one (authenticated purchasers only)."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def _get_product(self, pk: int):
        product = get_product_detail(pk)
        if product is None:
            raise NotFound('Product not found.')
        return product

    def get(self, request, pk: int):
        reviews = list_reviews(self._get_product(pk))
        return Response(ReviewSerializer(reviews, many=True).data)

    def post(self, request, pk: int):
        product = self._get_product(pk)
        serializer = ReviewSerializer(data=request.data, context={'request': request, 'product': product})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderListCreateView(generics.ListCreateAPIView):
    """The user's orders; creating an order checks out the session cart."""

    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer

    def get_queryset(self):
        return get_user_orders(self.request.user)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """One of the user's orders; PATCH/DELETE cancel it via the service."""

    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer
    http_method_names = ('get', 'patch', 'delete')

    def get_object(self):
        order = get_user_order(self.request.user, self.kwargs['pk'])
        if order is None:
            raise NotFound('Order not found.')
        return order

    def partial_update(self, request, *args, **kwargs):
        if request.data.get('status') != Order.Status.CANCELLED:
            raise ValidationError({'detail': 'Only cancellation is allowed.'})
        order = self.get_object()
        try:
            cancel_order(order)
        except OrderTransitionError as exc:
            raise ValidationError({'detail': str(exc)}) from exc
        return Response(self.get_serializer(order).data)

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        try:
            cancel_order(order)
        except OrderTransitionError as exc:
            raise ValidationError({'detail': str(exc)}) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisterView(APIView):
    """Create a user account."""

    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class CartView(APIView):
    """Session cart: read it or add/update/remove lines through cart services."""

    permission_classes = (IsAuthenticated,)

    def _get_product(self, product_id):
        try:
            product = get_product_detail(int(product_id))
        except (TypeError, ValueError) as exc:
            raise ValidationError({'product_id': 'A valid product id is required.'}) from exc
        if product is None:
            raise NotFound('Product not found.')
        return product

    def _quantity(self, value):
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError({'quantity': 'Quantity must be a whole number.'}) from exc

    def get(self, request):
        cart = Cart(request.session)
        lines = get_cart_lines(cart)
        return Response(
            {
                'lines': CartLineSerializer(lines, many=True).data,
                'total': str(get_cart_total(lines)),
                'is_empty': not lines,
            }
        )

    def post(self, request):
        product = self._get_product(request.data.get('product_id'))
        result = add_product_to_cart(Cart(request.session), product, self._quantity(request.data.get('quantity', 1)))
        if result.status == CartStatus.OUT_OF_STOCK:
            raise ValidationError({'detail': f'"{product.name}" is out of stock.'})
        return Response({'status': result.status.value, 'quantity': result.quantity}, status=status.HTTP_201_CREATED)

    def patch(self, request):
        product = self._get_product(request.data.get('product_id'))
        result = update_cart_quantity(Cart(request.session), product, self._quantity(request.data.get('quantity', 1)))
        if result.status == CartStatus.MISSING:
            raise NotFound('That product is not in your cart.')
        return Response({'status': result.status.value, 'quantity': result.quantity})

    def delete(self, request):
        product_id = request.data.get('product_id') or request.query_params.get('product_id')
        product = self._get_product(product_id)
        remove_from_cart(Cart(request.session), product)
        return Response(status=status.HTTP_204_NO_CONTENT)
