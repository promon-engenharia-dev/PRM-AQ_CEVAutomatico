"""Ficha da emissão (gabarito): leitura, dedução, formulário e gravação."""
from __future__ import annotations

import glob
import json
import os
import re

from .config import Config
from .regras import classe_documento

SEM_REV = r"(_R[0-9A-Z]{1,2}|-P_[A-Z0-9]{1,2})?(_CEV\d*)?(_auto)?$"


def caminho_ficha(pdf: str, cfg: Config) -> str:
    base = os.path.splitext(pdf)[0]
    base = re.sub(r"(_CEV\d*)?(_auto)?$", "", base)
    return base + cfg["ficha"]["arquivo_sufixo"]


def ler(caminho: str) -> dict | None:
    if os.path.isfile(caminho):
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    return None


def gravar(caminho: str, ficha: dict) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(ficha, f, ensure_ascii=False, indent=2)


def ficha_anterior(pdf: str, cfg: Config) -> dict | None:
    """Ficha de outra revisão do mesmo documento na mesma pasta (a mais recente)."""
    pasta = os.path.dirname(os.path.abspath(pdf))
    numero = re.sub(SEM_REV, "", os.path.splitext(os.path.basename(pdf))[0])
    cands = [c for c in glob.glob(os.path.join(pasta, "*" + cfg["ficha"]["arquivo_sufixo"]))
             if os.path.basename(c).startswith(numero)]
    cands.sort(key=os.path.getmtime, reverse=True)
    return ler(cands[0]) if cands else None


def deduzir(pdf: str, cfg: Config, ficha: dict) -> dict:
    f = dict(ficha)
    nome = os.path.splitext(os.path.basename(pdf))[0]
    if not f.get("classe_documento"):
        c = classe_documento(nome, cfg, {})
        if c:
            f["classe_documento"] = c
    rev = str(f.get("revisao", "")).strip()
    if not f.get("esquema_revisao") and rev:
        if rev.isalpha():
            f["esquema_revisao"] = "alfabetico"
        elif rev.isdigit() and rev != "0":
            f["esquema_revisao"] = "numerico"
    return f


def obter(pdf: str, cfg: Config, formulario: bool = True, sugestao: dict | None = None) -> dict | None:
    """Ficha existente; senão, formulário pré-preenchido (revisão anterior, depois a LD em `sugestao`)."""
    cam = caminho_ficha(pdf, cfg)
    existente = ler(cam)
    if existente is not None and not formulario:
        return deduzir(pdf, cfg, existente)
    if not formulario:
        return None
    base = dict(existente or ficha_anterior(pdf, cfg) or {})
    for k, v in (sugestao or {}).items():
        if v and not base.get(k):
            base[k] = v
    base = deduzir(pdf, cfg, base)
    resultado = formulario_tk(pdf, cfg, base)
    if resultado is None:
        return None
    resultado = deduzir(pdf, cfg, resultado)
    gravar(cam, resultado)
    return resultado


class _Dica:
    """Caixa explicativa que aparece ao passar o mouse sobre o nome do campo."""

    def __init__(self, widget, texto, p=None, fonte=None):
        self.widget, self.texto, self.janela = widget, texto, None
        self.p, self.fonte = p or {}, fonte
        widget.bind("<Enter>", self.mostrar)
        widget.bind("<Leave>", self.esconder)

    def mostrar(self, _=None):
        import tkinter as tk
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.janela = tk.Toplevel(self.widget)
        self.janela.wm_overrideredirect(True)
        self.janela.wm_geometry(f"+{x}+{y}")
        tk.Label(self.janela, text=self.texto, justify="left", wraplength=380,
                 background=self.p.get("surface_info", "#F4F7F9"), foreground=self.p.get("texto", "#333F48"),
                 highlightbackground=self.p.get("line_strong", "#CDD9E0"), highlightthickness=1,
                 font=self.fonte, padx=8, pady=6).pack()

    def esconder(self, _=None):
        if self.janela:
            self.janela.destroy()
            self.janela = None


