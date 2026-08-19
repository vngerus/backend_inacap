from django.contrib import admin

# Register your models here.
from .models import Michi


@admin.register(Michi)
class MichiAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo')
    search_fields = ('nombre', 'tipo')

    class Media:
        css = {'all': ('registro/admin_light.css',)}
