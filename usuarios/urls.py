from django.urls import path

from . import views

urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),
    path('entrar-com-outro-id/', views.entrar_com_outro_id, name='entrar_com_outro_id'),
    path('cadastro/', views.cadastrar_usuario, name='cadastro'),
    path('administracao/usuarios/', views.usuarios_admin, name='usuarios_admin'),
    path('administracao/relatorios/', views.relatorios_admin, name='relatorios_admin'),
    path('administracao/configuracoes/', views.configuracoes_admin, name='configuracoes_admin'),
]
