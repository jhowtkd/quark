"""
Gerador de OASIS Agent Profile
Converte entidades do grafo Zep no formato de Agent Profile exigido pela plataforma de simulação OASIS.

Melhorias:
1. Utiliza a função de busca do Zep para enriquecer informações dos nós
2. Otimiza os prompts para gerar personas muito detalhadas
3. Distingue entidades individuais de entidades de grupo abstratas
"""

import json
import random
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from openai import OpenAI
from zep_cloud.client import Zep

from ..config import Config
from ..utils.logger import get_logger
from ..utils.locale import get_language_instruction, get_locale, set_locale, t
from .zep_entity_reader import EntityNode, ZepEntityReader

logger = get_logger('futuria.oasis_profile')


@dataclass
class OasisAgentProfile:
    """Estrutura de dados do OASIS Agent Profile"""
    # 通用字段
    user_id: int
    user_name: str
    name: str
    bio: str
    persona: str
    
    # 可选字段 - Reddit风格
    karma: int = 1000
    
    # 可选字段 - Twitter风格
    friend_count: int = 100
    follower_count: int = 150
    statuses_count: int = 500
    
    # 额外人设信息
    age: Optional[int] = None
    gender: Optional[str] = None
    mbti: Optional[str] = None
    country: Optional[str] = None
    profession: Optional[str] = None
    interested_topics: List[str] = field(default_factory=list)
    
    # 来源实体信息
    source_entity_uuid: Optional[str] = None
    source_entity_type: Optional[str] = None
    
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    def to_reddit_format(self) -> Dict[str, Any]:
        """Converter para o formato da plataforma Reddit"""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,  # OASIS 库要求字段名为 username（无下划线）
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "created_at": self.created_at,
        }
        
        # 添加额外人设信息（如果有）
        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics
        
        return profile
    
    def to_twitter_format(self) -> Dict[str, Any]:
        """Converter para o formato da plataforma Twitter"""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,  # OASIS 库要求字段名为 username（无下划线）
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "created_at": self.created_at,
        }
        
        # 添加额外人设信息
        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics
        
        return profile
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para formato de dicionário completo"""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "age": self.age,
            "gender": self.gender,
            "mbti": self.mbti,
            "country": self.country,
            "profession": self.profession,
            "interested_topics": self.interested_topics,
            "source_entity_uuid": self.source_entity_uuid,
            "source_entity_type": self.source_entity_type,
            "created_at": self.created_at,
        }


class OasisProfileGenerator:
    """
    Gerador de OASIS Profile
    
    Converte entidades do grafo Zep no Agent Profile necessário para a simulação OASIS.
    
    Características otimizadas:
    1. Utiliza a função de busca do grafo Zep para obter contexto mais rico
    2. Gera personas muito detalhadas (incluindo informações básicas, experiência profissional, traços de personalidade, comportamento em mídias sociais, etc.)
    3. Distingue entidades individuais de entidades de grupo abstratas
    """
    
    # MBTI类型列表
    MBTI_TYPES = [
        "INTJ", "INTP", "ENTJ", "ENTP",
        "INFJ", "INFP", "ENFJ", "ENFP",
        "ISTJ", "ISFJ", "ESTJ", "ESFJ",
        "ISTP", "ISFP", "ESTP", "ESFP"
    ]
    
    # 常见国家列表
    COUNTRIES = [
        "China", "US", "UK", "Japan", "Germany", "France", 
        "Canada", "Australia", "Brazil", "India", "South Korea"
    ]
    
    # Tipos de entidade individual (requerem geração de persona específica)
    INDIVIDUAL_ENTITY_TYPES = [
        "student", "alumni", "professor", "person", "publicfigure", 
        "expert", "faculty", "official", "journalist", "activist"
    ]
    
    # Tipos de entidade de grupo/instituição (requerem geração de persona representativa)
    GROUP_ENTITY_TYPES = [
        "university", "governmentagency", "organization", "ngo", 
        "mediaoutlet", "company", "institution", "group", "community"
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        zep_api_key: Optional[str] = None,
        graph_id: Optional[str] = None,
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

        # Cliente Zep para buscar contexto enriquecido
        self.zep_api_key = zep_api_key or Config.ZEP_API_KEY
        self.zep_client = None
        self.graph_id = graph_id

        if self.zep_api_key:
            try:
                self.zep_client = Zep(api_key=self.zep_api_key)
            except Exception as e:
                logger.warning(f"Falha na inicialização do cliente Zep: {e}")
    
    def generate_profile_from_entity(
        self,
        entity: EntityNode,
        user_id: int,
        use_llm: bool = True,
        observation: Any = None,
    ) -> OasisAgentProfile:
        """
        Gerar OASIS Agent Profile a partir de uma entidade Zep

        Args:
            entity: Nó de entidade Zep
            user_id: ID do usuário (para OASIS)
            use_llm: Se deve usar LLM para gerar persona detalhada
            observation: Span de observabilidade opcional para rastrear a geração de profile desta entidade

        Returns:
            OasisAgentProfile
        """
        entity_type = entity.get_entity_type() or "Entity"

        # Informações básicas
        name = entity.name
        user_name = self._generate_username(name)

        # Construir informações de contexto
        context = self._build_entity_context(entity)

        # Criar span filho para a geração de profile desta entidade
        span = None
        if observation is not None:
            span = observation.start_span(
                name="profile_generation",
                metadata={
                    "entity_name": name,
                    "entity_type": entity_type,
                    "user_id": user_id,
                    "use_llm": use_llm,
                    "model": self.model_name,
                    "graph_id": self.graph_id,
                    "context_length": len(context),
                },
            )
            span.update(input={"entity_name": name, "entity_type": entity_type})

        if use_llm:
            # Usar LLM para gerar persona detalhada
            try:
                profile_data = self._generate_profile_with_llm(
                    entity_name=name,
                    entity_type=entity_type,
                    entity_summary=entity.summary,
                    entity_attributes=entity.attributes,
                    context=context,
                    observation=span,
                )
            except Exception as e:
                logger.warning(f"Falha na geração de profile pelo LLM: {e}")
                profile_data = self._generate_profile_rule_based(
                    entity_name=name,
                    entity_type=entity_type,
                    entity_summary=entity.summary,
                    entity_attributes=entity.attributes,
                )
                if span is not None:
                    span.update(status_message=f"LLM falhou, usado baseado em regras: {str(e)}")
        else:
            # Usar regras para gerar persona base
            profile_data = self._generate_profile_rule_based(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes,
            )

        if span is not None:
            span.update(output={"bio_length": len(profile_data.get("bio", ""))})
            span.end()
        
        return OasisAgentProfile(
            user_id=user_id,
            user_name=user_name,
            name=name,
            bio=profile_data.get("bio", f"{entity_type}: {name}"),
            persona=profile_data.get("persona", entity.summary or f"Um {entity_type} chamado {name}."),
            karma=profile_data.get("karma", random.randint(500, 5000)),
            friend_count=profile_data.get("friend_count", random.randint(50, 500)),
            follower_count=profile_data.get("follower_count", random.randint(100, 1000)),
            statuses_count=profile_data.get("statuses_count", random.randint(100, 2000)),
            age=profile_data.get("age"),
            gender=profile_data.get("gender"),
            mbti=profile_data.get("mbti"),
            country=profile_data.get("country"),
            profession=profile_data.get("profession"),
            interested_topics=profile_data.get("interested_topics", []),
            source_entity_uuid=entity.uuid,
            source_entity_type=entity_type,
        )
    
    def _generate_username(self, name: str) -> str:
        """Gerar nome de usuário"""
        # Remover caracteres especiais e converter para minúsculas
        username = name.lower().replace(" ", "_")
        username = ''.join(c for c in username if c.isalnum() or c == '_')
        
        # Adicionar sufixo aleatório para evitar duplicatas
        suffix = random.randint(100, 999)
        return f"{username}_{suffix}"
    
    def _search_zep_for_entity(self, entity: EntityNode) -> Dict[str, Any]:
        """
        Usar a função de busca híbrida do grafo Zep para obter informações ricas sobre a entidade
        
        O Zep não possui interface de busca híbrida integrada; é necessário buscar edges e nodes separadamente e depois mesclar os resultados.
        Utiliza requisições paralelas para aumentar a eficiência.
        
        Args:
            entity: Objeto do nó de entidade
            
        Returns:
            Dicionário contendo facts, node_summaries, context
        """
        import concurrent.futures
        
        if not self.zep_client:
            return {"facts": [], "node_summaries": [], "context": ""}
        
        entity_name = entity.name
        
        results = {
            "facts": [],
            "node_summaries": [],
            "context": ""
        }
        
        # É necessário ter graph_id para realizar a busca
        if not self.graph_id:
            logger.debug(f"Pulando busca Zep: graph_id não definido")
            return results
        
        comprehensive_query = t('progress.zepSearchQuery', name=entity_name)
        
        def search_edges():
            """Buscar edges (fatos/relacionamentos) - com mecanismo de retry"""
            max_retries = 3
            last_exception = None
            delay = 2.0
            
            for attempt in range(max_retries):
                try:
                    return self.zep_client.graph.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=30,
                        scope="edges",
                        reranker="rrf"
                    )
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.debug(f"Falha na busca de edges Zep (tentativa {attempt + 1}): {str(e)[:80]}, tentando novamente...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Busca de edges Zep falhou após {max_retries} tentativas: {e}")
            return None
        
        def search_nodes():
            """Buscar nodes (resumos de entidades) - com mecanismo de retry"""
            max_retries = 3
            last_exception = None
            delay = 2.0
            
            for attempt in range(max_retries):
                try:
                    return self.zep_client.graph.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=20,
                        scope="nodes",
                        reranker="rrf"
                    )
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.debug(f"Falha na busca de nodes Zep (tentativa {attempt + 1}): {str(e)[:80]}, tentando novamente...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Busca de nodes Zep falhou após {max_retries} tentativas: {e}")
            return None
        
        try:
            # Executar buscas de edges e nodes em paralelo
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                edge_future = executor.submit(search_edges)
                node_future = executor.submit(search_nodes)
                
                # Obter resultados
                edge_result = edge_future.result(timeout=30)
                node_result = node_future.result(timeout=30)
            
            # Processar resultados de edges
            all_facts = set()
            if edge_result and hasattr(edge_result, 'edges') and edge_result.edges:
                for edge in edge_result.edges:
                    if hasattr(edge, 'fact') and edge.fact:
                        all_facts.add(edge.fact)
            results["facts"] = list(all_facts)
            
            # Processar resultados de nodes
            all_summaries = set()
            if node_result and hasattr(node_result, 'nodes') and node_result.nodes:
                for node in node_result.nodes:
                    if hasattr(node, 'summary') and node.summary:
                        all_summaries.add(node.summary)
                    if hasattr(node, 'name') and node.name and node.name != entity_name:
                        all_summaries.add(f"Entidade relacionada: {node.name}")
            results["node_summaries"] = list(all_summaries)
            
            # Construir contexto combinado
            context_parts = []
            if results["facts"]:
                context_parts.append("Informações factuais:\n" + "\n".join(f"- {f}" for f in results["facts"][:20]))
            if results["node_summaries"]:
                context_parts.append("Entidades relacionadas:\n" + "\n".join(f"- {s}" for s in results["node_summaries"][:10]))
            results["context"] = "\n\n".join(context_parts)
            
            logger.info(f"Busca híbrida Zep concluída: {entity_name}, obtidos {len(results['facts'])} fatos, {len(results['node_summaries'])} nodes relacionados")
            
        except concurrent.futures.TimeoutError:
            logger.warning(f"Timeout na busca Zep ({entity_name})")
        except Exception as e:
            logger.warning(f"Falha na busca Zep ({entity_name}): {e}")
        
        return results
    
    def _build_entity_context(self, entity: EntityNode) -> str:
        """
        Construir informações de contexto completas da entidade
        
        Inclui:
        1. Informações de edges (fatos) da própria entidade
        2. Detalhes de nodes relacionados
        3. Informações enriquecidas da busca híbrida Zep
        """
        context_parts = []
        
        # 1. Adicionar informações de atributos da entidade
        if entity.attributes:
            attrs = []
            for key, value in entity.attributes.items():
                if value and str(value).strip():
                    attrs.append(f"- {key}: {value}")
            if attrs:
                context_parts.append("### Atributos da Entidade\n" + "\n".join(attrs))
        
        # 2. Adicionar informações de edges relacionados (fatos/relacionamentos)
        existing_facts = set()
        if entity.related_edges:
            relationships = []
            for edge in entity.related_edges:  # Sem limite de quantidade
                fact = edge.get("fact", "")
                edge_name = edge.get("edge_name", "")
                direction = edge.get("direction", "")
                
                if fact:
                    relationships.append(f"- {fact}")
                    existing_facts.add(fact)
                elif edge_name:
                    if direction == "outgoing":
                        relationships.append(f"- {entity.name} --[{edge_name}]--> (entidade relacionada)")
                    else:
                        relationships.append(f"- (entidade relacionada) --[{edge_name}]--> {entity.name}")
            
            if relationships:
                context_parts.append("### Fatos e Relacionamentos Relacionados\n" + "\n".join(relationships))
        
        # 3. Adicionar detalhes de nodes relacionados
        if entity.related_nodes:
            related_info = []
            for node in entity.related_nodes:  # Sem limite de quantidade
                node_name = node.get("name", "")
                node_labels = node.get("labels", [])
                node_summary = node.get("summary", "")
                
                # Filtrar labels padrão
                custom_labels = [l for l in node_labels if l not in ["Entity", "Node"]]
                label_str = f" ({', '.join(custom_labels)})" if custom_labels else ""
                
                if node_summary:
                    related_info.append(f"- **{node_name}**{label_str}: {node_summary}")
                else:
                    related_info.append(f"- **{node_name}**{label_str}")
            
            if related_info:
                context_parts.append("### Informações de Entidades Relacionadas\n" + "\n".join(related_info))
        
        # 4. Usar busca híbrida Zep para obter informações mais ricas
        zep_results = self._search_zep_for_entity(entity)
        
        if zep_results.get("facts"):
            # Deduplicar: excluir fatos já existentes
            new_facts = [f for f in zep_results["facts"] if f not in existing_facts]
            if new_facts:
                context_parts.append("### Informações Factuais Encontradas pela Busca Zep\n" + "\n".join(f"- {f}" for f in new_facts[:15]))
        
        if zep_results.get("node_summaries"):
            context_parts.append("### Nodes Relacionados Encontrados pela Busca Zep\n" + "\n".join(f"- {s}" for s in zep_results["node_summaries"][:10]))
        
        return "\n\n".join(context_parts)
    
    def _is_individual_entity(self, entity_type: str) -> bool:
        """Verificar se é uma entidade do tipo individual"""
        return entity_type.lower() in self.INDIVIDUAL_ENTITY_TYPES
    
    def _is_group_entity(self, entity_type: str) -> bool:
        """Verificar se é uma entidade do tipo grupo/instituição"""
        return entity_type.lower() in self.GROUP_ENTITY_TYPES
    
    def _generate_profile_with_llm(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str,
        observation: Any = None,
    ) -> Dict[str, Any]:
        """
        Usar LLM para gerar uma persona muito detalhada

        Distinção por tipo de entidade:
        - Entidade individual: gera configuração de personagem específica
        - Entidade de grupo/instituição: gera configuração de conta representativa
        """

        is_individual = self._is_individual_entity(entity_type)

        if is_individual:
            prompt = self._build_individual_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context
            )
        else:
            prompt = self._build_group_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context
            )

        # 尝试多次生成，直到成功或达到最大重试次数
        max_attempts = 3
        last_error = None
        total_latency_ms = 0.0

        for attempt in range(max_attempts):
            attempt_start = time.perf_counter()
            attempt_span = None
            if observation is not None:
                attempt_span = observation.start_span(
                    name="profile_generation.attempt",
                    metadata={
                        "entity_name": entity_name,
                        "entity_type": entity_type,
                        "attempt": attempt + 1,
                        "max_attempts": max_attempts,
                        "is_individual": is_individual,
                        "model": self.model_name,
                    },
                )
                attempt_span.update(
                    input={
                        "entity_name": entity_name,
                        "entity_type": entity_type,
                        "attempt": attempt + 1,
                    }
                )
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt(is_individual)},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7 - (attempt * 0.1)  # Reduzir temperatura a cada retry
                    # Não definir max_tokens para deixar o LLM livre
                )

                latency_ms = (time.perf_counter() - attempt_start) * 1000
                total_latency_ms += latency_ms

                content = response.choices[0].message.content

                # Verificar se foi truncado (finish_reason não é 'stop')
                finish_reason = response.choices[0].finish_reason
                if finish_reason == 'length':
                    logger.warning(f"Saída do LLM truncada (tentativa {attempt+1}), tentando corrigir...")
                    content = self._fix_truncated_json(content)

                # Tentar analisar JSON
                try:
                    result = json.loads(content)

                    # Validar campos obrigatórios
                    if "bio" not in result or not result["bio"]:
                        result["bio"] = entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}"
                    if "persona" not in result or not result["persona"]:
                        result["persona"] = entity_summary or f"{entity_name} é um {entity_type}."

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
                    if attempt_span is not None:
                        attempt_span.update(
                            output=result,
                            latency_ms=latency_ms,
                            usage={
                                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                                "total_tokens": getattr(response.usage, "total_tokens", 0),
                            },
                        )

                    return result

                except json.JSONDecodeError as je:
                    logger.warning(f"Falha ao analisar JSON (tentativa {attempt+1}): {str(je)[:80]}")

                    # Tentar corrigir JSON
                    result = self._try_fix_json(content, entity_name, entity_type, entity_summary)
                    if result.get("_fixed"):
                        del result["_fixed"]
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
                        if attempt_span is not None:
                            attempt_span.update(
                                output=result,
                                latency_ms=latency_ms,
                                usage={
                                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                                    "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                                },
                            )
                        return result

                    last_error = je
                    if attempt_span is not None:
                        attempt_span.update(status_message=f"json_decode_error: {str(je)}", output="")

            except Exception as e:
                total_latency_ms += time.perf_counter() * 1000
                logger.warning(f"Falha na chamada ao LLM (tentativa {attempt+1}): {str(e)[:80]}")
                last_error = e
                if attempt_span is not None:
                    attempt_span.update(status_message=f"error: {str(e)}", output="")
                time.sleep(1 * (attempt + 1))  # Backoff exponencial
            finally:
                if attempt_span is not None:
                    attempt_span.end()

        # Todas as tentativas esgotadas
        if observation is not None:
            observation.update(
                status_message=f"error after {max_attempts} attempts: {str(last_error)}",
                output="",
            )

        logger.warning(f"Falha na geração de persona pelo LLM ({max_attempts} tentativas): {last_error}, usando geração por regras")
        return self._generate_profile_rule_based(
            entity_name, entity_type, entity_summary, entity_attributes
        )
    
    def _fix_truncated_json(self, content: str) -> str:
        """修复被截断的JSON（输出被max_tokens限制截断）"""
        import re
        
        # 如果JSON被截断，尝试闭合它
        content = content.strip()
        
        # 计算未闭合的括号
        open_braces = content.count('{') - content.count('}')
        open_brackets = content.count('[') - content.count(']')
        
        # 检查是否有未闭合的字符串
        # 简单检查：如果最后一个引号后没有逗号或闭合括号，可能是字符串被截断
        if content and content[-1] not in '",}]':
            # 尝试闭合字符串
            content += '"'
        
        # 闭合括号
        content += ']' * open_brackets
        content += '}' * open_braces
        
        return content
    
    def _try_fix_json(self, content: str, entity_name: str, entity_type: str, entity_summary: str = "") -> Dict[str, Any]:
        """尝试修复损坏的JSON"""
        import re
        
        # 1. 首先尝试修复被截断的情况
        content = self._fix_truncated_json(content)
        
        # 2. 尝试提取JSON部分
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group()
            
            # 3. 处理字符串中的换行符问题
            # 找到所有字符串值并替换其中的换行符
            def fix_string_newlines(match):
                s = match.group(0)
                # 替换字符串内的实际换行符为空格
                s = s.replace('\n', ' ').replace('\r', ' ')
                # 替换多余空格
                s = re.sub(r'\s+', ' ', s)
                return s
            
            # 匹配JSON字符串值
            json_str = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_string_newlines, json_str)
            
            # 4. 尝试解析
            try:
                result = json.loads(json_str)
                result["_fixed"] = True
                return result
            except json.JSONDecodeError as e:
                # 5. 如果还是失败，尝试更激进的修复
                try:
                    # 移除所有控制字符
                    json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
                    # 替换所有连续空白
                    json_str = re.sub(r'\s+', ' ', json_str)
                    result = json.loads(json_str)
                    result["_fixed"] = True
                    return result
                except:
                    pass
        
        # 6. 尝试从内容中提取部分信息
        bio_match = re.search(r'"bio"\s*:\s*"([^"]*)"', content)
        persona_match = re.search(r'"persona"\s*:\s*"([^"]*)', content)  # 可能被截断
        
        bio = bio_match.group(1) if bio_match else (entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}")
        persona = persona_match.group(1) if persona_match else (entity_summary or f"{entity_name} é um {entity_type}.")
        
        # 如果提取到了有意义的内容，标记为已修复
        if bio_match or persona_match:
            logger.info(f"Informações parciais extraídas de JSON corrompido")
            return {
                "bio": bio,
                "persona": persona,
                "_fixed": True
            }
        
        # 7. 完全失败，返回基础结构
        logger.warning(f"Falha na correção de JSON, retornando estrutura base")
        return {
            "bio": entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}",
            "persona": entity_summary or f"{entity_name} é um {entity_type}."
        }
    
    def _get_system_prompt(self, is_individual: bool) -> str:
        """Obter prompt de sistema"""
        base_prompt = "Você é um especialista em geração de personas para mídias sociais. Gere personas detalhadas e realistas para simulação de opinião pública, reproduzindo ao máximo a realidade existente. Deve retornar um JSON válido; todos os valores de string não podem conter quebras de linha não escapadas."
        return f"{base_prompt}\n\n{get_language_instruction()}"
    
    def _build_individual_persona_prompt(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str
    ) -> str:
        """Construir prompt de persona detalhada para entidade individual"""
        
        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "Nenhum"
        context_str = context[:3000] if context else "Nenhum contexto adicional"
        
        return f"""Gere uma persona detalhada de usuário de mídia social para a entidade, reproduzindo ao máximo a realidade existente.

