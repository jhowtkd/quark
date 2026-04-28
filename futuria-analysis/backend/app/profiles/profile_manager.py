"""
Profile Manager Module for Futur.ia

Provides specialized user profiles that configure the entire pipeline:
- Persona generation prompts and parameters
- Report generation prompts and rules
- Simulation configuration overrides
- Deep research focus areas
- Language validation rules

Profiles: MARKETING, DIREITO, ECONOMIA, SAUDE, GENERICO
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class UserProfile(str, Enum):
    """Perfil de usuario disponiveis no sistema"""
    MARKETING = "marketing"
    DIREITO = "direito"
    ECONOMIA = "economia"
    SAUDE = "saude"
    GENERICO = "generico"


# =============================================================================
# PERFIL MARKETING
# =============================================================================

MARKETING_CONFIG = {
    "persona_system_prompt": """Voce e um especialista em marketing digital e pesquisa de opiniao publica.
Gere personas de agentes de simulacao focadas em:
- Percepcao de marca e reputacao
- Reacao a campanhas publicitarias
- Engajamento em redes sociais
- Influenciadores e early adopters
- Sentimento do consumidor (positivo/negativo/neutro)
- Canais preferidos de comunicacao

REGRAS:
- Use linguagem de marketing padrao (awareness, engagement, NPS, sentiment)
- Proibir adjetivos poeticos ou raros
- Frases de maximo 25 palavras
- NUNCA use chines, japones ou coreano
""",

    "persona_user_prompt_suffix": """
Foque em:
- Percepcao de marca e reputacao
- Reacao a campanhas publicitarias
- Engajamento em redes sociais
- Influenciadores e early adopters
- Sentimento do consumidor (positivo/negativo/neutro)
- Canais preferidos de comunicacao
""",

    "report_system_prompt": """Voce e um analista senior de marketing digital e pesquisa de opiniao.
Escreva relatorios claros, diretos e acionaveis para equipes de marketing.

REGRAS DE LINGUAGEM:
- Frases de maximo 25 palavras
- Use bullets e numeros para dados
- Proibir adjetivos poeticos ou raros
- Usar terminologia de marketing padrao (awareness, engagement, NPS, sentiment)
- Tabelas devem ter formato: Fonte | Data | Metrica | Valor | Variacao
- NUNCA use chines, japones ou coreano
- Use notacao numerica consistente (1,5% ao inves de "um virgula cinco")

ESTRUTURA OBRIGATORIA:
1. Resumo Executivo (3 bullets)
2. Panorama de Sentimento (positivo/neutro/negativo com %)
3. Percepcao de Marca por Segmento
4. Influenciadores e Amplificadores
5. Oportunidades e Riscos
6. Recomendacoes Acionaveis (priorizadas)
""",

    "report_section_prompt": """Gere uma secao de relatorio de marketing com dados claros e acionaveis.
Use terminologia padrao de marketing. Cite fontes quando possivel.
Proibir linguagem poetica ou rebuscada.""",

    "simulation_overrides": {
        "peak_hours": [12, 13, 18, 19, 20, 21],
        "viral_threshold": 20,
        "echo_chamber_strength": 0.3,
        "narrative_direction": "analise de percepcao de marca e reacao a campanhas"
    },

    "entity_type_weights": {
        "MediaOutlet": 2.0,
        "PublicFigure": 1.8,
        "Student": 1.2,
        "Organization": 1.5,
    },

    "deep_research_prompt_suffix": """
Foque em: tendencias de consumo, percepcao de marca, campanhas recentes,
concorrentes, e reacoes em midias sociais. Priorize fontes de marketing e
pesquisa de opiniao.
""",
}


# =============================================================================
# PERFIL DIREITO
# =============================================================================

DIREITO_CONFIG = {
    "persona_system_prompt": """Voce e um consultor juridico senior especializado em analise de impacto regulatorio.
Gere personas de agentes de simulacao focadas em:
- Posicionamento juridico e interpretacao legal
- Precedentes e jurisprudencia relevantes
- Risco regulatório e compliance
- Impacto de decisoes judiciais
- Argumentacao forense e retorica juridica
- Relacao com orgaos reguladores

REGRAS:
- Use terminologia juridica padronizada (nao invente termos)
- Proibir linguagem poetica, metaforas ou adjetivos superlativos
- Frases de maximo 30 palavras
- NUNCA use chines, japones ou coreano
""",

    "persona_user_prompt_suffix": """
