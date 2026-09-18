from django import forms

from .models import Michi

INPUT_CLASSES = (
    'w-full rounded-lg border border-ink/15 px-3 py-2 text-sm '
    'focus:outline-none focus:ring-2 focus:ring-marmalade/50 focus:border-marmalade'
)


class MichiForm(forms.ModelForm):
    class Meta:
        model = Michi
        fields = ['nombre', 'tipo', 'dueno', 'foto']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'tipo': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'dueno': forms.Select(attrs={'class': INPUT_CLASSES}),
            'foto': forms.ClearableFileInput(attrs={'class': INPUT_CLASSES}),
        }
