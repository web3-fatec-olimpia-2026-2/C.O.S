from datetime import date, datetime, time, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.db.models.functions import TruncDate

from .forms import OrdemForm, FotoOSForm
from .models import OrdemServico, FotosOS
from .selectors import ordens_visiveis_para


def _verificar_acesso_ordens(request):
    if request.user.perfil == 'PRESTADOR':
        raise PermissionDenied('Prestadores não podem alterar ordens de serviço.')


def _ordem_visivel_para(request, pk):
    ordens = OrdemServico.objects.select_related('prestador').prefetch_related('fotos')
    if request.user.perfil == 'ADMINISTRADOR':
        return get_object_or_404(ordens, pk=pk)
    if request.user.perfil == 'PRESTADOR':
        return get_object_or_404(ordens.filter(prestador__usuario=request.user), pk=pk)
    raise PermissionDenied('Acesso restrito a administradores e prestadores da ordem.')


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
    _verificar_acesso_ordens(request)
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
    _verificar_acesso_ordens(request)
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


def _parametros_painel_admin(request):
    params = request.GET.copy()
    permitidos = {'q', 'status', 'prioridade', 'prestador', 'dia', 'pagina'}
    for chave in list(params):
        if chave not in permitidos:
            params.pop(chave, None)
    return params


def _url_painel_admin(request, manter_pagina=False, **alteracoes):
    params = _parametros_painel_admin(request)
    if not manter_pagina:
        params.pop('pagina', None)
    for chave, valor in alteracoes.items():
        if valor:
            params[chave] = valor
        else:
            params.pop(chave, None)

    url_admin = reverse('ordens:listar_admin')
    return f'{url_admin}?{params.urlencode()}' if params else url_admin


def _url_detalhe_admin(request, ordem_pk, pagina):
    params = _parametros_painel_admin(request)
    params['origem'] = 'admin'
    params['pagina'] = str(pagina)
    url_detalhe = reverse('ordens:detalhe', args=[ordem_pk])
    return f'{url_detalhe}?{params.urlencode()}'


def _url_retorno_detalhe(request):
    if (
        request.user.perfil != 'ADMINISTRADOR'
        or request.GET.get('origem') != 'admin'
    ):
        return reverse('pagina_inicial')

    return _url_painel_admin(request, manter_pagina=True)


def _contexto_detalhe(ordem, request, form=None, erro_foto=None):
    """Monta o contexto da tela de detalhe (usado pela view e por erro de upload)."""
    fotos_antes = list(ordem.fotos.filter(tipo=FotosOS.Tipo.ANTES).order_by('data_envio'))
    fotos_depois = list(ordem.fotos.filter(tipo=FotosOS.Tipo.DEPOIS).order_by('data_envio'))
    status_aberto = ordem.status in (
        OrdemServico.Status.ABERTA, OrdemServico.Status.EM_EXECUCAO
    )
    eh_prestador = request.user.perfil == 'PRESTADOR'
    return {
        'ordem': ordem,
        'voltar_url': _url_retorno_detalhe(request),
        'form': form or FotoOSForm(),
        'erro_foto': erro_foto,
        'fotos_antes': fotos_antes,
        'fotos_depois': fotos_depois,
        'qtd_antes': len(fotos_antes),
        'qtd_depois': len(fotos_depois),
        'pode_enviar_fotos': eh_prestador and status_aberto,
        'pode_enviar_aprovacao': (
            eh_prestador and status_aberto and bool(fotos_antes) and bool(fotos_depois)
        ),
        'mostrar_aprovacao_admin': (
            request.user.perfil == 'ADMINISTRADOR'
            and ordem.status == OrdemServico.Status.EM_ANALISE
        ),
    }


@login_required
def detalhe_ordem(request, pk):
    ordem = _ordem_visivel_para(request, pk)
    return render(request, 'ordens/detalhe.html', _contexto_detalhe(ordem, request))


