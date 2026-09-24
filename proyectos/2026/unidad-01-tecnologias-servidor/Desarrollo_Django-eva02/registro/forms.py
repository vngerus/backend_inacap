from django import forms

from .models import Michi

INPUT_CLASSES = (
    'w-full rounded-lg border border-ink/15 px-3 py-2 text-sm '
    'focus:outline-none focus:ring-2 focus:ring-marmalade/50 focus:border-marmalade'
)


MAX_FOTO_BYTES = 5 * 1024 * 1024  # 5 MB


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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        if not nombre:
            raise forms.ValidationError('El nombre no puede estar vacío o ser solo espacios.')
        return nombre

    def clean_tipo(self):
        tipo = self.cleaned_data['tipo'].strip()
        if not tipo:
            raise forms.ValidationError('El tipo no puede estar vacío o ser solo espacios.')
        return tipo

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        if foto and hasattr(foto, 'size') and foto.size > MAX_FOTO_BYTES:
            raise forms.ValidationError('La foto no puede superar los 5 MB.')
        return foto
