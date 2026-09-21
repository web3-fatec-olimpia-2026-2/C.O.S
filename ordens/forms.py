from django import forms
from .models import OrdemServico

class OrdemForm (forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = [
            'numero_OS',
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