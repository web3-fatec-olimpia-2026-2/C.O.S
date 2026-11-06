from django.db import migrations


PRESTADORES_EXEMPLO = [
    {
        'nome': 'Carlos Silva (Exemplo)',
        'documento': 'EXEMPLO-PRESTADOR-001',
        'telefone': '(17) 90000-0001',
        'email': 'carlos.exemplo@example.com',
    },
    {
        'nome': 'Mariana Oliveira (Exemplo)',
        'documento': 'EXEMPLO-PRESTADOR-002',
        'telefone': '(17) 90000-0002',
        'email': 'mariana.exemplo@example.com',
    },
    {
        'nome': 'Rafael Santos (Exemplo)',
        'documento': 'EXEMPLO-PRESTADOR-003',
        'telefone': '(17) 90000-0003',
        'email': 'rafael.exemplo@example.com',
    },
]


def criar_prestadores_exemplo(apps, schema_editor):
    Prestador = apps.get_model('usuarios', 'Prestador')
    if Prestador.objects.exists():
        return

    Prestador.objects.bulk_create([
        Prestador(**dados) for dados in PRESTADORES_EXEMPLO
    ])


def remover_prestadores_exemplo(apps, schema_editor):
    Prestador = apps.get_model('usuarios', 'Prestador')
    documentos = [dados['documento'] for dados in PRESTADORES_EXEMPLO]
    Prestador.objects.filter(documento__in=documentos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            criar_prestadores_exemplo,
            remover_prestadores_exemplo,
        ),
    ]
