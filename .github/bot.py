#!/usr/bin/env python3
import json
import time
import hashlib
import logging
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import (
    OUTPUT_HTML_FILE,
    MAX_EDITAL_AGE_DAYS,
    PALAVRAS_IGNORADAS,
    HISTORY_FILE,
    FAPS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("FAP-HTML-Generator")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def gerar_id(titulo: str, link: str) -> str:
    texto = f"{titulo.strip().lower()}|{link.strip().lower()}"
    return hashlib.md5(texto.encode("utf-8")).hexdigest()

def carregar_dados_salvos() -> dict:
    path = Path(HISTORY_FILE)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao carregar dados salvos: {e}")
    return {"ids": [], "editais": []}

def salvar_dados(dados: dict):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar dados: {e}")

def baixar_pagina(url: str) -> Optional[BeautifulSoup]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.error(f"Erro ao baixar {url}: {e}")
        return None

def extrair_resumo(url: str, max_chars: int = 400) -> str:
    soup = baixar_pagina(url)
    if not soup:
        return "Resumo não disponível."

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    texto_completo = " ".join(soup.get_text(separator=" ", strip=True).split())
    
    paragrafos = []
    for p in soup.find_all(["p", "div"]):
        t = p.get_text(" ", strip=True)
        if len(t) > 60 and not any(x in t.lower() for x in ["cookie", "javascript", "menu", "login"]):
            paragrafos.append(t)
        if len(" ".join(paragrafos)) > max_chars:
            break

    if paragrafos:
        resumo = " ".join(paragrafos)
        return resumo[:max_chars].rsplit(" ", 1)[0] + "..." if len(resumo) > max_chars else resumo

    return texto_completo[:max_chars].rsplit(" ", 1)[0] + "..." if len(texto_completo) > 80 else "Resumo não disponível."

def contem_palavras_ignoradas(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(palavra.lower() in texto_lower for palavra in PALAVRAS_IGNORADAS)

def parser_generic(soup: BeautifulSoup, base_url: str, nome_fap: str, estado: str) -> List[Dict]:
    editais = []
    vistos = set()
    palavras = ["edital", "chamada", "chamadas", "programa", "bolsa", "auxílio", "fomento"]

    for a in soup.find_all("a", href=True):
        texto = a.get_text(" ", strip=True)
        href = a["href"]

        if not texto or len(texto) < 12:
            continue

        if any(p in texto.lower() for p in palavras):
            link = href if href.startswith("http") else urljoin(base_url, href)
            if link in vistos or any(x in link.lower() for x in ["#", "javascript:", "mailto:"]):
                continue

            vistos.add(link)
            editais.append({"titulo": texto[:200], "link": link, "fonte": nome_fap, "estado": estado})

    return editais[:15]

def gerar_pagina_html(editais: List[Dict]):
    agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    
    cards_html = ""
    for ed in editais:
        cards_html += f"""
        <div class="col-md-6 col-lg-4 mb-4 edital-card" data-fonte="{ed['fonte']}" data-texto="{ed['titulo'].lower()} {ed.get('resumo', '').lower()}">
            <div class="card h-100 shadow-sm border-0">
                <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                    <strong>{ed['fonte']}</strong>
                    <small class="badge bg-light text-dark">{ed.get('estado', '')}</small>
                </div>
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title text-dark fs-6 fw-bold">{ed['titulo']}</h5>
                    <p class="card-text text-muted small flex-grow-1 mt-2">
                        {ed.get('resumo', 'Resumo não disponível.')}
                    </p>
                    <a href="{ed['link']}" target="_blank" class="btn btn-outline-primary btn-sm mt-3 w-100">
                        🔗 Acessar Edital Oficial
                    </a>
                </div>
                <div class="card-footer text-muted small text-end bg-light">
                    Coletado em: {ed.get('detectado_em', agora_str)}
                </div>
            </div>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Editais - FAPs</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f4f6f9; font-family: system-ui, -apple-system, sans-serif; }}
        .hero {{ background: linear-gradient(135deg, #0d6efd, #084298); color: white; padding: 2.5rem 1rem; }}
        .card {{ transition: transform 0.2s, box-shadow 0.2s; border-radius: 8px; }}
        .card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important; }}
    </style>
</head>
<body>

    <div class="hero text-center mb-4 shadow-sm">
        <div class="container">
            <h1 class="fw-bold">📢 Monitor de Editais FAPs</h1>
            <p class="mb-1">Atualização automática e acompanhamento de oportunidades</p>
            <small class="opacity-75">Última atualização: {agora_str} | Total de editais: <strong>{len(editais)}</strong></small>
        </div>
    </div>

    <div class="container mb-5">
        <div class="row justify-content-center mb-4">
            <div class="col-md-8">
                <input type="text" id="searchInput" class="form-control form-control-lg shadow-sm" placeholder="🔍 Filtrar por palavra-chave ou FAP...">
            </div>
        </div>

        <div class="row" id="editaisContainer">
            {cards_html if cards_html else '<div class="col-12 text-center text-muted py-5"><h4>Nenhum edital encontrado no momento.</h4></div>'}
        </div>
    </div>

    <footer class="text-center py-3 text-muted border-top bg-white">
        <small>Atualizado automaticamente pelo GitHub Actions.</small>
    </footer>

    <script>
        document.getElementById('searchInput').addEventListener('keyup', function() {{
            let filter = this.value.toLowerCase();
            let cards = document.querySelectorAll('.edital-card');

            cards.forEach(card => {{
                let texto = card.getAttribute('data-texto');
                let fonte = card.getAttribute('data-fonte').toLowerCase();
                if (texto.includes(filter) || fonte.includes(filter)) {{
                    card.style.display = '';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }});
    </script>
</body>
</html>
"""

    with open(OUTPUT_HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"✓ '{OUTPUT_HTML_FILE}' atualizado!")

def executar_monitoramento():
    logger.info("Iniciando varredura...")
    dados = carregar_dados_salvos()
    historico_ids = set(dados.get("ids", []))
    editais_salvos = dados.get("editais", [])

    novos_editais = []

    for fap in FAPS:
        if not fap.get("enabled"):
            continue

        nome = fap["nome"]
        url = fap["url"]
        logger.info(f"Verificando {nome}...")

        soup = baixar_pagina(url)
        if not soup:
            continue

        encontrados = parser_generic(soup, url, nome, fap["estado"])

        for ed in encontrados:
            eid = gerar_id(ed["titulo"], ed["link"])
            if eid in historico_ids:
                continue

            if contem_palavras_ignoradas(ed["titulo"]):
                historico_ids.add(eid)
                continue

            resumo = extrair_resumo(ed["link"])
            if contem_palavras_ignoradas(resumo):
                historico_ids.add(eid)
                continue

            ed["resumo"] = resumo
            ed["id"] = eid
            ed["detectado_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            historico_ids.add(eid)
            novos_editais.append(ed)

    editais_finais = novos_editais + editais_salvos
    salvar_dados({"ids": list(historico_ids), "editais": editais_finais})
    gerar_pagina_html(editais_finais)

if __name__ == "__main__":
    executar_monitoramento()
