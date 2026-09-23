from decimal import Decimal
from typing import Any

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Avg, Count, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.core.utils import make_slug


class Category(TimeStampedModel):
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

    class Meta:
        ordering = ('name',)
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse('catalog:product_list', kwargs={'category_slug': self.slug})

    def get_descendants(self) -> list['Category']:
        """All nested child categories, excluding self."""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = make_slug(self.name)
        super().save(*args, **kwargs)


class ProductManager(models.Manager['Product']):
    """Query API for active products annotated with review ratings."""

    def for_listing(self) -> models.QuerySet['Product']:
        return self.filter(is_active=True).annotate(
            _rating_avg=Coalesce(Avg('reviews__rating'), Value(0.0)),
            _rating_count=Count('reviews'),
        )


class Product(TimeStampedModel):
    objects = ProductManager()
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

    def get_absolute_url(self) -> str:
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    @property
    def rating_avg(self) -> float:
        return float(getattr(self, '_rating_avg', 0.0) or 0.0)

    @property
    def rating_count(self) -> int:
        return int(getattr(self, '_rating_count', 0) or 0)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = make_slug(self.name)
        super().save(*args, **kwargs)
