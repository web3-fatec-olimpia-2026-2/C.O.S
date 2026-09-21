from django.shortcuts import render, redirect, get_object_or_404
from .forms import OrdemForm
from .models import OrdemServico

def listar_ordens(request):
    ordens = OrdemServico.objects.all()
    return render(request, "ordens/lista.html", {"ordens": ordens})

def criar_ordem(request):
    form = OrdemForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("lista_ordens")
    return render(request, "ordens/nova.html", {"form": form})

def editar_ordem(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    form = OrdemForm(request.POST or None, instance=ordem)
    if form.is_valid():
        form.save()
        return redirect("lista_ordens")
    return render(request, "ordens/nova.html", {"form": form})

def excluir_ordem(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    if request.method == "POST":
        ordem.delete()
        return redirect("lista_ordens")
    return render(request, "ordens/confirmar_excluir.html", {"ordem": ordem})