from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone

from .forms import OrdemForm
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
def apagar_os_htmx(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    ordem.delete()
    return HttpResponse(status=204)
