"""Seed script for the homebrew shop demo data.

Creates categories (with a hierarchy), products (copying sample images from
static/img/products), demo users and reviews.
"""

import os
import shutil
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from faker import Faker  # type: ignore[import-untyped]

from apps.catalog.models import Category, Product
from apps.core.utils import make_slug
from apps.reviews.models import Review

PRODUCTS: list[dict[str, Any]] = [
    {
        'name': 'Maris Otter Malt',
        'category': 'base-malts',
        'price': '4.50',
        'stock': 40,
        'image': 'maris_otter_malt',
        'description': 'Класичний британський базовий солод з нотками печива та горіхів.',
    },
    {
        'name': 'Pilsner Malt',
        'category': 'base-malts',
        'price': '3.90',
        'stock': 55,
        'image': 'pilsner_malt',
        'description': 'Світлий базовий солод для лагерів та золотистих елів.',
    },
    {
        'name': 'Caramel Malt',
        'category': 'specialty-malts',
        'price': '4.20',
        'stock': 30,
        'image': 'caramel_malt',
        'description': 'Карамельний солод для кольору та карамельної солодкості.',
    },
    {
        'name': 'Unmalted Wheat',
        'category': 'specialty-malts',
        'price': '3.40',
        'stock': 25,
        'image': 'unmalted_wheat',
        'description': 'Непшенична пшениця для пшеничного пива та хмарного стилю.',
    },
    {
        'name': 'Cascade Hops',
        'category': 'hops',
        'price': '5.80',
        'stock': 60,
        'image': 'cascade_hops',
        'description': 'Ароматний хміль з цитрусовими та квітковими нотами.',
    },
    {
        'name': 'Centennial Hops',
        'category': 'hops',
        'price': '6.20',
        'stock': 0,
        'image': 'centennial_hops',
        'description': 'Універсальний хміль, збалансований між гіркотою та ароматом.',
    },
    {
        'name': 'Citra Hops',
        'category': 'hops',
        'price': '7.10',
        'stock': 45,
        'image': 'citra_hops',
        'description': 'Тропічні ноти манго, маракуї та лайму.',
    },
    {
        'name': 'Mosaic Hops',
        'category': 'hops',
        'price': '7.40',
        'stock': 38,
        'image': 'mosaic_hops',
        'description': 'Ягідний та тропічний аромат, ідеальний для NEIPA.',
    },
    {
        'name': 'Saaz Hops',
        'category': 'hops',
        'price': '5.30',
        'stock': 50,
        'image': 'saaz_hops',
        'description': 'Чеський класичний хміль для лагерів та пільзерів.',
    },
    {
        'name': 'Safale US-05 Yeast',
        'category': 'yeast',
        'price': '4.90',
        'stock': 70,
        'image': 'safale_us05_yeast',
        'description': 'Сухі дріжджі для американських елів та IPA.',
    },
    {
        'name': 'Imperial Yeast',
        'category': 'yeast',
        'price': '8.60',
        'stock': 20,
        'image': 'imperial_yeast',
        'description': 'Потужні дріжджі з високою зброджуваністю для міцних сортів.',
    },
    {
        'name': 'IPA Brewing Kit',
        'category': 'kits',
        'price': '45.00',
        'stock': 12,
        'image': 'ipa_kit',
        'description': 'Готовий набір для варіння хмелевого IPA вдома.',
    },
    {
        'name': 'Hydrometer',
        'category': 'equipment',
        'price': '9.90',
        'stock': 18,
        'image': None,
        'description': 'Ареометр для вимірювання густини сусла.',
    },
    {
        'name': 'Fermenting Bucket 32L',
        'category': 'equipment',
        'price': '24.00',
        'stock': 9,
        'image': None,
        'description': 'Ферментер на 32 літри з кришкою та гідрозатвором.',
    },
    {
        'name': 'Bottling Wand',
        'category': 'equipment',
        'price': '8.50',
        'stock': 22,
        'image': None,
        'description': 'Сифон із кульовим клапаном для розливу пива.',
    },
]

