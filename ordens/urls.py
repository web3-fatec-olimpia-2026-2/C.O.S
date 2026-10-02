from django.urls import path
from . import views

app_name = 'ordens'

urlpatterns = [
    path('', views.listar_ordens, name='listar'),
    path('nova/', views.criar_ordem, name='criar'),
    path('<int:pk>/editar/', views.editar_ordem, name='editar'),
    path('<int:pk>/excluir/', views.excluir_ordem, name='excluir'),
]