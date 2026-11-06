from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from usuarios.models import Prestador

class OrdemServico(models.Model):

    class Status(models.TextChoices):
        ABERTA = 'ABERTA', 'Aberta'
        EM_EXECUCAO = 'EM EXECUÇÃO', 'Em execução'
        EM_ANALISE = 'EM ANÁLISE', 'Em análise'
        CONCLUIDA = 'CONCLUÍDA', 'Concluída'

    class Prioridade(models.TextChoices):
        BAIXA = 'BAIXA', 'Baixa'
        NORMAL = 'NORMAL', 'Normal'
        ALTA = 'ALTA', 'Alta'
        URGENTE = 'URGENTE', 'Urgente'

    class Categoria(models.TextChoices):
        SINALIZACAO_HORIZONTAL = 'SINALIZAÇÃO HORIZONTAL', 'Sinalização horizontal'
        SINALIZACAO_VERTICAL = 'SINALIZAÇÃO VERTICAL', 'Sinalização vertical'
        SINALIZACAO_SEMAFORICA = 'SINALIZAÇÃO SEMAFÓRICA', 'Sinalização semafórica'

    # Número OS — gerado automaticamente no formato 0001
    numero_OS = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        verbose_name="Número OS"
    )

    data_prevista = models.DateField()
    criada_em = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    entregue_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Entregue em',
    )
    descricao = models.TextField()
    endereco = models.CharField(max_length=255)
    numero_endereco = models.CharField(max_length=20)
    bairro = models.CharField(max_length=100)
    complemento = models.CharField(max_length=100, blank=True, null=True)

    categoria = models.CharField(
        max_length=30,
        choices=Categoria.choices,
        default=Categoria.SINALIZACAO_HORIZONTAL
    )

    prioridade = models.CharField(
        max_length=20,
        choices=Prioridade.choices,
        default=Prioridade.NORMAL
    )

    prestador = models.ForeignKey(
        Prestador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordens_atribuidas'
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ABERTA
    )

    def clean(self):
        super().clean()
        if not self.data_prevista:
            return

        data_anterior = None
        if self.pk:
            data_anterior = type(self).objects.filter(pk=self.pk).values_list(
                'data_prevista',
                flat=True,
            ).first()

        if self.data_prevista < timezone.localdate() and data_anterior != self.data_prevista:
            raise ValidationError({
                'data_prevista': 'A data prevista não pode ser anterior à data atual.'
            })

    # Método de geração automática — ÚNICO e completo
    def save(self, *args, **kwargs):
        if not self.numero_OS:
            ultima = OrdemServico.objects.order_by('-id').first()
            proximo_numero = ultima.id + 1 if ultima else 1
            self.numero_OS = f"{proximo_numero:04d}"  # Formato: 1 → "0001"

        update_fields = kwargs.get('update_fields')
        status_sera_salvo = update_fields is None or 'status' in update_fields
        if status_sera_salvo and self.status == self.Status.CONCLUIDA:
            if self.pk:
                status_anterior = type(self).objects.filter(pk=self.pk).values_list(
                    'status',
                    flat=True,
                ).first()
                if status_anterior != self.Status.CONCLUIDA:
                    self.entregue_em = timezone.now()
            elif self.entregue_em is None:
                self.entregue_em = timezone.now()

            if self.entregue_em is not None and update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {'entregue_em'}

        super().save(*args, **kwargs)

    def __str__(self):
        return f"OS-{self.numero_OS}"