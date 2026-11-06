from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0003_ordemservico_criada_em'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordemservico',
            name='entregue_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Entregue em',
            ),
        ),
    ]
