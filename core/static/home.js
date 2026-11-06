
// Funções de Popup
function abrirPopup() {
    const fundoPopup = document.getElementById('fundoPopup');
    if (fundoPopup) {
        fundoPopup.classList.add('aberto');
    }
    document.body.style.overflow = 'hidden';
}

function fecharPopup() {
    const fundoPopup = document.getElementById('fundoPopup');
    if (!fundoPopup) return;

    fundoPopup.classList.remove('aberto');
    document.body.style.overflow = '';
}

function limparErrosFormulario() {
    document.querySelectorAll('.erro-form-campo').forEach((el) => el.remove());
    const errosGerais = document.getElementById('errosGerais');
    if (errosGerais) {
        errosGerais.textContent = '';
    }
}

function exibirErrosFormulario(errors) {
    limparErrosFormulario();
    const geral = document.getElementById('errosGerais');

    if (errors.__all__ && geral) {
        geral.textContent = errors.__all__.join(' ');
    }

    Object.entries(errors || {}).forEach(([campo, mensagens]) => {
        if (campo === '__all__') return;

        const input = document.querySelector(`[name="${campo}"]`);
        if (!input) return;

        const mensagensLista = Array.isArray(mensagens) ? mensagens : [mensagens];
        const container = input.parentElement;
        if (!container) return;

        mensagensLista.forEach((mensagem) => {
            const erro = document.createElement('span');
            erro.className = 'erro-form erro-form-campo';
            erro.textContent = mensagem.message || mensagem;
            container.appendChild(erro);
        });
    });
}

function abrirConfirmacaoExclusao(botao) {
    const modal = document.getElementById('modalConfirmarExclusao');
    const numero = document.getElementById('numeroOrdemExclusao');
    const erro = document.getElementById('erroExclusao');
    const confirmar = document.getElementById('confirmarExclusao');
    const linha = botao.closest('tr');

    if (!modal || !confirmar) return;

    modal.dataset.url = linha?.dataset.deleteUrl || botao.dataset.deleteUrl || '';
    modal.dataset.linhaId = linha?.id || '';
    if (numero) {
        numero.textContent = linha?.cells[0]?.textContent.trim() || '';
    }
    if (erro) {
        erro.textContent = '';
        erro.hidden = true;
    }
    confirmar.disabled = false;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    confirmar.focus();
}

function fecharConfirmacaoExclusao() {
    const modal = document.getElementById('modalConfirmarExclusao');
    if (!modal || modal.hidden) return;

    modal.hidden = true;
    modal.dataset.url = '';
    modal.dataset.linhaId = '';
    document.body.style.overflow = '';
}

function abrirLoginOutroId() {
    const modal = document.getElementById('modalLoginOutroId');
    const form = document.getElementById('formLoginOutroId');
    const erro = document.getElementById('erroLoginOutroId');
    const botaoEntrar = document.getElementById('confirmarLoginOutroId');
    const contaDropdown = document.querySelector('.conta-dropdown');

    if (!modal || !form) return;

    contaDropdown?.removeAttribute('open');
    form.reset();
    if (erro) {
        erro.textContent = '';
        erro.hidden = true;
    }
    if (botaoEntrar) botaoEntrar.disabled = false;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    document.getElementById('loginOutroIdUsuario')?.focus();
}

function fecharLoginOutroId() {
    const modal = document.getElementById('modalLoginOutroId');
    const form = document.getElementById('formLoginOutroId');
    if (!modal || modal.hidden) return;

    modal.hidden = true;
    form?.reset();
    document.body.style.overflow = '';
}

async function excluirOrdemConfirmada() {
    const modal = document.getElementById('modalConfirmarExclusao');
    const confirmar = document.getElementById('confirmarExclusao');
    const erro = document.getElementById('erroExclusao');
    const url = modal?.dataset.url;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    if (!modal || !confirmar || !url || !csrfToken) {
        if (erro) {
            erro.textContent = 'Não foi possível preparar a exclusão. Atualize a página e tente novamente.';
            erro.hidden = false;
        }
        return;
    }

    confirmar.disabled = true;

    try {
        const resposta = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: new URLSearchParams({ csrfmiddlewaretoken: csrfToken })
        });

        if (!resposta.ok) {
            throw new Error('A exclusão não foi concluída. Tente novamente.');
        }

        const linha = document.getElementById(modal.dataset.linhaId);
        const corpoTabela = document.getElementById('corpoTabelaOrdens');
        linha?.remove();

        if (corpoTabela && corpoTabela.querySelectorAll('tr').length === 0) {
            document.getElementById('estadoVazio')?.removeAttribute('hidden');
            document.getElementById('tabelaOrdens')?.setAttribute('hidden', 'hidden');
            document.getElementById('containerTabelaOrdens')?.setAttribute('hidden', 'hidden');
        }

        fecharConfirmacaoExclusao();
    } catch (error) {
        if (erro) {
            erro.textContent = error.message || 'Ocorreu um erro ao excluir a ordem.';
            erro.hidden = false;
        }
    } finally {
        confirmar.disabled = false;
    }
}

