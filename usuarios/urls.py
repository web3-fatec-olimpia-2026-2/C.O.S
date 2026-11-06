from django.urls import path
from . import views

urlpatterns = [
    # ✅ Só a página depois de logar
    path('', views.pagina_inicial, name='pagina_inicial'),
    path('entrar-com-outro-id/', views.entrar_com_outro_id, name='entrar_com_outro_id'),
]