from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


class CadastroUsuarioForm(UserCreationForm):
    email = forms.EmailField(
        label='E-mail',
        required=True
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Este e-mail já está cadastrado.'
            )

        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data['email']
        usuario.perfil = 'COMUM'

        if commit:
            usuario.save()

        return usuario