Foque em:
- Posicionamento juridico e interpretacao legal
- Precedentes e jurisprudencia relevantes
- Risco regulatório e compliance
- Impacto de decisoes judiciais
- Argumentacao forense e retorica juridica
- Relacao com orgaos reguladores
""",

    "report_system_prompt": """Voce e um consultor juridico senior especializado em analise de impacto regulatório.
Escreva relatorios precisos, estruturados e juridicamente rigorosos.

REGRAS DE LINGUAGEM:
- Frases de maximo 30 palavras
- Use terminologia juridica padronizada (nao invente termos)
- Cite fontes com data e orgao emissor
- Tabelas devem ter formato: Documento | Orgao | Data | Dispositivo | Efeito
- Proibir linguagem poetica, metaforas ou adjetivos superlativos
- NUNCA use chines, japones ou coreano
- Use notacao numerica consistente

ESTRUTURA OBRIGATORIA:
1. Resumo Executivo (3 bullets)
2. Marco Regulatório Atual (legislacao vigente)
3. Analise de Precedentes
4. Riscos Juridicos por Cenario
5. Impacto Compliance
6. Recomendacoes Estrategicas (com base legal)
""",

    "report_section_prompt": """Gere uma secao de relatorio juridico com rigor tecnico e precisao.
Cite legislacao, jurisprudencia e orgaos emissores. Use terminologia padronizada.
Proibir linguagem figurada ou metaforas.""",

    "simulation_overrides": {
        "peak_hours": [9, 10, 11, 14, 15, 16],
        "viral_threshold": 8,
        "echo_chamber_strength": 0.7,
        "narrative_direction": "analise de posicionamento juridico e impacto regulatório"
    },

    "entity_type_weights": {
        "GovernmentAgency": 2.5,
        "Official": 2.0,
        "Expert": 1.8,
        "Organization": 1.3,
    },

    "deep_research_prompt_suffix": """
Foque em: legislacao vigente, projetos de lei, decisoes judiciais recentes,
posicionamentos de orgaos reguladores, pareceres tecnicos, e jurisprudencia.
Priorize fontes oficiais (.gov, DOU, STF, tribunais).
""",
}


# =============================================================================
# PERFIL ECONOMIA
# =============================================================================

ECONOMIA_CONFIG = {
    "persona_system_prompt": """Voce e um economista senior e analista de mercado.
Gere personas de agentes de simulacao focadas em:
- Posicionamento economico e vies ideologico
- Sensibilidade a indicadores macroeconomicos
- Reacao a politicas monetarias/fiscais
- Perfil de risco e comportamento de mercado
- Relacao com setores produtivos
- Expectativas inflacionarias e de crescimento

REGRAS:
- Use terminologia economica padronizada (PIB, inflacao, Selic, dolar)
- Proibir linguagem figurada, metaforas ou adjetivos emocionais
- Frases de maximo 25 palavras
- NUNCA use chines, japones ou coreano
""",

    "persona_user_prompt_suffix": """
Foque em:
- Posicionamento economico e vies ideologico
- Sensibilidade a indicadores macroeconomicos
- Reacao a politicas monetarias/fiscais
- Perfil de risco e comportamento de mercado
- Relacao com setores produtivos
- Expectativas inflacionarias e de crescimento
""",

    "report_system_prompt": """Voce e um economista senior e analista de mercado.
Escreva relatorios com rigor quantitativo, dados claros e cenarios probabilisticos.

REGRAS DE LINGUAGEM:
- Frases de maximo 25 palavras
- Use terminologia economica padronizada (PIB, inflacao, Selic, dolar)
- Todo dado deve ter fonte, data e margem de erro quando aplicavel
- Tabelas devem ter formato: Indicador | Valor | Data | Fonte | Variacao MoM/YoY
- Proibir linguagem figurada, metaforas ou adjetivos emocionais
- NUNCA use chines, japones ou coreano
- Use notacao numerica consistente (1,5% ao inves de "um virgula cinco")

ESTRUTURA OBRIGATORIA:
1. Resumo Executivo (3 bullets com KPIs principais)
2. Panorama Macroeconomico (indicadores atuais)
3. Analise de Cenarios (Otimista / Base / Pessimista com probabilidades)
4. Impacto Setorial
5. Riscos e Sensibilidades
6. Recomendacoes Estrategicas (com retorno esperado)
""",

    "report_section_prompt": """Gere uma secao de relatorio economico com rigor quantitativo.
