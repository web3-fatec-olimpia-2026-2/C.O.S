from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone

from .forms import OrdemForm, FotoOSForm
from .models import OrdemServico
from .selectors import ordens_visiveis_para

def _dados_ordem(ordem):
    return {
        'pk': ordem.pk,
        'numero': ordem.numero_OS,
        'criada_em': timezone.localtime(ordem.criada_em).strftime('%d/%m/%Y %H:%M'),
        'entregue_em': (
            timezone.localtime(ordem.entregue_em).strftime('%d/%m/%Y %H:%M')
            if ordem.entregue_em
            else ''
        ),
        'descricao': ordem.descricao,
        'data_prevista': ordem.data_prevista.strftime('%d/%m/%Y'),
        'categoria': ordem.get_categoria_display(),
        'prioridade': ordem.get_prioridade_display(),
        'endereco': f'{ordem.endereco}, {ordem.numero_endereco} - {ordem.bairro}',
        'prestador': str(ordem.prestador) if ordem.prestador else 'Não atribuído',
        'status': ordem.get_status_display(),
        'editar_url': reverse('ordens:editar', args=[ordem.pk]),
        'excluir_url': reverse('ordens:excluir', args=[ordem.pk]),
    }


@login_required
def listar_ordens(request):
    ordens = ordens_visiveis_para(request.user)
    return render(request, "ordens/lista.html", {"ordens": ordens})


@login_required
def criar_ordem(request):
    form = OrdemForm(request.POST or None)
    if form.is_valid():
        ordem = form.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'ordem': _dados_ordem(ordem)})
        return redirect('pagina_inicial')
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'errors': form.errors.get_json_data()},
                status=400,
            )
        return render(
            request,
            'usuarios/home.html',
            {
                'usuario': request.user,
                'form': form,
                'abrir_popup': True,
                'ordens': ordens_visiveis_para(request.user).order_by('-id'),
            },
        )
    return render(request, "ordens/nova.html", {"form": form})


@login_required
def editar_ordem(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    if (
        request.method == 'GET'
        and request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    ):
        return JsonResponse({
            'success': True,
            'form': {
                'data_prevista': ordem.data_prevista.isoformat(),
                'descricao': ordem.descricao,
                'endereco': ordem.endereco,
                'numero_endereco': ordem.numero_endereco,
                'bairro': ordem.bairro,
                'complemento': ordem.complemento or '',
                'categoria': ordem.categoria,
                'prioridade': ordem.prioridade,
                'prestador': ordem.prestador_id or '',
                'status': ordem.status,
            },
            'numero': ordem.numero_OS,
        })

    form = OrdemForm(request.POST or None, instance=ordem)
    if form.is_valid():
        ordem = form.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'ordem': _dados_ordem(ordem)})
        return redirect('pagina_inicial')
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(
            {'success': False, 'errors': form.errors.get_json_data()},
            status=400,
        )
    return render(
        request,
        'usuarios/home.html',
        {
            'usuario': request.user,
            'form': form,
            'ordens': ordens_visiveis_para(request.user).order_by('-id'),
            'abrir_popup': True,
        },
    )


@login_required
def excluir_ordem(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)

    if request.method == "POST":
        ordem.delete()
        if request.headers.get("HX-Request") == "true":
            return HttpResponse(status=200)
        return redirect("ordens:listar")

    return render(request, "ordens/confirmar_excluir.html", {"ordem": ordem})

@login_required
@require_POST
def anexar_foto(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    form = FotoOSForm(request.POST, request.FILES)

    if form.is_valid():
        foto = form.save(commit=False)
        foto.ordem = ordem
        foto.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'foto': {
                    'id': foto.pk,
                    'url': foto.imagem.url,
                    'data_envio': timezone.localtime(foto.data_envio).strftime('%d/%m/%Y %H:%M'),
                }
            })
        return redirect('pagina_inicial')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(
            {'success': False, 'errors': form.errors.get_json_data()},
            status=400,
        )
    return redirect('pagina_inicial')


