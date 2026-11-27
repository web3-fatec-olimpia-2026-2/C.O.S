from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Prestador


class UsuarioAuthTests(TestCase):
    def test_tela_login_exibe_marca_responsiva_e_controle_de_senha(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Controle de Ordens de Serviço')
        self.assertContains(response, 'Use seu usuário ou, se for prestador, o seu documento.')
        self.assertContains(response, 'logo-mobile')
        self.assertContains(response, 'class="alternar-senha"')
        self.assertContains(response, 'static/css/login.css')
        self.assertContains(response, 'static/js/login.js')

    def test_django_admin_disponibiliza_perfil_e_vinculo_de_prestador(self):
        administrador = get_user_model().objects.create_superuser(
            username='admin-configuracao',
            email='admin-configuracao@example.com',
            password='SenhaAdmin@123',
        )
        self.client.force_login(administrador)

        resposta_usuario = self.client.get(
            reverse('admin:usuarios_usuario_add')
        )
        resposta_prestador = self.client.get(
            reverse('admin:usuarios_prestador_add')
        )

        self.assertEqual(resposta_usuario.status_code, 200)
        self.assertContains(resposta_usuario, 'name="perfil"')
        self.assertEqual(resposta_prestador.status_code, 200)
        self.assertContains(resposta_prestador, 'name="usuario"')

    def test_administrador_continua_entrando_com_usuario_e_senha(self):
        administrador = get_user_model().objects.create_user(
            username='administrador-teste',
            email='administrador@example.com',
            password='SenhaAdmin@123',
            perfil='ADMINISTRADOR',
        )

        response = self.client.post(
            reverse('login'),
            {'username': 'administrador-teste', 'password': 'SenhaAdmin@123'},
        )

        self.assertRedirects(response, reverse('pagina_inicial'))
        self.assertEqual(
            self.client.get(reverse('pagina_inicial')).wsgi_request.user,
            administrador,
        )

    def test_pagina_inicial_requer_autenticacao(self):
        response = self.client.get(reverse('pagina_inicial'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('pagina_inicial')}")

    def test_sair_encerrar_sessao_e_redirecionar_para_login(self):
        usuario = get_user_model().objects.create_user(
            username='usuario-teste',
            password='Senha@123',
        )
        self.client.force_login(usuario)

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_entrar_com_outro_id_troca_conta_somente_apos_autenticacao(self):
        usuario_atual = get_user_model().objects.create_user(
            username='usuario-atual',
            email='usuario-atual@example.com',
            password='Senha@123',
        )
        outro_usuario = get_user_model().objects.create_user(
            username='outro-usuario',
            email='outro-usuario@example.com',
            password='OutraSenha@123',
        )
        self.client.force_login(usuario_atual)

        response = self.client.post(
            reverse('entrar_com_outro_id'),
            {'username': 'outro-usuario', 'password': 'SenhaErrada'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertEqual(self.client.get(reverse('pagina_inicial')).wsgi_request.user, usuario_atual)

        response = self.client.post(
            reverse('entrar_com_outro_id'),
            {'username': 'outro-usuario', 'password': 'OutraSenha@123'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['redirect_url'], reverse('pagina_inicial'))
        self.assertEqual(self.client.get(reverse('pagina_inicial')).wsgi_request.user, outro_usuario)

    def test_prestador_pode_entrar_com_documento_e_senha(self):
        usuario_prestador = get_user_model().objects.create_user(
            username='prestador-teste',
            email='prestador@example.com',
            password='SenhaPrestador@123',
            perfil='PRESTADOR',
        )
        Prestador.objects.create(
            usuario=usuario_prestador,
            nome='Prestador de teste',
            documento='123.456.789-00',
            telefone='(17) 90000-0000',
            email='prestador@example.com',
        )

        response = self.client.post(
            reverse('login'),
            {'username': '123.456.789-00', 'password': 'SenhaPrestador@123'},
        )

        self.assertRedirects(response, reverse('pagina_inicial'))
        self.assertEqual(
            self.client.get(reverse('pagina_inicial')).wsgi_request.user,
            usuario_prestador,
        )

    def test_documento_nao_autentica_prestador_sem_vinculo_ou_inativo(self):
        usuario_sem_vinculo = get_user_model().objects.create_user(
            username='sem-vinculo',
            email='sem-vinculo@example.com',
            password='SenhaPrestador@123',
            perfil='PRESTADOR',
        )
        Prestador.objects.create(
            nome='Prestador sem vínculo',
            documento='111.111.111-11',
            telefone='(17) 90000-0001',
            email='sem-vinculo@example.com',
        )
        usuario_inativo = get_user_model().objects.create_user(
            username='prestador-inativo',
            email='prestador-inativo@example.com',
            password='SenhaPrestador@123',
            perfil='PRESTADOR',
        )
        Prestador.objects.create(
            usuario=usuario_inativo,
            nome='Prestador inativo',
            documento='222.222.222-22',
            telefone='(17) 90000-0002',
            email='prestador-inativo@example.com',
            status=False,
        )

        for documento in ('111.111.111-11', '222.222.222-22'):
            response = self.client.post(
                reverse('login'),
                {'username': documento, 'password': 'SenhaPrestador@123'},
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Usuário ou senha inválidos')

        self.assertTrue(usuario_sem_vinculo.check_password('SenhaPrestador@123'))

    def test_entrar_com_outro_id_aceita_documento_de_prestador_vinculado(self):
        usuario_atual = get_user_model().objects.create_user(
            username='usuario-atual',
            email='usuario-atual@example.com',
            password='SenhaAtual@123',
        )
        usuario_prestador = get_user_model().objects.create_user(
            username='prestador-teste',
            email='prestador@example.com',
            password='SenhaPrestador@123',
            perfil='PRESTADOR',
        )
        Prestador.objects.create(
            usuario=usuario_prestador,
            nome='Prestador de teste',
            documento='123.456.789-00',
            telefone='(17) 90000-0000',
            email='prestador@example.com',
        )
        self.client.force_login(usuario_atual)

        response = self.client.post(
            reverse('entrar_com_outro_id'),
            {'username': '123.456.789-00', 'password': 'SenhaPrestador@123'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(
            self.client.get(reverse('pagina_inicial')).wsgi_request.user,
            usuario_prestador,
        )


class CadastroUsuarioTests(TestCase):
    """Auto-cadastro de usuários comuns na tela pública."""

    def test_tela_cadastro_aberta_para_visitante(self):
        response = self.client.get(reverse('cadastro'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Criar conta')
        self.assertContains(response, 'name="password2"')
        

    def test_cadastro_valido_cria_usuario_comum_e_autentica(self):
        response = self.client.post(
            reverse('cadastro'),
            {
            'username': 'novousuario',
            'first_name': 'Novo',
            'last_name': 'Usuario',
            'email': 'novousuario@example.com',
            'password1': 'SenhaForte@123',     
            'password2': 'SenhaForte@123',
        }
        )

        self.assertRedirects(response, reverse('pagina_inicial'))
        usuario = get_user_model().objects.get(username='novousuario')
        self.assertTrue(usuario.check_password('SenhaForte@123'))
        self.assertEqual(usuario.perfil, 'COMUM')
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)

    def test_cadastro_rejeita_senhas_diferentes(self):
        response = self.client.post(
            reverse('cadastro'),
            {
            'username': 'senhadiferente',
            'email': 'senha.diferente@example.com',
            'password1': 'SenhaForte@123',     
            'password2': 'OutaSenhaForte@123',
        },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(username='senhadiferente').exists()
        )

    def test_cadastro_rejeita_email_duplicado(self):
        get_user_model().objects.create_user(
            username='existente',
            email='repetido@example.com',
            password='SenhaExistente@123',
        )

        response = self.client.post(
            reverse('cadastro'),
            {
                'username': 'novooutro',
                'email': 'repetido@example.com',
                'password': 'SenhaForte@123',
                'password2': 'SenhaForte@123',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(username='novooutro').exists()
        )


class AreaAdministrativaTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username='admin-area',
            email='admin-area@example.com',
            password='SenhaAdmin@123',
            perfil='ADMINISTRADOR',
        )
        self.client.force_login(self.admin)

    def test_navegacao_admin_abre_usuarios_relatorios_e_configuracoes(self):
        for nome, item, template in (
            ('usuarios_admin', 'Usuários', 'usuarios/admin_usuarios.html'),
            ('relatorios_admin', 'Relatórios', 'usuarios/admin_relatorios.html'),
            ('configuracoes_admin', 'Configurações', 'usuarios/admin_configuracoes.html'),
        ):
            with self.subTest(pagina=nome):
                resposta = self.client.get(reverse(nome))
                self.assertEqual(resposta.status_code, 200)
                self.assertTemplateUsed(resposta, template)
                self.assertContains(resposta, f'aria-current="page"')
                self.assertContains(resposta, item)

    def test_nao_administrador_nao_acessa_telas_administrativas(self):
        usuario = get_user_model().objects.create_user(
            username='usuario-comum-admin',
            email='usuario-comum-admin@example.com',
            password='Senha@123',
            perfil='COMUM',
        )
        self.client.force_login(usuario)

        for nome in ('usuarios_admin', 'relatorios_admin', 'configuracoes_admin'):
            with self.subTest(pagina=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 403)

    def test_configuracoes_cadastra_usuario_comum_com_senha_segura(self):
        resposta = self.client.post(
            reverse('configuracoes_admin'),
            {
                'username': 'novo-comum',
                'first_name': 'Novo',
                'last_name': 'Comum',
                'email': 'novo-comum@example.com',
                'perfil': 'COMUM',
                'password': 'SenhaForte@123',
                'password2': 'SenhaForte@123',
                'documento': '',
                'telefone': '',
            },
        )

        self.assertEqual(
            resposta.status_code, 
            302, 
        f"Falha no cadastro. Resposta: {resposta.content.decode()}"
        )
        usuario = get_user_model().objects.get(username='novo-comum')
        self.assertRedirects(resposta, reverse('usuarios_admin'))
        self.assertTrue(usuario.check_password('SenhaForte@123'))
        self.assertEqual(usuario.perfil, 'COMUM')
        self.assertFalse(Prestador.objects.filter(usuario=usuario).exists())

    def test_configuracoes_cria_perfil_de_prestador_vinculado(self):
        resposta = self.client.post(
            reverse('configuracoes_admin'),
            {
                'username': 'novo-prestador',
                'first_name': 'Novo',
                'last_name': 'Prestador',
                'email': 'novo-prestador@example.com',
                'perfil': 'PRESTADOR',
                'password': 'SenhaForte@123',
                'password2': 'SenhaForte@123',
                'documento': 'DOC-NOVO-PRESTADOR-01',
                'telefone': '(17) 90000-0000',
            },
        )

        self.assertEqual(
            resposta.status_code, 
            302, 
            f"Falha no cadastro. Resposta: {resposta.content.decode()}"
    )

        usuario = get_user_model().objects.get(username='novo-prestador')
        self.assertRedirects(resposta, reverse('usuarios_admin'))
        self.assertEqual(usuario.perfil, 'PRESTADOR')
        prestador = Prestador.objects.get(usuario=usuario)
        self.assertEqual(prestador.nome, 'Novo Prestador')
        self.assertEqual(prestador.documento, 'DOC-NOVO-PRESTADOR-01')

    def test_relatorio_apresenta_metricas_agregadas(self):
        from ordens.models import OrdemServico

        OrdemServico.objects.create(
            data_prevista='2026-12-01',
            descricao='Ordem do relatório',
            endereco='Rua Teste',
            numero_endereco='1',
            bairro='Centro',
            status=OrdemServico.Status.EM_ANALISE,
        )

        resposta = self.client.get(reverse('relatorios_admin'))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context['metricas']['total'], 1)
        self.assertEqual(resposta.context['metricas']['em_analise'], 1)
        self.assertContains(resposta, 'Relatório geral')
        self.assertContains(resposta, 'Sinalização horizontal')

    def test_dashboard_administrativo_filtra_ordens_e_preserva_retorno_do_detalhe(self):
        from ordens.models import OrdemServico

        ordem_aberta = OrdemServico.objects.create(
            data_prevista='2026-12-01',
            descricao='Ordem aberta global',
            endereco='Rua Teste',
            numero_endereco='1',
            bairro='Centro',
        )
        ordem_em_analise = OrdemServico.objects.create(
            data_prevista='2026-12-01',
            descricao='Ordem em análise global',
            endereco='Rua Teste',
            numero_endereco='2',
            bairro='Centro',
            status=OrdemServico.Status.EM_ANALISE,
        )

        resposta = self.client.get(reverse('relatorios_admin'))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context['metricas']['total'], 2)
        self.assertEqual(resposta.context['page_obj'].paginator.count, 2)
        self.assertTrue(
            hasattr(resposta.context['page_obj'].object_list[0], 'relatorio_detalhe_url')
        )

        query = urlencode({
            'status': OrdemServico.Status.EM_ANALISE,
            'pagina': '1',
        })
        resposta_filtrada = self.client.get(f'{reverse("relatorios_admin")}?{query}')

        self.assertEqual(resposta_filtrada.status_code, 200)
        self.assertEqual(resposta_filtrada.context['metricas']['total'], 2)
        self.assertEqual(resposta_filtrada.context['page_obj'].paginator.count, 1)
        ordem_filtrada = resposta_filtrada.context['page_obj'].object_list[0]
        self.assertEqual(ordem_filtrada.pk, ordem_em_analise.pk)

        detalhe = self.client.get(ordem_filtrada.relatorio_detalhe_url)

        self.assertEqual(detalhe.status_code, 200)
        self.assertEqual(
            detalhe.context['voltar_url'],
            f'{reverse("relatorios_admin")}?{urlencode({"pagina": "1", "status": OrdemServico.Status.EM_ANALISE})}',
        )
        self.assertNotEqual(ordem_filtrada.pk, ordem_aberta.pk)

    def test_prestador_visualiza_dashboard_com_suas_ordens_e_filtros_clicaveis(self):
        from ordens.models import OrdemServico

        prestador_user = get_user_model().objects.create_user(
            username='prestador-dashboard',
            email='prestador-dashboard@example.com',
            password='SenhaPrestador@123',
            perfil='PRESTADOR',
        )
        prestador = Prestador.objects.create(
            usuario=prestador_user,
            nome='Prestador do painel',
            documento='DOC-PRESTADOR-DASHBOARD',
            telefone='(17) 90000-0100',
            email='prestador-dashboard@example.com',
        )
        outro_usuario = get_user_model().objects.create_user(
            username='outro-prestador-dashboard',
            email='outro-prestador-dashboard@example.com',
            password='SenhaPrestador@123',
            perfil='PRESTADOR',
        )
        outro_prestador = Prestador.objects.create(
            usuario=outro_usuario,
            nome='Outro prestador',
            documento='DOC-OUTRO-DASHBOARD',
            telefone='(17) 90000-0101',
            email='outro-dashboard@example.com',
        )
        estados = (
            OrdemServico.Status.ABERTA,
            OrdemServico.Status.EM_EXECUCAO,
            OrdemServico.Status.EM_ANALISE,
            OrdemServico.Status.CONCLUIDA,
        )
        for indice, estado in enumerate(estados):
            OrdemServico.objects.create(
                data_prevista='2026-12-01',
                descricao=f'Ordem do painel {indice}',
                endereco='Rua Teste',
                numero_endereco=str(indice + 1),
                bairro='Centro',
                status=estado,
                prestador=prestador,
            )
        OrdemServico.objects.create(
            data_prevista='2026-12-01',
            descricao='Ordem privada de outro prestador',
            endereco='Rua Privada',
            numero_endereco='99',
            bairro='Centro',
            prestador=outro_prestador,
        )
        self.client.force_login(prestador_user)

        resposta = self.client.get(reverse('relatorios_admin'))

        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, 'usuarios/prestador_relatorios.html')
        self.assertEqual(resposta.context['metricas']['total'], 4)
        self.assertEqual(resposta.context['metricas']['abertas'], 1)
        self.assertEqual(resposta.context['metricas']['em_execucao'], 1)
        self.assertEqual(resposta.context['metricas']['em_analise'], 1)
        self.assertEqual(resposta.context['metricas']['concluidas'], 1)
        self.assertEqual(len(resposta.context['status_cards']), 5)
        self.assertContains(resposta, 'Ordens por status')
        self.assertContains(resposta, 'Ordens cadastradas')
        self.assertContains(resposta, 'Ordem do painel 0')
        self.assertNotContains(resposta, 'Ordem privada de outro prestador')
        self.assertNotContains(resposta, '>Menus<')

        card_abertas = next(
            card for card in resposta.context['status_cards']
            if card['valor'] == OrdemServico.Status.ABERTA
        )
        self.assertContains(resposta, f'href="{card_abertas["url"]}"')
        resposta_filtrada = self.client.get(
            card_abertas['url'],
        )
        self.assertEqual(resposta_filtrada.status_code, 200)
        self.assertEqual(resposta_filtrada.context['metricas']['total'], 4)
        self.assertEqual(resposta_filtrada.context['page_obj'].paginator.count, 1)
        self.assertContains(resposta_filtrada, 'Ordem do painel 0')
        self.assertNotContains(resposta_filtrada, 'Ordem do painel 1')
