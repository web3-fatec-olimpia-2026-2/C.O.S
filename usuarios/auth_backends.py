from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .models import Prestador


class UsuarioOuDocumentoPrestadorBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(get_user_model().USERNAME_FIELD)
        if username is None or password is None:
            return None

        UserModel = get_user_model()
        usuario = UserModel._default_manager.filter(
            **{UserModel.USERNAME_FIELD: username}
        ).first()

        if usuario is None:
            prestador = Prestador.objects.select_related('usuario').filter(
                documento=username,
                status=True,
                usuario__isnull=False,
                usuario__perfil='PRESTADOR',
            ).first()
            usuario = prestador.usuario if prestador else None

        if usuario is None:
            UserModel().set_password(password)
            return None

        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
