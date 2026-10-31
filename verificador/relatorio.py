"""Saídas de lista de achados: CSV e relatório HTML."""
from __future__ import annotations

import csv
import datetime
import html as h
import os
from collections import Counter

from .anotador import tag
from .config import Config
from .modelo import Achado


def gravar_csv(caminho: str, arquivo_pdf: str, achados: list[Achado], cfg: Config) -> None:
    nc = cfg["nome_arquivo"]
    pt_mm = cfg["unidades"]["pt_para_mm"]
    with open(caminho, "w", newline="", encoding=nc["csv_encoding"]) as f:
        w = csv.writer(f, delimiter=nc["csv_separador"])
        w.writerow(["indice", "regra", "severidade", "folha", "ocorrencias", "comentario", "x_mm", "y_mm", "arquivo", "origem"])
        for a in achados:
            w.writerow([tag(cfg, a), a.regra, a.severidade, a.pagina + 1, 1 + len(a.extras), a.texto,
                        round(a.alvo.x0 * pt_mm), round(a.alvo.y0 * pt_mm), arquivo_pdf, a.dados.get("origem", "offline")])


# relatório HTML ---------------------------------------------------------------
# Identidade Promon (promon-parametros-formatacao.md §2, §2.1, §7.1). Autocontido: nada é baixado
# da internet; o modo claro/escuro segue o Windows pelo `prefers-color-scheme` do navegador.

_CSS = """
:root{--bg:#EDF1F4;--surface:#FFFFFF;--surface-alt:#F8FAFC;--surface-head:#F1F5F8;--surface-info:#F4F7F9;
--line:#E2E8EC;--line-strong:#CDD9E0;--line-field:#C9D3DB;--hover:#EAF2F8;--texto:#333F48;--texto-2:#5B6770;
--texto-3:#7C878E;--azul:#004976;--sobre-azul:#FFFFFF;--laranja:#E35205;--laranja-txt:#BE531C;--erro-bg:#F7E4E2;
--erro-fg:#911913;--aten-bg:#FBF0DD;--aten-fg:#8A5A00;--ok-bg:#E4F1EA;--ok-fg:#2E7D5B;--sombra:0 1px 2px rgba(16,42,67,.04);
--fonte:'Soleto','Mulish',Tahoma,Arial,sans-serif;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#141A20;--surface:#1D252D;
--surface-alt:#222B33;--surface-head:#22303B;--surface-info:#26394A;--line:#33404B;--line-strong:#3E4C57;
--line-field:#3E4C57;--hover:#26394A;--texto:#E6EBEF;--texto-2:#A2AAAD;--texto-3:#A2AAAD;--azul:#8DBBD3;
--sobre-azul:#141A20;--laranja:#FF671F;--laranja-txt:#FF9D6E;--erro-bg:#3A1E1C;--erro-fg:#F0A39C;
--aten-bg:#33291A;--aten-fg:#F2AB1C;--ok-bg:#16301F;--ok-fg:#7CC99E;--sombra:0 1px 2px rgba(0,0,0,.28);color-scheme:dark}
:root:not([data-theme="light"]) .logo.pos{display:none} :root:not([data-theme="light"]) .logo.neg{display:block}}
.logo{height:30px;width:auto;display:block;margin:6px} .logo.neg{display:none}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--texto);font:500 13px/1.45 var(--fonte);-webkit-font-smoothing:antialiased}
header{background:var(--surface);border-bottom:1px solid var(--line);padding:14px 28px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
header .regua{width:1px;align-self:stretch;background:var(--line)}
header h1{margin:0;font-size:18px;font-weight:800;color:var(--azul)}
header p{margin:2px 0 0;font-size:11.5px;color:var(--texto-3)}
header p b{color:var(--texto)}
.filete{height:2px;background:var(--laranja)}
main{max-width:1500px;margin:0 auto;padding:22px 28px}
h2{font-size:15px;font-weight:800;color:var(--azul);border-left:3px solid var(--laranja);padding-left:10px;margin:22px 0 12px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}
.cartao{background:var(--surface);border:1px solid var(--line);border-radius:6px;box-shadow:var(--sombra)}
.kpi{padding:16px}
.kpi .rot{font-size:10px;text-transform:uppercase;letter-spacing:.6px;color:var(--texto-3);font-weight:700}
.kpi .num{font-size:29px;font-weight:800;color:var(--azul);font-variant-numeric:tabular-nums}
.kpi.erro .num{color:var(--erro-fg)} .kpi.aten .num{color:var(--aten-fg)}
.kpi .sub{font-size:11px;color:var(--texto-3)}
.info{background:var(--surface-info);border:1px solid var(--line);border-radius:5px;padding:10px 12px;font-size:11.5px;color:var(--texto-2);margin-bottom:12px}
.filtros{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px;align-items:center}
button,select,input{font:inherit;color:var(--texto)}
.filtros button{background:var(--surface);border:1px solid var(--line-field);border-radius:5px;padding:6px 12px;cursor:pointer;color:var(--azul);font-weight:700}
.filtros button[aria-pressed=true]{border-color:var(--azul);box-shadow:inset 0 -2px 0 var(--laranja)}
.filtros button.prim{background:var(--azul);border-color:var(--azul);color:var(--sobre-azul);margin-left:auto}
.tabela{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12px;font-variant-numeric:tabular-nums}
thead th{background:var(--surface-head);color:var(--azul);font-size:10.5px;font-weight:700;text-align:center;
border-bottom:1.5px solid var(--line-strong);padding:8px;position:sticky;top:0}
tbody td{padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:nth-child(even){background:var(--surface-alt)} tbody tr:hover{background:var(--hover)}
td.num{text-align:right;white-space:nowrap}
td.cod{white-space:nowrap;font-family:Consolas,'Liberation Mono',monospace;font-size:11.5px}
.sev{display:inline-block;border-radius:3px;padding:2px 6px;font-size:10px;font-weight:800;letter-spacing:.3px}
.sev.ERRO{background:var(--erro-bg);color:var(--erro-fg)} .sev.ATENCAO{background:var(--aten-bg);color:var(--aten-fg)}
.sev.CORRETO{background:var(--ok-bg);color:var(--ok-fg)} .kpi.ok .num{color:var(--ok-fg)}
.origem{display:block;font-size:10.5px;color:var(--texto-3);font-family:var(--fonte)} .titulo-ra{font-weight:700}
select,input[type=text]{background:var(--surface);border:1px solid var(--line-field);border-radius:5px;padding:4px 6px}
select:focus,input:focus{outline:none;border-color:var(--azul)}
input[type=text]{width:100%;min-width:140px}
footer{max-width:1500px;margin:0 auto;padding:8px 28px 28px;font-size:11px;color:var(--texto-3)}
@media print{.filtros{display:none} thead th{position:static}}
"""

