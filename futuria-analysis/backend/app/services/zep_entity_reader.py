"""
Zep实体读取与过滤服务
从Zep图谱中读取节点，筛选出符合预定义实体类型的节点
"""

import time
from typing import Dict, Any, List, Optional, Set, Callable, TypeVar
from dataclasses import dataclass, field

from zep_cloud.client import Zep

from ..config import Config
from ..utils.logger import get_logger
from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges

logger = get_logger('futuria.zep_entity_reader')


def _contains_forbidden_script(text: str, forbidden_scripts: List[str] = None) -> bool:
    """
    Verifica se o texto contém scripts proibidos (chines, japones, coreano).

    Args:
        text: Texto a verificar
        forbidden_scripts: Lista de scripts proibidos ['zh', 'ja', 'ko']

    Returns:
        True se contiver scripts proibidos
    """
    if not text:
        return False

    forbidden = forbidden_scripts or ['zh', 'ja', 'ko']

    # Unicode ranges for CJK scripts
    script_ranges = {
        'zh': [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x20000, 0x2A6DF)],  # CJK Unified
        'ja': [(0x3040, 0x309F), (0x30A0, 0x30FF), (0x4E00, 0x9FFF)],     # Hiragana, Katakana, Kanji
        'ko': [(0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x3130, 0x318F)],     # Hangul
    }

    for ch in text:
        code = ord(ch)
        for script in forbidden:
            if script in script_ranges:
                for start, end in script_ranges[script]:
                    if start <= code <= end:
                        return True
    return False


def _infer_entity_type_from_context(name: str, summary: str, labels: List[str]) -> Optional[str]:
    """
    Inferencia heuristica de tipo de entidade baseada em nome e summary.
    Usada quando Zep retorna apenas labels genericas ("Entity", "Node").

    Args:
        name: Nome da entidade
        summary: Resumo da entidade
        labels: Labels existentes

    Returns:
        Tipo inferido ou None
    """
    text = f"{name} {summary}".lower()

    # Heuristicas baseadas em palavras-chave
    keywords_map = {
        "GovernmentAgency": ["ministerio", "secretaria", "agencia", "orgao", "tribunal", "camara", "senado", "prefeitura", "governo", "instituto", "federal", "estadual"],
        "PublicFigure": ["politico", "deputado", "senador", "prefeito", "presidente", "vereador", "ministro", "governador", "candidato", "eleito", "lider", "ativista", "jornalista"],
        "Expert": ["professor", "pesquisador", "cientista", "medico", "economista", "advogado", "doutor", "phd", "especialista", "consultor", "analista", "engenheiro"],
        "Organization": ["empresa", "instituicao", "fundacao", "associacao", "cooperativa", "sociedade", "ong", "startup", "corporacao", "grupo", "holdings"],
        "MediaOutlet": ["jornal", "revista", "portal", "tv", "radio", "blog", "site", "midia", "imprensa", "emissora", "canal", "publicacao"],
        "Student": ["aluno", "estudante", "graduacao", "mestrado", "doutorado", "universitario", "escola", "faculdade"],
        "University": ["universidade", "faculdade", "instituto federal", "escola tecnica", "centro universitario"],
    }

    for entity_type, keywords in keywords_map.items():
        for kw in keywords:
            if kw in text:
                return entity_type

    return None


# 用于泛型返回类型
T = TypeVar('T')


