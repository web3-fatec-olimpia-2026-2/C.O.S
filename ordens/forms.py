from django import forms
from django.utils import timezone
from usuarios.models import Prestador

from .models import OrdemServico


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