Inclua fontes, datas e margens de erro. Use terminologia padronizada.
Proibir metaforas ou adjetivos emocionais.""",

    "simulation_overrides": {
        "peak_hours": [8, 9, 10, 11, 14, 15, 16, 17],
        "viral_threshold": 15,
        "echo_chamber_strength": 0.6,
        "narrative_direction": "analise de impacto economico e reacao de mercado"
    },

    "entity_type_weights": {
        "Expert": 2.0,
        "Organization": 1.8,
        "MediaOutlet": 1.5,
        "PublicFigure": 1.3,
    },

    "deep_research_prompt_suffix": """
Foque em: indicadores macroeconomicos (PIB, inflacao, desemprego, Selic, dolar),
balanca comercial, dados do BCB, IBGE, FMI, Banco Mundial. Priorize fontes
oficiais e instituicoes financeiras.
""",
}


# =============================================================================
# PERFIL SAUDE
# =============================================================================

SAUDE_CONFIG = {
    "persona_system_prompt": """Voce e um consultor senior em saude publica e pesquisa clinica.
Gere personas de agentes de simulacao focadas em:
- Percepcao clinica e experiencia pratica com pacientes
- Posicionamento sobre diretrizes medicas e evidencias cientificas
- Relacao com conferencias, congressos e publicacoes academicas
- Sensibilidade a inovacoes terapeuticas e tecnologicas
- Interacao com pacientes, cuidadores e comunidade cientifica
- Postura etica e regulatória em pesquisa clinica

REGRAS:
- Use terminologia medica padronizada (CID, diretrizes, consensus)
- Proibir linguagem poetica, metaforas ou adjetivos emocionais
- Frases de maximo 25 palavras
- NUNCA use chines, japones ou coreano
""",

    "persona_user_prompt_suffix": """
Foque em:
- Percepcao clinica e experiencia pratica com pacientes
- Posicionamento sobre diretrizes medicas e evidencias cientificas
- Relacao com conferencias, congressos e publicacoes academicas
- Sensibilidade a inovacoes terapeuticas e tecnologicas
- Interacao com pacientes, cuidadores e comunidade cientifica
- Postura etica e regulatória em pesquisa clinica
""",

    "report_system_prompt": """Voce e um consultor senior em saude publica e pesquisa clinica.
Escreva relatorios claros, baseados em evidencias e orientados para a pratica medica.

REGRAS DE LINGUAGEM:
- Frases de maximo 25 palavras
- Use terminologia medica padronizada (CID, diretrizes, consensus)
- Todo dado clinico deve ter fonte (revista, congresso, data)
- Tabelas devem ter formato: Parametro | Valor | N | Intervalo | Fonte
- Proibir linguagem poetica, metaforas ou adjetivos emocionais
- NUNCA use chines, japones ou coreano
- Use notacao cientifica consistente (%, n, p-valor quando relevante)

ESTRUTURA OBRIGATORIA:
1. Resumo Executivo (3 bullets)
2. Panorama da Evidencia (revisao rapida do estado da arte)
3. Percepcao por Stakeholder (clinicos, pacientes, reguladores, industria)
4. Diretrizes e Consenso (posicionamentos oficiais)
5. Cenarios de Impacto Clinico (otimista/base/pessimista)
6. Recomendacoes para Pratica e Politica
""",

    "report_section_prompt": """Gere uma secao de relatorio de saude baseada em evidencias.
Cite fontes cientificas (revistas, congressos). Use terminologia medica padronizada.
Proibir metaforas ou linguagem emocional.""",

    "simulation_overrides": {
        "peak_hours": [7, 8, 12, 13, 18, 19, 20, 21],
        "viral_threshold": 12,
        "echo_chamber_strength": 0.5,
        "narrative_direction": "analise de percepcao clinica, reacao a diretrizes e impacto de politicas de saude"
    },

    "entity_type_weights": {
        "Expert": 2.5,
        "Organization": 1.8,
        "PublicFigure": 1.5,
        "GovernmentAgency": 1.5,
        "MediaOutlet": 1.2,
    },

    "deep_research_prompt_suffix": """
