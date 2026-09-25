from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
#    path('usuarios/', include('usuarios.urls')),
    path('ordens/', include('ordens.urls', namespace='ordens')),

    # ✅ Esta linha É AQUI — liga as rotas da sua página inicial
    path('', include('usuarios.urls')),

    # ✅ Login e Logout — o Django já faz!
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]