@login_required
def excluir_ordem(request, pk):
    _verificar_acesso_ordens(request)
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
    ordem = _ordem_visivel_para(request, pk)

    if request.user.perfil != 'PRESTADOR':
        raise PermissionDenied('Apenas o prestador pode enviar fotos da O.S.')

    status_liberado = ordem.status in (
        OrdemServico.Status.ABERTA, OrdemServico.Status.EM_EXECUCAO
    )
    if not status_liberado:
        erro = (
            f'Esta O.S. está com status "{ordem.get_status_display()}" e '
            'não aceita mais envio de fotos.'
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'errors': {'imagem': [{'message': erro}]}},
                status=400,
            )
        return render(
            request, 'ordens/detalhe.html',
            _contexto_detalhe(ordem, request, erro_foto=erro),
            status=400,
        )

    tipo = request.POST.get('tipo', '').strip().upper()
    if tipo not in (FotosOS.Tipo.ANTES, FotosOS.Tipo.DEPOIS):
        tipo = FotosOS.Tipo.DEPOIS

    form = FotoOSForm(request.POST, request.FILES)

    if form.is_valid():
        foto = form.save(commit=False)
        foto.ordem = ordem
        foto.tipo = tipo
        foto.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'foto': {
                    'id': foto.pk,
                    'tipo': foto.tipo,
                    'url': foto.imagem.url,
                    'data_envio': timezone.localtime(foto.data_envio).strftime('%d/%m/%Y %H:%M'),
                }
            })
        messages.success(request, f'Foto {foto.get_tipo_display()} enviada com sucesso.')
        return redirect('ordens:detalhe', pk=ordem.pk)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(
            {'success': False, 'errors': form.errors.get_json_data()},
            status=400,
        )
    return render(
        request, 'ordens/detalhe.html',
        _contexto_detalhe(ordem, request, form=form),
        status=400,
    )


@login_required
@require_POST
def apagar_os_htmx(request, pk):
    _verificar_acesso_ordens(request)
    ordem = get_object_or_404(OrdemServico, pk=pk)
    ordem.delete()
    return HttpResponse(status=200)


