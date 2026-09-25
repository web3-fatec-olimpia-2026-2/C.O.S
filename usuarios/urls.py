from django.urls import path
from . import views

urlpatterns = [
    # ✅ Só a página depois de logar
    path('', views.pagina_inicial, name='pagina_inicial'),
]