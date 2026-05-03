"""
Catálogo ontologico expandido de tipos de entidade.
Mapeia dominios, keywords heuristicas e aliases para inferencia de tipo.
"""

from typing import Dict, List, Literal

# ---------------------------------------------------------------------------
# Taxonomia Actor vs Non-Actor
# ---------------------------------------------------------------------------

ACTOR_ENTITY_TYPES: frozenset[str] = frozenset({
    "Person",
    "Student",
    "Professor",
    "Expert",
    "PublicFigure",
    "Official",
    "Journalist",
    "Celebrity",
    "Executive",
    "Lawyer",
    "Doctor",
    "Organization",
    "University",
    "Company",
    "GovernmentAgency",
    "MediaOutlet",
    "Hospital",
    "School",
    "NGO",
    "SocialMediaPlatform",
})

NON_ACTOR_ENTITY_TYPES: frozenset[str] = frozenset({
    "Concept",
    "Event",
    "Location",
    "Technology",
    "Product",
    "Artefact",
})

ENTITY_TYPE_DESCRIPTIONS: Dict[str, str] = {
    # Atores sociais
    "Person": "Individuo capaz de expressar opiniao e interagir em redes sociais.",
    "Student": "Ator social ativo em comunidades academicas e plataformas digitais.",
    "Professor": "Ator social com voz em debates academicos e midia.",
    "Expert": "Ator social que participa de discussoes publicas como especialista.",
    "PublicFigure": "Ator social com alta visibilidade e capacidade de influencia.",
    "Official": "Representante de governo ou instituicao com voz oficial.",
    "Journalist": "Ator social que produz e dissemina conteudo na midia.",
    "Celebrity": "Figura publica com grande alcance em redes sociais.",
    "Executive": "Lider empresarial com voz em debates de negocios.",
    "Lawyer": "Profissional do direito que participa de discussoes juridicas.",
    "Doctor": "Profissional de saude com voz em debates de saude publica.",
    "Organization": "Entidade coletiva que pode atuar como agente institutional.",
    "University": "Instituicao de ensino com presenca e voz em redes sociais.",
    "Company": "Empresa com capacidade de comunicacao institutional.",
    "GovernmentAgency": "Orgao governamental com voz oficial.",
    "MediaOutlet": "Veiculo de comunicacao com capacidade de disseminar informacao.",
    "Hospital": "Instituicao de saude com presenca publica e voz institucional.",
    "School": "Instituicao educacional com presenca em comunidades.",
    "NGO": "Organizacao nao-governamental com voz em causas sociais.",
    "SocialMediaPlatform": "Plataforma digital como ator do ecossistema de informacao.",
    # Nao-atores
    "Concept": "Entidade abstrata; nao possui voz propria em rede social.",
    "Event": "Ocorrencia temporal; nao pode postar ou interagir.",
    "Location": "Lugar geografico; deve ser modelado como atributo de um ator.",
    "Technology": "Ferramenta ou sistema; nao tem agency social.",
    "Product": "Bem ou servico; nao e agente de simulacao social.",
    "Artefact": "Objeto material ou documento; nao participa de interacoes sociais.",
}


def classify_actor_status(entity_type: str) -> Literal["actor", "non_actor", "unknown"]:
    """Classifica um tipo de entidade como ator, nao-ator ou desconhecido."""
    if not entity_type:
        return "unknown"
    resolved = resolve_entity_type(entity_type)
    if resolved in ACTOR_ENTITY_TYPES:
        return "actor"
    if resolved in NON_ACTOR_ENTITY_TYPES:
        return "non_actor"
    return "unknown"


# ---------------------------------------------------------------------------
# Catalogo ontologico expandido
# ---------------------------------------------------------------------------

ENTITY_TYPE_CATALOG: Dict[str, List[str]] = {
    "Health": [
        "Hospital", "Doctor", "Patient", "PharmaceuticalCompany",
        "MedicalResearcher", "HealthAgency", "MedicalDevice", "Nurse",
    ],
    "Marketing": [
        "Brand", "Influencer", "AdvertisingAgency", "Consumer",
        "MediaPlatform", "MarketingCampaign", "Product", "MarketAnalyst",
    ],
    "Law": [
        "LawFirm", "Judge", "Lawyer", "Court",
        "LegalOrganization", "Legislation", "RegulatoryAgency", "Prosecutor",
    ],
    "Economy": [
        "Bank", "Company", "Investor", "StockExchange",
        "Startup", "Entrepreneur", "FinancialAnalyst", "Corporation",
    ],
    "Geopolitics": [
        "GovernmentAgency", "PublicFigure", "PoliticalParty", "Country",
        "MilitaryOrganization", "Diplomat", "NGO", "InternationalOrganization",
    ],
    "General": [
        "Person", "Organization", "University", "MediaOutlet",
        "Expert", "Student", "Event", "Location", "Technology", "Concept",
    ],
}

