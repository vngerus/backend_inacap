from django.contrib import admin

from .models import Dueno, Michi


@admin.register(Dueno)
class DuenoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono')
    search_fields = ('nombre',)

    class Media:
        css = {'all': ('registro/admin_light.css',)}


@admin.register(Michi)
class MichiAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'dueno')
    search_fields = ('nombre', 'tipo')
    list_filter = ('dueno',)

    class Media:
        css = {'all': ('registro/admin_light.css',)}
