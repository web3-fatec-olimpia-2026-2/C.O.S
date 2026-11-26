# Importa a função para renderizar templates HTML.
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q

from .forms import CadastroUsuarioForm
from ordens.forms import OrdemForm
from ordens.models import OrdemServico
from ordens.selectors import ordens_visiveis_para

# Garante que apenas usuários logados consigam acessar esta página.
# Assistido por IA (Claude): "métricas agregadas por status na home"
@login_required
def pagina_inicial(request):
    """Página que aparece depois de logar"""
    ordens = ordens_visiveis_para(request.user)
    metricas = ordens.aggregate(
        total=Count('pk'),
        abertas=Count('pk', filter=Q(status=OrdemServico.Status.ABERTA)),
        em_execucao=Count('pk', filter=Q(status=OrdemServico.Status.EM_EXECUCAO)),
        em_analise=Count('pk', filter=Q(status=OrdemServico.Status.EM_ANALISE)),
        concluidas=Count('pk', filter=Q(status=OrdemServico.Status.CONCLUIDA)),
    )
    # Renderiza a tela inicial e envia o usuário, a lista e as métricas ao template.
    return render(
        request,
        'usuarios/home.html',
        {
            'usuario': request.user,
            'form': OrdemForm(),
            'ordens': ordens.order_by('-id'),
            'metricas': metricas,
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


def cadastro(request):
    if request.user.is_authenticated:
        return redirect('pagina_inicial')

    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect(f"{reverse('login')}?cadastro=sucesso")
    else:
        form = CadastroUsuarioForm()

    return render(request, 'usuarios/cadastro.html', {
        'form': form
    })
