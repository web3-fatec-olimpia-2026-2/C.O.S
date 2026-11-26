import io
import pytest
from datetime import timedelta
from unittest.mock import patch
from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from .forms import OrdemForm, FotoOSForm
from .models import OrdemServico, FotosOS
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

    def test_administrador_aprova_ordem_em_analise(self):
        inicio = timezone.now()
        ordem = OrdemServico.objects.create(
            data_prevista=timezone.localdate(),
            descricao='Ordem aguardando aprovação',
            endereco='Rua das Flores',
            numero_endereco='100',
            bairro='Centro',
            status=OrdemServico.Status.EM_ANALISE,
            motivo_reprovacao='',
        )

        response = self.client.post(
            reverse('ordens:aprovar', args=[ordem.pk])
        )

        self.assertRedirects(
            response,
            reverse('ordens:detalhe', args=[ordem.pk]),
        )
        ordem.refresh_from_db()
        self.assertEqual(ordem.status, OrdemServico.Status.CONCLUIDA)
        self.assertEqual(ordem.motivo_reprovacao, '')
        self.assertIsNotNone(ordem.entregue_em)
        self.assertGreaterEqual(ordem.entregue_em, inicio)
        self.assertLessEqual(ordem.entregue_em, timezone.now())

        pagina_inicial = self.client.get(reverse('pagina_inicial'))
        self.assertEqual(pagina_inicial.status_code, 200)
        self.assertContains(pagina_inicial, 'Entregue em')
        self.assertNotContains(pagina_inicial, '{{ ordem.entregue_em')

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

    def test_pagina_inicial_exibe_nome_do_prestador_e_endereco_sem_codigo_template(self):
        prestador = Prestador.objects.create(
            nome='Douglas Pereira',
            documento='TESTE-PRESTADOR-EXIBICAO',
            telefone='(17) 90000-0001',
            email='douglas@example.com',
        )
        OrdemServico.objects.create(
            data_prevista='2026-12-01',
            descricao='Teste de exibição do prestador',
            endereco='Rua Teste',
            numero_endereco='123',
            bairro='Centro',
            prestador=prestador,
        )

        response = self.client.get(reverse('pagina_inicial'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rua Teste, 123 - Centro')
        self.assertContains(response, 'Douglas Pereira')
        self.assertNotContains(response, '{{ ordem.')

    def test_pagina_inicial_exibe_nome_e_perfil_do_usuario(self):
        self.user.first_name = 'Gleice'
        self.user.last_name = 'Constâncio'
        self.user.save(update_fields=['first_name', 'last_name'])

        response = self.client.get(reverse('pagina_inicial'))

        self.assertNotContains(response, 'perfil-resumo')
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.get_perfil_display())
        self.assertContains(response, '<span class="avatar-usuario" aria-hidden="true">GC</span>', html=True)
        self.assertNotContains(response, '{{ usuario.last_name')
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

    def test_prestador_visualiza_somente_ordens_atribuidas_a_ele(self):
        self.verificar_listagens(self.prestador_user, {self.ordem_prestador.id})

    def test_prestador_pode_abrir_ordem_atribuida_e_nao_ve_acoes_de_edicao(self):
        self.client.force_login(self.prestador_user)

        response = self.client.get(reverse('pagina_inicial'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ordem_prestador.descricao)
        self.assertNotContains(response, self.ordem_outro_prestador.descricao)
        self.assertNotContains(response, 'id="btnNovaOS"')
        self.assertNotContains(response, 'data-editar')
        self.assertNotContains(response, 'data-excluir')
        self.assertNotContains(response, 'id="formNovaOrdem"')
        self.assertContains(response, reverse('ordens:detalhe', args=[self.ordem_prestador.pk]))

        detalhe = self.client.get(
            reverse('ordens:detalhe', args=[self.ordem_prestador.pk])
        )
        self.assertEqual(detalhe.status_code, 200)
        self.assertContains(detalhe, 'Enviar fotos do serviço')
        self.assertContains(detalhe, 'Adicionar foto ANTES')
        self.assertContains(detalhe, 'Adicionar foto DEPOIS')
        self.assertEqual(
            self.client.get(
                reverse('ordens:detalhe', args=[self.ordem_outro_prestador.pk])
            ).status_code,
            404,
        )

    def test_prestador_nao_pode_criar_editar_ou_excluir(self):
        self.client.force_login(self.prestador_user)
        url_editar = reverse('ordens:editar', args=[self.ordem_prestador.pk])
        urls_post = [
            reverse('ordens:criar'),
            url_editar,
            reverse('ordens:excluir', args=[self.ordem_prestador.pk]),
            reverse('ordens:apagar_os_htmx', args=[self.ordem_prestador.pk]),
        ]

        self.assertEqual(self.client.get(url_editar).status_code, 403)
        total_ordens = OrdemServico.objects.count()
        for url in urls_post:
            response = self.client.post(url, {'descricao': 'Tentativa indevida'})
            self.assertEqual(response.status_code, 403, url)

        self.assertEqual(OrdemServico.objects.count(), total_ordens)
        self.ordem_prestador.refresh_from_db()
        self.assertEqual(self.ordem_prestador.descricao, 'Ordem do prestador de teste')

    def test_usuario_comum_nao_visualiza_ordens(self):
        self.verificar_listagens(self.comum, set())

    def test_usuario_premium_nao_visualiza_ordens(self):
        self.verificar_listagens(self.premium, set())


class ListarAdminTests(TestCase):
    """A tela /ordens/admin/ é restrita a administradores."""

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username='admintela', email='admintela@example.com',
            password='Senha@123', perfil='ADMINISTRADOR',
        )
        self.prestador_user = User.objects.create_user(
            username='presttela', email='presttela@example.com',
            password='Senha@123', perfil='PRESTADOR',
        )

    def test_admin_acessa_tela(self):
        self.admin.first_name = 'Gleice'
        self.admin.last_name = 'Constâncio'
        self.admin.save(update_fields=['first_name', 'last_name'])
        self.client.force_login(self.admin)
        resposta = self.client.get(reverse('ordens:listar_admin'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Ordens de Serviço')
        self.assertContains(resposta, '<span class="avatar-usuario" aria-hidden="true">GC</span>', html=True)
        self.assertNotContains(resposta, '{{ usuario.last_name')
        self.assertTemplateUsed(resposta, 'ordens/admin_lista.html')

    def test_menu_principal_fica_no_cabecalho_com_home(self):
        self.client.force_login(self.admin)

        resposta = self.client.get(reverse('pagina_inicial'))

        self.assertContains(resposta, 'Menus')
        self.assertContains(resposta, 'Home')
        self.assertContains(resposta, 'menu-navegacao-casa')
        self.assertNotContains(resposta, '<span class="pagina-nome">Visão geral</span>', html=True)
        self.assertNotContains(resposta, 'rodape-links')

    def test_voltar_de_fotos_retorna_ao_painel_com_filtros(self):
        self.client.force_login(self.admin)
        ordem = OrdemServico.objects.create(
            data_prevista=timezone.localdate(),
            descricao='Teste painel retorno',
            endereco='Rua das Flores',
            numero_endereco='10',
            bairro='Centro',
        )

        painel = self.client.get(reverse('ordens:listar_admin'), {'q': 'Teste painel'})
        self.assertContains(
            painel,
            f'{reverse("ordens:detalhe", args=[ordem.pk])}?q=Teste+painel&amp;origem=admin&amp;pagina=1',
        )

        detalhe = self.client.get(
            reverse('ordens:detalhe', args=[ordem.pk]),
            {
                'origem': 'admin',
                'q': 'Teste painel',
                'pagina': '1',
                'next': 'https://example.com',
            },
        )

        self.assertEqual(detalhe.status_code, 200)
        self.assertEqual(
            detalhe.context['voltar_url'],
            f'{reverse("ordens:listar_admin")}?q=Teste+painel&pagina=1',
        )
        self.assertContains(
            detalhe,
            f'href="{reverse("ordens:listar_admin")}?q=Teste+painel&amp;pagina=1"',
        )

    def test_prestador_bloqueado_com_403(self):
        self.client.force_login(self.prestador_user)
        resposta = self.client.get(reverse('ordens:listar_admin'))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_redireciona_para_login(self):
        resposta = self.client.get(reverse('ordens:listar_admin'))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn('/login/', resposta.url)

    def test_busca_e_filtro_sao_aceitos(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(reverse('ordens:listar_admin'), {
            'q': 'faixa', 'status': 'ABERTA', 'prestador': '99',
        })
        self.assertEqual(resposta.status_code, 200)

    def test_painel_resume_todos_os_status_e_aplica_filtro_de_prioridade(self):
        self.client.force_login(self.admin)
        estados = (
            OrdemServico.Status.ABERTA,
            OrdemServico.Status.EM_EXECUCAO,
            OrdemServico.Status.EM_ANALISE,
            OrdemServico.Status.CONCLUIDA,
        )
        for indice, estado in enumerate(estados):
            OrdemServico.objects.create(
                data_prevista=timezone.localdate(),
                descricao=f'Ordem de teste {indice}',
                endereco='Rua das Flores',
                numero_endereco=str(indice + 1),
                bairro='Centro',
                prioridade=(
                    OrdemServico.Prioridade.ALTA
                    if indice == 0
                    else OrdemServico.Prioridade.NORMAL
                ),
                status=estado,
            )

        resposta = self.client.get(reverse('ordens:listar_admin'), {
            'status': OrdemServico.Status.ABERTA,
            'prioridade': OrdemServico.Prioridade.ALTA,
        })

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context['total'], 1)
        self.assertEqual(resposta.context['metricas']['total'], 1)
        self.assertEqual(resposta.context['metricas']['aberta'], 1)
        self.assertEqual(resposta.context['metricas']['execucao'], 0)
        self.assertEqual(resposta.context['metricas']['analise'], 0)
        self.assertEqual(resposta.context['metricas']['concluida'], 0)
        self.assertEqual(len(resposta.context['dias_semana']), 7)
        self.assertEqual(resposta.context['total_semana'], 1)
        self.assertEqual(resposta.context['status_chart']['analise_fim'], 100)
        self.assertContains(resposta, 'Todas as prioridades')

    def test_cards_e_barras_filtram_o_painel_em_conjunto(self):
        self.client.force_login(self.admin)
        estados = (
            OrdemServico.Status.ABERTA,
            OrdemServico.Status.EM_EXECUCAO,
            OrdemServico.Status.EM_ANALISE,
            OrdemServico.Status.CONCLUIDA,
        )
        for indice, estado in enumerate(estados):
            OrdemServico.objects.create(
                data_prevista=timezone.localdate(),
                descricao=f'Ordem interativa {indice}',
                endereco='Rua das Flores',
                numero_endereco=str(indice + 1),
                bairro='Centro',
                status=estado,
            )

        inicial = self.client.get(reverse('ordens:listar_admin'))
        card_abertas = next(
            card for card in inicial.context['status_cards']
            if card['chave'] == 'aberta'
        )
        self.assertEqual(
            card_abertas['url'],
            f'{reverse("ordens:listar_admin")}?status=ABERTA',
        )

        filtrado_status = self.client.get(card_abertas['url'])
        self.assertEqual(filtrado_status.context['total'], 1)
        self.assertEqual(filtrado_status.context['metricas']['aberta'], 1)
        self.assertEqual(filtrado_status.context['metricas']['execucao'], 0)

        barra_hoje = next(
            dia for dia in filtrado_status.context['dias_semana']
            if dia['iso'] == timezone.localdate().isoformat()
        )
        filtrado_dia = self.client.get(barra_hoje['url'])
        self.assertEqual(filtrado_dia.context['total'], 1)
        self.assertTrue(
            next(
                dia for dia in filtrado_dia.context['dias_semana']
                if dia['iso'] == timezone.localdate().isoformat()
            )['selecionado']
        )
        ordem = OrdemServico.objects.get(status=OrdemServico.Status.ABERTA)
        self.assertContains(
            filtrado_dia,
            f'href="{reverse("ordens:detalhe", args=[ordem.pk])}?status=ABERTA&amp;dia={timezone.localdate().isoformat()}&amp;origem=admin&amp;pagina=1"',
        )
User = get_user_model()


def gerar_imagem_teste(nome='comprovante.jpg', formato='JPEG'):
    """Gera uma imagem válida em memória usando Pillow."""
    buffer = io.BytesIO()
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(buffer, format=formato)
    buffer.seek(0)
    return SimpleUploadedFile(
        name=nome,
        content=buffer.read(),
        content_type=f'image/{formato.lower()}',
    )


@pytest.fixture
def usuario(db):
    usuario = User.objects.create_user(
        username='dev_teste',
        password='SenhaForte123!',
        perfil='PRESTADOR',
    )
    Prestador.objects.create(
        usuario=usuario,
        nome='Prestador de Teste',
        documento='TESTE-PRESTADOR-FOTOS',
        telefone='(17) 90000-0001',
        email='prestador_fotos@example.com',
    )
    return usuario


@pytest.fixture
def ordem(db, usuario):
    return OrdemServico.objects.create(
        data_prevista=timezone.localdate(),
        descricao='Manutenção de semáforo',
        endereco='Av. Principal',
        numero_endereco='100',
        bairro='Centro',
        prestador=Prestador.objects.get(usuario=usuario),
    )


@pytest.fixture(autouse=True)
def media_temporaria(settings, tmp_path):
    """Isola o MEDIA_ROOT em uma pasta temporária para cada teste."""
    settings.MEDIA_ROOT = tmp_path



# 1. TESTES DO MODELO (FotoOS)


@pytest.mark.django_db
def test_criar_foto_os_e_relacionamento(ordem):
    foto1 = FotosOS.objects.create(ordem=ordem, imagem=gerar_imagem_teste('foto1.jpg'))
    foto2 = FotosOS.objects.create(ordem=ordem, imagem=gerar_imagem_teste('foto2.jpg'))

    assert ordem.fotos.count() == 2
    assert list(ordem.fotos.all()) == [foto1, foto2]
    assert foto1.data_envio is not None
    assert str(foto1) == f"Comprovante OS-{ordem.numero_OS} ({foto1.id})"


@pytest.mark.django_db
def test_cascade_ao_excluir_ordem_remove_fotos(ordem):
    FotosOS.objects.create(ordem=ordem, imagem=gerar_imagem_teste())
    assert FotosOS.objects.count() == 1

    ordem.delete()
    assert FotosOS.objects.count() == 0


# 2. TESTES DO FORMULÁRIO (FotoOSForm)


def test_foto_form_valido():
    arquivo = gerar_imagem_teste()
    form = FotoOSForm(data={}, files={'imagem': arquivo})
    assert form.is_valid()

def test_foto_form_aceita_nome_de_arquivo_longo():
    arquivo = gerar_imagem_teste(nome=f"{'foto_' * 25}.jpg")
    form = FotoOSForm(data={}, files={'imagem': arquivo})

    assert form.is_valid(), form.errors
    assert len(form.cleaned_data['imagem'].name) <= 80


def test_foto_form_invalido_com_arquivo_nao_imagem():
    arquivo_txt = SimpleUploadedFile(
        'documento.txt',
        b'conteudo invalido que nao e imagem',
        content_type='text/plain',
    )
    form = FotoOSForm(data={}, files={'imagem': arquivo_txt})
    assert not form.is_valid()
    assert 'imagem' in form.errors



# 3. TESTES DA VIEW (anexar_foto)

@pytest.mark.django_db
def test_anexar_foto_exige_login(client, ordem):
    url = reverse('ordens:anexar_foto', args=[ordem.pk])
    response = client.post(url, {'imagem': gerar_imagem_teste()})

    assert response.status_code == 302
    assert FotosOS.objects.count() == 0


@pytest.mark.django_db
def test_anexar_foto_bloqueia_get(client, usuario, ordem):
    client.force_login(usuario)
    url = reverse('ordens:anexar_foto', args=[ordem.pk])
    response = client.get(url)

    assert response.status_code == 405


@pytest.mark.django_db
def test_anexar_foto_upload_tradicional_sucesso(client, usuario, ordem):
    client.force_login(usuario)
    url = reverse('ordens:anexar_foto', args=[ordem.pk])

    response = client.post(url, {'imagem': gerar_imagem_teste()})

    assert response.status_code == 302
    assert response.url == reverse('ordens:detalhe', args=[ordem.pk])
    assert ordem.fotos.count() == 1


@pytest.mark.django_db
def test_anexar_foto_aceita_nome_de_arquivo_longo(client, usuario, ordem):
    client.force_login(usuario)
    arquivo = gerar_imagem_teste(nome=f"{'foto_' * 25}.jpg")

    response = client.post(
        reverse('ordens:anexar_foto', args=[ordem.pk]),
        {'imagem': arquivo, 'tipo': FotosOS.Tipo.ANTES},
    )

    assert response.status_code == 302
    foto = ordem.fotos.get()
    assert foto.tipo == FotosOS.Tipo.ANTES
    assert len(foto.imagem.name) <= 100
    assert foto.imagem.storage.exists(foto.imagem.name)


@pytest.mark.django_db
def test_anexar_foto_ajax_sucesso(client, usuario, ordem):
    client.force_login(usuario)
    url = reverse('ordens:anexar_foto', args=[ordem.pk])

    response = client.post(
        url,
        {'imagem': gerar_imagem_teste()},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
    )

    assert response.status_code == 200
    dados = response.json()
    assert dados['success'] is True
    assert 'url' in dados['foto']
    assert 'data_envio' in dados['foto']
    assert ordem.fotos.count() == 1


@pytest.mark.django_db
def test_anexar_foto_ajax_erro_validacao(client, usuario, ordem):
    client.force_login(usuario)
    url = reverse('ordens:anexar_foto', args=[ordem.pk])

    response = client.post(
        url,
        {},  # Sem imagem
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
    )

    assert response.status_code == 400
    dados = response.json()
    assert dados['success'] is False
    assert 'imagem' in dados['errors']
    assert FotosOS.objects.count() == 0


@pytest.mark.django_db
def test_anexar_foto_ordem_inexistente_retorna_404(client, usuario):
    client.force_login(usuario)
    url = reverse('ordens:anexar_foto', args=[99999])

    response = client.post(url, {'imagem': gerar_imagem_teste()})
    assert response.status_code == 404


@pytest.mark.django_db
def test_anexar_foto_bloqueia_ordem_de_outro_prestador(client, usuario):
    outro_usuario = User.objects.create_user(
        username='outro_prestador',
        email='outro_prestador_fotos@example.com',
        password='SenhaForte123!',
        perfil='PRESTADOR',
    )
    outro_prestador = Prestador.objects.create(
        usuario=outro_usuario,
        nome='Outro Prestador',
        documento='TESTE-OUTRO-PRESTADOR-FOTOS',
        telefone='(17) 90000-0002',
        email='outro_prestador_fotos@example.com',
    )
    outra_ordem = OrdemServico.objects.create(
        data_prevista=timezone.localdate(),
        descricao='Ordem de outro prestador',
        endereco='Rua B',
        numero_endereco='200',
        bairro='Centro',
        prestador=outro_prestador,
    )
    client.force_login(usuario)

    response = client.post(
        reverse('ordens:anexar_foto', args=[outra_ordem.pk]),
        {'imagem': gerar_imagem_teste()},
    )

    assert response.status_code == 404
    assert FotosOS.objects.count() == 0

User = get_user_model()


def gerar_imagem_teste(nome='comprovante.jpg', formato='JPEG'):
    """Gera uma imagem válida em memória usando Pillow."""
    buffer = io.BytesIO()
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(buffer, format=formato)
    buffer.seek(0)
    return SimpleUploadedFile(
        name=nome,
        content=buffer.read(),
        content_type=f'image/{formato.lower()}',
    )


@pytest.fixture
def usuario(db):
    usuario = User.objects.create_user(
        username='dev_teste',
        password='SenhaForte123!',
        perfil='PRESTADOR',
    )
    Prestador.objects.create(
        usuario=usuario,
        nome='Prestador de Teste',
        documento='TESTE-PRESTADOR-FOTOS',
        telefone='(17) 90000-0001',
        email='prestador_fotos@example.com',
    )
    return usuario


@pytest.fixture
def ordem(db, usuario):
    return OrdemServico.objects.create(
        data_prevista=timezone.localdate(),
        descricao='Manutenção de semáforo',
        endereco='Av. Principal',
        numero_endereco='100',
        bairro='Centro',
        prestador=Prestador.objects.get(usuario=usuario),
    )


@pytest.fixture(autouse=True)
def media_temporaria(settings, tmp_path):
    """Isola o MEDIA_ROOT em uma pasta temporária para cada teste."""
    settings.MEDIA_ROOT = tmp_path



# 1. TESTES DO MODELO (FotoOS)


@pytest.mark.django_db
def test_criar_foto_os_e_relacionamento(ordem):
    foto1 = FotosOS.objects.create(ordem=ordem, imagem=gerar_imagem_teste('foto1.jpg'))
    foto2 = FotosOS.objects.create(ordem=ordem, imagem=gerar_imagem_teste('foto2.jpg'))

    assert ordem.fotos.count() == 2
    assert list(ordem.fotos.all()) == [foto1, foto2]
    assert foto1.data_envio is not None
    assert str(foto1) == f"Comprovante OS-{ordem.numero_OS} ({foto1.id})"


@pytest.mark.django_db
def test_cascade_ao_excluir_ordem_remove_fotos(ordem):
    FotosOS.objects.create(ordem=ordem, imagem=gerar_imagem_teste())
    assert FotosOS.objects.count() == 1

    ordem.delete()
    assert FotosOS.objects.count() == 0



# 2. TESTES DO FORMULÁRIO (FotoOSForm)


def test_foto_form_valido():
    arquivo = gerar_imagem_teste()
    form = FotoOSForm(data={}, files={'imagem': arquivo})
    assert form.is_valid()


def test_foto_form_invalido_com_arquivo_nao_imagem():
    arquivo_txt = SimpleUploadedFile(
        'documento.txt',
        b'conteudo invalido que nao e imagem',
        content_type='text/plain',
    )
    form = FotoOSForm(data={}, files={'imagem': arquivo_txt})
    assert not form.is_valid()
    assert 'imagem' in form.errors



# 3. TESTES DA VIEW (anexar_foto)


@pytest.mark.django_db
def test_anexar_foto_exige_login(client, ordem):
    url = reverse('ordens:anexar_foto', args=[ordem.pk])
    response = client.post(url, {'imagem': gerar_imagem_teste()})

    assert response.status_code == 302
    assert FotosOS.objects.count() == 0


@pytest.mark.django_db
def test_anexar_foto_bloqueia_get(client, usuario, ordem):
    client.force_login(usuario)
    url = reverse('ordens:anexar_foto', args=[ordem.pk])
    response = client.get(url)

    assert response.status_code == 405


@pytest.mark.django_db
def test_anexar_foto_upload_tradicional_sucesso(client, usuario, ordem):
    client.force_login(usuario)
    url = reverse('ordens:anexar_foto', args=[ordem.pk])

    response = client.post(url, {'imagem': gerar_imagem_teste()})

    assert response.status_code == 302
    assert response.url == reverse('ordens:detalhe', args=[ordem.pk])
    assert ordem.fotos.count() == 1


@pytest.mark.django_db
def test_anexar_foto_ajax_sucesso(client, usuario, ordem):
    client.force_login(usuario)
    url = reverse('ordens:anexar_foto', args=[ordem.pk])

    response = client.post(
        url,
        {'imagem': gerar_imagem_teste()},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
    )

    assert response.status_code == 200
    dados = response.json()
    assert dados['success'] is True
    assert 'url' in dados['foto']
    assert 'data_envio' in dados['foto']
    assert ordem.fotos.count() == 1


@pytest.mark.django_db
def test_anexar_foto_ajax_erro_validacao(client, usuario, ordem):
    client.force_login(usuario)
    url = reverse('ordens:anexar_foto', args=[ordem.pk])

    response = client.post(
        url,
        {},  # Sem imagem
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
    )

    assert response.status_code == 400
    dados = response.json()
    assert dados['success'] is False
    assert 'imagem' in dados['errors']
    assert FotosOS.objects.count() == 0


@pytest.mark.django_db
def test_anexar_foto_ordem_inexistente_retorna_404(client, usuario):
    client.force_login(usuario)
    url = reverse('ordens:anexar_foto', args=[99999])

    response = client.post(url, {'imagem': gerar_imagem_teste()})
    assert response.status_code == 404

class FluxoExecucaoPrestadorTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()

        self.usuario_prestador = Usuario.objects.create_user(
            username='prestador_fluxo',
            email='prestador_fluxo@example.com',
            password='Senha@123',
            perfil='PRESTADOR',
        )

        self.usuario_outro_prestador = Usuario.objects.create_user(
            username='outro_prestador',
            email='outro_prestador@example.com',
            password='Senha@123',
            perfil='PRESTADOR',
        )

        self.usuario_admin = Usuario.objects.create_user(
            username='admin_fluxo',
            email='admin_fluxo@example.com',
            password='Senha@123',
            perfil='ADMINISTRADOR',
        )

        self.prestador = Prestador.objects.create(
            usuario=self.usuario_prestador,
            nome='Prestador do Fluxo',
            documento='FLUXO-001',
            telefone='(17) 90000-0001',
            email='prestador_fluxo@example.com',
        )

        self.outro_prestador = Prestador.objects.create(
            usuario=self.usuario_outro_prestador,
            nome='Outro Prestador',
            documento='FLUXO-002',
            telefone='(17) 90000-0002',
            email='outro_prestador@example.com',
        )

        self.ordem = OrdemServico.objects.create(
            data_prevista=timezone.localdate(),
            descricao='Manutenção de sinalização',
            endereco='Rua das Flores',
            numero_endereco='100',
            bairro='Centro',
            prestador=self.prestador,
            status=OrdemServico.Status.ABERTA,
        )

    def test_prestador_inicia_ordem_aberta(self):
        self.client.force_login(self.usuario_prestador)

        response = self.client.post(
            reverse('ordens:iniciar_servico', args=[self.ordem.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.ordem.refresh_from_db()
        self.assertEqual(
            self.ordem.status,
            OrdemServico.Status.EM_EXECUCAO,
        )

    def test_prestador_encaminha_ordem_para_analise(self):
        self.ordem.status = OrdemServico.Status.EM_EXECUCAO
        self.ordem.save()

        FotosOS.objects.create(
            ordem=self.ordem,
            imagem='comprovantes/teste_antes.jpg',
            tipo=FotosOS.Tipo.ANTES,
        )

        FotosOS.objects.create(
            ordem=self.ordem,
            imagem='comprovantes/teste_depois.jpg',
            tipo=FotosOS.Tipo.DEPOIS,
        )

        self.client.force_login(self.usuario_prestador)

        response = self.client.post(
            reverse('ordens:finalizar_servico', args=[self.ordem.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.ordem.refresh_from_db()
        self.assertEqual(
            self.ordem.status,
            OrdemServico.Status.EM_ANALISE,
        )

    def test_prestador_nao_inicia_ordem_de_outro_prestador(self):
        outra_ordem = OrdemServico.objects.create(
            data_prevista=timezone.localdate(),
            descricao='Ordem de outro prestador',
            endereco='Rua das Palmeiras',
            numero_endereco='200',
            bairro='Centro',
            prestador=self.outro_prestador,
        )

        self.client.force_login(self.usuario_prestador)

        response = self.client.post(
            reverse('ordens:iniciar_servico', args=[outra_ordem.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_administrador_nao_pode_usar_acoes_do_prestador(self):
        self.client.force_login(self.usuario_admin)

        response = self.client.post(
            reverse('ordens:iniciar_servico', args=[self.ordem.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_prestador_nao_pode_iniciar_ordem_com_status_diferente_de_aberta(self):
        self.ordem.status = OrdemServico.Status.EM_EXECUCAO
        self.ordem.save()

        self.client.force_login(self.usuario_prestador)

        response = self.client.post(
            reverse('ordens:iniciar_servico', args=[self.ordem.pk])
        )

        self.assertEqual(response.status_code, 400)
