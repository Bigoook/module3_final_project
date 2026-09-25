from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    phone = models.CharField(_('phone'), max_length=32, blank=True, default='')
    default_address = models.TextField(_('default address'), blank=True, default='')
