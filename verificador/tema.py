"""Identidade visual Promon para a janela (Tkinter), com modo claro/escuro seguindo o Windows.

Tokens de `promon-parametros-formatacao.md` (§1, §2, §2.1 e §7.1). Regras aplicadas:
laranja só como acento (filete, aba ativa); texto corrido em cinza #333F48; azul em títulos e
no botão principal; uma cor nunca é o único indicador (ERRO/ATENÇÃO sempre escritos).
"""
from __future__ import annotations

import sys

CLARO = {
    "bg": "#EDF1F4", "surface": "#FFFFFF", "surface_alt": "#F8FAFC", "surface_head": "#F1F5F8",
    "surface_info": "#F4F7F9", "line": "#E2E8EC", "line_strong": "#CDD9E0", "line_field": "#C9D3DB",
    "hover": "#EAF2F8", "texto": "#333F48", "texto_2": "#5B6770", "texto_3": "#7C878E",
    "azul": "#004976", "azul_hover": "#01426A", "sobre_azul": "#FFFFFF",
    "laranja": "#E35205", "laranja_texto": "#BE531C",
    "erro_bg": "#F7E4E2", "erro_fg": "#911913", "aten_bg": "#FBF0DD", "aten_fg": "#8A5A00",
    "ok_bg": "#E4F1EA", "ok_fg": "#2E7D5B", "selecao": "#E4EDF3",
}
ESCURO = {
    "bg": "#141A20", "surface": "#1D252D", "surface_alt": "#222B33", "surface_head": "#22303B",
    "surface_info": "#26394A", "line": "#33404B", "line_strong": "#3E4C57", "line_field": "#3E4C57",
    "hover": "#26394A", "texto": "#E6EBEF", "texto_2": "#A2AAAD", "texto_3": "#A2AAAD",
    "azul": "#8DBBD3", "azul_hover": "#A9CCDF", "sobre_azul": "#141A20",
    "laranja": "#FF671F", "laranja_texto": "#FF9D6E",
    "erro_bg": "#3A1E1C", "erro_fg": "#F0A39C", "aten_bg": "#33291A", "aten_fg": "#F2AB1C",
    "ok_bg": "#16301F", "ok_fg": "#7CC99E", "selecao": "#2A3F52",
}


def windows_escuro() -> bool:
    """True quando o Windows está em modo escuro para aplicativos (leitura do registro, sem alterar nada)."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
            return winreg.QueryValueEx(k, "AppsUseLightTheme")[0] == 0
    except OSError:
        return False


def paleta() -> dict:
    return ESCURO if windows_escuro() else CLARO


def familia_fonte(root) -> str:
    """Soleto (instalada nas máquinas Promon) → Arial → Tahoma (MD §3)."""
    from tkinter import font
    disponiveis = {f.lower() for f in font.families(root)}
    for f in ("Soleto", "Arial", "Tahoma"):
        if f.lower() in disponiveis:
            return f
    return "TkDefaultFont"


def fontes(root) -> dict:
    """Escala de interface do MD (px): 10 / 11,5 / 13 / 15 / 18 / 29. Tamanho negativo = pixels no Tk."""
    f = familia_fonte(root)
    return {
        "base": (f, -13), "media": (f, -13, "bold"), "pequena": (f, -11), "mini": (f, -10),
        "h1": (f, -18, "bold"), "h2": (f, -15, "bold"), "kpi": (f, -29, "bold"),
        "rotulo": (f, -10, "bold"),
    }


def barra_titulo_escura(janela, escuro: bool) -> None:
    """Barra de título do Windows no mesmo tema (DWMWA_USE_IMMERSIVE_DARK_MODE). Só aparência."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        janela.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(janela.winfo_id())
        valor = ctypes.c_int(1 if escuro else 0)
        for atributo in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, atributo, ctypes.byref(valor), ctypes.sizeof(valor)) == 0:
                break
    except Exception:
        pass


