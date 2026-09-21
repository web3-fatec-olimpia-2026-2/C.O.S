from django.db import models
from django.core.validators import MinValueValidator
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


    numero_OS = models.IntegerField(validators=[MinValueValidator(1)])
    data_prevista = models.DateField()
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