CATEGORIES: list[dict[str, Any]] = [
    {'name': 'Kits', 'slug': 'kits', 'parent': None},
    {'name': 'Malts', 'slug': 'malts', 'parent': None},
    {'name': 'Base Malts', 'slug': 'base-malts', 'parent': 'malts'},
    {'name': 'Specialty Malts', 'slug': 'specialty-malts', 'parent': 'malts'},
    {'name': 'Hops', 'slug': 'hops', 'parent': None},
    {'name': 'Yeast', 'slug': 'yeast', 'parent': None},
    {'name': 'Equipment', 'slug': 'equipment', 'parent': None},
]

DEMO_USERS = 6
REVIEW_RATINGS = (5, 4, 5, 3, 4, 5)

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = os.environ.get('DJANGO_SEED_ADMIN_PASSWORD', 'admin12345')
DEMO_PASSWORD = os.environ.get('DJANGO_SEED_DEMO_PASSWORD', 'demo-pass-123')


class Command(BaseCommand):
    help = 'Заповнює базу демо-даними: категорії, товари, користувачі, відгуки.'

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            '--force',
            action='store_true',
            help='Очищає каталог і відгуки перед завантаженням.',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if Product.objects.exists() and not options['force']:
            self.stdout.write('Демо-дані вже завантажені. Використайте --force, щоб перестворити.')
            return

        if options['force']:
            Review.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()

        self._create_categories()
        self._create_products()
        self._create_users()
        self._create_reviews()

        self.stdout.write(
            self.style.SUCCESS(
                f'Готово: {Category.objects.count()} категорій, '
                f'{Product.objects.count()} товарів, {Review.objects.count()} відгуків.'
            )
        )

    def _create_categories(self) -> None:
        for item in CATEGORIES:
            parent = None
            if item['parent']:
                parent = Category.objects.get(slug=item['parent'])
            Category.objects.get_or_create(
                slug=item['slug'],
                defaults={'name': item['name'], 'parent': parent},
            )

    def _create_products(self) -> None:
        media_products = Path(settings.MEDIA_ROOT) / 'products'
        source_dir = Path(settings.BASE_DIR) / 'static' / 'img' / 'products'

        for item in PRODUCTS:
            category = Category.objects.get(slug=item['category'])
            product, _ = Product.objects.get_or_create(
                slug=make_slug(item['name']),
                defaults={
                    'name': item['name'],
                    'category': category,
                    'price': item['price'],
                    'stock': item['stock'],
                    'description': item['description'],
                },
            )
            if item['image']:
                source = source_dir / f'{item["image"]}.jpg'
                if not source.exists():
                    raise CommandError(f'Зображення не знайдено: {source}')
                media_products.mkdir(parents=True, exist_ok=True)
                product.image = self._copy_image(source, media_products)
                product.save(update_fields=['image'])

    @staticmethod
    def _copy_image(source: Path, media_products: Path) -> str:
        destination = media_products / source.name
        if not destination.exists():
            shutil.copy2(source, destination)
        return f'products/{source.name}'

    def _create_users(self) -> None:
        User = get_user_model()

        if not User.objects.filter(username=ADMIN_USERNAME).exists():
            User.objects.create_superuser(
                username=ADMIN_USERNAME,
                email='admin@example.com',
                password=ADMIN_PASSWORD,
            )

        fake = Faker()
        uk = Faker('uk_UA')
        for index in range(DEMO_USERS):
            username = fake.user_name() + str(index)
            if User.objects.filter(username=username).exists():
                continue
            User.objects.create_user(
                username=username,
                email=fake.email(),
                password=DEMO_PASSWORD,
                first_name=uk.first_name(),
                last_name=uk.last_name(),
            )

    def _create_reviews(self) -> None:
        uk = Faker('uk_UA')
        User = get_user_model()
        users = list(User.objects.filter(is_superuser=False)[:DEMO_USERS])
        if not users:
            return

        for index, product in enumerate(Product.objects.order_by('pk')[: len(REVIEW_RATINGS)]):
            author = users[index % len(users)]
            Review.objects.get_or_create(
                product=product,
                user=author,
                defaults={
                    'rating': REVIEW_RATINGS[index],
                    'comment': uk.sentence(nb_words=8),
                },
            )
