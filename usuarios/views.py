# Importa a função para renderizar templates HTML.
from django.shortcuts import render

# Importa o decorador que bloqueia acesso a usuários não autenticados.
from django.contrib.auth.decorators import login_required

# Garante que apenas usuários logados consigam acessar esta página.
@login_required
def pagina_inicial(request):
    """Página que aparece depois de logar"""
    # Renderiza a tela inicial e envia o usuário autenticado para o template.
    return render(request, 'usuarios/home.html', {'usuario': request.user})