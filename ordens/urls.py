
from django.urls import path
from . import views

app_name = 'ordens'

urlpatterns = [
    path('', views.listar_ordens, name='listar'),
    path('admin/', views.listar_ordens_admin, name='listar_admin'),
    path('nova/', views.criar_ordem, name='criar'),
    path('<int:pk>/editar/', views.editar_ordem, name='editar'),
    path('<int:pk>/excluir/', views.excluir_ordem, name='excluir'),
    path('<int:pk>/apagar/', views.apagar_os_htmx, name='apagar_os_htmx'),
    path('<int:pk>/anexar-foto/', views.anexar_foto, name='anexar_foto'),
    path('<int:pk>/iniciar/', views.iniciar_servico, name='iniciar_servico'),
    path('<int:pk>/finalizar/', views.finalizar_servico, name='finalizar_servico'),
    path('<int:pk>/enviar-aprovacao/', views.enviar_para_aprovacao, name='enviar_aprovacao'),
    path('<int:pk>/aprovar/', views.aprovar_os, name='aprovar'),
    path('<int:pk>/reprovar/', views.reprovar_os, name='reprovar'),
    path('<int:pk>/pdf/', views.os_pdf, name='pdf'),
    path('<int:pk>/', views.detalhe_ordem, name='detalhe'),
]
