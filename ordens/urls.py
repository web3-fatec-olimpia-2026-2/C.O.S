from django.urls import path
from . import views

app_name = 'ordens'

urlpatterns = [
    path('', views.listar_ordens, name='listar'),
    path('nova/', views.criar_ordem, name='criar'),
    path('<int:id>/editar/', views.editar_ordem, name='editar'),
    path('<int:id>/excluir/', views.excluir_ordem, name='excluir'),
]