"""Janela da ferramenta em HTML (pywebview + WebView2 do Windows), na identidade Promon.

A página (`web/index.html`) é local e não carrega nada da internet. Esta classe `Api` é a ponte:
cada método é chamado pelo JavaScript como `pywebview.api.<método>()` e roda numa thread própria.
Modo claro/escuro: o WebView2 segue o Windows (`prefers-color-scheme`); a barra de título acompanha.
"""
from __future__ import annotations

import csv
import datetime
import json
import os
import sys
import uuid

from . import ficha as fichas
from . import nucleo
from .anotador import tag
from .config import Config


def _pasta_web() -> str:
    if getattr(sys, "frozen", False):                       # executável PyInstaller
        return os.path.join(sys._MEIPASS, "verificador", "web")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


def _info(caminho: str) -> dict:
    c = os.path.abspath(caminho)
    return {"caminho": c, "nome": os.path.basename(c), "pasta": os.path.dirname(c)}


def _barra_titulo(janela, escuro: bool) -> None:
    """Barra de título do Windows no mesmo tema (só aparência)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = janela.native.Handle.ToInt32()
        valor = ctypes.c_int(1 if escuro else 0)
        for atributo in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, atributo, ctypes.byref(valor), ctypes.sizeof(valor)) == 0:
                break
    except Exception:
        pass


class Api:
    def __init__(self, cfg: Config, pdfs: list[str]):
        self._cfg = cfg
        self._iniciais = [p for p in pdfs if p.lower().endswith(".pdf") and os.path.isfile(p)]
        self._preparos: dict[str, nucleo.Preparo] = {}
        self._resultados: list[nucleo.Resultado] = []
        self._janela = None

    # usado pelo Python ------------------------------------------------------------------
    def _definir_janela(self, janela):
        self._janela = janela

    def _opcoes(self, op: dict) -> nucleo.Opcoes:
        return nucleo.Opcoes(ld=(op.get("ld") or None), saida=(op.get("saida") or None),
                             sem_ficha=not op.get("usar_ficha", True),
                             gerar_csv=bool(op.get("csv")), gerar_html=bool(op.get("html")))

    # chamados pela página -------------------------------------------------------------
    def configuracao(self) -> dict:
        fc = self._cfg["ficha"]
        from . import ld as ld_mod
        prefs = {"csv": self._cfg["saidas"]["csv"], "html": self._cfg["saidas"]["html"], "usar_ficha": True}
        prefs.update({k: v for k, v in ld_mod.ler_preferencias().items() if k in prefs})
        return {
            "campos": [{"id": c, "rotulo": fc["rotulos"][c], "ajuda": fc["ajuda"][c]} for c in fc["campos"]],
            "iniciais": [_info(p) for p in self._iniciais],
            "preferencias": prefs,
        }

    def salvar_preferencias(self, prefs: dict) -> None:
        from . import ld as ld_mod
        atual = ld_mod.ler_preferencias()
        atual.update({k: bool(v) for k, v in prefs.items() if k in ("csv", "html", "usar_ficha")})
        ld_mod.gravar_preferencias(atual)

    def escolher_pdfs(self) -> list[dict]:
        import webview
        r = self._janela.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=True,
                                            file_types=("PDF (*.pdf)", "Todos os arquivos (*.*)"))
        return [_info(p) for p in (r or []) if p.lower().endswith(".pdf")]

    def escolher_ld(self) -> str:
        import webview
        r = self._janela.create_file_dialog(webview.FileDialog.OPEN,
                                            file_types=("Excel (*.xlsx)", "Todos os arquivos (*.*)"))
        return r[0] if r else ""

    def escolher_pasta(self) -> str:
        import webview
        r = self._janela.create_file_dialog(webview.FileDialog.FOLDER)
        return r[0] if r else ""

    def preparar(self, caminho: str, opcoes: dict) -> dict:
        """Lê o PDF, acha a LD e devolve a ficha pré-preenchida (sem gravar nada)."""
        try:
            pre = nucleo.preparar(caminho, self._cfg, self._opcoes(opcoes))
            pid = uuid.uuid4().hex
            self._preparos[pid] = pre
            ld = None
            if pre.ld:
                ld = {"caminho": pre.caminho_ld, "nome": os.path.basename(pre.caminho_ld), "docs": len(pre.ld.docs)}
            return {"id": pid, "nome": os.path.basename(caminho), "operacao": pre.operacao, "ld": ld,
                    "ficha": nucleo.ficha_inicial(pre, self._cfg), "avisos": pre.avisos}
        except Exception as e:
            return {"erro": f"{type(e).__name__}: {e}"}

    def finalizar(self, pid: str, ficha: dict | None, opcoes: dict) -> dict:
        pre = self._preparos.pop(pid, None)
        if pre is None:
            return {"erro": "Preparação não encontrada; verifique de novo."}
        try:
            if ficha is not None:
                ficha = fichas.deduzir(pre.pdf, self._cfg, {k: (v or "").strip() for k, v in ficha.items()})
                fichas.gravar(fichas.caminho_ficha(pre.pdf, self._cfg), ficha)
            res = nucleo.finalizar(pre, ficha, self._cfg, self._opcoes(opcoes))
            self._resultados.append(res)
            return {
                "nome": os.path.basename(res.pdf), "saida": res.saida, "html": res.html, "csv": res.csv,
                "ld": os.path.basename(res.caminho_ld) if res.caminho_ld else "", "avisos": pre.avisos,
                "achados": [{"indice": tag(self._cfg, a), "folha": a.pagina + 1, "sev": a.severidade,
                             "regra": a.regra, "texto": a.texto, "ocorrencias": 1 + len(a.extras)}
                            for a in res.achados],
            }
        except PermissionError as e:
            return {"erro": f"Não consegui gravar {os.path.basename(e.filename or '')}: o arquivo está aberto em "
                            f"outro programa? Feche-o e verifique de novo."}
        except Exception as e:
            return {"erro": f"{type(e).__name__}: {e}"}

    def abrir(self, caminho: str) -> bool:
        if caminho and os.path.exists(caminho) and sys.platform == "win32":
            os.startfile(caminho)  # noqa: S606 — abre no programa padrão do Windows
            return True
        return False

    def abrir_pasta(self, caminho: str) -> bool:
        return self.abrir(os.path.dirname(caminho) if os.path.isfile(caminho) else caminho)

    def salvar_avaliacao(self, linhas: list[dict]) -> dict:
        """Grava a avaliação do piloto (procede / não procede) ao lado do primeiro arquivo anotado."""
        if not linhas:
            return {"erro": "Nenhuma avaliação marcada."}
        pasta = os.path.dirname(self._resultados[0].saida) if self._resultados else os.getcwd()
        nome = "avaliacao_" + datetime.datetime.now().strftime("%Y%m%d_%H%M") + ".csv"
        caminho = os.path.join(pasta, nome)
        try:
            with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["arquivo", "indice", "regra", "severidade", "folha", "avaliacao", "observacao", "comentario"])
                for l in linhas:
                    w.writerow([l.get(k, "") for k in ("arquivo", "indice", "regra", "sev", "folha",
                                                       "avaliacao", "observacao", "texto")])
            return {"caminho": caminho}
        except OSError as e:
            return {"erro": str(e)}

    def tema(self, escuro: bool) -> None:
        if self._janela:
            _barra_titulo(self._janela, bool(escuro))


def _ligar_arrastar(janela, api: Api):
    """PDFs arrastados para dentro da janela: o WebView2 entrega o caminho completo de cada arquivo."""
    from webview.dom import DOMEventHandler

    def soltar(e):
        caminhos = [f.get("pywebviewFullPath") for f in e.get("dataTransfer", {}).get("files", [])]
        infos = [_info(c) for c in caminhos if c and c.lower().endswith(".pdf")]
        if infos:
            janela.evaluate_js(f"app.incluir({json.dumps(infos)})")

    doc = janela.dom.document
    doc.events.dragover += DOMEventHandler(lambda e: None, prevent_default=True)
    doc.events.drop += DOMEventHandler(soltar, prevent_default=True)


def abrir(cfg: Config, pdfs: list[str] | None = None, tema_forcado: str | None = None, ao_iniciar=None) -> int:
    import webview

    api = Api(cfg, pdfs or [])
    pagina = os.path.join(_pasta_web(), "index.html")
    from pathlib import Path
    url = Path(pagina).as_uri() + (f"#tema={tema_forcado}" if tema_forcado else "")
    janela = webview.create_window("Verificador de Projetos — Arquitetura — CEV automática", url=url, js_api=api,
                                   width=1360, height=880, min_size=(1100, 700), background_color="#EDF1F4")
    api._definir_janela(janela)

    def iniciar(w):
        _ligar_arrastar(w, api)
        if ao_iniciar:
            ao_iniciar(w)

    webview.start(iniciar, janela, gui="edgechromium", private_mode=True)
    return 0
