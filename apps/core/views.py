from django.http import JsonResponse
from django.views.generic import TemplateView


class GuidesRecipesView(TemplateView):
    template_name = 'core/guides_recipes.html'


def health(request):
    return JsonResponse({'healthy': True})
