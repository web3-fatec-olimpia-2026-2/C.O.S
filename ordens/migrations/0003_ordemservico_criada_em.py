import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0002_alter_ordemservico_numero_os'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordemservico',
            name='criada_em',
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name='Criada em',
            ),
            preserve_default=False,
        ),
    ]
