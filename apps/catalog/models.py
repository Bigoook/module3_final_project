from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(_('name'), max_length=150)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    parent = models.ForeignKey(
        'self',
        verbose_name=_('parent category'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=250, unique=True)
    description = models.TextField(_('description'))
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    category = models.ForeignKey(
        Category,
        verbose_name=_('category'),
        on_delete=models.PROTECT,
        related_name='products',
    )
    image = models.ImageField(_('image'), upload_to='products/', blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    stock = models.IntegerField(_('stock'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = _('product')
        verbose_name_plural = _('products')
        constraints = (
            models.CheckConstraint(
                condition=models.Q(price__gt=0),
                name='product_price_positive',
            ),
        )

    def __str__(self) -> str:
        return self.name