ENTITY_KEYWORD_MAP: Dict[str, List[str]] = {
    "Person": [
        "pessoa", "individuo", "cidadão", "cidadã", "humano", "nascido", "nascida",
        "morador", "residente", "habitante", "personalidade", "figura", "protagonista",
        "autor", "artista", "escritor", "compositor", "diretor", "ator", "atriz",
    ],
    "Organization": [
        "organização", "instituição", "entidade", "associação", "fundação",
        "cooperativa", "sociedade", "grupo", "holdings", "conglomerado",
        "corporação", "consórcio", "sindicato", "federação", "confederação",
    ],
    "GovernmentAgency": [
        "ministério", "secretaria", "agência", "órgão", "tribunal", "câmara",
        "senado", "prefeitura", "governo", "instituto federal", "estadual",
        "municipal", "departamento", "autarquia", "repartição",
    ],
    "PublicFigure": [
        "político", "deputado", "senador", "prefeito", "presidente", "vereador",
        "ministro", "governador", "candidato", "eleito", "líder", "ativista",
        "jornalista", "celebridade", "influenciador",
    ],
    "Expert": [
        "professor", "pesquisador", "cientista", "médico", "economista",
        "advogado", "doutor", "phd", "especialista", "consultor", "analista",
        "engenheiro", "acadêmico", "sociólogo", "antropólogo",
    ],
    "MediaOutlet": [
        "jornal", "revista", "portal", "tv", "televisão", "rádio", "blog",
        "site", "mídia", "imprensa", "emissora", "canal", "publicação",
        "veículo", "comunicação",
    ],
    "University": [
        "universidade", "faculdade", "instituto federal", "escola técnica",
        "centro universitário", "academia", "colégio", "escola", "ensino",
        "educação", "graduação", "pós-graduação", "campus", "reitoria",
    ],
    "Student": [
        "aluno", "estudante", "graduação", "mestrado", "doutorado",
        "universitário", "discente", "bolsista", "calouro", "veterano",
        "acadêmico", "pupilo", "aprendiz", "trainee", "estagiário",
    ],
    "Hospital": [
        "hospital", "clínica", "pronto-socorro", "enfermaria", "unidade de saúde",
        "posto de saúde", "ambulatório", "centro médico", "sanatório",
        "maternidade", "urgência", "emergência", "uti", "centro cirúrgico",
        "enfermeiro", "enfermeira", "laboratório clínico",
    ],
    "Doctor": [
        "médico", "doutor", "dr.", "cirurgião", "cardiologista", "neurologista",
        "pediatra", "clínico", "psiquiatra", "ortopedista", "dermatologista",
        "oncologista", "anestesista", "radiologista", "patologista",
    ],
    "PharmaceuticalCompany": [
        "farmacêutica", "laboratório", "indústria farmacêutica", "biótica",
        "farmácia", "drogaria", "medicamento", "vacina", "remédio", "fármaco",
        "biofarmacêutica", "genérico", "prescrito", "clínico", "pesquisa clínica",
    ],
    "Company": [
        "empresa", "companhia", "corporação", "sociedade", "firma", "negócio",
        "comércio", "indústria", "multinacional", "startup", "s/a", "ltda",
        "mei", "holding", "grupo empresarial",
    ],
    "Bank": [
        "banco", "instituição financeira", "cooperativa de crédito",
        "caixa econômica", "fintech", "financeira", "investimento", "corretora",
        "seguradora", "bolsa de valores", "mercado financeiro", "capital",
        "fundo", "tesouraria", "caixa",
    ],
    "LawFirm": [
        "escritório de advocacia", "advogado", "sociedade de advogados",
        "consultoria jurídica", "defensoria", "procuradoria", "assessoria jurídica",
        "departamento legal", "compliance", "jurídico", "magistrado", "promotor",
        "defensor", "juiz", "desembargador",
    ],
    "Lawyer": [
        "advogado", "advogada", "procurador", "procuradora", "defensor",
        "defensora", "solicitador", "solicitadora", "jurista", "bacharel em direito",
        "advogado trabalhista", "advogado criminalista", "advogado civil",
        "advogado tributarista", "advogado previdenciário",
    ],
    "Event": [
        "evento", "conferência", "cimeira", "summit", "encontro", "reunião",
        "congresso", "seminário", "workshop", "festa", "celebração",
        "cerimônia", "inauguração", "lançamento", "mercado",
    ],
    "Location": [
        "local", "lugar", "cidade", "estado", "país", "região", "município",
        "bairro", "distrito", "zona", "área", "território", "província",
        "departamento", "condado", "nação",
    ],
    "Technology": [
        "tecnologia", "software", "hardware", "plataforma", "aplicativo", "app",
        "sistema", "algoritmo", "inteligência artificial", "ia", "machine learning",
        "blockchain", "protocolo", "framework", "banco de dados",
    ],
    "Product": [
        "produto", "mercadoria", "bem", "serviço", "commodity", "item",
        "artefato", "equipamento", "dispositivo", "aparelho", "instrumento",
        "ferramenta", "gadget", "modelo", "versão",
    ],
    "Concept": [
        "conceito", "teoria", "modelo", "hipótese", "paradigma", "framework",
        "índice", "métrica", "indicador", "variável", "taxa", "princípio",
        "ideia", "abordagem", "método",
    ],
    "NGO": [
        "ong", "organização não governamental", "organização social",
        "entidade filantrópica", "instituição beneficente", "associação civil",
        "fundação", "voluntariado", "advocacy", "ativismo", "direitos humanos",
        "ambientalista", "comunidade", "desenvolvimento", "assistência social",
    ],
    "MilitaryOrganization": [
        "exército", "forças armadas", "marinha", "aeronáutica", "exército",
        "tropas", "comando militar", "base militar", "arsenal", "defesa",
        "ministério da defesa", "estado-maior", "batalhão", "brigada", "regimento",
    ],
    "Diplomat": [
        "embaixador", "embaixada", "cônsul", "consulado", "diplomata",
        "missão diplomática", "chanceler", "ministro das relações exteriores",
        "negociador", "mediador internacional", "representante", "delegado",
        "enviado", "agregado", "adido",
    ],
    "Investor": [
        "investidor", "venture capital", "vc", "fundo de investimento",
        "angel investor", "anjo", "private equity", "acionista", "sócio",
        "patrocinador", "capitalista", "financiador", "apoiador", "investidora",
        "cotista",
    ],
    "Influencer": [
        "influenciador", "influenciadora", "criador de conteúdo", "youtuber",
        "streamer", "blogger", "digital creator", "personalidade digital",
        "celebridade digital", "tiktokeiro", "instagrammer", "podcaster",
        "vlogger", "content creator", "nano influencer",
    ],
    "Patient": [
        "paciente", "internado", "internada", "utente", "doente", "enfermo",
        "enferma", "portador", "portadora", "beneficiário", "beneficiária",
        "usuário do sus", "usuária do sus", "convênio", "plano de saúde",
    ],
    "HealthAgency": [
        "agência de saúde", " vigilância sanitária", "ans", "oms", "ministério da saúde",
        "secretaria de saúde", "conselho de medicina", "crm", "coren", "cfo",
        "agência nacional", "regulador sanitário", "agência reguladora",
        "autoridade sanitária", " órgão regulador",
    ],
    "PoliticalParty": [
        "partido político", "partido", "legenda", "coligação", "aliança",
        "frente política", "movimento político", "agremiação", "diretório",
        "executiva", "comitê", "convenção partidária", "filiação", "militância",
        "liderança partidária",
    ],
    "Country": [
        "país", "nação", "estado-nação", "república", "monarquia", "federação",
        "confederação", "nação soberana", "território nacional", "patria",
        "homeland", "estado membro", "membro da onu", "nação membro",
        "país membro",
    ],
    "MarketAnalyst": [
        "analista de mercado", "analista financeiro", "analista de ações",
        "consultor de investimentos", "estrategista", "econometrista",
        "analista quantitativo", "research analyst", "analista de risco",
        "analista de crédito", "analista de renda fixa", "analista de equities",
        "consultor econômico", "pesquisador de mercado",
    ],
    "Startup": [
        "startup", "scale-up", "empresa emergente", "empresa de base tecnológica",
        "ebt", "unicórnio", "centaur", "venture", "aceleradora", "incubadora",
        "pitch", "mvp", "produto mínimo viável", "early stage", "seed",
    ],
    "Entrepreneur": [
        "empreendedor", "empreendedora", "fundador", "fundadora", "ceo",
        "diretor executivo", "proprietário", "proprietária", "gestor", "gestora",
        "executivo", "executiva", "businessman", "businesswoman", " Visionário",
    ],
    "FinancialAnalyst": [
        "analista financeiro", "analista de finanças", "controller", " controlling",
        "tesoureiro", "tesoureira", "contador", "contadora", "auditor", "auditora",
        "cfo", "diretor financeiro", "planejador financeiro", "consultor fiscal",
        "especialista em finanças",
    ],
    "Corporation": [
        "corporação", "holding", "conglomerado", "multinacional", "grupo empresarial",
        "sociedade anônima", "s/a", "companhia aberta", "capital aberto",
        " corporativa", "grupo econômico", "trust", "cartel", "monopólio",
    ],
    "StockExchange": [
        "bolsa de valores", "bolsa", "mercado de capitais", "b3", "nasdaq",
        "nyse", "ibovespa", "índice bovespa", "corretora", "home broker",
        "day trade", "swing trade", "mercado acionário", "ações", "títulos",
    ],
    "LegalOrganization": [
        "organização jurídica", "instituição jurídica", "órgão jurisdicional",
        "poder judiciário", "supremo tribunal", "superior tribunal",
        "tribunal de justiça", "tribunal regional", "vara", "forum",
        "conselho da magistratura", "corregedoria", "oab", "ordem dos advogados",
    ],
    "Legislation": [
        "legislação", "lei", "decreto", "portaria", "resolução", "norma",
        "regulamento", "estatuto", "código", "constituição", "emenda",
        "projeto de lei", "medida provisória", "decreto-lei", "súmula",
    ],
    "RegulatoryAgency": [
        "agência reguladora", "regulador", "aneel", "anatel", "ans", "anvisa",
        "bacen", "banco central", "cvm", "conselho", "autarquia reguladora",
        " órgão regulador", "autoridade reguladora", "fiscalizador", "superintendência",
    ],
    "Prosecutor": [
        "promotor", "promotora", "procurador", "procuradora", "ministério público",
        "mp", "mpf", "mpm", "deltan", "denunciador", "acusador", "acusadora",
        "representante do mp", "procuradoria-geral", "promotoria",
    ],
    "Judge": [
        "juiz", "juíza", "desembargador", "desembargadora", "ministro", "ministra",
        "magistrado", "magistrada", "árbitro", "árbitra", "conciliador",
        "conciliadora", "mediador", "mediadora", "relator", "relatora",
    ],
    "Court": [
        "tribunal", "vara", "forum", "fórum", "corte", "corte suprema",
        "corte especial", "juizado", "juizado especial", "câmara", "câmara criminal",
        "câmara cível", "turma", "secção", "sessão",
    ],
    "AdvertisingAgency": [
        "agência de publicidade", "agência de propaganda", "publicitária",
        "anunciante", "media agency", "digital agency", "agência criativa",
        "agência full service", "agência de mídia", "agência de marketing",
        "produtora", "produtora de conteúdo", "agência btl", "agência atl",
        "house agency",
    ],
    "Consumer": [
        "consumidor", "consumidora", "cliente", "comprador", "compradora",
        "usuário", "usuária", "utilizador", "utilizadora", "público-alvo",
        "target", "demanda", "demandante", "freguês", "freguesa",
    ],
    "MediaPlatform": [
        "plataforma de mídia", "rede social", "social media", "streaming",
        "plataforma digital", "portal", "marketplace", "ecommerce", "e-commerce",
        "aplicativo de mídia", " aggregator", "plataforma de conteúdo",
        "plataforma de vídeo", "plataforma de áudio", "community",
    ],
    "Brand": [
        "marca", "brand", "logo", "identidade visual", "trademark", "patente",
        "franquia", "franchising", "linha de produto", "portfolio", "griffe",
        "label", "selo", "certificação", "certification",
    ],
    "MarketingCampaign": [
        "campanha de marketing", "campanha publicitária", "campanha",
        "ação de marketing", "promoção", "promotional", "lançamento de produto",
        "roadshow", "feira", "exposição", "evento de lançamento", "pré-lançamento",
        "branding", "rebranding", "posicionamento",
    ],
    "MedicalResearcher": [
        "pesquisador médico", "pesquisador clínico", "pesquisador em saúde",
        "cientista da saúde", "investigador clínico", "coordenador de estudo",
        "principal investigator", "pi", "pesquisador principal", "pesquisador associado",
        "pesquisador sênior", "pesquisador júnior", "pesquisador em biologia",
        "pesquisador em genética", "pesquisador em imunologia",
    ],
    "MedicalDevice": [
        "dispositivo médico", "equipamento médico", "aparelho médico",
        "instrumento médico", "prótese", "ortese", "cadeira de rodas", "andador",
        "marcapasso", "desfibrilador", "ventilador mecânico", "ecg", "eletrocardiograma",
        "ressonância magnética", "tomógrafo", "ultrassom", "endoscópio",
    ],
    "Nurse": [
        "enfermeiro", "enfermeira", "técnico de enfermagem", "auxiliar de enfermagem",
        "tecenf", "auxenf", "enfermeiro chefia", "enfermeiro supervisor",
        "enfermeiro especialista", "enfermeiro obstetra", "enfermeiro pediátrico",
        "enfermeiro uti", "enfermeiro psiquiátrico", "enfermeiro home care",
    ],
    "InternationalOrganization": [
        "organização internacional", "organização multilateral", "onu", "uno",
        "nato", "otan", "omc", "unesco", "oms", "fmi", "bce", "banco mundial",
        "g7", "g20", "brics", " União Europeia", "mercosul", "oas",
    ],
}

