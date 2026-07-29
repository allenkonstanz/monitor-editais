#!/usr/bin/env python3
import concurrent.futures
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests

from config import (
    FAPS,
    HISTORY_FILE,
    MAX_EDITAL_AGE_DAYS,
    OUTPUT_HTML_FILE,
    PALAVRAS_IGNORADAS,
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

# Timeout global para evitar travamentos longos (8 segundos)
TIMEOUT_HTTP = 8


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
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT_HTTP)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return BeautifulSoup(resp.text, "lxml")
  except Exception as e:
    logger.error(f"Erro/Timeout ao baixar {url}: {e}")
    return None


def extrair_resumo(url: str, max_chars: int = 350) -> str:
    # 1. Se a URL terminar em .pdf, já define como arquivo PDF diretamente
    if url.lower().endswith(".pdf"):
        return "Edital em formato PDF. Acesse o link oficial abaixo para visualizar o documento completo."

    try:
        # Fazer uma requisição HEAD ou GET leve para verificar o tipo de conteúdo
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT_HTTP, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "").lower()

        # 2. Se o servidor responder informando que o arquivo é PDF
        if "application/pdf" in content_type:
            return "Edital em formato PDF. Acesse o link oficial abaixo para visualizar o documento completo."

        # Garante a codificação correta para caracteres em português (acentos)
        resp.encoding = resp.apparent_encoding or "utf-8"
        
        # Lê o conteúdo HTML
        soup = BeautifulSoup(resp.text, "lxml")

        # Se o texto baixado começar com a assinatura de arquivo PDF (caso o Content-Type venha errado)
        if resp.text.startswith("%PDF"):
            return "Edital em formato PDF. Acesse o link oficial abaixo para visualizar o documento completo."

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

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

        texto_completo = " ".join(soup.get_text(separator=" ", strip=True).split())
        return texto_completo[:max_chars].rsplit(" ", 1)[0] + "..." if len(texto_completo) > 80 else "Consulte o edital completo no portal oficial."

    except Exception as e:
        logger.error(f"Erro ao extrair resumo de {url}: {e}")
        return "Consulte o edital completo no portal oficial."

  for tag in soup(
      ["script", "style", "nav", "footer", "header", "aside", "form"]
  ):
    tag.decompose()

  paragrafos = []
  for p in soup.find_all(["p", "div"]):
    t = p.get_text(" ", strip=True)
    if len(t) > 60 and not any(
        x in t.lower() for x in ["cookie", "javascript", "menu", "login"]
    ):
      paragrafos.append(t)
    if len(" ".join(paragrafos)) > max_chars:
      break

  if paragrafos:
    resumo = " ".join(paragrafos)
    return (
        resumo[:max_chars].rsplit(" ", 1)[0] + "..."
        if len(resumo) > max_chars
        else resumo
    )

  texto_completo = " ".join(soup.get_text(separator=" ", strip=True).split())
  return (
      texto_completo[:max_chars].rsplit(" ", 1)[0] + "..."
      if len(texto_completo) > 80
      else "Consulte o edital completo no portal oficial."
  )


def contem_palavras_ignoradas(texto: str) -> bool:
  texto_lower = texto.lower()
  return any(palavra.lower() in texto_lower for palavra in PALAVRAS_IGNORADAS)


def parser_generic(
    soup: BeautifulSoup, base_url: str, nome_fap: str, estado: str
) -> List[Dict]:
  editais = []
  vistos = set()
  palavras = [
      "edital",
      "chamada",
      "chamadas",
      "programa",
      "bolsa",
      "auxílio",
      "fomento",
  ]

  for a in soup.find_all("a", href=True):
    texto = a.get_text(" ", strip=True)
    href = a["href"]

    if not texto or len(texto) < 10:
      continue

    if any(p in texto.lower() for p in palavras):
      link = href if href.startswith("http") else urljoin(base_url, href)
      if link in vistos or any(
          x in link.lower() for x in ["#", "javascript:", "mailto:"]
      ):
        continue

      vistos.add(link)
      editais.append({
          "titulo": texto[:200],
          "link": link,
          "fonte": nome_fap,
          "estado": estado,
      })

  return editais[:10]  # Limita a 10 links por FAP para agilidade


