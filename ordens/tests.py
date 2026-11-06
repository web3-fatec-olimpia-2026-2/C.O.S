from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import OrdemServico


class OrdemServicoModelTests(TestCase):
    def setUp(self):
        self.ordem = OrdemServico.objects.create(
            numero_OS=1,
            data_prevista=date(2026, 11, 10),
            descricao="Implantação de sinalização viária",
            endereco="Rua Exemplo",
            numero_endereco="100",
            bairro="Centro",
        )

    def test_criar_ordem_servico(self):
        self.assertEqual(OrdemServico.objects.count(), 1)
        self.assertEqual(self.ordem.numero_OS, 1)
        self.assertEqual(
            self.ordem.descricao,
            "Implantação de sinalização viária",
        )

    def test_valores_padrao_da_ordem(self):
        self.assertEqual(
            self.ordem.status,
            OrdemServico.Status.ABERTA,
        )
        self.assertEqual(
            self.ordem.prioridade,
            OrdemServico.Prioridade.NORMAL,
        )
        self.assertEqual(
            self.ordem.categoria,
            OrdemServico.Categoria.SINALIZACAO_HORIZONTAL,
        )

    def test_numero_os_nao_pode_ser_zero(self):
        ordem = OrdemServico(
            numero_OS=0,
            data_prevista=date(2026, 11, 10),
            descricao="Teste de validação",
            endereco="Rua Exemplo",
            numero_endereco="100",
            bairro="Centro",
        )

        with self.assertRaises(ValidationError):
            ordem.full_clean()