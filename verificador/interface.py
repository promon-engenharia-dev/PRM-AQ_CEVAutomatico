"""Janela da ferramenta (Tkinter), na identidade Promon, com modo claro/escuro seguindo o Windows.

Fluxo: 1 · arquivos → 2 · opções (LD, ficha, pasta de saída) → Verificar → 3 · resultado.
O processamento roda numa thread; a ficha de cada PDF é pedida na thread da janela.
"""
from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import ficha as fichas
from . import nucleo, tema
from .config import Config

TITULO = "Verificador de Projetos — Arquitetura"


def _abrir_arquivo(caminho: str) -> None:
    if caminho and os.path.exists(caminho):
        if sys.platform == "win32":
            os.startfile(caminho)  # noqa: S606 — abre no programa padrão do Windows
        else:
            import subprocess
            subprocess.Popen(["xdg-open", caminho])


class Janela:
    def __init__(self, cfg: Config, pdfs: list[str]):
        self.cfg = cfg
        self.root = tk.Tk()
        self.root.title(f"{TITULO} — CEV automática")
        self.root.geometry("1360x860")
        self.root.minsize(1100, 700)
        self.fs = tema.fontes(self.root)
        self.escuro = tema.windows_escuro()
        self.p = tema.ESCURO if self.escuro else tema.CLARO
        tema.aplicar(self.root, self.p, self.fs)
        self.fila: queue.Queue = queue.Queue()
        self.resultados: list[nucleo.Resultado] = []
        self.linhas_resultado: list[tuple] = []
        self.filtro = "todos"
        self.rodando = False
        self._montar()
        self._aplicar_tags()
        for p in pdfs:
            self._incluir(p)
        tema.barra_titulo_escura(self.root, self.escuro)
        self.root.after(100, self._ler_fila)
        self.root.after(3000, self._vigiar_tema)

    # montagem -------------------------------------------------------------------------
    def _montar(self):
        r = self.root
        r.columnconfigure(0, weight=1)
        r.rowconfigure(3, weight=1)

        cab = ttk.Frame(r, style="Cabecalho.TFrame", padding=(28, 14))
        cab.grid(row=0, column=0, sticky="ew")
        self.logo = ttk.Label(cab, style="Cartao.TLabel")
        self.logo.grid(row=0, column=0, rowspan=2, sticky="w", padx=(6, 6), pady=6)
        ttk.Frame(cab, style="Linha.TFrame", width=1).grid(row=0, column=1, rowspan=2, sticky="ns", padx=(10, 16))
        ttk.Label(cab, text=TITULO, style="Titulo.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Label(cab, text="Verificação automática de apresentação · CEV · processamento 100% local",
                  style="Subtitulo.TLabel").grid(row=1, column=2, sticky="w")
        self._trocar_logo()
        ttk.Frame(r, style="Linha.TFrame", height=1).grid(row=1, column=0, sticky="ew")
        ttk.Frame(r, style="Filete.TFrame", height=2).grid(row=2, column=0, sticky="ew")

        corpo = ttk.Frame(r, padding=(28, 18))
        corpo.grid(row=3, column=0, sticky="nsew")
        corpo.columnconfigure(0, weight=0, minsize=460)
        corpo.columnconfigure(1, weight=1)
        corpo.rowconfigure(0, weight=1)

        esq = ttk.Frame(corpo)
        esq.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        esq.columnconfigure(0, weight=1)
        esq.rowconfigure(0, weight=1)
        self._cartao_arquivos(esq).grid(row=0, column=0, sticky="nsew")
        self._cartao_opcoes(esq).grid(row=1, column=0, sticky="ew", pady=(16, 0))

        acao = ttk.Frame(esq)
        acao.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        acao.columnconfigure(1, weight=1)
        self.bt_verificar = ttk.Button(acao, text="Verificar", style="Primario.TButton", command=self._verificar)
        self.bt_verificar.grid(row=0, column=0, sticky="w")
        self.progresso = ttk.Progressbar(acao, mode="determinate")
        self.progresso.grid(row=0, column=1, sticky="ew", padx=(12, 0))
        self.status = ttk.Label(acao, text="Adicione os PDFs e clique em Verificar.", style="Status.TLabel")
        self.status.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        self._cartao_resultado(corpo).grid(row=0, column=1, sticky="nsew")

    def _titulo_cartao(self, pai, numero: str, texto: str, ajuda: str | None = None):
        ttk.Label(pai, text=f"{numero} · {texto}", style="Secao.TLabel").grid(row=0, column=0, columnspan=4, sticky="w")
        if ajuda:
            ttk.Label(pai, text=ajuda, style="Ajuda.TLabel", wraplength=400).grid(
                row=1, column=0, columnspan=4, sticky="w", pady=(2, 8))

    def _cartao_arquivos(self, pai):
        c = ttk.Frame(pai, style="Cartao.TFrame", padding=16)
        c.columnconfigure(0, weight=1)
        c.rowconfigure(2, weight=1)
        self._titulo_cartao(c, "1", "Arquivos",
                            "PDFs de pranchas ou relatórios. Também dá para arrastar os PDFs sobre o Verificador.bat.")
        quadro = ttk.Frame(c, style="Plano.TFrame")
        quadro.grid(row=2, column=0, columnspan=4, sticky="nsew")
        quadro.columnconfigure(0, weight=1)
        quadro.rowconfigure(0, weight=1)
        self.lista = ttk.Treeview(quadro, columns=("arquivo", "situacao"), show="headings", height=8, selectmode="extended")
        self.lista.heading("arquivo", text="Arquivo")
        self.lista.heading("situacao", text="Situação")
        self.lista.column("arquivo", width=250, anchor="w")
        self.lista.column("situacao", width=150, anchor="w", stretch=False)
        self.lista.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(quadro, orient="vertical", command=self.lista.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.lista.configure(yscrollcommand=sb.set)
        bts = ttk.Frame(c, style="Plano.TFrame")
        bts.grid(row=3, column=0, columnspan=4, sticky="w", pady=(10, 0))
        ttk.Button(bts, text="Adicionar PDFs…", command=self._adicionar).pack(side="left")
        ttk.Button(bts, text="Remover", command=self._remover).pack(side="left", padx=(8, 0))
        ttk.Button(bts, text="Limpar", command=self._limpar).pack(side="left", padx=(8, 0))
        self.caminhos: dict[str, str] = {}
        return c

    def _cartao_opcoes(self, pai):
        c = ttk.Frame(pai, style="Cartao.TFrame", padding=16)
        c.columnconfigure(1, weight=1)
        self._titulo_cartao(c, "2", "Opções")
        ttk.Label(c, text="LD do projeto", style="Campo.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 10))
        self.var_ld = tk.StringVar()
        ttk.Entry(c, textvariable=self.var_ld, width=28).grid(row=2, column=1, sticky="ew")
        ttk.Button(c, text="Escolher…", command=self._escolher_ld).grid(row=2, column=2, padx=(8, 0))
        ttk.Label(c, text="Vazio: procura a LD da operação (*-PL2-*.xlsx) na pasta do PDF e acima.",
                  style="Ajuda.TLabel", wraplength=300).grid(row=3, column=1, columnspan=2, sticky="w", pady=(2, 8))
        ttk.Label(c, text="Pasta de saída", style="Campo.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 10))
        self.var_saida = tk.StringVar()
        ttk.Entry(c, textvariable=self.var_saida, width=28).grid(row=4, column=1, sticky="ew")
        ttk.Button(c, text="Escolher…", command=self._escolher_saida).grid(row=4, column=2, padx=(8, 0))
        ttk.Label(c, text="Vazio: grava o _CEV.pdf ao lado de cada PDF.", style="Ajuda.TLabel").grid(
            row=5, column=1, columnspan=2, sticky="w", pady=(2, 8))
        self.var_ficha = tk.BooleanVar(value=True)
        ttk.Checkbutton(c, text="Pedir a ficha da emissão para cada PDF", variable=self.var_ficha).grid(row=6, column=0, columnspan=3, sticky="w")
        saidas = ttk.Frame(c, style="Plano.TFrame")
        saidas.grid(row=7, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Label(saidas, text="Gravar também:", style="Campo.TLabel").pack(side="left", padx=(0, 8))
        self.var_html = tk.BooleanVar(value=self.cfg["saidas"]["html"])
        self.var_csv = tk.BooleanVar(value=self.cfg["saidas"]["csv"])
        ttk.Checkbutton(saidas, text="Relatório HTML", variable=self.var_html).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(saidas, text="Lista em CSV", variable=self.var_csv).pack(side="left")
        return c

    def _cartao_resultado(self, pai):
        c = ttk.Frame(pai, style="Cartao.TFrame", padding=16)
        c.columnconfigure(0, weight=1)
        c.rowconfigure(4, weight=1)
        self._titulo_cartao(c, "3", "Resultado")
        kpis = ttk.Frame(c, style="Plano.TFrame")
        kpis.grid(row=1, column=0, sticky="ew", pady=(8, 12))
        self.kpi = {}
        for i, (chave, rot, estilo) in enumerate((("total", "ACHADOS", "Kpi.TLabel"), ("ERRO", "ERRO", "KpiErro.TLabel"),
                                                 ("ATENCAO", "ATENÇÃO", "KpiAten.TLabel"))):
            f = ttk.Frame(kpis, style="Plano.TFrame")
            f.grid(row=0, column=i, sticky="w", padx=(0, 36))
            ttk.Label(f, text=rot, style="Rotulo.TLabel").pack(anchor="w")
            self.kpi[chave] = ttk.Label(f, text="—", style=estilo)
            self.kpi[chave].pack(anchor="w")
        filtros = ttk.Frame(c, style="Plano.TFrame")
        filtros.grid(row=2, column=0, sticky="ew")
        ttk.Label(filtros, text="Mostrar:", style="Ajuda.TLabel").pack(side="left", padx=(0, 8))
        self.bt_filtro = {}
        for chave, rot in (("todos", "Todos"), ("ERRO", "Erro"), ("ATENCAO", "Atenção")):
            b = ttk.Button(filtros, text=rot, command=lambda k=chave: self._filtrar(k))
            b.pack(side="left", padx=(0, 6))
            self.bt_filtro[chave] = b
        ttk.Frame(c, style="Plano.TFrame", height=10).grid(row=3, column=0)
        acoes = ttk.Frame(c, style="Plano.TFrame")
        acoes.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(acoes, text="Dois cliques num achado abrem o PDF anotado.", style="Ajuda.TLabel").pack(side="left")
        ttk.Button(acoes, text="Abrir pasta", command=self._abrir_pasta).pack(side="right")
        ttk.Button(acoes, text="Abrir relatório", command=self._abrir_relatorio).pack(side="right", padx=(0, 8))
        ttk.Button(acoes, text="Abrir PDF anotado", style="Primario.TButton",
                   command=self._abrir_pdf).pack(side="right", padx=(0, 8))
        quadro = ttk.Frame(c, style="Plano.TFrame")
        quadro.grid(row=4, column=0, sticky="nsew")
        quadro.columnconfigure(0, weight=1)
        quadro.rowconfigure(0, weight=1)
        cols = ("arquivo", "indice", "folha", "sev", "regra", "comentario")
        self.tabela = ttk.Treeview(quadro, columns=cols, show="headings", selectmode="browse")
        for col, rot, w, anc in (("arquivo", "Arquivo", 190, "w"), ("indice", "Índice", 82, "w"), ("folha", "Folha", 50, "e"),
                                 ("sev", "Severidade", 86, "w"), ("regra", "Regra", 64, "w"),
                                 ("comentario", "Comentário", 260, "w")):
            self.tabela.heading(col, text=rot)
            self.tabela.column(col, width=w, anchor=anc, stretch=(col == "comentario"))
        self.tabela.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(quadro, orient="vertical", command=self.tabela.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tabela.configure(yscrollcommand=sb.set)
        self.tabela.bind("<Double-1>", lambda e: self._abrir_pdf())
        self.tabela.bind("<<TreeviewSelect>>", self._mostrar_detalhe)
        self.detalhe = ttk.Label(c, text="Selecione um achado para ver o comentário completo.", style="Detalhe.TLabel",
                                 wraplength=760, justify="left", anchor="w")
        self.detalhe.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        self._marcar_filtro()
        return c

    # tema ---------------------------------------------------------------------------------
    def _trocar_logo(self):
        """Logo oficial a 30 px: positivo no claro, negativo no escuro (MD §5)."""
        nome = "logo-promon-negativo.png" if self.escuro else "logo-promon-positivo.png"
        try:
            img = tk.PhotoImage(file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "img", nome))
            fator = max(1, round(img.height() / 30))
            self._img_logo = img.subsample(fator, fator)
            self.logo.configure(image=self._img_logo)
        except tk.TclError:
            self.logo.configure(text="Promon Engenharia")

    def _aplicar_tags(self):
        p = self.p
        # só a cor do texto + zebra: fundo cheio pesa numa lista longa; a severidade continua escrita
        self.tabela.tag_configure("ERRO", foreground=p["erro_fg"])
        self.tabela.tag_configure("ATENCAO", foreground=p["aten_fg"])
        self.tabela.tag_configure("par", background=p["surface_alt"])
        self.tabela.tag_configure("impar", background=p["surface"])
        self.lista.tag_configure("ok", foreground=p["ok_fg"])
        self.lista.tag_configure("falha", foreground=p["erro_fg"])

    def _vigiar_tema(self):
        escuro = tema.windows_escuro()
        if escuro != self.escuro:
            self.escuro = escuro
            self.p = tema.ESCURO if escuro else tema.CLARO
            tema.aplicar(self.root, self.p, self.fs)
            self._aplicar_tags()
            self._marcar_filtro()
            self._trocar_logo()
            tema.barra_titulo_escura(self.root, escuro)
        self.root.after(3000, self._vigiar_tema)

    # arquivos -----------------------------------------------------------------------------
    def _incluir(self, caminho: str):
        caminho = os.path.abspath(caminho)
        if not caminho.lower().endswith(".pdf") or caminho in self.caminhos.values():
            return
        iid = self.lista.insert("", "end", values=(os.path.basename(caminho), "na fila"))
        self.caminhos[iid] = caminho

    def _adicionar(self):
        for c in filedialog.askopenfilenames(parent=self.root, title="PDFs para verificar",
                                             filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")]):
            self._incluir(c)

    def _remover(self):
        for iid in self.lista.selection():
            self.caminhos.pop(iid, None)
            self.lista.delete(iid)

    def _limpar(self):
        for iid in list(self.caminhos):
            self.lista.delete(iid)
        self.caminhos.clear()

    def _escolher_ld(self):
        c = filedialog.askopenfilename(parent=self.root, title="Lista de Documentos do projeto",
                                       filetypes=[("Excel", "*.xlsx"), ("Todos", "*.*")])
        if c:
            self.var_ld.set(c)

    def _escolher_saida(self):
        c = filedialog.askdirectory(parent=self.root, title="Pasta de saída")
        if c:
            self.var_saida.set(c)

    # verificação ----------------------------------------------------------------------------
    def _verificar(self):
        if self.rodando:
            return
        itens = list(self.caminhos.items())
        if not itens:
            messagebox.showinfo(TITULO, "Adicione pelo menos um PDF.", parent=self.root)
            return
        op = nucleo.Opcoes(ld=self.var_ld.get().strip() or None, saida=self.var_saida.get().strip() or None,
                           sem_ficha=not self.var_ficha.get(), gerar_html=self.var_html.get(), gerar_csv=self.var_csv.get())
        self.rodando = True
        self.bt_verificar.state(["disabled"])
        self.progresso.configure(maximum=len(itens), value=0)
        threading.Thread(target=self._trabalhar, args=(itens, op), daemon=True).start()

    def _trabalhar(self, itens, op):
        """Thread de processamento. Pede a ficha à janela e espera a resposta."""
        for n, (iid, pdf) in enumerate(itens, 1):
            nome = os.path.basename(pdf)
            try:
                self.fila.put(("item", iid, "lendo…"))
                self.fila.put(("status", f"Lendo {nome} ({n} de {len(itens)})…"))
                pre = nucleo.preparar(pdf, self.cfg, op)
                ficha = None
                if not op.sem_ficha:
                    pedido = {"pronto": threading.Event(), "ficha": None}
                    self.fila.put(("ficha", pre, pedido))
                    pedido["pronto"].wait()
                    ficha = pedido["ficha"]
                self.fila.put(("item", iid, "verificando…"))
                self.fila.put(("status", f"Verificando {nome}…"))
                res = nucleo.finalizar(pre, ficha, self.cfg, op)
                self.fila.put(("resultado", iid, res, pre.avisos))
            except PermissionError as e:
                self.fila.put(("falha", iid, f"Não consegui gravar {os.path.basename(e.filename or '')}: o arquivo "
                                             f"está aberto em outro programa? Feche-o e verifique de novo."))
            except Exception as e:
                self.fila.put(("falha", iid, f"{type(e).__name__}: {e}"))
            self.fila.put(("progresso", n))
        self.fila.put(("fim",))

    def _ler_fila(self):
        try:
            while True:
                msg = self.fila.get_nowait()
                tipo = msg[0]
                if tipo == "status":
                    self.status.configure(text=msg[1])
                elif tipo == "item":
                    self._situacao(msg[1], msg[2])
                elif tipo == "progresso":
                    self.progresso.configure(value=msg[1])
                elif tipo == "ficha":
                    _, pre, pedido = msg
                    inicial = nucleo.ficha_inicial(pre, self.cfg)
                    valor = fichas.formulario_tk(pre.pdf, self.cfg, inicial, parent=self.root)
                    if valor is not None:
                        valor = fichas.deduzir(pre.pdf, self.cfg, valor)
                        fichas.gravar(fichas.caminho_ficha(pre.pdf, self.cfg), valor)
                    pedido["ficha"] = valor
                    pedido["pronto"].set()
                elif tipo == "resultado":
                    _, iid, res, avisos = msg
                    self.resultados.append(res)
                    n_erro = sum(a.severidade == "ERRO" for a in res.achados)
                    self._situacao(iid, f"{len(res.achados)} achado(s) · {n_erro} erro", "ok")
                    for a in res.achados:
                        self.linhas_resultado.append((res, a))
                    self._atualizar_resultado()
                    for av in avisos:
                        self.status.configure(text="Aviso: " + av)
                elif tipo == "falha":
                    _, iid, texto = msg
                    self._situacao(iid, "falhou", "falha")
                    messagebox.showerror(TITULO, f"{self.lista.set(iid, 'arquivo')}\n\n{texto}", parent=self.root)
                elif tipo == "fim":
                    self.rodando = False
                    self.bt_verificar.state(["!disabled"])
                    total = len(self.linhas_resultado)
                    self.status.configure(text=f"Concluído: {len(self.resultados)} arquivo(s), {total} achado(s). "
                                               f"Dê dois cliques num achado para abrir o PDF anotado.")
        except queue.Empty:
            pass
        self.root.after(100, self._ler_fila)

    def _situacao(self, iid, texto, tag=None):
        if self.lista.exists(iid):
            self.lista.set(iid, "situacao", texto)
            if tag:
                self.lista.item(iid, tags=(tag,))

    # resultado ------------------------------------------------------------------------------
    def _atualizar_resultado(self):
        from .anotador import tag as tag_cv
        self.tabela.delete(*self.tabela.get_children())
        self.mapa = {}
        cont = {"ERRO": 0, "ATENCAO": 0}
        n = 0
        for res, a in self.linhas_resultado:
            cont[a.severidade] = cont.get(a.severidade, 0) + 1
            if self.filtro != "todos" and a.severidade != self.filtro:
                continue
            rotulo = "ATENÇÃO" if a.severidade == "ATENCAO" else a.severidade
            n += 1
            iid = self.tabela.insert("", "end", tags=(a.severidade, "par" if n % 2 == 0 else "impar"), values=(
                os.path.basename(res.pdf), tag_cv(self.cfg, a), a.pagina + 1, rotulo, a.regra, a.texto))
            self.mapa[iid] = res
        self.kpi["total"].configure(text=str(len(self.linhas_resultado)))
        self.kpi["ERRO"].configure(text=str(cont.get("ERRO", 0)))
        self.kpi["ATENCAO"].configure(text=str(cont.get("ATENCAO", 0)))

    def _mostrar_detalhe(self, _=None):
        sel = self.tabela.selection()
        if sel:
            v = self.tabela.item(sel[0], "values")
            self.detalhe.configure(text=f"{v[1]} · folha {v[2]} · {v[3]} · {v[4]}\n{v[5]}")

    def _filtrar(self, chave):
        self.filtro = chave
        self._marcar_filtro()
        self._atualizar_resultado()

    def _marcar_filtro(self):
        for chave, b in self.bt_filtro.items():
            b.configure(style="FiltroAtivo.TButton" if chave == self.filtro else "Filtro.TButton")

    def _selecionado(self) -> nucleo.Resultado | None:
        sel = self.tabela.selection()
        if sel and sel[0] in getattr(self, "mapa", {}):
            return self.mapa[sel[0]]
        return self.resultados[-1] if self.resultados else None

    def _abrir_pdf(self):
        r = self._selecionado()
        if r:
            _abrir_arquivo(r.saida)

    def _abrir_relatorio(self):
        r = self._selecionado()
        if r and r.html:
            _abrir_arquivo(r.html)
        elif r:
            messagebox.showinfo(TITULO, "O relatório HTML não foi gravado (opção desligada).", parent=self.root)

    def _abrir_pasta(self):
        r = self._selecionado()
        if r:
            _abrir_arquivo(os.path.dirname(r.saida))

    def rodar(self) -> int:
        self.root.mainloop()
        return 0


def abrir(cfg: Config, pdfs: list[str] | None = None) -> int:
    return Janela(cfg, pdfs or []).rodar()
