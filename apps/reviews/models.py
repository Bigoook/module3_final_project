from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Review(models.Model):
    product = models.ForeignKey(
        'catalog.Product',
        verbose_name=_('product'),
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
        on_delete=models.PROTECT,
        related_name='reviews',
    )
    rating = models.IntegerField(
        _('rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(_('comment'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='unique_product_user',
            ),
        )
        ordering = ('-created_at',)
        verbose_name = _('review')
        verbose_name_plural = _('reviews')

    def __str__(self) -> str:
        return f'{self.user} / {self.product}'
