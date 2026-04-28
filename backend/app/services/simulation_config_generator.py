"""
Gerador Inteligente de Configuração de Simulação
Utiliza LLM para gerar automaticamente parâmetros detalhados de simulação
com base nos requisitos, documentos e informações do grafo.
Implementação totalmente automatizada, sem necessidade de configuração manual.

Estratégia de geração em etapas para evitar falhas por conteúdo excessivo:
1. Gerar configuração de tempo
2. Gerar configuração de eventos
3. Gerar configurações de Agentes em lotes
4. Gerar configuração de plataforma
"""

import json
import math
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime

from openai import OpenAI

from ..config import Config
from ..utils.logger import get_logger
from ..utils.locale import get_language_instruction, t
from .zep_entity_reader import EntityNode, ZepEntityReader

logger = get_logger('futuria.simulation_config')

# Configuração de fuso horário de referência (Brasil - UTC-3)
BRAZIL_TIMEZONE_CONFIG = {
    # Madrugada (quase nenhuma atividade)
    "dead_hours": [0, 1, 2, 3, 4, 5],
    # Manhã (ativ gradualmente)
    "morning_hours": [6, 7, 8],
    # Horário de trabalho
    "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
    # Pico noturno (mais ativo)
    "peak_hours": [19, 20, 21, 22],
    # Noite (atividade diminuindo)
    "night_hours": [23],
    # Coeficientes de atividade
    "activity_multipliers": {
        "dead": 0.05,      # Madrugada quase vazia
        "morning": 0.4,    # Manhã gradualmente ativa
        "work": 0.7,       # Trabalho médio
        "peak": 1.5,       # Pico noturno
        "night": 0.5       # Noite diminuindo
    }
}


@dataclass
class AgentActivityConfig:
    """Configuração de atividade de um único Agente"""
    agent_id: int
    entity_uuid: str
    entity_name: str
    entity_type: str
    
    # 活跃度配置 (0.0-1.0)
    activity_level: float = 0.5  # 整体活跃度
    
    # 发言频率（每小时预期发言次数）
    posts_per_hour: float = 1.0
    comments_per_hour: float = 2.0
    
    # 活跃时间段（24小时制，0-23）
    active_hours: List[int] = field(default_factory=lambda: list(range(8, 23)))
    
    # 响应速度（对热点事件的反应延迟，单位：模拟分钟）
    response_delay_min: int = 5
    response_delay_max: int = 60
    
    # 情感倾向 (-1.0到1.0，负面到正面)
    sentiment_bias: float = 0.0
    
    # 立场（对特定话题的态度）
    stance: str = "neutral"  # supportive, opposing, neutral, observer
    
    # 影响力权重（决定其发言被其他Agent看到的概率）
    influence_weight: float = 1.0


@dataclass  
class TimeSimulationConfig:
    """Configuração de tempo da simulação (baseada em hábitos do Brasil)"""
    # 模拟总时长（模拟小时数）
    total_simulation_hours: int = 72  # 默认模拟72小时（3天）
    
    # 每轮代表的时间（模拟分钟）- 默认60分钟（1小时），加快时间流速
    minutes_per_round: int = 60
    
    # 每小时激活的Agent数量范围
    agents_per_hour_min: int = 5
    agents_per_hour_max: int = 20
    
    # Horários de pico (19-22h, horário mais ativo no Brasil)
    peak_hours: List[int] = field(default_factory=lambda: [19, 20, 21, 22])
    peak_activity_multiplier: float = 1.5
    
    # Horários de vazio (0-5h, quase nenhuma atividade)
    off_peak_hours: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5])
    off_peak_activity_multiplier: float = 0.05  # Atividade mínima de madrugada
    
    # Manhã
    morning_hours: List[int] = field(default_factory=lambda: [6, 7, 8])
    morning_activity_multiplier: float = 0.4
    
    # Horário de trabalho
    work_hours: List[int] = field(default_factory=lambda: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18])
    work_activity_multiplier: float = 0.7


@dataclass
class EventConfig:
    """Configuração de eventos"""
    # 初始事件（模拟开始时的触发事件）
    initial_posts: List[Dict[str, Any]] = field(default_factory=list)
    
    # 定时事件（在特定时间触发的事件）
    scheduled_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # 热点话题关键词
    hot_topics: List[str] = field(default_factory=list)
    
    # 舆论引导方向
    narrative_direction: str = ""


@dataclass
class PlatformConfig:
    """Configuração específica da plataforma"""
    platform: str  # twitter or reddit
    
    # 推荐算法权重
    recency_weight: float = 0.4  # 时间新鲜度
    popularity_weight: float = 0.3  # 热度
    relevance_weight: float = 0.3  # 相关性
    
    # 病毒传播阈值（达到多少互动后触发扩散）
    viral_threshold: int = 10
    
    # 回声室效应强度（相似观点聚集程度）
    echo_chamber_strength: float = 0.5


