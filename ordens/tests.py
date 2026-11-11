from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import OrdemForm
from .models import OrdemServico
from usuarios.models import Prestador


class OrdemServicoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='Senha@123',
            perfil='ADMINISTRADOR',
        )
        self.client.force_login(self.user)

    def test_criar_ordem_exibe_template_de_formulario(self):
        response = self.client.get(reverse('ordens:criar'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ordens/nova.html')

    def test_formulario_lista_prestadores_ativos_de_exemplo(self):
        nomes = set(OrdemForm().fields['prestador'].queryset.values_list('nome', flat=True))

        self.assertEqual(nomes, {'Douglas Pereira'})

    def test_formulario_nao_lista_prestador_inativo(self):
        inativo = Prestador.objects.create(
            nome='Prestador inativo',
            documento='TESTE-INATIVO-001',
            telefone='(17) 90000-0004',
            email='inativo@example.com',
            status=False,
        )

        prestadores_formulario = OrdemForm().fields['prestador'].queryset

        self.assertFalse(prestadores_formulario.filter(pk=inativo.pk).exists())

    def test_criar_ordem_pelo_popup_volta_para_pagina_inicial(self):
        response = self.client.post(
            reverse('ordens:criar'),
            {
                'data_prevista': '2026-12-01',
                'descricao': 'Manutenção de sinalização',
                'endereco': 'Rua das Flores',
                'numero_endereco': '100',
                'bairro': 'Centro',
                'complemento': 'Próximo ao posto',
                'categoria': OrdemServico.Categoria.SINALIZACAO_HORIZONTAL,
                'prioridade': OrdemServico.Prioridade.NORMAL,
                'prestador': '',
                'status': OrdemServico.Status.ABERTA,
            },
        )

        self.assertRedirects(response, reverse('pagina_inicial'))
        self.assertTrue(
            OrdemServico.objects.filter(descricao='Manutenção de sinalização').exists()
        )

    def test_criar_ordem_ajax_retorna_dados_para_atualizar_tabela(self):
        inicio = timezone.now()
        response = self.client.post(
            reverse('ordens:criar'),
            {
                'data_prevista': timezone.localdate().isoformat(),
                'descricao': 'Reparo de placa',
                'endereco': 'Avenida Brasil',
                'numero_endereco': '200',
                'bairro': 'Centro',
                'categoria': OrdemServico.Categoria.SINALIZACAO_VERTICAL,
                'prioridade': OrdemServico.Prioridade.ALTA,
                'prestador': '',
                'status': OrdemServico.Status.ABERTA,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['ordem']['descricao'], 'Reparo de placa')
        ordem = OrdemServico.objects.get(descricao='Reparo de placa')
        self.assertGreaterEqual(ordem.criada_em, inicio)
        self.assertLessEqual(ordem.criada_em, timezone.now())
        self.assertEqual(timezone.localtime(ordem.criada_em).date(), timezone.localdate())
        self.assertEqual(
            response.json()['ordem']['criada_em'],
            timezone.localtime(ordem.criada_em).strftime('%d/%m/%Y %H:%M'),
        )

    def test_criar_ordem_rejeita_data_prevista_no_passado(self):
        response = self.client.post(
            reverse('ordens:criar'),
            {
                'data_prevista': (timezone.localdate() - timedelta(days=1)).isoformat(),
                'descricao': 'Ordem com data passada',
                'endereco': 'Rua das Flores',
                'numero_endereco': '100',
                'bairro': 'Centro',
                'categoria': OrdemServico.Categoria.SINALIZACAO_HORIZONTAL,
                'prioridade': OrdemServico.Prioridade.NORMAL,
                'prestador': '',
                'status': OrdemServico.Status.ABERTA,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('data_prevista', response.json()['errors'])
        self.assertFalse(OrdemServico.objects.filter(descricao='Ordem com data passada').exists())

    def test_editar_ordem_antiga_sem_alterar_data_prevista(self):
        data_passada = timezone.localdate() - timedelta(days=1)
        ordem = OrdemServico.objects.create(
            data_prevista=data_passada,
            descricao='Ordem antiga',
            endereco='Rua das Flores',
            numero_endereco='100',
            bairro='Centro',
        )

        response = self.client.post(
            reverse('ordens:editar', args=[ordem.pk]),
            {
                'data_prevista': data_passada.isoformat(),
                'descricao': 'Ordem antiga atualizada',
                'endereco': 'Rua das Flores',
                'numero_endereco': '100',
                'bairro': 'Centro',
                'categoria': OrdemServico.Categoria.SINALIZACAO_HORIZONTAL,
                'prioridade': OrdemServico.Prioridade.NORMAL,
                'prestador': '',
                'status': OrdemServico.Status.EM_EXECUCAO,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        ordem.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ordem.data_prevista, data_passada)
        self.assertEqual(ordem.status, OrdemServico.Status.EM_EXECUCAO)

    def test_editar_ordem_ajax_carrega_dados_para_popup(self):
        ordem = OrdemServico.objects.create(
            data_prevista='2026-12-01',
            descricao='Revisar semáforo',
            endereco='Avenida Brasil',
            numero_endereco='200',
            bairro='Centro',
        )

        response = self.client.get(
            reverse('ordens:editar', args=[ordem.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['numero'], ordem.numero_OS)
        self.assertEqual(response.json()['form']['descricao'], 'Revisar semáforo')
        self.assertEqual(response.json()['form']['data_prevista'], '2026-12-01')

    def test_editar_ordem_por_url_abre_popup_na_pagina_inicial(self):
        ordem = OrdemServico.objects.create(
            data_prevista='2026-12-01',
            descricao='Revisar semáforo',
            endereco='Avenida Brasil',
            numero_endereco='200',
            bairro='Centro',
        )

        response = self.client.get(reverse('ordens:editar', args=[ordem.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/home.html')
        self.assertTrue(response.context['abrir_popup'])
        self.assertContains(response, f'Editar O.S. #{ordem.numero_OS}')
        self.assertContains(response, 'data-editing-pk="')

    def test_editar_ordem_ajax_atualiza_dados_para_linha_da_tabela(self):
        ordem = OrdemServico.objects.create(
            data_prevista='2026-12-01',
            descricao='Descrição anterior',
            endereco='Avenida Brasil',
            numero_endereco='200',
            bairro='Centro',
        )

        response = self.client.post(
            reverse('ordens:editar', args=[ordem.pk]),
            {
                'data_prevista': '2026-12-15',
                'descricao': 'Descrição atualizada',
                'endereco': 'Rua Nova',
                'numero_endereco': '25',
                'bairro': 'Jardim',
                'complemento': '',
                'categoria': OrdemServico.Categoria.SINALIZACAO_VERTICAL,
                'prioridade': OrdemServico.Prioridade.ALTA,
                'prestador': '',
                'status': OrdemServico.Status.EM_ANALISE,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        ordem.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ordem.descricao, 'Descrição atualizada')
        self.assertEqual(response.json()['ordem']['endereco'], 'Rua Nova, 25 - Jardim')

    def test_concluir_ordem_registra_horario_e_retorna_no_ajax(self):
        ordem = OrdemServico.objects.create(
            data_prevista=timezone.localdate(),
            descricao='Reparo de sinalização',
            endereco='Rua das Flores',
            numero_endereco='100',
            bairro='Centro',
        )
        inicio = timezone.now()

        response = self.client.post(
            reverse('ordens:editar', args=[ordem.pk]),
            {
                'data_prevista': timezone.localdate().isoformat(),
                'descricao': ordem.descricao,
                'endereco': ordem.endereco,
                'numero_endereco': ordem.numero_endereco,
                'bairro': ordem.bairro,
                'complemento': '',
                'categoria': ordem.categoria,
                'prioridade': ordem.prioridade,
                'prestador': '',
                'status': OrdemServico.Status.CONCLUIDA,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        ordem.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(ordem.entregue_em)
        self.assertGreaterEqual(ordem.entregue_em, inicio)
        self.assertLessEqual(ordem.entregue_em, timezone.now())
        self.assertEqual(
            response.json()['ordem']['entregue_em'],
            timezone.localtime(ordem.entregue_em).strftime('%d/%m/%Y %H:%M'),
        )
        self.assertContains(self.client.get(reverse('pagina_inicial')), 'Entregue em')

    def test_horario_de_entrega_so_muda_ao_concluir_novamente(self):
        ordem = OrdemServico.objects.create(
            data_prevista=timezone.localdate(),
            descricao='Reparo de sinalização',
            endereco='Rua das Flores',
            numero_endereco='100',
            bairro='Centro',
        )
        self.assertIsNone(ordem.entregue_em)

        primeira_entrega = timezone.now()
        ordem.status = OrdemServico.Status.CONCLUIDA
        with patch('ordens.models.timezone.now', return_value=primeira_entrega):
            ordem.save()
        ordem.refresh_from_db()
        self.assertEqual(ordem.entregue_em, primeira_entrega)

        ordem.descricao = 'Descrição atualizada'
        ordem.save()
        self.assertEqual(ordem.entregue_em, primeira_entrega)

        ordem.status = OrdemServico.Status.EM_EXECUCAO
        ordem.save()
        self.assertEqual(ordem.entregue_em, primeira_entrega)

        nova_entrega = primeira_entrega + timedelta(minutes=1)
        ordem.status = OrdemServico.Status.CONCLUIDA
        with patch('ordens.models.timezone.now', return_value=nova_entrega):
            ordem.save()
        ordem.refresh_from_db()
        self.assertEqual(ordem.entregue_em, nova_entrega)

    def test_pagina_inicial_exibe_ordens_cadastradas(self):
        ordem = OrdemServico.objects.create(
            data_prevista='2026-12-01',
            descricao='Pintura de faixa de pedestres',
            endereco='Rua das Flores',
            numero_endereco='100',
            bairro='Centro',
        )

        response = self.client.get(reverse('pagina_inicial'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'<span class="identificador-os">{ordem.numero_OS}</span>',
            html=True,
        )
        self.assertContains(response, 'Pintura de faixa de pedestres')
        self.assertContains(response, 'Editar')
        self.assertContains(response, 'data-excluir')
        self.assertIn(ordem, response.context['ordens'])

    def test_pagina_inicial_exibe_nome_e_perfil_do_usuario(self):
        response = self.client.get(reverse('pagina_inicial'))

        self.assertNotContains(response, 'perfil-resumo')
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.get_perfil_display())
        self.assertContains(response, 'Entrar com outro ID')
        self.assertContains(response, 'Sair')
        self.assertNotContains(response, 'Você está logado com sucesso.')
        self.assertNotContains(response, 'Bem-vindo,')

    def test_excluir_ordem_com_requisicao_htmx_remove_ordem(self):
        ordem = OrdemServico.objects.create(
            data_prevista='2026-12-01',
            descricao='Retirar placa danificada',
            endereco='Rua das Flores',
            numero_endereco='100',
            bairro='Centro',
        )

        response = self.client.post(
            reverse('ordens:excluir', args=[ordem.pk]),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(OrdemServico.objects.filter(pk=ordem.pk).exists())

    def test_formulario_invalido_mantem_popup_aberto_na_pagina_inicial(self):
        response = self.client.post(
            reverse('ordens:criar'),
            {'data_prevista': '', 'descricao': 'Ordem incompleta'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/home.html')
        self.assertTrue(response.context['abrir_popup'])
        self.assertTrue(response.context['form'].errors)

    def test_excluir_ordem_por_post_remove_o_registro(self):
        ordem = OrdemServico.objects.create(
            numero_OS=101,
            data_prevista='2026-12-01',
            descricao='Manutenção de sinalização',
            endereco='Rua das Flores',
            numero_endereco='100',
            bairro='Centro',
            complemento='Próximo ao posto',
        )

        response = self.client.post(reverse('ordens:excluir', args=[ordem.pk]))

        self.assertRedirects(response, reverse('ordens:listar'))
        self.assertFalse(OrdemServico.objects.filter(pk=ordem.pk).exists())

    def test_excluir_ordem_com_htmx_retorna_sucesso_sem_redirecionar(self):
        ordem = OrdemServico.objects.create(
            numero_OS=102,
            data_prevista='2026-12-01',
            descricao='Reparo de semáforo',
            endereco='Avenida Brasil',
            numero_endereco='200',
            bairro='Centro',
        )

        response = self.client.post(
            reverse('ordens:excluir', args=[ordem.pk]),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertFalse(OrdemServico.objects.filter(pk=ordem.pk).exists())


class ControleAcessoListagemTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()

        self.admin = Usuario.objects.create_user(
            username='admin_acesso',
            email='admin_acesso@example.com',
            password='Senha@123',
            perfil='ADMINISTRADOR',
        )

        self.prestador_user = Usuario.objects.create_user(
            username='prestador_acesso',
            email='prestador_acesso@example.com',
            password='Senha@123',
            perfil='PRESTADOR',
        )

        self.outro_prestador_user = Usuario.objects.create_user(
            username='outro_prestador',
            email='outro_prestador@example.com',
            password='Senha@123',
            perfil='PRESTADOR',
        )

        self.comum = Usuario.objects.create_user(
            username='comum_acesso',
            email='comum_acesso@example.com',
            password='Senha@123',
            perfil='COMUM',
        )

        self.premium = Usuario.objects.create_user(
            username='premium_acesso',
            email='premium_acesso@example.com',
            password='Senha@123',
            perfil='PREMIUM',
        )

        self.prestador = Prestador.objects.create(
            usuario=self.prestador_user,
            nome='Prestador de Teste',
            documento='TESTE-ACESSO-001',
            telefone='(17) 90000-0001',
            email='prestador_teste@example.com',
        )

        self.outro_prestador = Prestador.objects.create(
            usuario=self.outro_prestador_user,
            nome='Outro Prestador',
            documento='TESTE-ACESSO-002',
            telefone='(17) 90000-0002',
            email='outro_teste@example.com',
        )

        self.ordem_prestador = OrdemServico.objects.create(
            data_prevista=timezone.localdate(),
            descricao='Ordem do prestador de teste',
            endereco='Rua A',
            numero_endereco='100',
            bairro='Centro',
            prestador=self.prestador,
        )

        self.ordem_outro_prestador = OrdemServico.objects.create(
            data_prevista=timezone.localdate(),
            descricao='Ordem de outro prestador',
            endereco='Rua B',
            numero_endereco='200',
            bairro='Centro',
            prestador=self.outro_prestador,
        )

        self.ordem_sem_prestador = OrdemServico.objects.create(
            data_prevista=timezone.localdate(),
            descricao='Ordem sem prestador',
            endereco='Rua C',
            numero_endereco='300',
            bairro='Centro',
        )

    def verificar_listagens(self, usuario, ids_esperados):
        self.client.force_login(usuario)

        urls = [
            reverse('pagina_inicial'),
            reverse('ordens:listar'),
        ]

        for url in urls:
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)

            ids_exibidos = set(
                response.context['ordens'].values_list('id', flat=True)
            )

            self.assertEqual(ids_exibidos, ids_esperados)

    def test_administrador_visualiza_todas_as_ordens(self):
        ids_esperados = {
            self.ordem_prestador.id,
            self.ordem_outro_prestador.id,
            self.ordem_sem_prestador.id,
        }

        self.verificar_listagens(self.admin, ids_esperados)

    def test_prestador_visualiza_somente_suas_ordens(self):
        ids_esperados = {self.ordem_prestador.id}

        self.verificar_listagens(self.prestador_user, ids_esperados)

    def test_usuario_comum_nao_visualiza_ordens(self):
        self.verificar_listagens(self.comum, set())

    def test_usuario_premium_nao_visualiza_ordens(self):
        self.verificar_listagens(self.premium, set())