ENTITY_TYPE_ALIASES: Dict[str, str] = {
    # Organization variants
    "Corporation": "Organization",
    "Firm": "Organization",
    "Institution": "Organization",
    "Association": "Organization",
    "Foundation": "Organization",
    # Person variants
    "Individual": "Person",
    "Human": "Person",
    "Citizen": "Person",
    # PublicFigure variants
    "Politician": "PublicFigure",
    "PoliticalFigure": "PublicFigure",
    "Celebrity": "PublicFigure",
    "Official": "PublicFigure",
    "Leader": "PublicFigure",
    # Doctor variants
    "Physician": "Doctor",
    "Clinician": "Doctor",
    "Medic": "Doctor",
    # Hospital variants
    "Clinic": "Hospital",
    "HealthCenter": "Hospital",
    "MedicalCenter": "Hospital",
    # Expert variants
    "Researcher": "Expert",
    "Scientist": "Expert",
    "Academic": "Expert",
    "Professor": "Expert",
    "Scholar": "Expert",
    # MediaOutlet variants
    "NewsOutlet": "MediaOutlet",
    "Press": "MediaOutlet",
    "NewsAgency": "MediaOutlet",
    "Broadcasting": "MediaOutlet",
    # University variants
    "School": "University",
    "College": "University",
    "Institute": "University",
    "Academy": "University",
    # Company variants
    "Enterprise": "Company",
    "Business": "Company",
    "Multinational": "Company",
    "Corporation": "Company",
    # Bank variants
    "FinancialInstitution": "Bank",
    "Cooperative": "Bank",
    "Fintech": "Bank",
    "InsuranceCompany": "Bank",
    # LawFirm variants
    "LawOffice": "LawFirm",
    "LegalFirm": "LawFirm",
    # Lawyer variants
    "Attorney": "Lawyer",
    "Solicitor": "Lawyer",
    "LegalAdvisor": "Lawyer",
    "Jurist": "Lawyer",
    # Location variants
    "City": "Location",
    "State": "Location",
    "Nation": "Location",
    "Region": "Location",
    # Country (specific location)
    "Country": "Location",
    # GovernmentAgency variants
    "Government": "GovernmentAgency",
    "Ministry": "GovernmentAgency",
    "Department": "GovernmentAgency",
    "PublicAgency": "GovernmentAgency",
    # NGO variants
    "NonProfit": "NGO",
    "CivilSociety": "NGO",
    "Charity": "NGO",
    # Technology variants
    "Software": "Technology",
    "App": "Technology",
    "Platform": "Technology",
    # Product variants
    "Drug": "Product",
    "Medicine": "Product",
    "Device": "Product",
    "Equipment": "Product",
    # Event variants
    "Conference": "Event",
    "Summit": "Event",
    "Meeting": "Event",
    "Ceremony": "Event",
    # Student variants
    "Pupil": "Student",
    "Learner": "Student",
    "Trainee": "Student",
    # Military
    "Army": "MilitaryOrganization",
    "ArmedForces": "MilitaryOrganization",
    "Navy": "MilitaryOrganization",
    "AirForce": "MilitaryOrganization",
    # Diplomat
    "Ambassador": "Diplomat",
    "Embassy": "Diplomat",
    "Consul": "Diplomat",
    # Investor
    "VentureCapital": "Investor",
    "VC": "Investor",
    "Fund": "Investor",
    "AngelInvestor": "Investor",
    # Influencer
    "ContentCreator": "Influencer",
    "Blogger": "Influencer",
    "Streamer": "Influencer",
    "YouTuber": "Influencer",
    # Patient
    "SickPerson": "Patient",
    "IllPerson": "Patient",
    # HealthAgency
    "HealthRegulator": "HealthAgency",
    # PoliticalParty
    "Party": "PoliticalParty",
    # MarketAnalyst
    "EquityAnalyst": "MarketAnalyst",
    "ResearchAnalyst": "MarketAnalyst",
    # Startup
    "Unicorn": "Startup",
    "ScaleUp": "Startup",
    # Entrepreneur
    "Founder": "Entrepreneur",
    "Businessman": "Entrepreneur",
    "Businesswoman": "Entrepreneur",
    # FinancialAnalyst
    "Accountant": "FinancialAnalyst",
    "Auditor": "FinancialAnalyst",
    # StockExchange
    "Exchange": "StockExchange",
    # LegalOrganization
    "Judiciary": "LegalOrganization",
    # Legislation
    "Law": "Legislation",
    "Statute": "Legislation",
    # RegulatoryAgency
    "Regulator": "RegulatoryAgency",
    # Prosecutor
    "DistrictAttorney": "Prosecutor",
    # Judge
    "Magistrate": "Judge",
    # Court
    "JudicialCourt": "Court",
    # AdvertisingAgency
    "AdAgency": "AdvertisingAgency",
    # Consumer
    "Buyer": "Consumer",
    "User": "Consumer",
    # MediaPlatform
    "SocialNetwork": "MediaPlatform",
    "StreamingPlatform": "MediaPlatform",
    # Brand
    "Trademark": "Brand",
    # MarketingCampaign
    "Campaign": "MarketingCampaign",
    # MedicalResearcher
    "ClinicalResearcher": "MedicalResearcher",
    # MedicalDevice
    "MedicalEquipment": "MedicalDevice",
    # Nurse
    "NursingProfessional": "Nurse",
    # InternationalOrganization
    "MultilateralOrganization": "InternationalOrganization",
    "GlobalOrganization": "InternationalOrganization",
}


