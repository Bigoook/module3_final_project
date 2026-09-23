from typing import ClassVar

from django import forms

from apps.reviews.models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(str(value), value) for value in range(1, 6)],
        widget=forms.RadioSelect,
        coerce=int,
    )

    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets: ClassVar[dict] = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }
