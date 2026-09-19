from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    PERFIS_CHOICES = (
        ('ADMINISTRADOR', 'Administrador'),
        ('PRESTADOR','Prestador de Serviço'),
        ('COMUM','Usuário Comum'),
        ('PREMIUM','Usuário Premium'),
    )

    perfil = models.CharField(max_length=20, choices=PERFIS_CHOICES, default='COMUM')

    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.username} - {self.perfil}"

class Prestador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='prestador_perfil', null=True, blank=True)
    nome = models.CharField(max_length=255)
    documento = models.CharField(max_length=50, unique=True)
    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.nome