Nome da entidade: {entity_name}
Tipo da entidade: {entity_type}
Resumo da entidade: {entity_summary}
Atributos da entidade: {attrs_str}

Informações de contexto:
{context_str}

Gere JSON com os seguintes campos:

1. bio: Resumo da mídia social, 200 caracteres
2. persona: Descrição detalhada da persona (texto puro de 2000 caracteres), deve incluir:
   - Informações básicas (idade, profissão, formação educacional, localidade)
   - Histórico da pessoa (experiências importantes, vínculo com o evento, relações sociais)
   - Traços de personalidade (tipo MBTI, personalidade central, forma de expressar emoções)
   - Comportamento em mídias sociais (frequência de posts, preferências de conteúdo, estilo de interação, características linguísticas)
   - Posicionamento e opiniões (atitude sobre o tema, o que pode irritar/emoionar)
   - Características únicas (bordões, experiências especiais, hobbies pessoais)
   - Memórias pessoais (parte importante da persona: relação deste indivíduo com o evento, ações e reações já tomadas no evento)
3. age: Número da idade (deve ser inteiro)
4. gender: Gênero, deve estar em inglês: "male" ou "female"
5. mbti: Tipo MBTI (ex.: INTJ, ENFP, etc.)
6. country: País (ex.: "Brasil")
7. profession: Profissão
8. interested_topics: Array de tópicos de interesse

