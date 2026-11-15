# Importa a função para renderizar templates HTML.
from django.contrib.auth import authenticate, login
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST

from ordens.forms import OrdemForm
from ordens.selectors import ordens_visiveis_para

# Garante que apenas usuários logados consigam acessar esta página.
@login_required
def pagina_inicial(request):
    """Página que aparece depois de logar"""
    # Renderiza a tela inicial e envia o usuário autenticado para o template.
    return render(
        request,
        'usuarios/home.html',
        {
            'usuario': request.user,
            'form': OrdemForm(),
            'ordens': ordens_visiveis_para(request.user).order_by('-id'),
        },
    )


@login_required
@require_POST
def entrar_com_outro_id(request):
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')

    usuario = authenticate(request, username=username, password=password)
    if usuario is None:
        return JsonResponse(
            {'success': False, 'error': 'Usuário ou senha inválidos.'},
            status=400,
        )

    login(request, usuario)
    return JsonResponse(
        {'success': True, 'redirect_url': reverse('pagina_inicial')}
    )