function atualizarLinhaOrdem(ordem) {
    const linha = document.getElementById('linha-' + ordem.pk);
    if (!linha) return;

    const celulas = linha.cells;
    const valores = [
        ordem.numero,
        ordem.criada_em,
        ordem.descricao,
        ordem.data_prevista,
        ordem.categoria,
        ordem.prioridade,
        ordem.endereco,
        ordem.prestador,
    ];
    const rotulos = [
        'Número O.S.', 'Gerada em', 'Descrição', 'Data prevista',
        'Categoria', 'Prioridade', 'Endereço', 'Prestador'
    ];

    valores.forEach(function (valor, indice) {
        if (celulas[indice]) {
            if (indice === 0) {
                const identificador = document.createElement('span');
                identificador.className = 'identificador-os';
                identificador.textContent = valor;
                celulas[indice].replaceChildren(identificador);
            } else {
                celulas[indice].textContent = valor;
            }
            celulas[indice].dataset.label = rotulos[indice];
        }
    });

    const status = document.createElement('span');
    status.className = 'status-tabela';
    status.textContent = ordem.status;
    if (celulas[8]) {
        celulas[8].dataset.label = 'Status';
        const conteudoStatus = [status];
        if (ordem.entregue_em) {
            const entrega = document.createElement('small');
            entrega.className = 'data-entrega-status';
            entrega.textContent = 'Entregue em ' + ordem.entregue_em;
            conteudoStatus.push(entrega);
        }
        celulas[8].replaceChildren(...conteudoStatus);
    }

    linha.dataset.deleteUrl = ordem.excluir_url;
    linha.dataset.editUrl = ordem.editar_url;
    const botaoEditar = linha.querySelector('[data-editar]');
    if (botaoEditar) {
        botaoEditar.dataset.editUrl = ordem.editar_url;
    }
}

function adicionarLinhaOrdem(ordem) {
    const corpoTabela = document.getElementById('corpoTabelaOrdens');
    const tabela = document.getElementById('tabelaOrdens');
    const vazio = document.getElementById('estadoVazio');
    const containerTabela = document.getElementById('containerTabelaOrdens');

    if (!corpoTabela) return;

    const linha = document.createElement('tr');
    linha.id = 'linha-' + ordem.pk;
    linha.dataset.deleteUrl = ordem.excluir_url;
    linha.dataset.editUrl = ordem.editar_url;

    const dadosLinha = [
        { texto: ordem.numero, classe: 'numero-os', label: 'Número O.S.' },
        { texto: ordem.criada_em, classe: 'col-criada-em', label: 'Gerada em' },
        { texto: ordem.descricao, classe: 'col-descricao', label: 'Descrição' },
        { texto: ordem.data_prevista, classe: 'col-data', label: 'Data prevista' },
        { texto: ordem.categoria, classe: 'col-categoria', label: 'Categoria' },
        { texto: ordem.prioridade, classe: 'col-prioridade', label: 'Prioridade' },
        { texto: ordem.endereco, classe: 'col-endereco', label: 'Endereço' },
        { texto: ordem.prestador, classe: 'col-prestador', label: 'Prestador' },
        {
            texto: ordem.status,
            classe: 'status-tabela',
            label: 'Status',
            entregueEm: ordem.entregue_em
        }
    ];

    dadosLinha.forEach(function (item) {
        const celula = document.createElement('td');
        celula.dataset.label = item.label;
        if (item.classe === 'status-tabela') {
            const span = document.createElement('span');
            span.className = item.classe;
            span.textContent = item.texto;
            celula.appendChild(span);
            if (item.entregueEm) {
                const entrega = document.createElement('small');
                entrega.className = 'data-entrega-status';
                entrega.textContent = 'Entregue em ' + item.entregueEm;
                celula.appendChild(entrega);
            }
        } else if (item.classe === 'numero-os') {
            const identificador = document.createElement('span');
            identificador.className = 'identificador-os';
            identificador.textContent = item.texto;
            celula.className = item.classe;
            celula.appendChild(identificador);
        } else {
            celula.className = item.classe;
            celula.textContent = item.texto;
        }
        linha.appendChild(celula);
    });

    const celulaAcoes = document.createElement('td');
    celulaAcoes.className = 'acoes-tabela';
    celulaAcoes.dataset.label = 'Ações';
    celulaAcoes.innerHTML = `
        <div class="grupo-acoes">
            <button class="btn-acao btn-editar" type="button" data-editar data-edit-url="${ordem.editar_url}">Editar</button>
            <button class="btn-acao btn-excluir" type="button" data-excluir>Excluir</button>
        </div>
    `;
    linha.appendChild(celulaAcoes);

    corpoTabela.prepend(linha);

    if (tabela) tabela.hidden = false;
    if (vazio) vazio.hidden = true;
    if (containerTabela) containerTabela.hidden = false;

    const botaoEditar = linha.querySelector('[data-editar]');
    if (botaoEditar) {
        botaoEditar.addEventListener('click', function (event) {
            editarOrdem(event, botaoEditar);
        });
    }

}