def processar_fap(fap: dict, historico_ids: set) -> List[Dict]:
  if not fap.get("enabled"):
    return []

  nome = fap["nome"]
  url = fap["url"]
  logger.info(f"Verificando {nome}...")

  soup = baixar_pagina(url)
  if not soup:
    return []

  encontrados = parser_generic(soup, url, nome, fap["estado"])
  novos = []

  for ed in encontrados:
    eid = gerar_id(ed["titulo"], ed["link"])
    if eid in historico_ids:
      continue

    if contem_palavras_ignoradas(ed["titulo"]):
      historico_ids.add(eid)
      continue

    # Baixa o resumo apenas para itens realmente novos
    resumo = extrair_resumo(ed["link"])
    if contem_palavras_ignoradas(resumo):
      historico_ids.add(eid)
      continue

    ed["resumo"] = resumo
    ed["id"] = eid
    ed["detectado_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")

    historico_ids.add(eid)
    novos.append(ed)

  return novos


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
                        {ed.get('resumo', 'Consulte o edital completo no portal oficial.')}
                    </p>
                    <a href="{ed['link']}" target="_blank" rel="noopener noreferrer" class="btn btn-outline-primary btn-sm mt-3 w-100">
                        🔗 Acessar Edital Oficial
                    </a>
                </div>
                <div class="card-footer text-muted small text-end bg-light">
                    Detectado em: {ed.get('detectado_em', agora_str)}
                </div>
            </div>
        </div>
        """

  html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agregador de Editais FAPs - Painel Independente</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f4f6f9; font-family: system-ui, -apple-system, sans-serif; }}
        .hero {{ background: linear-gradient(135deg, #0d6efd, #084298); color: white; padding: 2.5rem 1rem; }}
        .card {{ transition: transform 0.2s, box-shadow 0.2s; border-radius: 8px; }}
        .card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important; }}
        .disclaimer-box {{ background-color: #fff3cd; border-left: 5px solid #ffc107; color: #856404; font-size: 0.9rem; padding: 1rem; border-radius: 4px; }}
    </style>
</head>
<body>

    <div class="hero text-center mb-4 shadow-sm">
        <div class="container">
            <h1 class="fw-bold">📢 Monitor de Editais FAPs</h1>
            <p class="mb-1">Plataforma independente de agregação e acompanhamento de oportunidades</p>
            <small class="opacity-75">Última checagem: {agora_str} | Total de editais monitorados: <strong>{len(editais)}</strong></small>
        </div>
    </div>

    <div class="container mb-5">

        <!-- DISCLAIMER LEGAL -->
        <div class="disclaimer-box mb-4 shadow-sm">
            <strong>⚠️ AVISO IMPORTANTE:</strong>
            Este site é um <strong>agregador independente</strong> e não possui vínculo, parceria ou chancela oficial com nenhuma Fundação de Amparo à Pesquisa (FAP) ou órgão governamental. 
            As informações são coletadas automaticamente. <strong>Sempre consulte as publicações originais, prazos e eventuais retificações nos portais oficiais informados.</strong>
        </div>

        <div class="row justify-content-center mb-4">
            <div class="col-md-8">
                <input type="text" id="searchInput" class="form-control form-control-lg shadow-sm" placeholder="🔍 Filtrar por palavra-chave, FAP ou Estado...">
            </div>
        </div>

        <div class="row" id="editaisContainer">
            {cards_html if cards_html else '<div class="col-12 text-center text-muted py-5"><h4>Nenhum edital encontrado no momento.</h4></div>'}
        </div>
    </div>

    <footer class="text-center py-4 text-muted border-top bg-white">
        <div class="container">
            <p class="mb-1 small">Projeto mantido de forma automática e independente.</p>
            <p class="mb-0 extra-small opacity-75">Respeitamos a privacidade e a LGPD. Não coletamos dados pessoais sem consentimento explícito.</p>
        </div>
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
  logger.info(f"✓ '{OUTPUT_HTML_FILE}' atualizado com sucesso!")


def executar_monitoramento():
  logger.info("Iniciando varredura otimizada e paralela...")
  dados = carregar_dados_salvos()
  historico_ids = set(dados.get("ids", []))
  editais_salvos = dados.get("editais", [])

  novos_editais = []

  # Executa até 8 FAPs simultaneamente para evitar concorrência abusiva e acelerar o tempo
  with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    futures = [
        executor.submit(processar_fap, fap, historico_ids) for fap in FAPS
    ]
    for future in concurrent.futures.as_completed(futures):
      res = future.result()
      if res:
        novos_editais.extend(res)

  editais_finais = novos_editais + editais_salvos
  salvar_dados({"ids": list(historico_ids), "editais": editais_finais})
  gerar_pagina_html(editais_finais)


if __name__ == "__main__":
  executar_monitoramento()