_JS = r"""
const chave='cev-avaliacao:'+document.body.dataset.arquivo;
let salvo={};try{salvo=JSON.parse(localStorage.getItem(chave)||'{}')}catch(e){}
document.querySelectorAll('tbody tr[data-id]').forEach(tr=>{const id=tr.dataset.id,s=tr.querySelector('select'),o=tr.querySelector('input');
 if(salvo[id]){s.value=salvo[id].a||'';o.value=salvo[id].o||''}
 const g=()=>{salvo[id]={a:s.value,o:o.value};try{localStorage.setItem(chave,JSON.stringify(salvo))}catch(e){}};
 s.addEventListener('change',g);o.addEventListener('input',g)});
document.querySelectorAll('.filtros button[data-f]').forEach(b=>b.addEventListener('click',()=>{
 document.querySelectorAll('.filtros button[data-f]').forEach(x=>x.setAttribute('aria-pressed',x===b));
 const f=b.dataset.f;document.querySelectorAll('tbody tr[data-id]').forEach(tr=>{tr.hidden=!(f==='todos'||tr.dataset.sev===f)})}));
document.getElementById('exportar').addEventListener('click',()=>{
 const linhas=[['indice','regra','severidade','folha','avaliacao','observacao','comentario']];
 document.querySelectorAll('tbody tr[data-id]').forEach(tr=>{const c=tr.querySelectorAll('td');
  linhas.push([c[0].innerText,c[3].innerText,tr.dataset.sev,c[1].innerText,tr.querySelector('select').value,tr.querySelector('input').value,c[4].innerText])});
 const csv='﻿'+linhas.map(l=>l.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(';')).join('\r\n');
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
 a.download=document.body.dataset.arquivo.replace(/\.pdf$/i,'')+'_avaliacao.csv';a.click()});
"""


def _logo(nome: str) -> str:
    """Logo oficial embutido (o relatório é um arquivo único, sem dependências)."""
    import base64
    import sys
    base = os.path.join(sys._MEIPASS, "verificador") if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "web", "img", nome), "rb") as f:
        return base64.b64encode(f.read()).decode()


