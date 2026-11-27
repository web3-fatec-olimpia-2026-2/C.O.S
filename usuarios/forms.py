from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Prestador, Usuario


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
class CadastroUsuarioAdminForm(UserCreationForm):
    email = forms.EmailField(
        label='E-mail',
        required=True
    )
    perfil = forms.ChoiceField(
        choices=Usuario.Perfil.choices,
        required=True
    )
    documento = forms.CharField(label='Documento', required=False)
    telefone = forms.CharField(label='Telefone', required=False)

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'perfil')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data['email']
        usuario.perfil = self.cleaned_data['perfil']

        if commit:
            usuario.save()
            if usuario.perfil == Usuario.Perfil.PRESTADOR:
                nome = ' '.join(
                    parte for parte in (
                        usuario.first_name.strip(),
                        usuario.last_name.strip(),
                    ) if parte
                ) or usuario.username
                documento = self.cleaned_data.get('documento', '').strip()
                telefone = self.cleaned_data.get('telefone', '').strip()
                if documento:
                    Prestador.objects.update_or_create(
                        usuario=usuario,
                        defaults={
                            'nome': nome,
                            'documento': documento,
                            'telefone': telefone,
                            'email': usuario.email,
                        },
                    )
                else:
                    Prestador.objects.update_or_create(
                        usuario=usuario,
                        defaults={
                            'nome': nome,
                            'telefone': telefone,
                            'email': usuario.email,
                            'documento': f'usuario-{usuario.pk}',
                        },
                    )
        return usuario