Foque em: diretrizes clinicas, resultados de congressos (ACR, EULAR, etc.),
publicacoes em revistas indexadas (PubMed), posicionamentos da ANVISA/Ministerio da Saude,
prevalencia e epidemiologia, inovacoes terapeuticas. Priorize fontes cientificas
e instituicoes de saude reconhecidas.
""",
}


# =============================================================================
# PERFIL GENERICO (mantem comportamento atual)
# =============================================================================

GENERICO_CONFIG = {
    "persona_system_prompt": "",
    "persona_user_prompt_suffix": "",
    "report_system_prompt": "",
    "report_section_prompt": "",
    "simulation_overrides": {},
    "entity_type_weights": {},
    "deep_research_prompt_suffix": "",
}


# =============================================================================
# DATACLASS PRINCIPAL
# =============================================================================

@dataclass
class ProfileConfiguration:
    """Configuracao completa de um perfil de usuario"""
    profile_type: UserProfile

    # Prompts
    persona_system_prompt: str
    persona_user_prompt_suffix: str
    report_system_prompt: str
    report_section_prompt: str
    deep_research_prompt_suffix: str

    # Parametros de simulacao
    simulation_overrides: Dict[str, Any] = field(default_factory=dict)
    entity_type_weights: Dict[str, float] = field(default_factory=dict)

    # Parametros de report
    max_tool_calls_per_section: int = 5
    report_temperature: float = 0.3
    max_reflection_rounds: int = 2
    max_words_per_sentence: int = 25

    # Parametros de persona
    profile_temperature: float = 0.5
    parallel_profile_count: int = 5

    # Validacao de idioma
    forbidden_scripts: List[str] = field(default_factory=lambda: ['zh', 'ja', 'ko'])

    def apply_to_persona_generator(self, generator: Any) -> None:
        """Aplica configuracoes ao gerador de personas (OasisProfileGenerator).

        Adiciona atributos dinamicamente ao gerador para que o processo de
        geracao de personas respeite o perfil selecionado.
        """
        if self.persona_system_prompt:
            generator.system_prompt = self.persona_system_prompt
        if self.persona_user_prompt_suffix:
            generator.user_prompt_suffix = self.persona_user_prompt_suffix
        generator.temperature = self.profile_temperature
        generator.forbidden_scripts = self.forbidden_scripts or ['zh', 'ja', 'ko']
        generator.max_words_per_sentence = self.max_words_per_sentence
        generator.profile_type = self.profile_type.value
        generator.entity_type_weights = self.entity_type_weights

    def apply_to_report_agent(self, agent: Any) -> None:
        """Aplica configuracoes ao agente de relatorio (ReportAgent).

        Adiciona atributos dinamicamente ao agente para que a geracao de
        relatorios respeite as regras de linguagem e estrutura do perfil.
        """
        if self.report_system_prompt:
            agent.system_prompt = self.report_system_prompt
        if self.report_section_prompt:
            agent.section_prompt = self.report_section_prompt
        agent.max_tool_calls = self.max_tool_calls_per_section
        agent.temperature = self.report_temperature
        agent.max_reflection_rounds = self.max_reflection_rounds
        agent.forbidden_scripts = self.forbidden_scripts or ['zh', 'ja', 'ko']
        agent.max_words_per_sentence = self.max_words_per_sentence
        agent.profile_type = self.profile_type.value
        agent.entity_type_weights = self.entity_type_weights

    def apply_to_simulation_config(self, config: Any) -> None:
        """Aplica overrides a configuracao de simulacao (SimulationParameters).

        Sobrescreve atributos da configuracao com os valores definidos pelo perfil.
        """
        for key, value in self.simulation_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Retorna a configuracao como dicionario (util para APIs)."""
        return {
            "profile_type": self.profile_type.value,
            "persona_system_prompt": self.persona_system_prompt,
            "persona_user_prompt_suffix": self.persona_user_prompt_suffix,
            "report_system_prompt": self.report_system_prompt,
            "report_section_prompt": self.report_section_prompt,
            "deep_research_prompt_suffix": self.deep_research_prompt_suffix,
            "simulation_overrides": self.simulation_overrides,
            "entity_type_weights": self.entity_type_weights,
            "max_tool_calls_per_section": self.max_tool_calls_per_section,
            "report_temperature": self.report_temperature,
            "max_reflection_rounds": self.max_reflection_rounds,
            "max_words_per_sentence": self.max_words_per_sentence,
            "profile_temperature": self.profile_temperature,
            "parallel_profile_count": self.parallel_profile_count,
            "forbidden_scripts": self.forbidden_scripts,
        }


