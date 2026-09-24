from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views import generic

from .forms import MichiForm
from .models import Michi


class ListaMichisView(generic.ListView):
    template_name = 'registro/lista.html'
    context_object_name = 'michis'

    def get_queryset(self):
        return Michi.objects.all()


class DetalleMichiView(generic.DetailView):
    model = Michi
    template_name = 'registro/detalle.html'
    context_object_name = 'michi'


class MichiFormViewMixin:
    """Comparte template y contexto entre alta y edición (evita duplicación)."""
    model = Michi
    form_class = MichiForm
    template_name = 'registro/agregar.html'

    def get_success_url(self):
        return reverse('detalle_michi', args=(self.object.id,))


class AgregarMichiView(LoginRequiredMixin, MichiFormViewMixin, generic.CreateView):
    extra_context = {'titulo': 'Agregar michi'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_url'] = reverse('agregar_michi')
        return context


class EditarMichiView(LoginRequiredMixin, MichiFormViewMixin, generic.UpdateView):
    extra_context = {'titulo': 'Editar michi'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_url'] = reverse('editar_michi', args=(self.object.id,))
        return context


class MichiDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Michi
    template_name = 'registro/confirmar_eliminar.html'
    context_object_name = 'michi'
    success_url = reverse_lazy('lista_michis')