Importante:
- Todos os valores de campos devem ser string ou número; não use quebras de linha
- persona deve ser um texto contínuo e coerente
- {get_language_instruction()} (campo gender deve estar em inglês male/female)
- O conteúdo deve ser consistente com as informações da entidade
- age deve ser um inteiro válido; gender deve ser "male" ou "female"
"""

    def _build_group_persona_prompt(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str
    ) -> str:
        """Construir prompt de persona detalhada para entidade de grupo/instituição"""
        
        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "Nenhum"
        context_str = context[:3000] if context else "Nenhum contexto adicional"
        
        return f"""Gere uma configuração detalhada de conta de mídia social para uma entidade institucional/grupo, reproduzindo ao máximo a realidade existente.

Nome da entidade: {entity_name}
Tipo da entidade: {entity_type}
Resumo da entidade: {entity_summary}
Atributos da entidade: {attrs_str}

Informações de contexto:
{context_str}

Gere JSON com os seguintes campos:

1. bio: Resumo oficial da conta, 200 caracteres, profissional e adequado
2. persona: Descrição detalhada da configuração da conta (texto puro de 2000 caracteres), deve incluir:
   - Informações básicas da instituição (nome formal, natureza da instituição, histórico de fundação, principais funções)
   - Posicionamento da conta (tipo de conta, público-alvo, função principal)
   - Estilo de fala (características linguísticas, expressões comuns, tópicos proibidos)
   - Características do conteúdo publicado (tipos de conteúdo, frequência de publicação, períodos de atividade)
   - Posicionamento e atitude (posição oficial sobre os temas centrais, forma de lidar com controvérsias)
   - Observações especiais (retrato do grupo representado, hábitos de operação)
   - Memórias institucionais (parte importante da persona institucional: relação desta instituição com o evento, ações e reações já tomadas no evento)