@login_required
@require_POST
def apagar_os_htmx(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    ordem.delete()
    return HttpResponse(status=200)


# ============================================================
# Tela administrativa de Ordens de Serviço (somente ADMINISTRADOR)
# ============================================================
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from usuarios.models import Prestador

_CATEGORIA_CURTA = {
    OrdemServico.Categoria.SINALIZACAO_HORIZONTAL: 'Horizontal',
    OrdemServico.Categoria.SINALIZACAO_VERTICAL: 'Vertical',
    OrdemServico.Categoria.SINALIZACAO_SEMAFORICA: 'Semafórica',
}


def _nome_curto_prestador(prestador):
    """Douglas Pereira -> Douglas P. (como no mockup)."""
    if not prestador:
        return 'Não atribuído'
    partes = prestador.nome.strip().split()
    if len(partes) == 1:
        return partes[0]
    return f"{partes[0]} {partes[-1][:1]}."


@login_required
def listar_ordens_admin(request):
    """Painel administrativo: lista completa de O.S. com busca, filtros e paginação.
    Acesso restrito ao perfil ADMINISTRADOR."""
    if request.user.perfil != 'ADMINISTRADOR':
        raise PermissionDenied('Acesso restrito a administradores.')

    busca = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    prestador_id = request.GET.get('prestador', '').strip()

    ordens = OrdemServico.objects.select_related('prestador').order_by('-id')

    if busca:
        ordens = ordens.filter(
            Q(descricao__icontains=busca)
            | Q(endereco__icontains=busca)
            | Q(bairro__icontains=busca)
            | Q(numero_OS__icontains=busca)
        )
    if status:
        ordens = ordens.filter(status=status)
    if prestador_id:
        ordens = ordens.filter(prestador_id=prestador_id)

    paginador = Paginator(ordens, 10)
    pagina = paginador.get_page(request.GET.get('pagina'))

    for ordem in pagina.object_list:
        ordem.categoria_curta = _CATEGORIA_CURTA.get(
            ordem.categoria, ordem.get_categoria_display()
        )
        ordem.prestador_curto = _nome_curto_prestador(ordem.prestador)

    params = request.GET.copy()
    params.pop('pagina', None)
    query_base = params.urlencode()

    return render(request, 'ordens/admin_lista.html', {
        'usuario': request.user,
        'page_obj': pagina,
        'paginator': paginador,
        'is_paginated': pagina.has_other_pages(),
        'status_opcoes': OrdemServico.Status.choices,
        'prestadores': Prestador.objects.filter(status=True).order_by('nome'),
        'filtro': {'q': busca, 'status': status, 'prestador': prestador_id},
        'query_base': query_base,
        'total': paginador.count,
    })
# ============================================================
# Fluxo de execução da Ordem de Serviço (PRESTADOR)
# ============================================================

@login_required
@require_POST
def iniciar_servico(request, pk):
    """Permite ao prestador responsável iniciar uma O.S. aberta."""

    if request.user.perfil != 'PRESTADOR':
        raise PermissionDenied('Ação permitida somente para prestadores.')

    ordem = get_object_or_404(
        OrdemServico,
        pk=pk,
        prestador__usuario=request.user,
        prestador__status=True,
    )

    if ordem.status != OrdemServico.Status.ABERTA:
        return HttpResponse(status=400)

    ordem.status = OrdemServico.Status.EM_EXECUCAO
    ordem.save(update_fields=['status'])

    return redirect('ordens:listar')


@login_required
@require_POST
def finalizar_servico(request, pk):
    """Encaminha a O.S. em execução para análise administrativa."""

    if request.user.perfil != 'PRESTADOR':
        raise PermissionDenied('Ação permitida somente para prestadores.')

    ordem = get_object_or_404(
        OrdemServico,
        pk=pk,
        prestador__usuario=request.user,
        prestador__status=True,
    )

    if ordem.status != OrdemServico.Status.EM_EXECUCAO:
        return HttpResponse(status=400)

    ordem.status = OrdemServico.Status.EM_ANALISE
    ordem.save(update_fields=['status'])

    return redirect('ordens:listar')
