from django import forms

from .models import Category

class CategorySelectForm(forms.Form):
    categories = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