def formulario_tk(pdf: str, cfg: Config, inicial: dict, parent=None) -> dict | None:
    """Ficha da emissão. Com `parent`, abre como janela modal da interface; sem, como janela própria."""
    import tkinter as tk
    from tkinter import ttk
    from . import tema

    p = tema.paleta()
    if parent is None:
        raiz = tk.Tk()
        fs = tema.fontes(raiz)
        tema.aplicar(raiz, p, fs)
    else:
        raiz = tk.Toplevel(parent)
        raiz.transient(parent)
        fs = tema.fontes(raiz)
        raiz.configure(bg=p["bg"])
    raiz.title("Ficha da emissão — " + os.path.basename(pdf))
    raiz.resizable(False, False)
    tema.barra_titulo_escura(raiz, p is tema.ESCURO)

    fc = cfg["ficha"]
    externo = ttk.Frame(raiz, padding=16)
    externo.grid(sticky="nsew")
    cartao = ttk.Frame(externo, style="Cartao.TFrame", padding=(18, 14))
    cartao.grid(sticky="nsew")
    ttk.Label(cartao, text="Ficha da emissão", style="Secao.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
    ttk.Label(cartao, text=os.path.basename(pdf), style="Ajuda.TLabel").grid(row=1, column=0, columnspan=2, sticky="w")
    ttk.Label(cartao, text="Valores CORRETOS esperados para esta emissão. Passe o mouse sobre o nome de cada campo "
                           "para ver a explicação. Campos vazios não são comparados.",
              style="Ajuda.TLabel", wraplength=560).grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 12))
    entradas = {}
    for i, campo in enumerate(fc["campos"], 3):
        rot = ttk.Label(cartao, text=fc["rotulos"][campo] + "  ⓘ", style="Campo.TLabel", cursor="question_arrow")
        rot.grid(row=i, column=0, sticky="w", padx=(0, 14), pady=3)
        _Dica(rot, fc["ajuda"][campo], p, fs["pequena"])
        if campo == "esquema_revisao":
            w = ttk.Combobox(cartao, values=["", "alfabetico", "numerico"], width=55, state="readonly")
            w.set(inicial.get(campo, ""))
            w.grid(row=i, column=1, sticky="w", pady=3)
        elif campo == "ld":
            linha = ttk.Frame(cartao, style="Cartao.TFrame")
            linha.grid(row=i, column=1, sticky="w", pady=3)
            w = ttk.Entry(linha, width=50)
            w.insert(0, str(inicial.get(campo, "") or ""))
            w.pack(side="left")

            def escolher(e=w):
                from tkinter import filedialog
                c = filedialog.askopenfilename(parent=raiz, title="Lista de Documentos do projeto",
                                               filetypes=[("Excel", "*.xlsx"), ("Todos", "*.*")])
                if c:
                    e.delete(0, "end")
                    e.insert(0, c)
            ttk.Button(linha, text="Escolher…", command=escolher).pack(side="left", padx=(6, 0))
        else:
            w = ttk.Entry(cartao, width=58)
            w.insert(0, str(inicial.get(campo, "") or ""))
            w.grid(row=i, column=1, sticky="w", pady=3)
        entradas[campo] = w
    saida = {"valor": None}

    def ok(_=None):
        saida["valor"] = {c: e.get().strip() for c, e in entradas.items()}
        raiz.destroy()

    def sem(_=None):
        saida["valor"] = None
        raiz.destroy()

    botoes = ttk.Frame(externo)
    botoes.grid(sticky="e", pady=(12, 0))
    ttk.Button(botoes, text="Verificar sem ficha", command=sem).pack(side="right", padx=(8, 0))
    ttk.Button(botoes, text="Salvar ficha e verificar", style="Primario.TButton", command=ok).pack(side="right")
    raiz.bind("<Return>", ok)
    raiz.bind("<Escape>", sem)
    if parent is None:
        raiz.mainloop()
    else:
        raiz.grab_set()
        raiz.focus_set()
        parent.wait_window(raiz)
    return saida["valor"]


def ajuda_texto(cfg: Config) -> str:
    fc = cfg["ficha"]
    return "\n".join(f"{fc['rotulos'][c]} ({c}):\n    {fc['ajuda'][c]}" for c in fc["campos"])
