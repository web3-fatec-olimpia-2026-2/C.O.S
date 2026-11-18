import os

from django import forms
from django.utils import timezone
from usuarios.models import Prestador

from .models import OrdemServico, FotosOS


class OrdemForm (forms.ModelForm):
    prestador = forms.ModelChoiceField(
        queryset=Prestador.objects.filter(status=True).order_by('nome'),
        required=False,
        empty_label='Selecione um prestador',
    )

    class Meta:
        model = OrdemServico
        fields = [
            'data_prevista',
            'descricao',
            'endereco',
            'numero_endereco',
            'bairro',
            'complemento',
            'categoria',
            'prioridade',
            'prestador',
            'status'
        ]

        widgets = {
            'data_prevista': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data_minima = timezone.localdate()
        if self.instance.pk and self.instance.data_prevista < data_minima:
            data_minima = self.instance.data_prevista
        self.fields['data_prevista'].widget.attrs['min'] = data_minima.isoformat()

class _ImagemComNomeCurtoField(forms.ImageField):
    max_nome_arquivo = 80

    def to_python(self, data):
        nome = getattr(data, 'name', None)
        if isinstance(nome, str) and len(nome) > self.max_nome_arquivo:
            base, extensao = os.path.splitext(nome)
            extensao = extensao[-20:]
            data.name = f'{base[:self.max_nome_arquivo - len(extensao)]}{extensao}'
        return super().to_python(data)


class FotoOSForm(forms.ModelForm):
    imagem = _ImagemComNomeCurtoField(
        max_length=100,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
    )

    class Meta:
        model = FotosOS
        fields = ['imagem']