3. age: Preencher fixo com 30 (idade virtual de conta institucional)
4. gender: Preencher fixo com "other" (contas institucionais usam other para indicar não-pessoa)
5. mbti: Tipo MBTI, usado para descrever o estilo da conta; ex.: ISTJ representa rigor e conservadorismo
6. country: País (ex.: "Brasil")
7. profession: Descrição das funções da instituição
8. interested_topics: Array de áreas de interesse

Importante:
- Todos os valores de campos devem ser string ou número; valores nulos não são permitidos
- persona deve ser um texto contínuo e coerente; não use quebras de linha
- {get_language_instruction()} (campo gender deve estar em inglês "other")
- age deve ser o inteiro 30; gender deve ser a string "other"
- A fala de contas institucionais deve estar em conformidade com sua identidade
"""
    
    def _generate_profile_rule_based(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gerar persona base usando regras"""
        
        # Gerar personas diferentes conforme o tipo de entidade
        entity_type_lower = entity_type.lower()
        
        if entity_type_lower in ["student", "alumni"]:
            return {
                "bio": f"{entity_type} com interesses em acadêmicos e questões sociais.",
                "persona": f"{entity_name} é um {entity_type.lower()} ativamente envolvido em discussões acadêmicas e sociais. Gosta de compartilhar perspectivas e conectar-se com colegas.",
                "age": random.randint(18, 30),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(self.MBTI_TYPES),
                "country": random.choice(self.COUNTRIES),
                "profession": "Student",
                "interested_topics": ["Educação", "Questões Sociais", "Tecnologia"],
            }
        
        elif entity_type_lower in ["publicfigure", "expert", "faculty"]:
            return {
                "bio": f"Expert e líder de opinião em sua área.",
                "persona": f"{entity_name} é um {entity_type.lower()} reconhecido que compartilha insights e opiniões sobre assuntos importantes. É conhecido por sua expertise e influência no discurso público.",
                "age": random.randint(35, 60),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(["ENTJ", "INTJ", "ENTP", "INTP"]),
                "country": random.choice(self.COUNTRIES),
                "profession": entity_attributes.get("occupation", "Expert"),
                "interested_topics": ["Política", "Economia", "Cultura e Sociedade"],
            }
        
        elif entity_type_lower in ["mediaoutlet", "socialmediaplatform"]:
            return {
                "bio": f"Conta oficial de {entity_name}. Notícias e atualizações.",
                "persona": f"{entity_name} é uma entidade de mídia que reporta notícias e facilita o discurso público. A conta compartilha atualizações oportunas e se envolve com o público sobre eventos atuais.",
                "age": 30,  # Idade virtual de instituição
                "gender": "other",  # Instituições usam other
                "mbti": "ISTJ",  # Estilo institucional: rigoroso e conservador
                "country": "Brasil",
                "profession": "Mídia",
                "interested_topics": ["Notícias Gerais", "Eventos Atuais", "Assuntos Públicos"],
            }
        
        elif entity_type_lower in ["university", "governmentagency", "ngo", "organization"]:
            return {
                "bio": f"Conta oficial de {entity_name}.",
                "persona": f"{entity_name} é uma entidade institucional que comunica posições oficiais, anúncios e se envolve com stakeholders sobre assuntos relevantes.",
                "age": 30,  # Idade virtual de instituição
                "gender": "other",  # Instituições usam other
                "mbti": "ISTJ",  # Estilo institucional: rigoroso e conservador
                "country": "Brasil",
                "profession": entity_type,
                "interested_topics": ["Políticas Públicas", "Comunidade", "Anúncios Oficiais"],
            }
        
        else:
            # Persona padrão
            return {
                "bio": entity_summary[:150] if entity_summary else f"{entity_type}: {entity_name}",
                "persona": entity_summary or f"{entity_name} é um {entity_type.lower()} participando de discussões sociais.",
                "age": random.randint(25, 50),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(self.MBTI_TYPES),
                "country": random.choice(self.COUNTRIES),
                "profession": entity_type,
                "interested_topics": ["Geral", "Questões Sociais"],
            }
    
    def set_graph_id(self, graph_id: str):
        """Definir graph_id para busca Zep"""
        self.graph_id = graph_id
    
    def generate_profiles_from_entities(
        self,
        entities: List[EntityNode],
        use_llm: bool = True,
        progress_callback: Optional[callable] = None,
        graph_id: Optional[str] = None,
        parallel_count: int = 5,
        realtime_output_path: Optional[str] = None,
        output_platform: str = "reddit",
        observation: Any = None,
    ) -> List[OasisAgentProfile]:
        """
        Gerar Agent Profiles em lote a partir de entidades (suporta geração paralela)

        Args:
            entities: Lista de entidades
            use_llm: Se deve usar LLM para gerar persona detalhada
            progress_callback: Função de callback de progresso (current, total, message)
            graph_id: ID do grafo, para busca Zep obter contexto mais rico
            parallel_count: Quantidade de geração paralela, padrão 5
            realtime_output_path: Caminho de arquivo para escrita em tempo real (se fornecido, escreve a cada geração)
            output_platform: Formato de saída da plataforma ("reddit" ou "twitter")
            observation: Span de observabilidade pai opcional

        Returns:
            Lista de Agent Profiles
        """
        import concurrent.futures
        from threading import Lock
        
        # Definir graph_id para busca Zep
        if graph_id:
            self.graph_id = graph_id
        
        total = len(entities)
        profiles = [None] * total  # Pré-alocar lista para manter ordem
        completed_count = [0]  # Usar lista para permitir modificação no closure
        lock = Lock()
        
        # Função auxiliar para salvar profiles em tempo real
        def save_profiles_realtime():
            """Salvar profiles gerados em tempo real no arquivo"""
            if not realtime_output_path:
                return
            
            with lock:
                # Filtrar profiles já gerados
                existing_profiles = [p for p in profiles if p is not None]
                if not existing_profiles:
                    return
                
                try:
                    if output_platform == "reddit":
                        # Formato JSON do Reddit
                        profiles_data = [p.to_reddit_format() for p in existing_profiles]
                        with open(realtime_output_path, 'w', encoding='utf-8') as f:
                            json.dump(profiles_data, f, ensure_ascii=False, indent=2)
                    else:
                        # Formato CSV do Twitter
                        import csv
                        profiles_data = [p.to_twitter_format() for p in existing_profiles]
                        if profiles_data:
                            fieldnames = list(profiles_data[0].keys())
                            with open(realtime_output_path, 'w', encoding='utf-8', newline='') as f:
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writeheader()
                                writer.writerows(profiles_data)
                except Exception as e:
                    logger.warning(f"Falha ao salvar profiles em tempo real: {e}")
        
        # Capturar locale antes de iniciar workers do thread pool
        current_locale = get_locale()

        def generate_single_profile(idx: int, entity: EntityNode) -> tuple:
            """Função de trabalho para gerar um único profile"""
            set_locale(current_locale)
            entity_type = entity.get_entity_type() or "Entity"

            try:
                profile = self.generate_profile_from_entity(
                    entity=entity,
                    user_id=idx,
                    use_llm=use_llm,
                    observation=observation,
                )

                # Saída em tempo real do profile gerado para console e logs
                self._print_generated_profile(entity.name, entity_type, profile)

                return idx, profile, None

            except Exception as e:
                logger.error(f"Falha ao gerar persona da entidade {entity.name}: {str(e)}")
                # Criar um profile base
                fallback_profile = OasisAgentProfile(
                    user_id=idx,
                    user_name=self._generate_username(entity.name),
                    name=entity.name,
                    bio=f"{entity_type}: {entity.name}",
                    persona=entity.summary or f"Um participante em discussões sociais.",
                    source_entity_uuid=entity.uuid,
                    source_entity_type=entity_type,
                )
                return idx, fallback_profile, str(e)
        
        logger.info(f"Iniciando geração paralela de {total} personas de Agentes (paralelismo: {parallel_count})...")
        print(f"\n{'='*60}")
        print(f"Iniciando geração de personas de Agentes - Total: {total} entidades, paralelismo: {parallel_count}")
        print(f"{'='*60}\n")
        
        # Executar em paralelo com thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_count) as executor:
            # Submeter todas as tarefas
            future_to_entity = {
                executor.submit(generate_single_profile, idx, entity): (idx, entity)
                for idx, entity in enumerate(entities)
            }
            
            # Coletar resultados
            for future in concurrent.futures.as_completed(future_to_entity):
                idx, entity = future_to_entity[future]
                entity_type = entity.get_entity_type() or "Entity"
                
                try:
                    result_idx, profile, error = future.result()
                    profiles[result_idx] = profile
                    
                    with lock:
                        completed_count[0] += 1
                        current = completed_count[0]
                    
                    # Salvar em tempo real
                    save_profiles_realtime()
                    
                    if progress_callback:
                        progress_callback(
                            current, 
                            total, 
                            self._format_profile_progress_message(current, total, entity.name, entity_type)
                        )
                    
                    if error:
                        logger.warning(f"[{current}/{total}] {entity.name} usando persona de contingência: {error}")
                    else:
                        logger.info(f"[{current}/{total}] Persona gerada com sucesso: {entity.name} ({entity_type})")
                        
                except Exception as e:
                    logger.error(f"Exceção ao processar entidade {entity.name}: {str(e)}")
                    with lock:
                        completed_count[0] += 1
                    profiles[idx] = OasisAgentProfile(
                        user_id=idx,
                        user_name=self._generate_username(entity.name),
                        name=entity.name,
                        bio=f"{entity_type}: {entity.name}",
                        persona=entity.summary or "Um participante em discussões sociais.",
                        source_entity_uuid=entity.uuid,
                        source_entity_type=entity_type,
                    )
                    # Salvar em tempo real (mesmo para persona de contingência)
                    save_profiles_realtime()
        
        print(f"\n{'='*60}")
        print(f"Geração de personas concluída! Total gerado: {len([p for p in profiles if p])} Agentes")
        print(f"{'='*60}\n")
        
        return profiles

    def _format_profile_progress_message(self, current: int, total: int, entity_name: str, entity_type: str) -> str:
        """Formatar mensagem de progresso para o frontend, evitando caracteres chineses e símbolos de largura total."""
        return f"Concluído {current}/{total}: {entity_name} ({entity_type})"
    
    def _print_generated_profile(self, entity_name: str, entity_type: str, profile: OasisAgentProfile):
        """Saída em tempo real do profile gerado para o console (conteúdo completo, sem truncar)"""
        separator = "-" * 70
        
        # Construir saída completa (sem truncar)
        topics_str = ', '.join(profile.interested_topics) if profile.interested_topics else 'Nenhum'
        
        output_lines = [
            f"\n{separator}",
            t('progress.profileGenerated', name=entity_name, type=entity_type),
            f"{separator}",
            f"Nome de usuário: {profile.user_name}",
            f"",
            f"[Bio]",
            f"{profile.bio}",
            f"",
            f"[Persona Detalhada]",
            f"{profile.persona}",
            f"",
            f"[Atributos Básicos]",
            f"Idade: {profile.age} | Gênero: {profile.gender} | MBTI: {profile.mbti}",
            f"Profissão: {profile.profession} | País: {profile.country}",
            f"Tópicos de interesse: {topics_str}",
            separator
        ]
        
        output = "\n".join(output_lines)
        
        # Apenas saída para console (evitar duplicação; logger não imprime conteúdo completo)
        print(output)
    
    def save_profiles(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """
        Salvar Profiles no arquivo (formato correto conforme a plataforma)
        
        Requisitos de formato da plataforma OASIS:
        - Twitter: formato CSV
        - Reddit: formato JSON
        
        Args:
            profiles: Lista de Profiles
            file_path: Caminho do arquivo
            platform: Tipo de plataforma ("reddit" ou "twitter")
        """
        if platform == "twitter":
            self._save_twitter_csv(profiles, file_path)
        else:
            self._save_reddit_json(profiles, file_path)
    
    def _save_twitter_csv(self, profiles: List[OasisAgentProfile], file_path: str):
        """
        Salvar Twitter Profile em formato CSV (conforme requisitos oficiais do OASIS)
        
        Campos CSV exigidos pelo OASIS Twitter:
        - user_id: ID do usuário (sequencial a partir de 0 no CSV)
        - name: nome real do usuário
        - username: nome de usuário no sistema
        - user_char: descrição detalhada da persona (injetada no prompt de sistema do LLM para guiar comportamento do Agente)
        - description: resumo público breve (exibido na página de perfil do usuário)
        
        Diferença user_char vs description:
        - user_char: uso interno, prompt de sistema do LLM, determina como o Agente pensa e age
        - description: exibição externa, resumo visível para outros usuários
        """
        import csv
        
        # Garantir extensão .csv
        if not file_path.endswith('.csv'):
            file_path = file_path.replace('.json', '.csv')
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Escrever cabeçalho exigido pelo OASIS
            headers = ['user_id', 'name', 'username', 'user_char', 'description']
            writer.writerow(headers)
            
            # Escrever linhas de dados
            for idx, profile in enumerate(profiles):
                # user_char: persona completa (bio + persona), usada no prompt de sistema do LLM
                user_char = profile.bio
                if profile.persona and profile.persona != profile.bio:
                    user_char = f"{profile.bio} {profile.persona}"
                # Tratar quebras de linha (substituir por espaço no CSV)
                user_char = user_char.replace('\n', ' ').replace('\r', ' ')
                
                # description: resumo breve, para exibição externa
                description = profile.bio.replace('\n', ' ').replace('\r', ' ')
                
                row = [
                    idx,                    # user_id: ID sequencial a partir de 0
                    profile.name,           # name: nome real
                    profile.user_name,      # username: nome de usuário
                    user_char,              # user_char: persona completa (uso interno do LLM)
                    description             # description: resumo breve (exibição externa)
                ]
                writer.writerow(row)
        
        logger.info(f"Salvos {len(profiles)} Twitter Profiles em {file_path} (formato CSV OASIS)")
    
    def _normalize_gender(self, gender: Optional[str]) -> str:
        """
        Normalizar campo gender para o formato em inglês exigido pelo OASIS
        
        OASIS exige: male, female, other
        """
        if not gender:
            return "other"
        
        gender_lower = gender.lower().strip()
        
        # Mapeamento de gênero (inclui chinês como fallback defensivo)
        gender_map = {
            "男": "male",
            "女": "female",
            "机构": "other",
            "其他": "other",
            # Português
            "masculino": "male",
            "feminino": "female",
            "outro": "other",
            # Inglês
            "male": "male",
            "female": "female",
            "other": "other",
        }
        
        return gender_map.get(gender_lower, "other")
    
    def _save_reddit_json(self, profiles: List[OasisAgentProfile], file_path: str):
        """
        Salvar Reddit Profile em formato JSON
        
        Usar formato consistente com to_reddit_format(), garantindo que OASIS leia corretamente.
        O campo user_id é obrigatório; é a chave para o matching do OASIS agent_graph.get_agent()!
        
        Campos obrigatórios:
        - user_id: ID do usuário (inteiro, para corresponder ao poster_agent_id dos initial_posts)
        - username: nome de usuário
        - name: nome de exibição
        - bio: resumo
        - persona: persona detalhada
        - age: idade (inteiro)
        - gender: "male", "female" ou "other"
        - mbti: tipo MBTI
        - country: país
        """
        data = []
        for idx, profile in enumerate(profiles):
            # Usar formato consistente com to_reddit_format()
            item = {
                "user_id": profile.user_id if profile.user_id is not None else idx,  # Chave: deve conter user_id
                "username": profile.user_name,
                "name": profile.name,
                "bio": profile.bio[:150] if profile.bio else f"{profile.name}",
                "persona": profile.persona or f"{profile.name} é um participante em discussões sociais.",
                "karma": profile.karma if profile.karma else 1000,
                "created_at": profile.created_at,
                # Campos obrigatórios do OASIS — garantir defaults
                "age": profile.age if profile.age else 30,
                "gender": self._normalize_gender(profile.gender),
                "mbti": profile.mbti if profile.mbti else "ISTJ",
                "country": profile.country if profile.country else "Brasil",
            }
            
            # Campos opcionais
            if profile.profession:
                item["profession"] = profile.profession
            if profile.interested_topics:
                item["interested_topics"] = profile.interested_topics
            
            data.append(item)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Salvos {len(profiles)} Reddit Profiles em {file_path} (formato JSON, incluindo campo user_id)")
    
    # Manter nome antigo como alias para compatibilidade retroativa
    def save_profiles_to_json(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """[Obsoleto] Use o método save_profiles()"""
        logger.warning("save_profiles_to_json está obsoleto, use save_profiles")
        self.save_profiles(profiles, file_path, platform)