def gravar_html(caminho: str, pdf: str, saida_pdf: str, achados: list[Achado], cfg: Config, ld: str | None) -> None:
    _LOGO_POS, _LOGO_NEG = _logo("logo-promon-positivo.png"), _logo("logo-promon-negativo.png")
    sev = Counter(a.severidade for a in achados)
    problemas = [a for a in achados if a.severidade != "CORRETO"]
    folhas = len({a.pagina for a in problemas})
    nome = os.path.basename(pdf)
    ra = cfg["revisao_assistida"]
    assistida = any(a.dados.get("origem") == "claude" for a in achados)
    linhas = []
    for a in achados:
        rotulo = {"ATENCAO": "ATENÇÃO"}.get(a.severidade, a.severidade)
        origem = ra["origem_rotulo"][a.dados.get("origem", "offline")]
        titulo = f'<span class="titulo-ra">{h.escape(a.dados["titulo"])}</span><br>' if a.dados.get("titulo") else ""
        t = h.escape(tag(cfg, a))
        linhas.append(
            f'<tr data-id="{t}" data-sev="{a.severidade}"><td class="cod">{t}</td><td class="num">{a.pagina + 1}</td>'
            f'<td><span class="sev {a.severidade}">{rotulo}</span></td><td class="cod">{a.regra}<span class="origem">{origem}</span></td>'
            f'<td>{titulo}{h.escape(a.texto)}</td><td class="num">{1 + len(a.extras)}</td>'
            f'<td><select aria-label="Avaliação"><option value="">—</option><option>procede</option>'
            f'<option>não procede</option></select></td><td><input type="text" aria-label="Observação"></td></tr>')
    corpo = "\n".join(linhas) or '<tr><td colspan="8">Nenhum achado.</td></tr>'
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    if assistida:
        subtitulo = "Verificação automática · CEV + revisão assistida (versão Claude)"
        rodape = ("Achados “Verificador”: regras locais e determinísticas. Achados “Revisão assistida”: análise do Claude "
                  "(licença enterprise), incluindo questões técnicas, a confirmar pelo verificador. A decisão final é do verificador.")
    else:
        subtitulo = "Verificação automática de apresentação · CEV"
        rodape = ("Processamento 100% local — nenhum arquivo foi enviado para fora deste computador. "
                  "O juízo técnico de engenharia é do verificador.")
    kpi_ok = (f'<div class="cartao kpi ok"><div class="rot">Correto</div><div class="num">{sev["CORRETO"]}</div>'
              f'<div class="sub">conferido, sem anotação no PDF</div></div>') if sev.get("CORRETO") else ""
    filtro_ok = (f'\n <button data-f="CORRETO" aria-pressed="false">Correto ({sev["CORRETO"]})</button>'
                 if sev.get("CORRETO") else "")
    doc = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verificação — {h.escape(nome)}</title><style>{_CSS}</style></head>
<body data-arquivo="{h.escape(nome)}">
<header><img class="logo pos" alt="Promon Engenharia" src="data:image/png;base64,{_LOGO_POS}">
<img class="logo neg" alt="Promon Engenharia" src="data:image/png;base64,{_LOGO_NEG}"><div class="regua"></div>
<div><h1>Verificador de Projetos — Arquitetura</h1><p>{subtitulo}</p></div>
<div class="regua"></div><div><p><b>{h.escape(nome)}</b></p>
<p>Gerado em {agora} · arquivo anotado: {h.escape(os.path.basename(saida_pdf))} · LD: {h.escape(os.path.basename(ld)) if ld else "nenhuma"}</p></div></header>
<div class="filete"></div>
<main>
<div class="kpis">
 <div class="cartao kpi"><div class="rot">Achados</div><div class="num">{len(problemas)}</div><div class="sub">em {folhas} folha(s)</div></div>
 <div class="cartao kpi erro"><div class="rot">Erro</div><div class="num">{sev.get('ERRO', 0)}</div><div class="sub">divergência objetiva</div></div>
 <div class="cartao kpi aten"><div class="rot">Atenção</div><div class="num">{sev.get('ATENCAO', 0)}</div><div class="sub">o verificador confirma</div></div>
{kpi_ok}</div>
<h2>Achados</h2>
<div class="info">Marque “procede” ou “não procede” em cada linha e use <b>Exportar avaliação</b> para guardar o
resultado do piloto. A avaliação fica salva neste computador enquanto os dados do navegador não forem limpos.</div>
<div class="filtros" role="group" aria-label="Filtrar">
 <button data-f="todos" aria-pressed="true">Todos ({len(achados)})</button>
 <button data-f="ERRO" aria-pressed="false">Erro ({sev.get('ERRO', 0)})</button>
 <button data-f="ATENCAO" aria-pressed="false">Atenção ({sev.get('ATENCAO', 0)})</button>{filtro_ok}
 <button id="exportar" class="prim">Exportar avaliação (CSV)</button>
</div>
<div class="cartao tabela">
<table><thead><tr><th>Índice</th><th>Folha</th><th>Severidade</th><th>Regra</th><th>Comentário</th><th>Ocorr.</th><th>Avaliação</th><th>Observação</th></tr></thead>
<tbody>
{corpo}
</tbody></table></div>
</main>
<footer>{rodape}</footer>
<script>{_JS}</script>
</body></html>"""
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(doc)