def resolve_entity_type(raw_type: str) -> str:
    """Normaliza um tipo de entidade via aliases; retorna o tipo canonico ou o original."""
    if not raw_type:
        return raw_type
    return ENTITY_TYPE_ALIASES.get(raw_type, raw_type)


def infer_entity_type_from_text(text: str) -> str:
    """
    Inferencia heuristica de tipo de entidade baseada em texto.
    Usa ENTITY_KEYWORD_MAP como fonte unica de heuristicas.
    Retorna o tipo com maior score ou 'Entity' se nenhum match.
    """
    text_lower = text.lower()
    scores: Dict[str, int] = {}
    for entity_type, keywords in ENTITY_KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[entity_type] = score
    if scores:
        return max(scores, key=scores.get)
    return "Entity"


def infer_entity_type_second_pass(name: str, summary: str) -> str:
    """
    Segunda passada de inferencia mais agressiva.
    Tenta match apenas no nome, depois apenas no summary.
    """
    # Passo 1: nome isolado
    name_type = infer_entity_type_from_text(name)
    if name_type != "Entity":
        return name_type

    # Passo 2: summary isolado
    summary_type = infer_entity_type_from_text(summary)
    if summary_type != "Entity":
        return summary_type

    # Passo 3: matching parcial por palavra (somente keyword dentro da palavra,
    # evitando falsos positivos de palavras curtas dentro de keywords longas)
    words = (name + " " + summary).lower().split()
    for entity_type, keywords in ENTITY_KEYWORD_MAP.items():
        for kw in keywords:
            kw_lower = kw.lower()
            if len(kw_lower) < 4:
                continue
            for word in words:
                if kw_lower in word:
                    return entity_type

    return "Entity"
