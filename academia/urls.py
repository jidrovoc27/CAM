from django.contrib import admin
from django.urls import path
from administrativo.funciones import *
from academia.conf_acceso_modulo import view_acceso_modulo
from academia.views import *


urlpatterns = [
path(r'loginacademia/inicio/', dashboard, name='dashboard'),
    path(r'loginacademia/', login_academia, name='login_academia'),
    path(r'registrate/', registrate, name='registrate_usuario'),
    path(r'logoutacademia/', logout_usuario, name='logout_usuario_a'),
    # path(r'conf_sistemas/grupos/', view_grupo, name='conf_grupo'),
    # path(r'conf_sistemas/modulos/', view_modulo, name='conf_modulo'),
    # path(r'conf_sistemas/acceso_modulos/', view_acceso_modulo, name='conf_acceso_modulo'),
    # path(r'conf_sistemas/personas/', view_persona, name='conf_persona'),
    # path(r'conf_sistemas/usuarios/', view_usuario, name='conf_usuario'),
    # path(r'docentes/', view_docente, name='docentes'),
    # path(r'alumnos/', view_alumno, name='alumnos'),
    # path(r'finanzas/',view_finanzas ,name='finanzas'),
    # path(r'mis_finanzas/',view_mis_finanzas ,name='mis_finanzas'),
    path('change-password/', PasswordChangeView.as_view(), name="CambiarContraseña"),
]