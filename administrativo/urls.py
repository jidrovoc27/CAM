from django.contrib import admin
from django.urls import path
from administrativo.funciones import *
from administrativo.conf_acceso_modulo import view_acceso_modulo
from administrativo.conf_grupo import view_grupo
from administrativo.conf_modulo import view_modulo

from administrativo.conf_persona import view_persona
from administrativo.conf_usuario import view_usuario


from administrativo.views import *
from administrativo.view_finanzas import *
from administrativo.view_mis_finanzas import *
from administrativo.view_docente import *
from administrativo.view_periodo import *
from administrativo.view_alumno import *
from administrativo.view_tiporubro import *
from administrativo.view_cajas import *
from administrativo.view_sesioncaja import *
from administrativo.view_cargoocupacional import *

urlpatterns = [
path(r'', dashboard, name='dashboard'),
    path(r'login/', login_usuario, name='login_usuario'),
    path(r'registrate/', registrate, name='registrate_usuario'),
    path(r'logout/', logout_usuario, name='logout_usuario'),
    path(r'conf_sistemas/grupos/', view_grupo, name='conf_grupo'),
    path(r'conf_sistemas/modulos/', view_modulo, name='conf_modulo'),
    path(r'conf_sistemas/acceso_modulos/', view_acceso_modulo, name='conf_acceso_modulo'),
    path(r'conf_sistemas/personas/', view_persona, name='conf_persona'),
    path(r'conf_sistemas/usuarios/', view_usuario, name='conf_usuario'),
    path(r'docentes/', view_docente, name='docentes'),
    path(r'alumnos/', view_alumno, name='alumnos'),
    path(r'periodo/', view_periodo, name='periodo'),
    path(r'tiporubros/', view_tiporubro, name='tiporubros'),
    path(r'finanzas/',view_finanzas ,name='finanzas'),
    path(r'mis_finanzas/',view_mis_finanzas ,name='mis_finanzas'),
    path(r'cajas/',view_cajas ,name='cajas'),
    path(r'sesioncaja/',view_sesioncaja ,name='sesioncaja'),
    path(r'cargos/',view_cargoocupacional ,name='cargos'),
    path('change-password/', PasswordChangeView.as_view(), name="CambiarContraseña"),
    path(r'CAM/', paginaweb, name='paginaweb'),
]