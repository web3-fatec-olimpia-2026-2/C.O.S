from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Prestador, Usuario


class UsuarioCadastroForm(forms.ModelForm):
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput,
    )
    senha_confirmacao = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput,
    )

    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if Usuario.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Este nome de usuário já está cadastrado.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Este e-mail já está cadastrado.'
            )

        return email

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        senha_confirmacao = cleaned_data.get('senha_confirmacao')
        if senha and senha_confirmacao and senha != senha_confirmacao:
            self.add_error('senha_confirmacao', 'As senhas não coincidem.')
        elif senha:
            try:
                validate_password(
                    senha,
                    user=Usuario(
                        username=cleaned_data.get('username', ''),
                        email=cleaned_data.get('email', ''),
                        first_name=cleaned_data.get('first_name', ''),
                        last_name=cleaned_data.get('last_name', ''),
                    ),
                )
            except ValidationError as erro:
                self.add_error('senha', list(erro))
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data['email']
        usuario.perfil = 'COMUM'
        usuario.set_password(self.cleaned_data['senha'])

        if commit:
            usuario.save()

        return usuario


class CadastroUsuarioForm(UsuarioCadastroForm):
    """Compatibilidade com o nome usado por partes antigas do projeto."""
    pass


class AdminUsuarioCadastroForm(forms.Form):
    username = forms.CharField(label='Usuário', max_length=150)
    first_name = forms.CharField(label='Nome', max_length=150, required=False)
    last_name = forms.CharField(label='Sobrenome', max_length=150, required=False)
    email = forms.EmailField(label='E-mail')
    perfil = forms.ChoiceField(label='Perfil', choices=Usuario.PERFIS_CHOICES)
    senha = forms.CharField(label='Senha', widget=forms.PasswordInput)
    senha_confirmacao = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput,
    )
    documento = forms.CharField(label='Documento', max_length=50, required=False)
    telefone = forms.CharField(label='Telefone', max_length=20, required=False)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if Usuario.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Este nome de usuário já está cadastrado.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        senha_confirmacao = cleaned_data.get('senha_confirmacao')

        if senha and senha_confirmacao and senha != senha_confirmacao:
            self.add_error('senha_confirmacao', 'As senhas não coincidem.')
        elif senha:
            try:
                validate_password(senha)
            except ValidationError as erro:
                self.add_error('senha', list(erro))

        if cleaned_data.get('perfil') == 'PRESTADOR':
            if not cleaned_data.get('documento'):
                self.add_error('documento', 'Informe o documento do prestador.')
            if not cleaned_data.get('telefone'):
                self.add_error('telefone', 'Informe o telefone do prestador.')
            documento = cleaned_data.get('documento', '').strip()
            if documento and Prestador.objects.filter(documento__iexact=documento).exists():
                self.add_error('documento', 'Este documento já está cadastrado.')

        return cleaned_data

    def save(self):
        usuario = Usuario.objects.create_user(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', ''),
            email=self.cleaned_data['email'],
            password=self.cleaned_data['senha'],
            perfil=self.cleaned_data['perfil'],
        )

        if usuario.perfil == 'PRESTADOR':
            Prestador.objects.create(
                usuario=usuario,
                nome=' '.join(
                    parte for parte in (
                        usuario.first_name,
                        usuario.last_name,
                    ) if parte
                ) or usuario.username,
                documento=self.cleaned_data['documento'].strip(),
                telefone=self.cleaned_data['telefone'].strip(),
                email=usuario.email,
                status=True,
            )

        return usuario