def aplicar(root, p: dict, fs: dict) -> None:
    """Estilos ttk (tema 'clam', o único que aceita todas as cores)."""
    from tkinter import ttk
    st = ttk.Style(root)
    st.theme_use("clam")
    root.configure(bg=p["bg"])
    st.configure(".", background=p["bg"], foreground=p["texto"], font=fs["base"],
                 bordercolor=p["line"], lightcolor=p["line"], darkcolor=p["line"],
                 troughcolor=p["surface_alt"], focuscolor=p["azul"], fieldbackground=p["surface"],
                 selectbackground=p["selecao"], selectforeground=p["texto"], insertcolor=p["texto"])
    st.configure("TFrame", background=p["bg"])
    st.configure("Cartao.TFrame", background=p["surface"], bordercolor=p["line"], relief="solid", borderwidth=1)
    st.configure("Cabecalho.TFrame", background=p["surface"])
    st.configure("Plano.TFrame", background=p["surface"], borderwidth=0, relief="flat")
    st.configure("Filete.TFrame", background=p["laranja"])
    st.configure("Linha.TFrame", background=p["line"])
    st.configure("TLabel", background=p["bg"], foreground=p["texto"])
    st.configure("Cartao.TLabel", background=p["surface"])
    st.configure("Titulo.TLabel", background=p["surface"], foreground=p["azul"], font=fs["h1"])
    st.configure("Subtitulo.TLabel", background=p["surface"], foreground=p["texto_3"], font=fs["pequena"])
    st.configure("Secao.TLabel", background=p["surface"], foreground=p["azul"], font=fs["h2"])
    st.configure("Ajuda.TLabel", background=p["surface"], foreground=p["texto_2"], font=fs["pequena"])
    st.configure("Rotulo.TLabel", background=p["surface"], foreground=p["texto_3"], font=fs["rotulo"])
    st.configure("Kpi.TLabel", background=p["surface"], foreground=p["azul"], font=fs["kpi"])
    st.configure("KpiErro.TLabel", background=p["surface"], foreground=p["erro_fg"], font=fs["kpi"])
    st.configure("KpiAten.TLabel", background=p["surface"], foreground=p["aten_fg"], font=fs["kpi"])
    st.configure("Status.TLabel", background=p["bg"], foreground=p["texto_2"], font=fs["pequena"])
    st.configure("Aviso.TLabel", background=p["surface"], foreground=p["laranja_texto"], font=fs["pequena"])
    st.configure("Campo.TLabel", background=p["surface"], foreground=p["texto"], font=fs["base"])
    # botões
    st.configure("TButton", background=p["surface"], foreground=p["azul"], bordercolor=p["line_field"],
                 lightcolor=p["surface"], darkcolor=p["surface"], padding=(12, 6), font=fs["media"], relief="solid")
    st.map("TButton", background=[("active", p["hover"]), ("disabled", p["surface_alt"])],
           foreground=[("disabled", p["texto_3"])])
    st.configure("Primario.TButton", background=p["azul"], foreground=p["sobre_azul"], bordercolor=p["azul"],
                 lightcolor=p["azul"], darkcolor=p["azul"])
    st.map("Primario.TButton", background=[("active", p["azul_hover"]), ("disabled", p["line_strong"])],
           foreground=[("disabled", p["texto_3"])])
    st.configure("Filtro.TButton", padding=(10, 4))
    st.configure("FiltroAtivo.TButton", background=p["surface_head"], foreground=p["azul"], bordercolor=p["azul"],
                 lightcolor=p["surface_head"], darkcolor=p["laranja"], padding=(10, 4))
    st.map("FiltroAtivo.TButton", background=[("active", p["hover"])])
    # campos
    st.configure("TEntry", fieldbackground=p["surface"], foreground=p["texto"], bordercolor=p["line_field"],
                 lightcolor=p["line_field"], darkcolor=p["line_field"], padding=5)
    st.map("TEntry", bordercolor=[("focus", p["azul"])], lightcolor=[("focus", p["azul"])])
    st.configure("TCombobox", fieldbackground=p["surface"], foreground=p["texto"], background=p["surface"],
                 bordercolor=p["line_field"], arrowcolor=p["azul"], padding=4)
    st.map("TCombobox", fieldbackground=[("readonly", p["surface"])], foreground=[("readonly", p["texto"])],
           selectbackground=[("readonly", p["surface"])], selectforeground=[("readonly", p["texto"])])
    root.option_add("*TCombobox*Listbox.background", p["surface"])
    root.option_add("*TCombobox*Listbox.foreground", p["texto"])
    st.configure("TCheckbutton", background=p["surface"], foreground=p["texto"], indicatorcolor=p["surface"],
                 indicatorbackground=p["surface"])
    st.configure("TCheckbutton", indicatorforeground=p["sobre_azul"], indicatorbackground=p["surface"],
                 indicatorrelief="flat", indicatormargin=(0, 0, 6, 0))
    st.map("TCheckbutton", indicatorbackground=[("selected", p["azul"])], indicatorcolor=[("selected", p["azul"])],
           indicatorforeground=[("selected", p["sobre_azul"])], background=[("active", p["surface"])])
    # tabela
    st.configure("Treeview", background=p["surface"], fieldbackground=p["surface"], foreground=p["texto"],
                 bordercolor=p["line"], rowheight=24, font=fs["base"])
    st.map("Treeview", background=[("selected", p["selecao"])], foreground=[("selected", p["texto"])])
    st.configure("Treeview.Heading", background=p["surface_head"], foreground=p["azul"], font=fs["rotulo"],
                 bordercolor=p["line_strong"], relief="flat", padding=(6, 6))
    st.map("Treeview.Heading", background=[("active", p["hover"])])
    st.configure("Vertical.TScrollbar", background=p["line_strong"], bordercolor=p["surface"], arrowcolor=p["texto_3"],
                 troughcolor=p["surface"], lightcolor=p["line_strong"], darkcolor=p["line_strong"])
    st.map("Vertical.TScrollbar", background=[("active", p["texto_3"])])
    st.configure("Detalhe.TLabel", background=p["surface_info"], foreground=p["texto"], font=fs["base"],
                 padding=(10, 8), bordercolor=p["line"], relief="solid", borderwidth=1)
    st.configure("Horizontal.TProgressbar", background=p["azul"], troughcolor=p["line"], bordercolor=p["line"])
