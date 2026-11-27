from datetime import datetime, time, timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CadastroUsuarioAdminForm, CadastroUsuarioForm
from ordens.forms import OrdemForm
from ordens.models import OrdemServico
from ordens.selectors import ordens_visiveis_para

from .models import Prestador, Usuario


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


def cadastrar_usuario(request):
    """Auto-cadastro de usuários comuns. Prestadores e admins são criados no Django admin."""
    if request.user.is_authenticated:
        return redirect('pagina_inicial')

    form = CadastroUsuarioForm(request.POST or None)
    if form.is_valid():
        usuario = form.save()
        login(request, usuario)
        return redirect('pagina_inicial')

    return render(request, 'usuarios/cadastro.html', {'form': form})


def _exigir_administrador(request):
    if request.user.perfil != 'ADMINISTRADOR':
        raise PermissionDenied('Acesso restrito a administradores.')


def _contexto_dashboard_ordens(request, ordens):
    ordens = ordens.order_by('-criada_em')
    hoje = timezone.localdate()
    metricas = ordens.aggregate(
        total=Count('pk'),
        abertas=Count('pk', filter=Q(status=OrdemServico.Status.ABERTA)),
        em_execucao=Count('pk', filter=Q(status=OrdemServico.Status.EM_EXECUCAO)),
        em_analise=Count('pk', filter=Q(status=OrdemServico.Status.EM_ANALISE)),
        concluidas=Count('pk', filter=Q(status=OrdemServico.Status.CONCLUIDA)),
        criadas_no_mes=Count('pk', filter=Q(criada_em__date__gte=hoje.replace(day=1))),
    )
    status_filtro = request.GET.get('status', '').strip()
    status_validos = {valor for valor, _ in OrdemServico.Status.choices}
    if status_filtro not in status_validos:
        status_filtro = ''

    url_relatorios = reverse('relatorios_admin')
    status_cards = []
    status_cards.append({
        'valor': '',
        'rotulo': 'Todas',
        'chave': 'total',
        'classe': 'aberta',
        'nota': (
            'Todo seu histórico'
            if request.user.perfil == 'PRESTADOR'
            else 'Todas as ordens'
        ),
        'quantidade': metricas['total'],
        'selecionado': not status_filtro,
        'url': url_relatorios,
    })
    for valor, rotulo, chave, classe, nota in (
        (OrdemServico.Status.ABERTA, 'A fazer', 'abertas', 'aberta', 'Aguardando início'),
        (OrdemServico.Status.EM_EXECUCAO, 'Em execução', 'em_execucao', 'execucao', 'Serviços em andamento'),
        (OrdemServico.Status.EM_ANALISE, 'Em análise', 'em_analise', 'analise', 'Aguardando conferência'),
        (OrdemServico.Status.CONCLUIDA, 'Concluídas', 'concluidas', 'concluida', 'Serviços finalizados'),
    ):
        selecionado = status_filtro == valor
        url = (
            url_relatorios
            if selecionado
            else f'{url_relatorios}?{urlencode({"status": valor})}'
        )
        status_cards.append({
            'valor': valor,
            'rotulo': rotulo,
            'chave': chave,
            'classe': classe,
            'nota': nota,
            'quantidade': metricas[chave],
            'selecionado': selecionado,
            'url': url,
        })

    inicio_semana = hoje - timedelta(days=6)
    inicio_periodo = timezone.make_aware(
        datetime.combine(inicio_semana, time.min),
        timezone.get_current_timezone(),
    )
    fim_periodo = timezone.make_aware(
        datetime.combine(hoje + timedelta(days=1), time.min),
        timezone.get_current_timezone(),
    )
    ordens_por_dia = {
        item['dia']: item['quantidade']
        for item in ordens.filter(
            criada_em__gte=inicio_periodo,
            criada_em__lt=fim_periodo,
        ).annotate(
            dia=TruncDate('criada_em', tzinfo=timezone.get_current_timezone())
        ).values('dia').annotate(quantidade=Count('pk'))
    }
    pico_semana = max(ordens_por_dia.values(), default=0)
    nomes_dias = ('seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom')
    dias_semana = []
    for deslocamento in range(7):
        dia = inicio_semana + timedelta(days=deslocamento)
        quantidade = ordens_por_dia.get(dia, 0)
        dias_semana.append({
            'data': dia.strftime('%d/%m'),
            'semana': nomes_dias[dia.weekday()],
            'quantidade': quantidade,
            'percentual': max(8, round(quantidade / pico_semana * 100)) if pico_semana else 8,
        })

    divisor = metricas['total'] or 1
    status_chart = {
        'aberta_fim': round(metricas['abertas'] / divisor * 100),
        'execucao_fim': round(
            (metricas['abertas'] + metricas['em_execucao']) / divisor * 100
        ),
        'analise_fim': round(
            (
                metricas['abertas']
                + metricas['em_execucao']
                + metricas['em_analise']
            ) / divisor * 100
        ),
    }
    rotulos_filtro = {
        OrdemServico.Status.ABERTA: 'abertas',
        OrdemServico.Status.EM_EXECUCAO: 'em execução',
        OrdemServico.Status.EM_ANALISE: 'em análise',
        OrdemServico.Status.CONCLUIDA: 'concluídas',
    }
    ordens_filtradas = ordens
    if status_filtro:
        ordens_filtradas = ordens_filtradas.filter(status=status_filtro)
    paginador = Paginator(ordens_filtradas, 10)
    page_obj = paginador.get_page(request.GET.get('pagina'))
    parametros = request.GET.copy()
    parametros.pop('pagina', None)
    if status_filtro:
        parametros['status'] = status_filtro
    else:
        parametros.pop('status', None)
    if request.user.perfil == 'ADMINISTRADOR':
        for ordem in page_obj.object_list:
            parametros_detalhe = {
                'origem': 'relatorios',
                'pagina': str(page_obj.number),
            }
            if status_filtro:
                parametros_detalhe['status'] = status_filtro
            ordem.relatorio_detalhe_url = (
                f'{reverse("ordens:detalhe", args=[ordem.pk])}?'
                f'{urlencode(parametros_detalhe)}'
            )

    return {
        'metricas': metricas,
        'status_cards': status_cards,
        'status_chart': status_chart,
        'dias_semana': dias_semana,
        'total_semana': sum(dia['quantidade'] for dia in dias_semana),
        'filtro_status': status_filtro,
        'filtro_status_rotulo': rotulos_filtro.get(status_filtro, ''),
        'page_obj': page_obj,
        'paginator': paginador,
        'is_paginated': page_obj.has_other_pages(),
        'query_base': parametros.urlencode(),
    }


