# ============================================================
# CONFIGURAÇÕES DO MONITOR DE EDITAIS - FAPs (GERADOR HTML)
# ============================================================

# Nome do arquivo HTML que será gerado
OUTPUT_HTML_FILE = "index.html"

# Intervalo de verificação para execução local (1 semana)
CHECK_INTERVAL_MINUTES = 10080

# Prazo máximo dos editais em dias
MAX_EDITAL_AGE_DAYS = 30

# Palavras-chave para ignorar editais
PALAVRAS_IGNORADAS = [
    "mestrado",
    "doutorado",
    "pós-graduação",
    "pos-graduacao",
    "stricto sensu",
]

# Arquivo onde o bot guarda o histórico de editais
HISTORY_FILE = "editais_vistos.json"

# ============================================================
# LISTA DE FAPs DO BRASIL
# ============================================================
FAPS = [
    # --- NORTE ---
    {"nome": "FAPEAM", "estado": "Amazonas", "url": "https://www.fapeam.am.gov.br/editais/", "enabled": True, "parser": "generic"},
    {"nome": "FAPESPA", "estado": "Pará", "url": "https://www.fapespa.pa.gov.br/chamadas-publicas", "enabled": True, "parser": "generic"},
    {"nome": "FAPERO", "estado": "Rondônia", "url": "https://fapero.ro.gov.br/category/chamadas-publicas/", "enabled": True, "parser": "generic"},
    {"nome": "FAPT", "estado": "Tocantins", "url": "https://www.to.gov.br/fapt/editais", "enabled": True, "parser": "generic"},
    {"nome": "FAPEAP", "estado": "Amapá", "url": "https://fapeap.ap.gov.br/editais", "enabled": True, "parser": "generic"},
    {"nome": "FAPAC", "estado": "Acre", "url": "https://fapac.ac.gov.br/editais/", "enabled": True, "parser": "generic"},
    {"nome": "FAPERR", "estado": "Roraima", "url": "https://faperr.rr.gov.br/editais/", "enabled": True, "parser": "generic"},

    # --- NORDESTE ---
    {"nome": "FAPEAL", "estado": "Alagoas", "url": "https://www.fapeal.br/category/editais/", "enabled": True, "parser": "fapeal"},
    {"nome": "FAPESB", "estado": "Bahia", "url": "http://www.fapesb.ba.gov.br/category/editais/", "enabled": True, "parser": "generic"},
    {"nome": "FUNCAP", "estado": "Ceará", "url": "https://www.funcap.ce.gov.br/categoria/editais/", "enabled": True, "parser": "generic"},
    {"nome": "FAPEMA", "estado": "Maranhão", "url": "https://www.fapema.br/category/editais/", "enabled": True, "parser": "generic"},
    {"nome": "FAPESQ", "estado": "Paraíba", "url": "https://fapesq.rpp.br/editais", "enabled": True, "parser": "generic"},
    {"nome": "FACEPE", "estado": "Pernambuco", "url": "https://www.facepe.br/editais/", "enabled": True, "parser": "generic"},
    {"nome": "FAPEPI", "estado": "Piauí", "url": "https://fapepi.pi.gov.br/category/editais/", "enabled": True, "parser": "generic"},
    {"nome": "FAPERN", "estado": "Rio Grande do Norte", "url": "http://www.fapern.rn.gov.br/Conteudo.asp?TRAN=ITEM&ID=14", "enabled": True, "parser": "generic"},
    {"nome": "FAPITEC", "estado": "Sergipe", "url": "https://fapitec.se.gov.br/category/editais/", "enabled": True, "parser": "generic"},

    # --- CENTRO-OESTE ---
    {"nome": "FAPDF", "estado": "Distrito Federal", "url": "https://www.fap.df.gov.br/chamadas-publicas/", "enabled": True, "parser": "generic"},
    {"nome": "FAPEG", "estado": "Goiás", "url": "https://www.fapeg.go.gov.br/editais/", "enabled": True, "parser": "generic"},
    {"nome": "FAPEMAT", "estado": "Mato Grosso", "url": "http://www.fapemat.mt.gov.br/editais", "enabled": True, "parser": "generic"},
    {"nome": "FUNDECT", "estado": "Mato Grosso do Sul", "url": "https://www.fundect.ms.gov.br/editais-abertos/", "enabled": True, "parser": "generic"},

    # --- SUDESTE ---
    {"nome": "FAPES", "estado": "Espírito Santo", "url": "https://fapes.es.gov.br/editais", "enabled": True, "parser": "generic"},
    {"nome": "FAPEMIG", "estado": "Minas Gerais", "url": "https://fapemig.br/pt/chamadas_abertas_flow/", "enabled": True, "parser": "generic"},
    {"nome": "FAPERJ", "estado": "Rio de Janeiro", "url": "https://www.faperj.br/?id=20.5.8", "enabled": True, "parser": "generic"},
    {"nome": "FAPESP", "estado": "São Paulo", "url": "https://fapesp.br/chamadas", "enabled": True, "parser": "generic"},

    # --- SUL ---
    {"nome": "FA", "estado": "Paraná", "url": "https://www.fundaoraucaria.org.br/Chamadas-Abertas", "enabled": True, "parser": "generic"},
    {"nome": "FAPERGS", "estado": "Rio Grande do Sul", "url": "https://fapergs.rs.gov.br/editais", "enabled": True, "parser": "generic"},
    {"nome": "FAPESC", "estado": "Santa Catarina", "url": "https://fapesc.sc.gov.br/categoria/editais/", "enabled": True, "parser": "generic"},
]
