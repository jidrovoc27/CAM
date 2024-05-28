from django.contrib import admin

# Register your models here.
from django.contrib.auth.models import User

from administrativo.models import *

admin.site.unregister(User)
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username','is_staff','is_active','is_superuser','date_joined',)
    search_fields = ('username',)
    list_filter = ('is_staff', 'is_active', 'is_superuser',)

@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    '''Admin View for Menu'''

    list_display = ('nombre','descripcion','icono','ruta','activo','usuario_creacion','fecha_creacion','usuario_modificacion','fecha_modificacion','status',)
    list_filter = ('nombre','descripcion','activo',)
    search_fields = (('nombre','descripcion',)

@admin.register(Modulo))
class CategoriaModulo(admin.ModelAdmin):
    '''Admin View for Menu'''

    list_display = ('nombre','orden','icono','status',)
    list_filter = ('nombre','orden','status',)
    search_fields = ('nombre')

@admin.register(Genero)
class GeneroAdmin(admin.ModelAdmin):
    '''Admin View for Genero'''

    list_display = ('nombre','usuario_creacion','fecha_creacion','usuario_modificacion','fecha_modificacion','status',)
    list_filter = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    '''Admin View for Persona'''

    list_display = ('usuario','nombres','apellidos','cedula','genero','telefono_movil','telefono_convencional','email','usuario_creacion','fecha_creacion','usuario_modificacion','fecha_modificacion','status',)
    search_fields = ('apellidos','nombres','email',)

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    '''Admin View for Persona'''

    list_display = ('persona',)
    search_fields = ('',)

@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    '''Admin View for Docente'''

    list_display = ('persona','usuario_creacion','fecha_creacion','usuario_modificacion','fecha_modificacion','status',)
    list_filter = ('persona',)
    search_fields = ('persona',)

@admin.register(PersonaPerfil)
class PersonaPerfilAdmin(admin.ModelAdmin):
    list_display = ('persona','is_profesor','is_administrador','is_alumno','usuario_creacion','fecha_creacion','usuario_modificacion','fecha_modificacion','status',)
    search_fields = ('persona',)


@admin.register(AccesoModulo)
class AccesoModuloAdmin(admin.ModelAdmin):
    list_display = ('grupo','modulo','activo','usuario_creacion','fecha_creacion','usuario_modificacion','fecha_modificacion','status',)
    search_fields = ('grupo','modulo',)
