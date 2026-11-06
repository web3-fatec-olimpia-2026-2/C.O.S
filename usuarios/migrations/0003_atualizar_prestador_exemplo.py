from django.db import migrations


DOCUMENTO_DOUGLAS_EXEMPLO = 'EXEMPLO-PRESTADOR-001'
DOCUMENTOS_EXEMPLO_REMOVIDOS = [
    'EXEMPLO-PRESTADOR-002',
    'EXEMPLO-PRESTADOR-003',
]


def atualizar_prestadores_exemplo(apps, schema_editor):
    Prestador = apps.get_model('usuarios', 'Prestador')
    Prestador.objects.filter(
        documento=DOCUMENTO_DOUGLAS_EXEMPLO,
    ).update(nome='Douglas Pereira', status=True)
    Prestador.objects.filter(
        documento__in=DOCUMENTOS_EXEMPLO_REMOVIDOS,
    ).update(status=False)


def reverter_prestadores_exemplo(apps, schema_editor):
    Prestador = apps.get_model('usuarios', 'Prestador')
    Prestador.objects.filter(
        documento=DOCUMENTO_DOUGLAS_EXEMPLO,
    ).update(nome='Carlos Silva (Exemplo)', status=True)
    Prestador.objects.filter(
        documento=DOCUMENTOS_EXEMPLO_REMOVIDOS,
    ).update(status=True)


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_seed_prestadores_exemplo'),
    ]

    operations = [
        migrations.RunPython(
            atualizar_prestadores_exemplo,
            reverter_prestadores_exemplo,
        ),
    ]