# ============================================================
# Tela administrativa de Ordens de Serviço (somente ADMINISTRADOR)
# ============================================================
from django.core.paginator import Paginator
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
    prioridade = request.GET.get('prioridade', '').strip()
    prestador_id = request.GET.get('prestador', '').strip()
    dia_parametro = request.GET.get('dia', '').strip()
    try:
        dia_selecionado = date.fromisoformat(dia_parametro) if dia_parametro else None
    except ValueError:
        return HttpResponseBadRequest('A data selecionada é inválida.')

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
    if prioridade:
        ordens = ordens.filter(prioridade=prioridade)
    if prestador_id:
        ordens = ordens.filter(prestador_id=prestador_id)

    ordens_sem_data_selecionada = ordens
    if dia_selecionado:
        ordens = ordens.filter(criada_em__date=dia_selecionado)

    metricas = ordens.aggregate(
        total=Count('pk'),
        aberta=Count('pk', filter=Q(status=OrdemServico.Status.ABERTA)),
        execucao=Count('pk', filter=Q(status=OrdemServico.Status.EM_EXECUCAO)),
        analise=Count('pk', filter=Q(status=OrdemServico.Status.EM_ANALISE)),
        concluida=Count('pk', filter=Q(status=OrdemServico.Status.CONCLUIDA)),
    )
    inicio_semana = timezone.localdate() - timedelta(days=6)
    inicio_periodo = timezone.make_aware(
        datetime.combine(inicio_semana, time.min),
        timezone.get_current_timezone(),
    )
    fim_periodo = timezone.make_aware(
        datetime.combine(timezone.localdate() + timedelta(days=1), time.min),
        timezone.get_current_timezone(),
    )
    ordens_por_dia = {
        item['dia']: item['quantidade']
        for item in ordens_sem_data_selecionada.filter(
            criada_em__gte=inicio_periodo,
            criada_em__lt=fim_periodo,
        ).annotate(
            dia=TruncDate('criada_em', tzinfo=timezone.get_current_timezone())
        ).values('dia').annotate(quantidade=Count('pk'))
    }
    dias_semana = []
    pico_semana = max(ordens_por_dia.values(), default=0)
    nomes_dias = ('seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom')
    for deslocamento in range(7):
        dia = inicio_semana + timedelta(days=deslocamento)
        quantidade = ordens_por_dia.get(dia, 0)
        dias_semana.append({
            'data': dia.strftime('%d/%m'),
            'iso': dia.isoformat(),
            'semana': nomes_dias[dia.weekday()],
            'quantidade': quantidade,
            'percentual': max(8, round(quantidade / pico_semana * 100)) if pico_semana else 8,
            'selecionado': dia == dia_selecionado,
            'url': _url_painel_admin(
                request,
                dia=None if dia == dia_selecionado else dia.isoformat(),
            ),
        })

    total_status = metricas['total']
    divisor = total_status or 1
    status_chart = {
        'aberta_fim': round(metricas['aberta'] / divisor * 100),
        'execucao_fim': round(
            (metricas['aberta'] + metricas['execucao']) / divisor * 100
        ),
        'analise_fim': round(
            (
                metricas['aberta']
                + metricas['execucao']
                + metricas['analise']
            ) / divisor * 100
        ),
    }
    status_cards = []
    for chave, rotulo, icone, classe, valor in (
        ('aberta', 'Abertas', '◯', 'aberta', OrdemServico.Status.ABERTA),
        ('execucao', 'Em execução', '▶', 'execucao', OrdemServico.Status.EM_EXECUCAO),
        ('analise', 'Em análise', '◉', 'analise', OrdemServico.Status.EM_ANALISE),
        ('concluida', 'Concluídas', '✓', 'concluida', OrdemServico.Status.CONCLUIDA),
    ):
        selecionado = status == valor
        status_cards.append({
            'chave': chave,
            'rotulo': rotulo,
            'icone': icone,
            'classe': classe,
            'quantidade': metricas[chave],
            'selecionado': selecionado,
            'url': _url_painel_admin(
                request,
                status=None if selecionado else valor,
            ),
        })

    paginador = Paginator(ordens, 10)
    pagina = paginador.get_page(request.GET.get('pagina'))

    for ordem in pagina.object_list:
        ordem.categoria_curta = _CATEGORIA_CURTA.get(
            ordem.categoria, ordem.get_categoria_display()
        )
        ordem.prestador_curto = _nome_curto_prestador(ordem.prestador)
        ordem.detalhe_admin_url = _url_detalhe_admin(
            request,
            ordem.pk,
            pagina.number,
        )

    params = request.GET.copy()
    params.pop('pagina', None)
    query_base = params.urlencode()

    return render(request, 'ordens/admin_lista.html', {
        'usuario': request.user,
        'page_obj': pagina,
        'paginator': paginador,
        'is_paginated': pagina.has_other_pages(),
        'status_opcoes': OrdemServico.Status.choices,
        'prioridade_opcoes': OrdemServico.Prioridade.choices,
        'prestadores': Prestador.objects.filter(status=True).order_by('nome'),
        'filtro': {
            'q': busca,
            'status': status,
            'prioridade': prioridade,
            'prestador': prestador_id,
            'dia': dia_selecionado.isoformat() if dia_selecionado else '',
        },
        'query_base': query_base,
        'total': paginador.count,
        'metricas': metricas,
        'status_cards': status_cards,
        'dias_semana': dias_semana,
        'total_semana': sum(dia['quantidade'] for dia in dias_semana),
        'status_chart': status_chart,
        'url_limpar_filtros': _url_painel_admin(
            request,
            q=None,
            status=None,
            prioridade=None,
            prestador=None,
            dia=None,
        ),
        'tem_filtros': bool(busca or status or prioridade or prestador_id or dia_selecionado),
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

    tem_antes = ordem.fotos.filter(tipo=FotosOS.Tipo.ANTES).exists()
    tem_depois = ordem.fotos.filter(tipo=FotosOS.Tipo.DEPOIS).exists()

    if not (tem_antes and tem_depois):
        messages.error(
            request,
            'Para finalizar são necessárias pelo menos uma foto ANTES '
            'e uma foto DEPOIS do serviço.'
        )
        return redirect('ordens:detalhe', pk=ordem.pk)

    ordem.status = OrdemServico.Status.EM_ANALISE
    ordem.motivo_reprovacao = ''
    ordem.save(update_fields=['status', 'motivo_reprovacao'])

    messages.success(
        request,
        f'O.S. {ordem.numero_OS} enviada para análise da administração.'
    )

    return redirect('ordens:detalhe', pk=ordem.pk)


# ============================================================
# Fluxo de aprovação: prestador envia para análise / admin decide
# ============================================================
@login_required
@require_POST
def enviar_para_aprovacao(request, pk):
    """Prestador finaliza o atendimento e envia a O.S. para análise administrativa.
    Exige pelo menos uma foto ANTES e uma foto DEPOIS."""
    ordem = _ordem_visivel_para(request, pk)

    if request.user.perfil != 'PRESTADOR':
        raise PermissionDenied('Apenas o prestador pode enviar a O.S. para aprovação.')

    if ordem.status not in (OrdemServico.Status.ABERTA, OrdemServico.Status.EM_EXECUCAO):
        messages.error(request, 'Esta O.S. não pode ser enviada para análise no status atual.')
        return redirect('ordens:detalhe', pk=ordem.pk)

    tem_antes = ordem.fotos.filter(tipo=FotosOS.Tipo.ANTES).exists()
    tem_depois = ordem.fotos.filter(tipo=FotosOS.Tipo.DEPOIS).exists()
    if not (tem_antes and tem_depois):
        messages.error(
            request,
            'Para enviar para aprovação são necessárias pelo menos uma foto ANTES '
            'e uma foto DEPOIS do serviço.'
        )
        return redirect('ordens:detalhe', pk=ordem.pk)

    ordem.status = OrdemServico.Status.EM_ANALISE
    ordem.motivo_reprovacao = ''
    ordem.save(update_fields=['status', 'motivo_reprovacao'])
    messages.success(
        request,
        f'O.S. {ordem.numero_OS} enviada para análise da administração. '
        'As fotos não podem mais ser alteradas.'
    )
    return redirect('ordens:detalhe', pk=ordem.pk)


@login_required
@require_POST
def aprovar_os(request, pk):
    """Administrador aprova a O.S. em análise e a marca como concluída."""
    if request.user.perfil != 'ADMINISTRADOR':
        raise PermissionDenied('Acesso restrito a administradores.')

    ordem = get_object_or_404(OrdemServico, pk=pk)

    if ordem.status != OrdemServico.Status.EM_ANALISE:
        messages.error(request, 'Esta O.S. não está em análise para ser aprovada.')
        return redirect('ordens:detalhe', pk=ordem.pk)

    ordem.status = OrdemServico.Status.CONCLUIDA
    ordem.motivo_reprovacao = ''
    ordem.save()
    messages.success(request, f'O.S. {ordem.numero_OS} aprovada e concluída com sucesso.')
    return redirect('ordens:detalhe', pk=ordem.pk)


@login_required
@require_POST
def reprovar_os(request, pk):
    """Administrador reprova a O.S. em análise e a devolve ao prestador (volta para execução)."""
    if request.user.perfil != 'ADMINISTRADOR':
        raise PermissionDenied('Acesso restrito a administradores.')

    ordem = get_object_or_404(OrdemServico, pk=pk)

    if ordem.status != OrdemServico.Status.EM_ANALISE:
        messages.error(request, 'Esta O.S. não está em análise para ser reprovada.')
        return redirect('ordens:detalhe', pk=ordem.pk)

    motivo = request.POST.get('motivo', '').strip()
    if not motivo:
        messages.error(request, 'Informe o motivo da reprovação para devolver ao prestador.')
        return redirect('ordens:detalhe', pk=ordem.pk)

    ordem.status = OrdemServico.Status.EM_EXECUCAO
    ordem.motivo_reprovacao = motivo
    ordem.save(update_fields=['status', 'motivo_reprovacao'])
    messages.success(
        request,
        f'O.S. {ordem.numero_OS} reprovada e devolvida ao prestador para ajustes.'
    )
    return redirect('ordens:detalhe', pk=ordem.pk)
