from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Prestador, Usuario


class UsuarioCadastroForm(forms.ModelForm):
    """Formulário público de auto-cadastro (sempre cria perfil COMUM)."""

    email = forms.EmailField(label='E-mail', required=True)
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput,
        required=True,
    )
    senha_confirmacao = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput,
        required=True,
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


class AdminUsuarioCadastroForm(forms.ModelForm):
    """Formulário administrativo para criar usuários e vincular prestadores."""

    email = forms.EmailField(label='E-mail', required=True)
    perfil = forms.ChoiceField(
        label='Tipo de usuário',
        choices=Usuario.PERFIS_CHOICES,
        required=True,
    )
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput,
        required=True,
    )
    senha_confirmacao = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput,
        required=True,
    )
    documento = forms.CharField(
        label='CPF ou CNPJ',
        max_length=50,
        required=False,
    )
    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
    )

    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'perfil')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def clean_documento(self):
        return self.cleaned_data.get('documento', '').strip()

    def clean_telefone(self):
        return self.cleaned_data.get('telefone', '').strip()

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        senha_confirmacao = cleaned_data.get('senha_confirmacao')
        perfil = cleaned_data.get('perfil')
        documento = cleaned_data.get('documento', '')
        telefone = cleaned_data.get('telefone', '')

        if senha and senha_confirmacao and senha != senha_confirmacao:
            self.add_error('senha_confirmacao', 'As senhas não conferem.')
        elif senha:
            validate_password(senha)

        if perfil == 'PRESTADOR':
            if not documento:
                self.add_error(
                    'documento',
                    'Informe o documento para usuários com perfil Prestador.',
                )
            elif Prestador.objects.filter(documento=documento).exists():
                self.add_error(
                    'documento',
                    'Já existe um prestador cadastrado com este documento.',
                )
            if not telefone:
                self.add_error(
                    'telefone',
                    'Informe o telefone para usuários com perfil Prestador.',
                )

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data['email']
        usuario.perfil = self.cleaned_data['perfil']
        usuario.set_password(self.cleaned_data['senha'])

        if commit:
            usuario.save()
            if usuario.perfil == 'PRESTADOR':
                nome_completo = (
                    f'{usuario.first_name} {usuario.last_name}'.strip()
                    or usuario.username
                )
                Prestador.objects.create(
                    usuario=usuario,
                    nome=nome_completo,
                    documento=self.cleaned_data['documento'],
                    telefone=self.cleaned_data['telefone'],
                    email=usuario.email,
                )

        return usuario


CadastroUsuarioForm = UsuarioCadastroForm
