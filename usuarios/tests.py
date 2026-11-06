from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Prestador


class UsuarioAuthTests(TestCase):
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
