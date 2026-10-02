from django.shortcuts import render, redirect, get_object_or_404
<<<<<<< HEAD
from django.http import HttpResponse
=======
>>>>>>> 82d5aed7ef080f87f0e97e3b8c8389f8240d1155
from .forms import OrdemForm
from .models import OrdemServico

def listar_ordens(request):
    ordens = OrdemServico.objects.all()
    return render(request, "ordens/lista.html", {"ordens": ordens})

def criar_ordem(request):
    form = OrdemForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('ordens:listar')
    return render(request, "ordens/nova.html", {"form": form})

def editar_ordem(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    form = OrdemForm(request.POST or None, instance=ordem)
    if form.is_valid():
        form.save()
        return redirect('ordens:listar')
    return render(request, "ordens/nova.html", {"form": form})

def excluir_ordem(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    if request.method == 'DELETE':
        ordem.delete()
        return HttpResponse('')
