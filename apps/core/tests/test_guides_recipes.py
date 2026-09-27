import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_guides_recipes_page_renders(client: Client) -> None:
    response = client.get(reverse('guides_recipes'))

    assert response.status_code == 200
    assert b'Guides &amp; Recipes' in response.content
    assert b'Coming Soon!' in response.content
    assert b'Guides &amp; Recipes' in response.content


@pytest.mark.django_db
def test_header_links_to_guides_recipes(client: Client) -> None:
    response = client.get(reverse('catalog:home'))

    assert response.status_code == 200
    assert reverse('guides_recipes').encode() in response.content