@dataclass
class SimulationParameters:
    """Configuração completa de parâmetros da simulação"""
    # 基础信息
    simulation_id: str
    project_id: str
    graph_id: str
    simulation_requirement: str
    
    # 时间配置
    time_config: TimeSimulationConfig = field(default_factory=TimeSimulationConfig)
    
    # Agent配置列表
    agent_configs: List[AgentActivityConfig] = field(default_factory=list)
    
    # 事件配置
    event_config: EventConfig = field(default_factory=EventConfig)
    
    # 平台配置
    twitter_config: Optional[PlatformConfig] = None
    reddit_config: Optional[PlatformConfig] = None
    
    # LLM配置
    llm_model: str = ""
    llm_base_url: str = ""
    
    # 生成元数据
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    generation_reasoning: str = ""  # LLM的推理说明
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        time_dict = asdict(self.time_config)
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "simulation_requirement": self.simulation_requirement,
            "time_config": time_dict,
            "agent_configs": [asdict(a) for a in self.agent_configs],
            "event_config": asdict(self.event_config),
            "twitter_config": asdict(self.twitter_config) if self.twitter_config else None,
            "reddit_config": asdict(self.reddit_config) if self.reddit_config else None,
            "llm_model": self.llm_model,
            "llm_base_url": self.llm_base_url,
            "generated_at": self.generated_at,
            "generation_reasoning": self.generation_reasoning,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class SimulationConfigGenerator:
    """
    模拟配置智能生成器
    
    使用LLM分析模拟需求、文档内容、图谱实体信息，
    自动生成最佳的模拟参数配置
    
    采用分步生成策略：
    1. 生成时间配置和事件配置（轻量级）
    2. 分批生成Agent配置（每批10-20个）
    3. 生成平台配置
    """
    
    # 上下文最大字符数
    MAX_CONTEXT_LENGTH = 50000
    # 每批生成的Agent数量
    AGENTS_PER_BATCH = 15
    
    # 各步骤的上下文截断长度（字符数）
    TIME_CONFIG_CONTEXT_LENGTH = 10000   # 时间配置
    EVENT_CONFIG_CONTEXT_LENGTH = 8000   # 事件配置
    ENTITY_SUMMARY_LENGTH = 300          # 实体摘要
    AGENT_SUMMARY_LENGTH = 300           # Agent配置中的实体摘要
    ENTITIES_PER_TYPE_DISPLAY = 20       # 每类实体显示数量
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        observability_client: Any = None,
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model_name = model_name or Config.LLM_MODEL_NAME
        self.observability_client = observability_client

        if not self.api_key:
            raise ValueError("LLM_API_KEY não configurada")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def generate_config(
        self,
        simulation_id: str,
        project_id: str,
        graph_id: str,
        simulation_requirement: str,
        document_text: str,
        entities: List[EntityNode],
        enable_twitter: bool = True,
        enable_reddit: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        observability_client: Any = None,
    ) -> SimulationParameters:
        """
        智能生成完整的模拟配置（分步生成）
        
        Args:
            simulation_id: 模拟ID
            project_id: 项目ID
            graph_id: 图谱ID
            simulation_requirement: 模拟需求描述
            document_text: 原始文档内容
            entities: 过滤后的实体列表
            enable_twitter: 是否启用Twitter
            enable_reddit: 是否启用Reddit
            progress_callback: 进度回调函数(current_step, total_steps, message)
            
        Returns:
            SimulationParameters: 完整的模拟参数
        """
        logger.info(f"Iniciando geração inteligente de configuração de simulação: simulation_id={simulation_id}, entidades={len(entities)}")

        # 计算总步骤数
        num_batches = math.ceil(len(entities) / self.AGENTS_PER_BATCH)
        total_steps = 3 + num_batches  # 时间配置 + 事件配置 + N批Agent + 平台配置
        current_step = 0
        
        def report_progress(step: int, message: str):
            nonlocal current_step
            current_step = step
            if progress_callback:
                progress_callback(step, total_steps, message)
            logger.info(f"[{step}/{total_steps}] {message}")

        # Create root observability span for the entire config generation
        obs = observability_client or self.observability_client
        root_span = None
        if obs is not None:
            root_span = obs.start_report_trace(
                name="simulation_config",
                session_id=simulation_id,
                metadata={
                    "simulation_id": simulation_id,
                    "project_id": project_id,
                    "graph_id": graph_id,
                    "entity_count": len(entities),
                    "simulation_requirement": simulation_requirement[:200],
                },
            )
            root_span.update(input={
                "simulation_id": simulation_id,
                "entity_count": len(entities),
            })

        try:
            # 1. Construir informações de contexto base
            context = self._build_context(
                simulation_requirement=simulation_requirement,
                document_text=document_text,
                entities=entities
            )
            
            reasoning_parts = []
            
            # ========== Etapa 1: Gerar configuração de tempo ==========
            report_progress(1, t('progress.generatingTimeConfig'))
            num_entities = len(entities)
            time_config_result = self._generate_time_config(context, num_entities, observation=root_span)
            time_config = self._parse_time_config(time_config_result, num_entities)
            reasoning_parts.append(f"{t('progress.timeConfigLabel')}: {time_config_result.get('reasoning', t('common.success'))}")

            # ========== Etapa 2: Gerar configuração de eventos ==========
            report_progress(2, t('progress.generatingEventConfig'))
            event_config_result = self._generate_event_config(context, simulation_requirement, entities, observation=root_span)
            event_config = self._parse_event_config(event_config_result)
            reasoning_parts.append(f"{t('progress.eventConfigLabel')}: {event_config_result.get('reasoning', t('common.success'))}")

            # ========== Etapas 3-N: Gerar configurações de Agentes em lotes ==========
            all_agent_configs = []
            for batch_idx in range(num_batches):
                start_idx = batch_idx * self.AGENTS_PER_BATCH
                end_idx = min(start_idx + self.AGENTS_PER_BATCH, len(entities))
                batch_entities = entities[start_idx:end_idx]

                report_progress(
                    3 + batch_idx,
                    t('progress.generatingAgentConfig', start=start_idx + 1, end=end_idx, total=len(entities))
                )

                batch_configs = self._generate_agent_configs_batch(
                    context=context,
                    entities=batch_entities,
                    start_idx=start_idx,
                    simulation_requirement=simulation_requirement,
                    observation=root_span,
                )
                all_agent_configs.extend(batch_configs)
            
            reasoning_parts.append(t('progress.agentConfigResult', count=len(all_agent_configs)))
            
            # ========== Atribuir Agentes publicadores aos posts iniciais ==========
            logger.info("Atribuindo Agentes publicadores apropriados aos posts iniciais...")
            event_config = self._assign_initial_post_agents(event_config, all_agent_configs)
            assigned_count = len([p for p in event_config.initial_posts if p.get("poster_agent_id") is not None])
            reasoning_parts.append(t('progress.postAssignResult', count=assigned_count))
            
            # ========== Etapa final: Gerar configuração de plataforma ==========
            report_progress(total_steps, t('progress.generatingPlatformConfig'))
            twitter_config = None
            reddit_config = None
            
            if enable_twitter:
                twitter_config = PlatformConfig(
                    platform="twitter",
                    recency_weight=0.4,
                    popularity_weight=0.3,
                    relevance_weight=0.3,
                    viral_threshold=10,
                    echo_chamber_strength=0.5
                )
            
            if enable_reddit:
                reddit_config = PlatformConfig(
                    platform="reddit",
                    recency_weight=0.3,
                    popularity_weight=0.4,
                    relevance_weight=0.3,
                    viral_threshold=15,
                    echo_chamber_strength=0.6
                )
            
            # 构建最终参数
            params = SimulationParameters(
                simulation_id=simulation_id,
                project_id=project_id,
                graph_id=graph_id,
                simulation_requirement=simulation_requirement,
                time_config=time_config,
                agent_configs=all_agent_configs,
                event_config=event_config,
                twitter_config=twitter_config,
                reddit_config=reddit_config,
                llm_model=self.model_name,
                llm_base_url=self.base_url,
                generation_reasoning=" | ".join(reasoning_parts)
            )
            
            logger.info(f"Geração de configuração de simulação concluída: {len(params.agent_configs)} configurações de Agente")

            if root_span is not None:
                root_span.update(output={
                    "agent_count": len(params.agent_configs),
                    "time_config_hours": params.time_config.total_simulation_hours,
                })

            return params
        except Exception as e:
            if root_span is not None:
                root_span.update(status_message=str(e), output={})
            raise
        finally:
            if root_span is not None:
                root_span.end()
    
    def _build_context(
        self,
        simulation_requirement: str,
        document_text: str,
        entities: List[EntityNode]
    ) -> str:
        """Construir contexto para o LLM, truncado ao comprimento máximo"""
        
        # Resumo das entidades
        entity_summary = self._summarize_entities(entities)
        
        # Construir contexto
        context_parts = [
            f"## Requisitos da Simulação\n{simulation_requirement}",
            f"\n## Informações das Entidades ({len(entities)})\n{entity_summary}",
        ]
        
        current_length = sum(len(p) for p in context_parts)
        remaining_length = self.MAX_CONTEXT_LENGTH - current_length - 500  # Reservar 500 caracteres
        
        if remaining_length > 0 and document_text:
            doc_text = document_text[:remaining_length]
            if len(document_text) > remaining_length:
                doc_text += "\n...(documento truncado)"
            context_parts.append(f"\n## Conteúdo do Documento Original\n{doc_text}")
        
        return "\n".join(context_parts)
    
    def _summarize_entities(self, entities: List[EntityNode]) -> str:
        """Gerar resumo das entidades"""
        lines = []
        
        # Agrupar por tipo
        by_type: Dict[str, List[EntityNode]] = {}
        for e in entities:
            t = e.get_entity_type() or "Unknown"
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(e)
        
        for entity_type, type_entities in by_type.items():
            lines.append(f"\n### {entity_type} ({len(type_entities)})")
            # Usar quantidade configurada de exibição e comprimento de resumo
            display_count = self.ENTITIES_PER_TYPE_DISPLAY
            summary_len = self.ENTITY_SUMMARY_LENGTH
            for e in type_entities[:display_count]:
                summary_preview = (e.summary[:summary_len] + "...") if len(e.summary) > summary_len else e.summary
                lines.append(f"- {e.name}: {summary_preview}")
            if len(type_entities) > display_count:
                lines.append(f"  ... e mais {len(type_entities) - display_count}")
        
        return "\n".join(lines)

    def _extract_json_payload(self, content: str) -> str:
        """提取模型响应中的 JSON payload，兼容 think 标签和 fenced code block。"""
        cleaned = content.strip()
        cleaned = re.sub(r'^\s*<think>.*?</think>\s*', '', cleaned, flags=re.IGNORECASE | re.DOTALL)

        fenced_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', cleaned, flags=re.IGNORECASE | re.DOTALL)
        if fenced_match:
            return fenced_match.group(1).strip()

        json_match = re.search(r'(\{.*\})', cleaned, flags=re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        return cleaned

    def _normalize_reasoning_text(self, reasoning: Any, fallback: str) -> str:
        """规范 reasoning 文本，发现 CJK 污染时回退到葡语说明。"""
        if not isinstance(reasoning, str):
            return fallback

        cleaned = reasoning.strip()
        if not cleaned:
            return fallback

        if re.search(r'[\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]', cleaned):
            return fallback

        return cleaned
    
    def _call_llm_with_retry(
        self,
        prompt: str,
        system_prompt: str,
        observation: Any = None,
    ) -> Dict[str, Any]:
        """Chamada ao LLM com retry, incluindo lógica de correção de JSON"""
        import re
        import time as _time

        max_attempts = 3
        last_error = None
        total_latency_ms = 0.0

        for attempt in range(max_attempts):
            attempt_start = _time.perf_counter()
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7 - (attempt * 0.1)  # Reduzir temperatura a cada retry
                    # Não definir max_tokens para deixar o LLM livre
                )

                latency_ms = (_time.perf_counter() - attempt_start) * 1000
                total_latency_ms += latency_ms

                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason

                # Verificar se foi truncado
                if finish_reason == 'length':
                    logger.warning(f"Saída do LLM truncada (tentativa {attempt+1})")
                    content = self._fix_truncated_json(content)

                # Tentar analisar JSON
                try:
                    result = json.loads(content)
                    # Update observability span with success
                    if observation is not None:
                        observation.update(
                            output=result,
                            latency_ms=latency_ms,
                            usage={
                                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                                "total_tokens": getattr(response.usage, "total_tokens", 0),
                            },
                        )
                    return result
                except json.JSONDecodeError as e:
                    logger.warning(f"Falha ao analisar JSON (tentativa {attempt+1}): {str(e)[:80]}")

                    # Tentar corrigir JSON
                    fixed = self._try_fix_config_json(content)
                    if fixed:
                        if observation is not None:
                            observation.update(
                                output=fixed,
                                latency_ms=latency_ms,
                                usage={
                                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                                    "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                                },
                            )
                        return fixed

                    last_error = e

            except Exception as e:
                total_latency_ms += _time.perf_counter() * 1000
                logger.warning(f"Falha na chamada ao LLM (tentativa {attempt+1}): {str(e)[:80]}")
                last_error = e
                _time.sleep(2 * (attempt + 1))

        # Todas as tentativas esgotadas — atualizar span com erro antes de lançar exceção
        if observation is not None:
            observation.update(
                status_message=f"error after {max_attempts} attempts: {str(last_error)}",
                output="",
            )
        raise last_error or Exception("Falha na chamada ao LLM")
    
    def _fix_truncated_json(self, content: str) -> str:
        """Corrigir JSON truncado"""
        content = content.strip()
        
        # Calcular parênteses não fechados
        open_braces = content.count('{') - content.count('}')
        open_brackets = content.count('[') - content.count(']')
        
        # Verificar se há string não fechada
        if content and content[-1] not in '",}]':
            content += '"'
        
        # Fechar parênteses
        content += ']' * open_brackets
        content += '}' * open_braces
        
        return content
    
    def _try_fix_config_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Tentar corrigir JSON de configuração"""
        import re
        
        # Corrigir caso truncado
        content = self._fix_truncated_json(content)
        
        # Extrair parte JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group()
            
            # Remover quebras de linha dentro de strings
            def fix_string(match):
                s = match.group(0)
                s = s.replace('\n', ' ').replace('\r', ' ')
                s = re.sub(r'\s+', ' ', s)
                return s
            
            json_str = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_string, json_str)
            
            try:
                return json.loads(json_str)
            except:
                # Tentar remover todos os caracteres de controle
                json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
                json_str = re.sub(r'\s+', ' ', json_str)
                try:
                    return json.loads(json_str)
                except:
                    pass
        
        return None
    
    def _generate_time_config(self, context: str, num_entities: int, observation: Any = None) -> Dict[str, Any]:
        """Gerar configuração de tempo"""
        # Usar comprimento de truncamento configurado para contexto
        context_truncated = context[:self.TIME_CONFIG_CONTEXT_LENGTH]
        
        # Calcular valor máximo permitido (90% do número de agentes)
        max_agents_allowed = max(1, int(num_entities * 0.9))
        
        prompt = f"""Com base nos seguintes requisitos de simulação, gere a configuração de tempo da simulação.

{context_truncated}

## Tarefa
Gere a configuração de tempo em JSON.

### Princípios básicos (apenas referência, ajuste conforme o evento e público participante):
- Infira o fuso horário e hábitos do público-alvo a partir do cenário de simulação. Abaixo um exemplo de referência para o Brasil (UTC-3):
- Madrugada 0-5h: quase nenhuma atividade (coeficiente 0,05)
- Manhã 6-8h: atividade gradual (coeficiente 0,4)
- Horário de trabalho 9-18h: atividade média (coeficiente 0,7)
- Noite 19-22h: pico de atividade (coeficiente 1,5)
- Após 23h: atividade diminuindo (coeficiente 0,5)
- Regra geral: madrugada baixa, manhã crescente, trabalho médio, noite pico
- **Importante**: os valores de exemplo abaixo são apenas referência; ajuste os horários conforme a natureza do evento e características do público
  - Ex.: estudantes podem ter pico 21-23h; mídia ativa o dia todo; órgãos oficiais só em horário comercial
  - Ex.: eventos urgentes podem gerar discussão até de madrugada; off_peak_hours pode ser encurtado

### Retorne JSON (sem markdown)

Exemplo:
{{
    "total_simulation_hours": 72,
    "minutes_per_round": 60,
    "agents_per_hour_min": 5,
    "agents_per_hour_max": 50,
    "peak_hours": [19, 20, 21, 22],
    "off_peak_hours": [0, 1, 2, 3, 4, 5],
    "morning_hours": [6, 7, 8],
    "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
    "reasoning": "Explicação da configuração de tempo para este evento"
}}

Descrição dos campos:
- total_simulation_hours (int): duração total da simulação em horas, 24-168h; eventos súbitos são curtos, temas persistentes são longos
- minutes_per_round (int): duração de cada turno em minutos, 30-120, recomendado 60
- agents_per_hour_min (int): mínimo de Agentes ativados por hora (intervalo: 1-{max_agents_allowed})
- agents_per_hour_max (int): máximo de Agentes ativados por hora (intervalo: 1-{max_agents_allowed})
- peak_hours (array int): horários de pico, ajustar conforme o público participante
- off_peak_hours (array int): horários de vazio, geralmente madrugada
- morning_hours (array int): período da manhã
- work_hours (array int): período de trabalho
- reasoning (string): breve justificativa da configuração"""

        system_prompt = "Você é um especialista em simulação de mídias sociais. Retorne apenas JSON puro. A configuração de tempo deve respeitar os hábitos do público-alvo do cenário simulado."
        system_prompt = f"{system_prompt}\n\n{get_language_instruction()}"

        # Create child span for this LLM call
        span = None
        if observation is not None:
            span = observation.start_span(
                name="simulation_config.time",
                metadata={"num_entities": num_entities, "model": self.model_name},
            )

        try:
            result = self._call_llm_with_retry(prompt, system_prompt, observation=span)
            result["reasoning"] = self._normalize_reasoning_text(
                result.get("reasoning"),
                "Configuração ajustada ao público e ao ritmo esperado da discussão.",
            )
            if span is not None:
                span.end()
            return result
        except Exception as e:
            logger.warning(f"Falha na geração de configuração de tempo pelo LLM: {e}, usando configuração padrão")
            if span is not None:
                span.update(status_message=f"error: {str(e)}", output="")
                span.end()
            return self._get_default_time_config(num_entities)
    
    def _get_default_time_config(self, num_entities: int) -> Dict[str, Any]:
        """Obter configuração de tempo padrão (hábitos do Brasil)"""
        return {
            "total_simulation_hours": 72,
            "minutes_per_round": 60,  # 1 hora por turno, acelerando o tempo
            "agents_per_hour_min": max(1, num_entities // 15),
            "agents_per_hour_max": max(5, num_entities // 5),
            "peak_hours": [19, 20, 21, 22],
            "off_peak_hours": [0, 1, 2, 3, 4, 5],
            "morning_hours": [6, 7, 8],
            "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
            "reasoning": "Usando configuração padrão de hábitos do Brasil (1 hora por turno)"
        }
    
    def _parse_time_config(self, result: Dict[str, Any], num_entities: int) -> TimeSimulationConfig:
        """Analisar resultado da configuração de tempo e validar que agents_per_hour não excede o total"""
        # Obter valores originais
        agents_per_hour_min = result.get("agents_per_hour_min", max(1, num_entities // 15))
        agents_per_hour_max = result.get("agents_per_hour_max", max(5, num_entities // 5))
        
        # Validar e corrigir: garantir que não excede o total de agentes
        if agents_per_hour_min > num_entities:
            logger.warning(f"agents_per_hour_min ({agents_per_hour_min}) excede o total de Agentes ({num_entities}), corrigido")
            agents_per_hour_min = max(1, num_entities // 10)
        
        if agents_per_hour_max > num_entities:
            logger.warning(f"agents_per_hour_max ({agents_per_hour_max}) excede o total de Agentes ({num_entities}), corrigido")
            agents_per_hour_max = max(agents_per_hour_min + 1, num_entities // 2)
        
        # Garantir min < max
        if agents_per_hour_min >= agents_per_hour_max:
            agents_per_hour_min = max(1, agents_per_hour_max // 2)
            logger.warning(f"agents_per_hour_min >= max, corrigido para {agents_per_hour_min}")
        
        return TimeSimulationConfig(
            total_simulation_hours=result.get("total_simulation_hours", 72),
            minutes_per_round=result.get("minutes_per_round", 60),  # Padrão 1 hora por turno
            agents_per_hour_min=agents_per_hour_min,
            agents_per_hour_max=agents_per_hour_max,
            peak_hours=result.get("peak_hours", [19, 20, 21, 22]),
            off_peak_hours=result.get("off_peak_hours", [0, 1, 2, 3, 4, 5]),
            off_peak_activity_multiplier=0.05,  # Madrugada quase vazia
            morning_hours=result.get("morning_hours", [6, 7, 8]),
            morning_activity_multiplier=0.4,
            work_hours=result.get("work_hours", list(range(9, 19))),
            work_activity_multiplier=0.7,
            peak_activity_multiplier=1.5
        )
    
    def _generate_event_config(
        self,
        context: str,
        simulation_requirement: str,
        entities: List[EntityNode],
        observation: Any = None,
    ) -> Dict[str, Any]:
        """Gerar configuração de eventos"""
        
        # Obter lista de tipos de entidade disponíveis para referência do LLM
        entity_types_available = list(set(
            e.get_entity_type() or "Unknown" for e in entities
        ))
        
        # Listar nomes representativos para cada tipo
        type_examples = {}
        for e in entities:
            etype = e.get_entity_type() or "Unknown"
            if etype not in type_examples:
                type_examples[etype] = []
            if len(type_examples[etype]) < 3:
                type_examples[etype].append(e.name)
        
        type_info = "\n".join([
            f"- {t}: {', '.join(examples)}" 
            for t, examples in type_examples.items()
        ])
        
        # Usar comprimento de truncamento configurado para contexto
        context_truncated = context[:self.EVENT_CONFIG_CONTEXT_LENGTH]
        
        prompt = f"""Com base nos seguintes requisitos de simulação, gere a configuração de eventos.

Requisitos da simulação: {simulation_requirement}

{context_truncated}

## Tipos de entidade disponíveis e exemplos
{type_info}

## Tarefa
Gere a configuração de eventos em JSON:
- Extraia palavras-chave dos tópicos quentes
- Descreva a direção do desenvolvimento da opinião pública
- Projete o conteúdo dos posts iniciais; **cada post deve especificar poster_type (tipo de publicador)**

**Importante**: poster_type DEVE ser escolhido entre os "tipos de entidade disponíveis" acima, para que os posts iniciais possam ser atribuídos ao Agente correto.
Ex.: declarações oficiais devem ser publicadas por tipos Official/University; notícias por MediaOutlet; opiniões de estudantes por Student.

Retorne JSON (sem markdown):
{{
    "hot_topics": ["palavra-chave1", "palavra-chave2", ...],
    "narrative_direction": "<descrição da direção do desenvolvimento da opinião pública>",
    "initial_posts": [
        {{"content": "conteúdo do post", "poster_type": "tipo de entidade (deve ser escolhido entre os disponíveis)"}},
        ...
    ],
    "reasoning": "<breve explicação>"
}}"""

        system_prompt = "Você é um especialista em análise de opinião pública. Retorne apenas JSON puro. O campo poster_type deve corresponder exatamente aos tipos de entidade disponíveis."
        system_prompt = f"{system_prompt}\n\n{get_language_instruction()}\nIMPORTANTE: O valor do campo 'poster_type' DEVE estar em inglês PascalCase correspondendo exatamente aos tipos de entidade disponíveis. Apenas os campos 'content', 'narrative_direction', 'hot_topics' e 'reasoning' devem usar o idioma especificado."

        # Create child span for this LLM call
        span = None
        if observation is not None:
            span = observation.start_span(
                name="simulation_config.event",
                metadata={"entity_count": len(entities), "model": self.model_name},
            )

        try:
            result = self._call_llm_with_retry(prompt, system_prompt, observation=span)
            if span is not None:
                span.end()
            return result
        except Exception as e:
            logger.warning(f"Falha na geração de configuração de eventos pelo LLM: {e}, usando configuração padrão")
            if span is not None:
                span.update(status_message=f"error: {str(e)}", output="")
                span.end()
            return {
                "hot_topics": [],
                "narrative_direction": "",
                "initial_posts": [],
                "reasoning": "Usando configuração padrão"
            }
    
    def _parse_event_config(self, result: Dict[str, Any]) -> EventConfig:
        """Analisar resultado da configuração de eventos"""
        return EventConfig(
            initial_posts=result.get("initial_posts", []),
            scheduled_events=[],
            hot_topics=result.get("hot_topics", []),
            narrative_direction=result.get("narrative_direction", "")
        )
    
    def _assign_initial_post_agents(
        self,
        event_config: EventConfig,
        agent_configs: List[AgentActivityConfig]
    ) -> EventConfig:
        """
        Atribuir Agente publicador apropriado aos posts iniciais
        
        Com base no poster_type de cada post, encontra o agent_id mais adequado
        """
        if not event_config.initial_posts:
            return event_config
        
        # Índice de agentes por tipo de entidade
        agents_by_type: Dict[str, List[AgentActivityConfig]] = {}
        for agent in agent_configs:
            etype = agent.entity_type.lower()
            if etype not in agents_by_type:
                agents_by_type[etype] = []
            agents_by_type[etype].append(agent)
        
        # Tabela de mapeamento de tipos (lida com variações de formato que o LLM pode retornar)
        type_aliases = {
            "official": ["official", "university", "governmentagency", "government"],
            "university": ["university", "official"],
            "mediaoutlet": ["mediaoutlet", "media"],
            "student": ["student", "person"],
            "professor": ["professor", "expert", "teacher"],
            "alumni": ["alumni", "person"],
            "organization": ["organization", "ngo", "company", "group"],
            "person": ["person", "student", "alumni"],
        }
        
        # 记录每种类型已使用的 agent 索引，避免重复使用同一个 agent
        used_indices: Dict[str, int] = {}
        
        updated_posts = []
        for post in event_config.initial_posts:
            poster_type = post.get("poster_type", "").lower()
            content = post.get("content", "")
            
            # 尝试找到匹配的 agent
            matched_agent_id = None
            
            # 1. 直接匹配
            if poster_type in agents_by_type:
                agents = agents_by_type[poster_type]
                idx = used_indices.get(poster_type, 0) % len(agents)
                matched_agent_id = agents[idx].agent_id
                used_indices[poster_type] = idx + 1
            else:
                # 2. 使用别名匹配
                for alias_key, aliases in type_aliases.items():
                    if poster_type in aliases or alias_key == poster_type:
                        for alias in aliases:
                            if alias in agents_by_type:
                                agents = agents_by_type[alias]
                                idx = used_indices.get(alias, 0) % len(agents)
                                matched_agent_id = agents[idx].agent_id
                                used_indices[alias] = idx + 1
                                break
                    if matched_agent_id is not None:
                        break
            
            # 3. Se ainda não encontrou, usar o agente com maior influência
            if matched_agent_id is None:
                logger.warning(f"Nenhum Agente correspondente encontrado para o tipo '{poster_type}', usando o de maior influência")
                if agent_configs:
                    # Ordenar por influência e escolher o maior
                    sorted_agents = sorted(agent_configs, key=lambda a: a.influence_weight, reverse=True)
                    matched_agent_id = sorted_agents[0].agent_id
                else:
                    matched_agent_id = 0
            
            updated_posts.append({
                "content": content,
                "poster_type": post.get("poster_type", "Unknown"),
                "poster_agent_id": matched_agent_id
            })
            
            logger.info(f"Atribuição de post inicial: poster_type='{poster_type}' -> agent_id={matched_agent_id}")
        
        event_config.initial_posts = updated_posts
        return event_config
    
    def _generate_agent_configs_batch(
        self,
        context: str,
        entities: List[EntityNode],
        start_idx: int,
        simulation_requirement: str,
        observation: Any = None,
    ) -> List[AgentActivityConfig]:
        """Gerar configurações de Agentes em lotes"""
        
        # Construir informações das entidades (usando comprimento de resumo configurado)
        entity_list = []
        summary_len = self.AGENT_SUMMARY_LENGTH
        for i, e in enumerate(entities):
            entity_list.append({
                "agent_id": start_idx + i,
                "entity_name": e.name,
                "entity_type": e.get_entity_type() or "Unknown",
                "summary": e.summary[:summary_len] if e.summary else ""
            })
        
        prompt = f"""Com base nas informações abaixo, gere a configuração de atividade em mídia social para cada entidade.

Requisitos da simulação: {simulation_requirement}

## Lista de Entidades
```json
{json.dumps(entity_list, ensure_ascii=False, indent=2)}
```

## Tarefa
Gere a configuração de atividade para cada entidade, observando:
- **Horários compatíveis com os hábitos do público-alvo**: abaixo uma referência para o Brasil (UTC-3); ajuste conforme o cenário de simulação
- **Órgãos oficiais** (University/GovernmentAgency): baixa atividade (0,1-0,3), ativos em horário comercial (9-17h), resposta lenta (60-240 min), alta influência (2,5-3,0)
- **Mídia** (MediaOutlet): atividade média (0,4-0,6), ativo o dia todo (8-23h), resposta rápida (5-30 min), alta influência (2,0-2,5)
- **Indivíduos** (Student/Person/Alumni): alta atividade (0,6-0,9), principalmente à noite (18-23h), resposta rápida (1-15 min), baixa influência (0,8-1,2)
- **Figuras públicas/expertos**: atividade média (0,4-0,6), influência média-alta (1,5-2,0)

Retorne JSON (sem markdown):
{{
    "agent_configs": [
        {{
            "agent_id": <deve ser idêntico ao de entrada>,
            "activity_level": <0.0-1.0>,
            "posts_per_hour": <frequência de posts>,
            "comments_per_hour": <frequência de comentários>,
            "active_hours": [<lista de horas ativas, considerando hábitos do Brasil>],
            "response_delay_min": <atraso mínimo de resposta em minutos>,
            "response_delay_max": <atraso máximo de resposta em minutos>,
            "sentiment_bias": <-1.0 a 1.0>,
            "stance": "<supportive/opposing/neutral/observer>",
            "influence_weight": <peso de influência>
        }},
        ...
    ]
}}"""

        system_prompt = "Você é um especialista em análise de comportamento em mídias sociais. Retorne apenas JSON puro. A configuração deve respeitar os hábitos do público-alvo do cenário simulado."
        system_prompt = f"{system_prompt}\n\n{get_language_instruction()}\nIMPORTANTE: O valor do campo 'stance' DEVE ser uma das strings em inglês: 'supportive', 'opposing', 'neutral', 'observer'. Todos os nomes de campos JSON e valores numéricos devem permanecer inalterados. Apenas campos de texto em linguagem natural devem usar o idioma especificado."

        # Create child span for this LLM call
        span = None
        if observation is not None:
            span = observation.start_span(
                name="simulation_config.agents",
                metadata={
                    "batch_start_idx": start_idx,
                    "batch_size": len(entities),
                    "model": self.model_name,
                },
            )

        try:
            result = self._call_llm_with_retry(prompt, system_prompt, observation=span)
            llm_configs = {cfg["agent_id"]: cfg for cfg in result.get("agent_configs", [])}
            if span is not None:
                span.end()
        except Exception as e:
            logger.warning(f"Falha na geração de lote de configurações de Agente pelo LLM: {e}, usando geração por regras")
            if span is not None:
                span.update(status_message=f"error: {str(e)}", output="")
                span.end()
            llm_configs = {}
        
        # Construir objetos AgentActivityConfig
        configs = []
        for i, entity in enumerate(entities):
            agent_id = start_idx + i
            cfg = llm_configs.get(agent_id, {})
            
            # Se o LLM não gerou, usar geração por regras
            if not cfg:
                cfg = self._generate_agent_config_by_rule(entity)
            
            config = AgentActivityConfig(
                agent_id=agent_id,
                entity_uuid=entity.uuid,
                entity_name=entity.name,
                entity_type=entity.get_entity_type() or "Unknown",
                activity_level=cfg.get("activity_level", 0.5),
                posts_per_hour=cfg.get("posts_per_hour", 0.5),
                comments_per_hour=cfg.get("comments_per_hour", 1.0),
                active_hours=cfg.get("active_hours", list(range(9, 23))),
                response_delay_min=cfg.get("response_delay_min", 5),
                response_delay_max=cfg.get("response_delay_max", 60),
                sentiment_bias=cfg.get("sentiment_bias", 0.0),
                stance=cfg.get("stance", "neutral"),
                influence_weight=cfg.get("influence_weight", 1.0)
            )
            configs.append(config)
        
        return configs
    
    def _generate_agent_config_by_rule(self, entity: EntityNode) -> Dict[str, Any]:
        """Gerar configuração de Agente único baseada em regras (hábitos do Brasil)"""
        entity_type = (entity.get_entity_type() or "Unknown").lower()
        
        if entity_type in ["university", "governmentagency", "ngo"]:
            # Órgãos oficiais: ativos em horário comercial, baixa frequência, alta influência
            return {
                "activity_level": 0.2,
                "posts_per_hour": 0.1,
                "comments_per_hour": 0.05,
                "active_hours": list(range(9, 18)),  # 9:00-17:59
                "response_delay_min": 60,
                "response_delay_max": 240,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 3.0
            }
        elif entity_type in ["mediaoutlet"]:
            # Mídia: ativo o dia todo, frequência média, alta influência
            return {
                "activity_level": 0.5,
                "posts_per_hour": 0.8,
                "comments_per_hour": 0.3,
                "active_hours": list(range(7, 24)),  # 7:00-23:59
                "response_delay_min": 5,
                "response_delay_max": 30,
                "sentiment_bias": 0.0,
                "stance": "observer",
                "influence_weight": 2.5
            }
        elif entity_type in ["professor", "expert", "official"]:
            # Expertos/professores: trabalho + noite, frequência média
            return {
                "activity_level": 0.4,
                "posts_per_hour": 0.3,
                "comments_per_hour": 0.5,
                "active_hours": list(range(8, 22)),  # 8:00-21:59
                "response_delay_min": 15,
                "response_delay_max": 90,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 2.0
            }
        elif entity_type in ["student"]:
            # Estudantes: principalmente à noite, alta frequência
            return {
                "activity_level": 0.8,
                "posts_per_hour": 0.6,
                "comments_per_hour": 1.5,
                "active_hours": [8, 9, 10, 11, 12, 13, 18, 19, 20, 21, 22, 23],  # manhã + noite
                "response_delay_min": 1,
                "response_delay_max": 15,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 0.8
            }
        elif entity_type in ["alumni"]:
            # Alumni: principalmente à noite
            return {
                "activity_level": 0.6,
                "posts_per_hour": 0.4,
                "comments_per_hour": 0.8,
                "active_hours": [12, 13, 19, 20, 21, 22, 23],  # almoço + noite
                "response_delay_min": 5,
                "response_delay_max": 30,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 1.0
            }
        else:
            # Público geral: pico noturno
            return {
                "activity_level": 0.7,
                "posts_per_hour": 0.5,
                "comments_per_hour": 1.2,
                "active_hours": [9, 10, 11, 12, 13, 18, 19, 20, 21, 22, 23],  # dia + noite
                "response_delay_min": 2,
                "response_delay_max": 20,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 1.0
            }
    
