from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
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


@login_required
def agregar_michi(request):
    if request.method == 'POST':
        form = MichiForm(request.POST, request.FILES)
        if form.is_valid():
            michi = form.save()
            return redirect(reverse('detalle_michi', args=(michi.id,)))
    else:
        form = MichiForm()

    return render(request, 'registro/agregar.html', {
        'form': form,
        'titulo': 'Agregar michi',
        'action_url': reverse('agregar_michi'),
    })


@login_required
def editar_michi(request, pk):
    michi = get_object_or_404(Michi, pk=pk)

    if request.method == 'POST':
        form = MichiForm(request.POST, request.FILES, instance=michi)
        if form.is_valid():
            form.save()
            return redirect(reverse('detalle_michi', args=(michi.id,)))
    else:
        form = MichiForm(instance=michi)

    return render(request, 'registro/agregar.html', {
        'form': form,
        'titulo': 'Editar michi',
        'action_url': reverse('editar_michi', args=(michi.id,)),
    })


class MichiDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Michi
    template_name = 'registro/confirmar_eliminar.html'
    context_object_name = 'michi'
    success_url = reverse_lazy('lista_michis')
