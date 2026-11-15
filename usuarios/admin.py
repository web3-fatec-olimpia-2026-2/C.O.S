from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Prestador, Usuario


class PrestadorAdminForm(forms.ModelForm):
    class Meta:
        model = Prestador
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['usuario'].queryset = Usuario.objects.filter(
            perfil='PRESTADOR'
        ).order_by('username')


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Acesso ao C.O.S.', {'fields': ('perfil',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Dados do C.O.S.', {'fields': ('email', 'perfil')}),
    )
    list_display = UserAdmin.list_display + ('perfil',)
    list_filter = UserAdmin.list_filter + ('perfil',)


@admin.register(Prestador)
class PrestadorAdmin(admin.ModelAdmin):
    form = PrestadorAdminForm
    list_display = ('nome', 'documento', 'usuario', 'status')
    list_filter = ('status',)
    search_fields = ('nome', 'documento', 'email', 'usuario__username')