async function editarOrdem(event, botao) {
    event.preventDefault();
    event.stopPropagation();

    const linha = botao.closest('tr');
    const urlEdicao = botao.dataset.editUrl || linha?.dataset.editUrl;
    if (!urlEdicao) return;

    botao.disabled = true;

    try {
        const resposta = await fetch(urlEdicao, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });

        if (!resposta.ok) throw new Error('Falha ao carregar a ordem.');
        const resultado = await resposta.json();

        Object.entries(resultado.form || {}).forEach(function ([nomeCampo, valor]) {
            const campo = document.getElementById(nomeCampo) || document.querySelector(`[name="${nomeCampo}"]`);
            if (campo) campo.value = valor;
        });

        const form = document.getElementById('formNovaOrdem');
        if (!form) return;

        form.action = urlEdicao;
        form.dataset.editingPk = linha?.id.replace('linha-', '') || '';
        const botaoSubmit = form.querySelector('button[type="submit"]');
        if (botaoSubmit) botaoSubmit.textContent = 'Salvar alterações';

        const titulo = document.getElementById('titulo-popup');
        if (titulo) {
            titulo.textContent = 'Editar O.S. #' + resultado.numero;
        }

        limparErrosFormulario();
        abrirPopup();
    } catch (erro) {
        window.alert('Não foi possível carregar a O.S. para edição.');
    } finally {
        botao.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('formNovaOrdem');
    const fundoPopup = document.getElementById('fundoPopup');
    const btnNovaOS = document.getElementById('btnNovaOS');
    const btnFecharPopup = document.getElementById('btnFecharPopup');
    const btnCancelar = document.getElementById('btnCancelar');
    const contaDropdown = document.querySelector('.conta-dropdown');
    const abrirLoginOutroIdBotao = document.getElementById('abrirLoginOutroId');
    const modalLoginOutroId = document.getElementById('modalLoginOutroId');
    const fecharLoginOutroIdBotao = document.getElementById('fecharLoginOutroId');
    const cancelarLoginOutroIdBotao = document.getElementById('cancelarLoginOutroId');
    const formLoginOutroId = document.getElementById('formLoginOutroId');

    if (contaDropdown) {
        document.addEventListener('click', function (event) {
            if (!contaDropdown.contains(event.target)) {
                contaDropdown.open = false;
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                contaDropdown.open = false;
            }
        });
    }

    if (btnNovaOS && form) {
        btnNovaOS.addEventListener('click', function () {
            form.reset();
            form.action = '/ordens/nova/';
            form.dataset.editingPk = '';
            const botaoSubmit = form.querySelector('button[type="submit"]');
            if (botaoSubmit) botaoSubmit.textContent = 'Salvar';

            const titulo = document.getElementById('titulo-popup');
            if (titulo) {
                titulo.textContent = 'Criar Nova Ordem de Serviço';
            }

            limparErrosFormulario();
            abrirPopup();
        });
    }

    if (fundoPopup) {
        fundoPopup.addEventListener('click', function (event) {
            if (event.target === fundoPopup) fecharPopup();
        });
    }

    if (btnFecharPopup) {
        btnFecharPopup.addEventListener('click', fecharPopup);
    }

    if (btnCancelar) {
        btnCancelar.addEventListener('click', fecharPopup);
    }

    if (abrirLoginOutroIdBotao) {
        abrirLoginOutroIdBotao.addEventListener('click', abrirLoginOutroId);
    }

    if (fecharLoginOutroIdBotao) {
        fecharLoginOutroIdBotao.addEventListener('click', fecharLoginOutroId);
    }

    if (cancelarLoginOutroIdBotao) {
        cancelarLoginOutroIdBotao.addEventListener('click', fecharLoginOutroId);
    }

    if (modalLoginOutroId) {
        modalLoginOutroId.addEventListener('click', function (event) {
            if (event.target === modalLoginOutroId) fecharLoginOutroId();
        });
    }

    if (formLoginOutroId) {
        formLoginOutroId.addEventListener('submit', async function (event) {
            event.preventDefault();

            const erro = document.getElementById('erroLoginOutroId');
            const botaoEntrar = document.getElementById('confirmarLoginOutroId');
            const dados = new FormData(formLoginOutroId);
            if (erro) {
                erro.textContent = '';
                erro.hidden = true;
            }
            if (botaoEntrar) botaoEntrar.disabled = true;

            try {
                const resposta = await fetch(formLoginOutroId.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: dados
                });
                const resultado = await resposta.json();

                if (!resposta.ok || !resultado.success) {
                    formLoginOutroId.reset();
                    document.getElementById('loginOutroIdUsuario')?.focus();
                    throw new Error(resultado.error || 'Não foi possível entrar com essa conta.');
                }

                window.location.assign(resultado.redirect_url);
            } catch (error) {
                if (erro) {
                    erro.textContent = error.message || 'Falha ao entrar. Tente novamente.';
                    erro.hidden = false;
                }
                if (botaoEntrar) botaoEntrar.disabled = false;
            }
        });
    }

    document.querySelectorAll('[data-editar]').forEach(function (botao) {
        botao.addEventListener('click', function (event) {
            editarOrdem(event, botao);
        });
    });

    document.addEventListener('click', function (event) {
        const botaoExcluir = event.target.closest('[data-excluir]');
        if (botaoExcluir) {
            event.preventDefault();
            abrirConfirmacaoExclusao(botaoExcluir);
        }
    });

    const modalExclusao = document.getElementById('modalConfirmarExclusao');
    const cancelarExclusao = document.getElementById('cancelarExclusao');
    const confirmarExclusao = document.getElementById('confirmarExclusao');
    if (modalExclusao) {
        modalExclusao.addEventListener('click', function (event) {
            if (event.target === modalExclusao) fecharConfirmacaoExclusao();
        });
    }
    if (cancelarExclusao) {
        cancelarExclusao.addEventListener('click', fecharConfirmacaoExclusao);
    }
    if (confirmarExclusao) {
        confirmarExclusao.addEventListener('click', excluirOrdemConfirmada);
    }
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            fecharLoginOutroId();
            fecharConfirmacaoExclusao();
            fecharPopup();
        }
    });

    if (form) {
        form.addEventListener('submit', async function (event) {
            event.preventDefault();

            const dados = new FormData(form);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
            const resposta = await fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                body: dados
            });

            const conteudo = await resposta.json().catch(function () {
                return null;
            });

            if (!resposta.ok) {
                if (conteudo && conteudo.errors) {
                    exibirErrosFormulario(conteudo.errors);
                }
                return;
            }

            if (conteudo && conteudo.ordem) {
                const ordem = conteudo.ordem;
                const linhaExistente = document.getElementById('linha-' + ordem.pk);
                if (linhaExistente) {
                    atualizarLinhaOrdem(ordem);
                } else {
                    adicionarLinhaOrdem(ordem);
                }
            }

            form.reset();
            fecharPopup();
            limparErrosFormulario();
            const titulo = document.getElementById('titulo-popup');
            if (titulo) {
                titulo.textContent = 'Criar Nova Ordem de Serviço';
            }
            const botaoSubmit = form.querySelector('button[type="submit"]');
            if (botaoSubmit) {
                botaoSubmit.textContent = 'Salvar';
            }
            form.action = '/ordens/nova/';
            form.dataset.editingPk = '';
        });
    }
});
