from .models import OrdemServico


def ordens_visiveis_para(usuario):
    ordens = OrdemServico.objects.select_related('prestador')

    if usuario.perfil == 'ADMINISTRADOR':
        return ordens

    if usuario.perfil == 'PRESTADOR':
        return ordens.filter(prestador__usuario=usuario)

    return ordens.none()