# =============================================================================
# PROFILE MANAGER
# =============================================================================

class ProfileManager:
    """
    Gerenciador de perfis de usuario.
    
    Responsavel por:
    1. Criar ProfileConfiguration a partir de um UserProfile
    2. Listar perfis disponiveis com metadados
    3. Fornecer valores padrao (GENERICO)
    """

    _PROFILE_METADATA: Dict[UserProfile, Dict[str, Any]] = {
        UserProfile.MARKETING: {
            "display_name": "Marketing",
            "description": "Analise de opiniao publica, campanhas, posicionamento de marca, reacao de mercado",
            "audience": "Gestores de marketing, comunicacao, PR",
            "primary_color": "#0066FF",
            "accent_color": "#00CCFF",
        },
        UserProfile.DIREITO: {
            "display_name": "Direito",
            "description": "Analise juridica, impacto regulatório, compliance, precedentes",
            "audience": "Advogados, juristas, consultores legislativos",
            "primary_color": "#8B4513",
            "accent_color": "#D2691E",
        },
        UserProfile.ECONOMIA: {
            "display_name": "Economia",
            "description": "Analise de mercado, impacto economico, cenarios financeiros, previsoes",
            "audience": "Economistas, analistas financeiros, gestores",
            "primary_color": "#006400",
            "accent_color": "#228B22",
        },
        UserProfile.SAUDE: {
            "display_name": "Saude",
            "description": "Analise de percepcao clinica, reacao a politicas de saude, consenso medico",
            "audience": "Medicos, pesquisadores, gestores de saude, formuladores de politicas",
            "primary_color": "#C41E3A",
            "accent_color": "#FF6B6B",
        },
        UserProfile.GENERICO: {
            "display_name": "Generico",
            "description": "Comportamento padrao do sistema, sem especializacao",
            "audience": "Usuarios gerais",
            "primary_color": "#000000",
            "accent_color": "#444444",
        },
    }

    @classmethod
    def get_profile(cls, profile_name: str) -> ProfileConfiguration:
        """
        Retorna a configuracao para um perfil pelo nome.
        
        Args:
            profile_name: Nome do perfil (marketing, direito, economia, saude, generico)
            
        Returns:
            ProfileConfiguration configurada
            
        Raises:
            ValueError: Se o perfil nao existir
        """
        try:
            profile_type = UserProfile(profile_name.lower().strip())
        except ValueError:
            # Perfil desconhecido: retorna generico
            profile_type = UserProfile.GENERICO

        if profile_type == UserProfile.MARKETING:
            return ProfileConfiguration(
                profile_type=profile_type,
                max_words_per_sentence=25,
                **MARKETING_CONFIG,
            )
        elif profile_type == UserProfile.DIREITO:
            return ProfileConfiguration(
                profile_type=profile_type,
                max_words_per_sentence=30,
                **DIREITO_CONFIG,
            )
        elif profile_type == UserProfile.ECONOMIA:
            return ProfileConfiguration(
                profile_type=profile_type,
                max_words_per_sentence=25,
                **ECONOMIA_CONFIG,
            )
        elif profile_type == UserProfile.SAUDE:
            return ProfileConfiguration(
                profile_type=profile_type,
                max_words_per_sentence=25,
                **SAUDE_CONFIG,
            )
        else:
            return ProfileConfiguration(
                profile_type=UserProfile.GENERICO,
                **GENERICO_CONFIG,
            )

    @classmethod
    def list_profiles(cls) -> List[Dict[str, Any]]:
        """
        Retorna lista de perfis disponiveis com metadados.
        
        Returns:
            Lista de dicionarios com informacoes de cada perfil
        """
        profiles = []
        for profile_type, meta in cls._PROFILE_METADATA.items():
            profiles.append({
                "id": profile_type.value,
                "display_name": meta["display_name"],
                "description": meta["description"],
                "audience": meta["audience"],
                "primary_color": meta["primary_color"],
                "accent_color": meta["accent_color"],
            })
        return profiles

    @classmethod
    def get_profile_or_default(cls, profile_name: Optional[str]) -> ProfileConfiguration:
        """
        Retorna o perfil solicitado ou GENERICO se nao fornecido/invalido.
        
        Args:
            profile_name: Nome opcional do perfil
            
        Returns:
            ProfileConfiguration
        """
        if not profile_name:
            return cls.get_profile(UserProfile.GENERICO.value)
        return cls.get_profile(profile_name)