@dataclass
class EntityNode:
    """实体节点数据结构"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    # 相关的边信息
    related_edges: List[Dict[str, Any]] = field(default_factory=list)
    # 相关的其他节点信息
    related_nodes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes,
            "related_edges": self.related_edges,
            "related_nodes": self.related_nodes,
        }
    
    def get_entity_type(self) -> Optional[str]:
        """获取实体类型（排除默认的Entity标签）"""
        for label in self.labels:
            if label not in ["Entity", "Node"]:
                return label
        return None


@dataclass
class FilteredEntities:
    """过滤后的实体集合"""
    entities: List[EntityNode]
    entity_types: Set[str]
    total_count: int
    filtered_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "entity_types": list(self.entity_types),
            "total_count": self.total_count,
            "filtered_count": self.filtered_count,
        }


class ZepEntityReader:
    """
    Zep实体读取与过滤服务
    
    主要功能：
    1. 从Zep图谱读取所有节点
    2. 筛选出符合预定义实体类型的节点（Labels不只是Entity的节点）
    3. 获取每个实体的相关边和关联节点信息
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ZEP_API_KEY
        if not self.api_key:
            raise ValueError("ZEP_API_KEY 未配置")
        
        self.client = Zep(api_key=self.api_key)
    
    def _call_with_retry(
        self, 
        func: Callable[[], T], 
        operation_name: str,
        max_retries: int = 3,
        initial_delay: float = 2.0
    ) -> T:
        """
        带重试机制的Zep API调用
        
        Args:
            func: 要执行的函数（无参数的lambda或callable）
            operation_name: 操作名称，用于日志
            max_retries: 最大重试次数（默认3次，即最多尝试3次）
            initial_delay: 初始延迟秒数
            
        Returns:
            API调用结果
        """
        last_exception = None
        delay = initial_delay
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Zep {operation_name} 第 {attempt + 1} 次尝试失败: {str(e)[:100]}, "
                        f"{delay:.1f}秒后重试..."
                    )
                    time.sleep(delay)
                    delay *= 2  # 指数退避
                else:
                    logger.error(f"Zep {operation_name} 在 {max_retries} 次尝试后仍失败: {str(e)}")
        
        raise last_exception
    
    def get_all_nodes(self, graph_id: str) -> List[Dict[str, Any]]:
        """
        获取图谱的所有节点（分页获取）

        Args:
            graph_id: 图谱ID

        Returns:
            节点列表
        """
        logger.info(f"获取图谱 {graph_id} 的所有节点...")

        nodes = fetch_all_nodes(self.client, graph_id)

        nodes_data = []
        for node in nodes:
            nodes_data.append({
                "uuid": getattr(node, 'uuid_', None) or getattr(node, 'uuid', ''),
                "name": node.name or "",
                "labels": node.labels or [],
                "summary": node.summary or "",
                "attributes": node.attributes or {},
            })

        logger.info(f"共获取 {len(nodes_data)} 个节点")
        return nodes_data

    def get_all_edges(self, graph_id: str) -> List[Dict[str, Any]]:
        """
        获取图谱的所有边（分页获取）

        Args:
            graph_id: 图谱ID

        Returns:
            边列表
        """
        logger.info(f"获取图谱 {graph_id} 的所有边...")

        edges = fetch_all_edges(self.client, graph_id)

        edges_data = []
        for edge in edges:
            edges_data.append({
                "uuid": getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', ''),
                "name": edge.name or "",
                "fact": edge.fact or "",
                "source_node_uuid": edge.source_node_uuid,
                "target_node_uuid": edge.target_node_uuid,
                "attributes": edge.attributes or {},
            })

        logger.info(f"共获取 {len(edges_data)} 条边")
        return edges_data
    
    def get_node_edges(self, node_uuid: str) -> List[Dict[str, Any]]:
        """
        获取指定节点的所有相关边（带重试机制）
        
        Args:
            node_uuid: 节点UUID
            
        Returns:
            边列表
        """
        try:
            # 使用重试机制调用Zep API
            edges = self._call_with_retry(
                func=lambda: self.client.graph.node.get_entity_edges(node_uuid=node_uuid),
                operation_name=f"获取节点边(node={node_uuid[:8]}...)"
            )
            
            edges_data = []
            for edge in edges:
                edges_data.append({
                    "uuid": getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', ''),
                    "name": edge.name or "",
                    "fact": edge.fact or "",
                    "source_node_uuid": edge.source_node_uuid,
                    "target_node_uuid": edge.target_node_uuid,
                    "attributes": edge.attributes or {},
                })
            
            return edges_data
        except Exception as e:
            logger.warning(f"获取节点 {node_uuid} 的边失败: {str(e)}")
            return []
    

    def _contains_forbidden_script(self, text: str, forbidden_scripts: Optional[List[str]] = None) -> bool:
        """
        Verifica se o texto contém caracteres de scripts proibidos (chinês, japonês, coreano).
        """
        if not forbidden_scripts or not text:
            return False
        script_ranges = {
            'zh': [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x3000, 0x303F)],
            'ja': [(0x3040, 0x309F), (0x30A0, 0x30FF)],
            'ko': [(0xAC00, 0xD7AF), (0x1100, 0x11FF)],
        }
        for script in forbidden_scripts:
            if script not in script_ranges:
                continue
            for start, end in script_ranges[script]:
                if any(start <= ord(c) <= end for c in text):
                    return True
        return False

    def _infer_entity_type_from_context(self, name: str, summary: str) -> str:
        """
        Infere o tipo de entidade a partir do nome e summary usando heurística.
        """
        text = (name + " " + summary).lower()
        heuristics = {
            "Person": ["professor", "doutor", "dr.", "médico", "engenheiro", "advogado",
                      "pesquisador", "cientista", "jornalista", "autor", "artista",
                      "presidente", "ministro", "deputado", "senador", "governador",
                      "ceo", "diretor", "fundador", "fundadora", "nascido", "nascida"],
            "Organization": ["empresa", "instituição", "universidade", "hospital",
                           "banco", "consultoria", "startup", "fundação", "instituto",
                           "associação", "cooperativa", "multinacional", "holding",
                           "s/a", "ltda", "mei", "ong"],
            "Event": ["eleição", "cop", "olimpíada", "conferência", "cimeira",
                     "guerra", "crise", "pandemia", "recessão", "boom", "colapso",
                     "inauguração", "lançamento", "merger", "aquisição", "ipo"],
            "Location": ["brasil", "estados unidos", "china", "europa", "áfrica",
                        "são paulo", "rio de janeiro", "brasília", "curitiba",
                        "continente", "país", "estado", "cidade", "região"],
            "Technology": ["algoritmo", "plataforma", "software", "hardware",
                          "inteligência artificial", "ia", "machine learning",
                          "blockchain", "app", "aplicativo", "sistema", "api",
                          "protocolo", "framework", "banco de dados"],
            "Product": ["medicamento", "vacina", "dispositivo", "equipamento",
                       "veículo", "smartphone", "computador", "drug", "remédio",
                       "suplemento", "aparelho", "instrumento", "ferramenta"],
            "Concept": ["teoria", "modelo", "hipótese", "paradigma", "framework",
                       "índice", "métrica", "indicador", "variável", "taxa",
                       "inflação", "pib", "desemprego", "juros", "dólar"],
        }
        scores = {}
        for entity_type, keywords in heuristics.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            if score > 0:
                scores[entity_type] = score
        if scores:
            return max(scores, key=scores.get)
        return "Entity"

    def filter_defined_entities(
        self, 
        graph_id: str,
        defined_entity_types: Optional[List[str]] = None,
        enrich_with_edges: bool = True,
        forbidden_scripts: Optional[List[str]] = None,
    ) -> FilteredEntities:
        """
        筛选出符合预定义实体类型的节点
        
        筛选逻辑：
        - 如果节点的Labels只有一个"Entity"，说明这个实体不符合我们预定义的类型，跳过
        - 如果节点的Labels包含除"Entity"和"Node"之外的标签，说明符合预定义类型，保留
        
        Args:
            graph_id: 图谱ID
            defined_entity_types: 预定义的实体类型列表（可选，如果提供则只保留这些类型）
            enrich_with_edges: 是否获取每个实体的相关边信息
            
        Returns:
            FilteredEntities: 过滤后的实体集合
        """
        logger.info(f"开始筛选图谱 {graph_id} 的实体...")
        
        # 获取所有节点
        all_nodes = self.get_all_nodes(graph_id)
        total_count = len(all_nodes)
        
        # 获取所有边（用于后续关联查找）
        all_edges = self.get_all_edges(graph_id) if enrich_with_edges else []
        
        # 构建节点UUID到节点数据的映射
        node_map = {n["uuid"]: n for n in all_nodes}
        
        # 筛选符合条件的实体
        filtered_entities = []
        entity_types_found = set()
        
        for node in all_nodes:
            labels = node.get("labels", [])
            
            # 筛选逻辑：Labels必须包含除"Entity"和"Node"之外的标签
            custom_labels = [l for l in labels if l not in ["Entity", "Node"]]
            
            # 验证语言：检查是否包含禁止脚本
            if forbidden_scripts and (self._contains_forbidden_script(node.get("name", ""), forbidden_scripts) or 
                                       self._contains_forbidden_script(node.get("summary", ""), forbidden_scripts)):
                logger.debug(f"跳过包含禁止脚本的实体: {node.get('name', '')[:50]}")
                continue

            if not custom_labels:
                # 只有默认标签，推断类型而不是跳过
                inferred_type = self._infer_entity_type_from_context(node.get("name", ""), node.get("summary", ""))
                custom_labels = [inferred_type]
                logger.debug(f"推断实体类型: '{node.get('name', '')[:50]}' -> {inferred_type}")
            
            # 如果指定了预定义类型，检查是否匹配
            if defined_entity_types:
                matching_labels = [l for l in custom_labels if l in defined_entity_types]
                if not matching_labels:
                    continue
                entity_type = matching_labels[0]
            else:
                entity_type = custom_labels[0]
            
            entity_types_found.add(entity_type)
            
            # 创建实体节点对象
            entity = EntityNode(
                uuid=node["uuid"],
                name=node["name"],
                labels=labels,
                summary=node["summary"],
                attributes=node["attributes"],
            )
            
            # 获取相关边和节点
            if enrich_with_edges:
                related_edges = []
                related_node_uuids = set()
                
                for edge in all_edges:
                    if edge["source_node_uuid"] == node["uuid"]:
                        related_edges.append({
                            "direction": "outgoing",
                            "edge_name": edge["name"],
                            "fact": edge["fact"],
                            "target_node_uuid": edge["target_node_uuid"],
                        })
                        related_node_uuids.add(edge["target_node_uuid"])
                    elif edge["target_node_uuid"] == node["uuid"]:
                        related_edges.append({
                            "direction": "incoming",
                            "edge_name": edge["name"],
                            "fact": edge["fact"],
                            "source_node_uuid": edge["source_node_uuid"],
                        })
                        related_node_uuids.add(edge["source_node_uuid"])
                
                entity.related_edges = related_edges
                
                # 获取关联节点的基本信息
                related_nodes = []
                for related_uuid in related_node_uuids:
                    if related_uuid in node_map:
                        related_node = node_map[related_uuid]
                        related_nodes.append({
                            "uuid": related_node["uuid"],
                            "name": related_node["name"],
                            "labels": related_node["labels"],
                            "summary": related_node.get("summary", ""),
                        })
                
                entity.related_nodes = related_nodes
            
            filtered_entities.append(entity)
        
        logger.info(f"筛选完成: 总节点 {total_count}, 符合条件 {len(filtered_entities)}, "
                   f"实体类型: {entity_types_found}")
        
        return FilteredEntities(
            entities=filtered_entities,
            entity_types=entity_types_found,
            total_count=total_count,
            filtered_count=len(filtered_entities),
        )
    
    def get_entity_with_context(
        self, 
        graph_id: str, 
        entity_uuid: str
    ) -> Optional[EntityNode]:
        """
        获取单个实体及其完整上下文（边和关联节点，带重试机制）
        
        Args:
            graph_id: 图谱ID
            entity_uuid: 实体UUID
            
        Returns:
            EntityNode或None
        """
        try:
            # 使用重试机制获取节点
            node = self._call_with_retry(
                func=lambda: self.client.graph.node.get(uuid_=entity_uuid),
                operation_name=f"获取节点详情(uuid={entity_uuid[:8]}...)"
            )
            
            if not node:
                return None
            
            # 获取节点的边
            edges = self.get_node_edges(entity_uuid)
            
            # 获取所有节点用于关联查找
            all_nodes = self.get_all_nodes(graph_id)
            node_map = {n["uuid"]: n for n in all_nodes}
            
            # 处理相关边和节点
            related_edges = []
            related_node_uuids = set()
            
            for edge in edges:
                if edge["source_node_uuid"] == entity_uuid:
                    related_edges.append({
                        "direction": "outgoing",
                        "edge_name": edge["name"],
                        "fact": edge["fact"],
                        "target_node_uuid": edge["target_node_uuid"],
                    })
                    related_node_uuids.add(edge["target_node_uuid"])
                else:
                    related_edges.append({
                        "direction": "incoming",
                        "edge_name": edge["name"],
                        "fact": edge["fact"],
                        "source_node_uuid": edge["source_node_uuid"],
                    })
                    related_node_uuids.add(edge["source_node_uuid"])
            
            # 获取关联节点信息
            related_nodes = []
            for related_uuid in related_node_uuids:
                if related_uuid in node_map:
                    related_node = node_map[related_uuid]
                    related_nodes.append({
                        "uuid": related_node["uuid"],
                        "name": related_node["name"],
                        "labels": related_node["labels"],
                        "summary": related_node.get("summary", ""),
                    })
            
            return EntityNode(
                uuid=getattr(node, 'uuid_', None) or getattr(node, 'uuid', ''),
                name=node.name or "",
                labels=node.labels or [],
                summary=node.summary or "",
                attributes=node.attributes or {},
                related_edges=related_edges,
                related_nodes=related_nodes,
            )
            
        except Exception as e:
            logger.error(f"获取实体 {entity_uuid} 失败: {str(e)}")
            return None
    
    def get_entities_by_type(
        self, 
        graph_id: str, 
        entity_type: str,
        enrich_with_edges: bool = True
    ) -> List[EntityNode]:
        """
        获取指定类型的所有实体
        
        Args:
            graph_id: 图谱ID
            entity_type: 实体类型（如 "Student", "PublicFigure" 等）
            enrich_with_edges: 是否获取相关边信息
            
        Returns:
            实体列表
        """
        result = self.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=[entity_type],
            enrich_with_edges=enrich_with_edges
        )
        return result.entities