def _relatorios_prestador(request):
    contexto = _contexto_dashboard_ordens(
        request,
        ordens_visiveis_para(request.user),
    )
    contexto.update({
        'usuario': request.user,
        'admin_section': 'reports',
        'admin_title': 'Relatórios',
    })
    return render(request, 'usuarios/prestador_relatorios.html', contexto)


@login_required
def usuarios_admin(request):
    _exigir_administrador(request)
    usuarios = Usuario.objects.select_related('prestador_perfil').order_by(
        'perfil', 'first_name', 'username'
    )
    return render(
        request,
        'usuarios/admin_usuarios.html',
        {
            'usuario': request.user,
            'usuarios': usuarios,
            'admin_section': 'users',
            'admin_title': 'Usuários',
        },
    )


@login_required
def relatorios_admin(request):
    if request.user.perfil == 'PRESTADOR':
        return _relatorios_prestador(request)
    _exigir_administrador(request)
    ordens = ordens_visiveis_para(request.user)
    contexto = _contexto_dashboard_ordens(request, ordens)
    categoria_rotulos = dict(OrdemServico.Categoria.choices)
    categorias = [
        {
            'rotulo': categoria_rotulos.get(item['categoria'], item['categoria']),
            'total': item['total'],
        }
        for item in ordens.order_by().values('categoria').annotate(
            total=Count('pk')
        ).order_by('categoria')
    ]
    contexto.update({
        'usuario': request.user,
        'categorias': categorias,
        'total_usuarios': Usuario.objects.count(),
        'total_prestadores': Prestador.objects.filter(status=True).count(),
        'admin_section': 'reports',
        'admin_title': 'Relatórios',
    })
    return render(request, 'usuarios/admin_relatorios.html', contexto)


@login_required
def configuracoes_admin(request):
    _exigir_administrador(request)
    # ⚠️ Atenção: esta função usa AdminUsuarioCadastroForm
    # Se essa classe não existir no forms.py, remova ou ajuste conforme necessário
    from .forms import CadastroUsuarioAdminForm
    form = CadastroUsuarioAdminForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario_criado = form.save()
        messages.success(
            request,
            f'Usuário "{usuario_criado.username}" criado com sucesso.',
        )
        return redirect('usuarios_admin')
    return render(
        request,
        'usuarios/admin_configuracoes.html',
        {
            'usuario': request.user,
            'form': form,
            'admin_section': 'settings',
            'admin_title': 'Configurações',
        },
    )
