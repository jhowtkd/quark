"""
图谱构建服务
接口2：使用Zep API构建Standalone Graph
"""

import os
import re
import uuid
import time
import threading
import unicodedata
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from zep_cloud.client import Zep
from zep_cloud import EpisodeData, EntityEdgeSourceTarget

from ..config import Config
from ..models.task import TaskManager, TaskStatus
from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges
from .text_processor import TextProcessor
from ..utils.locale import t, get_locale, set_locale


RESERVED_ATTR_NAMES = {'uuid', 'name', 'group_id', 'name_embedding', 'summary', 'created_at'}


def _strip_accents(value: str) -> str:
    """Convert unicode text to a plain ASCII representation for schema names."""
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _split_identifier(value: Any) -> List[str]:
    """Split free-form, snake_case, or camelCase names into semantic tokens."""
    text = _strip_accents(str(value or "")).strip()
    if not text:
        return []

    text = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
    text = re.sub(r'[^0-9A-Za-z]+', ' ', text)
    return [part for part in text.split() if part]


def _dedupe_identifier(candidate: str, used: set[str], separator: str = "") -> str:
    """Ensure dynamically generated names are unique inside a single ontology payload."""
    if candidate not in used:
        used.add(candidate)
        return candidate

    index = 2
    while True:
        deduped = f"{candidate}{separator}{index}"
        if deduped not in used:
            used.add(deduped)
            return deduped
        index += 1


def _normalize_pascal_case(value: Any, fallback: str = "Entity") -> str:
    """Normalize a type name to PascalCase for Zep entity/class identifiers."""
    parts = _split_identifier(value)
    if not parts:
        return fallback
    return ''.join(part[:1].upper() + part[1:].lower() for part in parts)


def _normalize_snake_case(value: Any, fallback: str = "field_name") -> str:
    """Normalize an attribute name to snake_case."""
    parts = _split_identifier(value)
    if not parts:
        return fallback
    return '_'.join(part.lower() for part in parts)


def _normalize_screaming_snake_case(value: Any, fallback: str = "RELATED_TO") -> str:
    """Normalize an edge key to SCREAMING_SNAKE_CASE for Zep edge identifiers."""
    return _normalize_snake_case(value, fallback.lower()).upper()


def _prepare_ontology_for_zep(ontology: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize ontology names for Zep and surface compatibility guardrails."""
    guardrails = {
        "can_build": True,
        "errors": [],
        "warnings": [],
    }

    entity_ref_map: Dict[str, str] = {}
    normalized_entities: List[Dict[str, Any]] = []
    normalized_edges: List[Dict[str, Any]] = []
    used_entity_names: set[str] = set()
    used_edge_names: set[str] = set()
    used_edge_class_names: set[str] = set()

    for index, entity_def in enumerate(ontology.get("entity_types", []), start=1):
        raw_name = entity_def.get("name")
        parts = _split_identifier(raw_name)
        if not parts:
            guardrails["errors"].append(f"Entity type #{index} has an empty or invalid name.")
            continue

        base_name = _normalize_pascal_case(raw_name, "Entity")
        normalized_name = _dedupe_identifier(base_name, used_entity_names)
        if raw_name != normalized_name:
            guardrails["warnings"].append(
                f"Entity '{raw_name}' will be sent to Zep as '{normalized_name}'."
            )
        if normalized_name != base_name:
            guardrails["warnings"].append(
                f"Entity '{raw_name}' collided after normalization and was deduped to '{normalized_name}'."
            )

        normalized_attributes = []
        used_attr_names: set[str] = set()
        for attr_index, attr_def in enumerate(entity_def.get("attributes", []), start=1):
            raw_attr_name = attr_def.get("name")
            attr_parts = _split_identifier(raw_attr_name)
            if not attr_parts:
                guardrails["errors"].append(
                    f"Attribute #{attr_index} on entity '{raw_name}' has an empty or invalid name."
                )
                continue

            normalized_attr = _normalize_snake_case(raw_attr_name, "field_name")
            if normalized_attr in RESERVED_ATTR_NAMES:
                normalized_attr = f"entity_{normalized_attr}"
            normalized_attr = _dedupe_identifier(normalized_attr, used_attr_names, separator="_")
            if raw_attr_name != normalized_attr:
                guardrails["warnings"].append(
                    f"Attribute '{raw_attr_name}' on entity '{raw_name}' will be sent as '{normalized_attr}'."
                )

            normalized_attributes.append({
                **attr_def,
                "name": normalized_attr,
            })

        entity_ref_map[_normalize_snake_case(raw_name, "entity")] = normalized_name
        entity_ref_map[_normalize_snake_case(normalized_name, "entity")] = normalized_name
        normalized_entities.append({
            **entity_def,
            "name": normalized_name,
            "attributes": normalized_attributes,
        })

    for index, edge_def in enumerate(ontology.get("edge_types", []), start=1):
        raw_name = edge_def.get("name")
        parts = _split_identifier(raw_name)
        if not parts:
            guardrails["errors"].append(f"Edge type #{index} has an empty or invalid name.")
            continue

        base_edge_name = _normalize_screaming_snake_case(raw_name, "RELATED_TO")
        normalized_edge_name = _dedupe_identifier(base_edge_name, used_edge_names, separator="_")
        if raw_name != normalized_edge_name:
            guardrails["warnings"].append(
                f"Edge '{raw_name}' will be sent to Zep as '{normalized_edge_name}'."
            )
        if normalized_edge_name != base_edge_name:
            guardrails["warnings"].append(
                f"Edge '{raw_name}' collided after normalization and was deduped to '{normalized_edge_name}'."
            )

        normalized_class_name = _dedupe_identifier(
            _normalize_pascal_case(raw_name, "RelatedTo"),
            used_edge_class_names,
        )

        normalized_attributes = []
        used_attr_names: set[str] = set()
        for attr_index, attr_def in enumerate(edge_def.get("attributes", []), start=1):
            raw_attr_name = attr_def.get("name")
            attr_parts = _split_identifier(raw_attr_name)
            if not attr_parts:
                guardrails["errors"].append(
                    f"Attribute #{attr_index} on edge '{raw_name}' has an empty or invalid name."
                )
                continue

            normalized_attr = _normalize_snake_case(raw_attr_name, "field_name")
            if normalized_attr in RESERVED_ATTR_NAMES:
                normalized_attr = f"entity_{normalized_attr}"
            normalized_attr = _dedupe_identifier(normalized_attr, used_attr_names, separator="_")
            if raw_attr_name != normalized_attr:
                guardrails["warnings"].append(
                    f"Attribute '{raw_attr_name}' on edge '{raw_name}' will be sent as '{normalized_attr}'."
                )

            normalized_attributes.append({
                **attr_def,
                "name": normalized_attr,
            })

        source_targets = []
        for st_index, st in enumerate(edge_def.get("source_targets", []), start=1):
            raw_source = st.get("source")
            raw_target = st.get("target")

            if not _split_identifier(raw_source):
                guardrails["errors"].append(
                    f"Source #{st_index} on edge '{raw_name}' has an empty or invalid name."
                )
                continue
            if not _split_identifier(raw_target):
                guardrails["errors"].append(
                    f"Target #{st_index} on edge '{raw_name}' has an empty or invalid name."
                )
                continue

            normalized_source = entity_ref_map.get(
                _normalize_snake_case(raw_source, "entity"),
                _normalize_pascal_case(raw_source, "Entity"),
            )
            normalized_target = entity_ref_map.get(
                _normalize_snake_case(raw_target, "entity"),
                _normalize_pascal_case(raw_target, "Entity"),
            )

            if raw_source != normalized_source:
                guardrails["warnings"].append(
                    f"Edge '{raw_name}' source '{raw_source}' will be sent as '{normalized_source}'."
                )
            if raw_target != normalized_target:
                guardrails["warnings"].append(
                    f"Edge '{raw_name}' target '{raw_target}' will be sent as '{normalized_target}'."
                )

            source_targets.append({
                "source": normalized_source,
                "target": normalized_target,
            })

        normalized_edges.append({
            **edge_def,
            "name": normalized_edge_name,
            "class_name": normalized_class_name,
            "attributes": normalized_attributes,
            "source_targets": source_targets,
        })

    guardrails["can_build"] = not guardrails["errors"]
    return {
        "guardrails": guardrails,
        "entity_types": normalized_entities,
        "edge_types": normalized_edges,
    }


@dataclass
class GraphInfo:
    """图谱信息"""
    graph_id: str
    node_count: int
    edge_count: int
    entity_types: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "entity_types": self.entity_types,
        }


class GraphBuilderService:
    """
    图谱构建服务
    负责调用Zep API构建知识图谱
    """
    
    def __init__(self, api_key: Optional[str] = None, observability_client: Any = None):
        self.api_key = api_key or Config.ZEP_API_KEY
        if not self.api_key:
            raise ValueError("ZEP_API_KEY 未配置")

        self.client = Zep(api_key=self.api_key)
        self.task_manager = TaskManager()
        self.observability_client = observability_client
    
    def incremental_build_graph_async(
        self,
        graph_id: str,
        chunks: List[str],
        batch_size: int = 3,
        observation: Any = None,
    ) -> str:
        """
        异步增量构建图谱 — 向已有图谱添加变更的 chunks。

        Args:
            graph_id: 已有图谱ID
            chunks: 变更的文本块列表
            batch_size: 每批发送的块数量
            observation: Observability span for tracing

        Returns:
            任务ID
        """
        span = None
        if observation is not None:
            span = observation.start_span(
                name="graph_builder.incremental_build_graph_async",
                metadata={
                    "graph_id": graph_id,
                    "changed_chunks": len(chunks),
                },
            )
            span.update(input={"graph_id": graph_id, "changed_chunks": len(chunks)})

        task_id = self.task_manager.create_task(
            task_type="graph_build_incremental",
            metadata={
                "graph_id": graph_id,
                "changed_chunks": len(chunks),
            }
        )

        current_locale = get_locale()

        thread = threading.Thread(
            target=self._incremental_build_graph_worker,
            args=(task_id, graph_id, chunks, batch_size, current_locale),
        )
        thread.daemon = True
        thread.start()

        if span is not None:
            span.update(output={"task_id": task_id})
            span.end()

        return task_id

    def _incremental_build_graph_worker(
        self,
        task_id: str,
        graph_id: str,
        chunks: List[str],
        batch_size: int,
        locale: str = 'zh'
    ):
        """增量图谱构建工作线程"""
        set_locale(locale)
        try:
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                progress=10,
                message=t('progress.startIncrementalBuild')
            )

            total_chunks = len(chunks)
            self.task_manager.update_task(
                task_id,
                progress=20,
                message=t('progress.sendingIncrementalChunks', count=total_chunks)
            )

            episode_uuids = self.add_text_batches(
                graph_id, chunks, batch_size,
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=20 + int(prog * 0.5),  # 20-70%
                    message=msg
                )
            )

            self.task_manager.update_task(
                task_id,
                progress=70,
                message=t('progress.waitingZepProcess')
            )

            self._wait_for_episodes(
                episode_uuids,
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=70 + int(prog * 0.25),  # 70-95%
                    message=msg
                )
            )

            self.task_manager.update_task(
                task_id,
                progress=95,
                message=t('progress.fetchingGraphInfo')
            )

            graph_info = self._get_graph_info(graph_id)

            self.task_manager.complete_task(task_id, {
                "graph_id": graph_id,
                "graph_info": graph_info.to_dict(),
                "chunks_processed": total_chunks,
                "incremental": True,
            })

        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.task_manager.fail_task(task_id, error_msg)

    def build_graph_async(
        self,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str = "FUTUR.IA Graph",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 3,
        observation: Any = None,
    ) -> str:
        """
        异步构建图谱

        Args:
            text: 输入文本
            ontology: 本体定义（来自接口1的输出）
            graph_name: 图谱名称
            chunk_size: 文本块大小
            chunk_overlap: 块重叠大小
            batch_size: 每批发送的块数量
            observation: Observability span for tracing

        Returns:
            任务ID
        """
        span = None
        if observation is not None:
            span = observation.start_span(
                name="graph_builder.build_graph_async",
                metadata={
                    "graph_name": graph_name,
                    "chunk_size": chunk_size,
                    "text_length": len(text),
                    "ontology_types": list(ontology.keys()) if ontology else [],
                },
            )
            span.update(input={"graph_name": graph_name, "text_length": len(text)})

        # 创建任务
        task_id = self.task_manager.create_task(
            task_type="graph_build",
            metadata={
                "graph_name": graph_name,
                "chunk_size": chunk_size,
                "text_length": len(text),
            }
        )

        # Capture locale before spawning background thread
        current_locale = get_locale()

        # 在后台线程中执行构建
        thread = threading.Thread(
            target=self._build_graph_worker,
            args=(task_id, text, ontology, graph_name, chunk_size, chunk_overlap, batch_size, current_locale),
        )
        thread.daemon = True
        thread.start()

        if span is not None:
            span.update(output={"task_id": task_id})
            span.end()

        return task_id
    
    def _build_graph_worker(
        self,
        task_id: str,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        batch_size: int,
        locale: str = 'zh'
    ):
        """图谱构建工作线程"""
        set_locale(locale)
        try:
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                progress=5,
                message=t('progress.startBuildingGraph')
            )
            
            # 1. 创建图谱
            graph_id = self.create_graph(graph_name)
            self.task_manager.update_task(
                task_id,
                progress=10,
                message=t('progress.graphCreated', graphId=graph_id)
            )
            
            # 2. 设置本体
            self.set_ontology(graph_id, ontology)
            self.task_manager.update_task(
                task_id,
                progress=15,
                message=t('progress.ontologySet')
            )
            
            # 3. 文本分块
            chunks = TextProcessor.split_text(text, chunk_size, chunk_overlap)
            total_chunks = len(chunks)
            self.task_manager.update_task(
                task_id,
                progress=20,
                message=t('progress.textSplit', count=total_chunks)
            )
            
            # 3b. 去重
            chunks = TextProcessor.deduplicate_chunks(chunks)
            deduped_count = len(chunks)
            if deduped_count < total_chunks:
                self.task_manager.update_task(
                    task_id,
                    progress=22,
                    message=t('progress.deduplicated', before=total_chunks, after=deduped_count)
                )
                total_chunks = deduped_count
            
            # 4. 分批发送数据
            episode_uuids = self.add_text_batches(
                graph_id, chunks, batch_size,
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=20 + int(prog * 0.4),  # 20-60%
                    message=msg
                )
            )
            
            # 5. 等待Zep处理完成
            self.task_manager.update_task(
                task_id,
                progress=60,
                message=t('progress.waitingZepProcess')
            )
            
            self._wait_for_episodes(
                episode_uuids,
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=60 + int(prog * 0.3),  # 60-90%
                    message=msg
                )
            )
            
            # 6. 获取图谱信息
            self.task_manager.update_task(
                task_id,
                progress=90,
                message=t('progress.fetchingGraphInfo')
            )
            
            graph_info = self._get_graph_info(graph_id)
            
            # 完成
            self.task_manager.complete_task(task_id, {
                "graph_id": graph_id,
                "graph_info": graph_info.to_dict(),
                "chunks_processed": total_chunks,
            })
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.task_manager.fail_task(task_id, error_msg)
    
    def create_graph(self, name: str) -> str:
        """Create Zep graph (public method)"""
        graph_id = f"futuria_{uuid.uuid4().hex[:16]}"
        
        self.client.graph.create(
            graph_id=graph_id,
            name=name,
            description="FUTUR.IA Social Simulation Graph"
        )
        
        return graph_id
    
    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """设置图谱本体（公开方法）"""
        import warnings
        from typing import Optional
        from pydantic import Field
        from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel
        
        # 抑制 Pydantic v2 关于 Field(default=None) 的警告
        # 这是 Zep SDK 要求的用法，警告来自动态类创建，可以安全忽略
        warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')
        
        prepared_ontology = _prepare_ontology_for_zep(ontology)
        guardrails = prepared_ontology["guardrails"]
        if not guardrails["can_build"]:
            raise ValueError("Ontology is incompatible with Zep: " + "; ".join(guardrails["errors"]))
        
        # 动态创建实体类型
        entity_types = {}
        for entity_def in prepared_ontology.get("entity_types", []):
            name = entity_def["name"]
            description = entity_def.get("description", f"A {name} entity.")
            
            # 创建属性字典和类型注解（Pydantic v2 需要）
            attrs = {"__doc__": description}
            annotations = {}
            
            for attr_def in entity_def.get("attributes", []):
                attr_name = attr_def["name"]
                attr_desc = attr_def.get("description", attr_name)
                # Zep API 需要 Field 的 description，这是必需的
                attrs[attr_name] = Field(description=attr_desc, default=None)
                annotations[attr_name] = Optional[EntityText]  # 类型注解
            
            attrs["__annotations__"] = annotations
            
            # 动态创建类
            entity_class = type(name, (EntityModel,), attrs)
            entity_class.__doc__ = description
            entity_types[name] = entity_class
        
        # 动态创建边类型
        edge_definitions = {}
        for edge_def in prepared_ontology.get("edge_types", []):
            name = edge_def["name"]
            description = edge_def.get("description", f"A {name} relationship.")
            
            # 创建属性字典和类型注解
            attrs = {"__doc__": description}
            annotations = {}
            
            for attr_def in edge_def.get("attributes", []):
                attr_name = attr_def["name"]
                attr_desc = attr_def.get("description", attr_name)
                # Zep API 需要 Field 的 description，这是必需的
                attrs[attr_name] = Field(description=attr_desc, default=None)
                annotations[attr_name] = Optional[str]  # 边属性用str类型
            
            attrs["__annotations__"] = annotations
            
            # 动态创建类
            class_name = edge_def["class_name"]
            edge_class = type(class_name, (EdgeModel,), attrs)
            edge_class.__doc__ = description
            
            # 构建source_targets
            source_targets = []
            for st in edge_def.get("source_targets", []):
                source_targets.append(
                    EntityEdgeSourceTarget(
                        source=st.get("source", "Entity"),
                        target=st.get("target", "Entity")
                    )
                )
            
            if source_targets:
                edge_definitions[name] = (edge_class, source_targets)
        
        # 调用Zep API设置本体
        if entity_types or edge_definitions:
            self.client.graph.set_ontology(
                graph_ids=[graph_id],
                entities=entity_types if entity_types else None,
                edges=edge_definitions if edge_definitions else None,
            )

    @staticmethod
    def analyze_ontology_guardrails(ontology: Dict[str, Any]) -> Dict[str, Any]:
        """Expose the ontology compatibility guardrails without mutating persisted data."""
        return _prepare_ontology_for_zep(ontology)["guardrails"]
    
    def add_text_batches(
        self,
        graph_id: str,
        chunks: List[str],
        batch_size: int = 3,
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """分批添加文本到图谱，返回所有 episode 的 uuid 列表"""
        episode_uuids = []
        total_chunks = len(chunks)
        
        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size
            
            if progress_callback:
                progress = (i + len(batch_chunks)) / total_chunks
                progress_callback(
                    t('progress.sendingBatch', current=batch_num, total=total_batches, chunks=len(batch_chunks)),
                    progress
                )
            
            # 构建episode数据
            episodes = [
                EpisodeData(data=chunk, type="text")
                for chunk in batch_chunks
            ]
            
            # 发送到Zep
            try:
                batch_result = self.client.graph.add_batch(
                    graph_id=graph_id,
                    episodes=episodes
                )
                
                # 收集返回的 episode uuid
                if batch_result and isinstance(batch_result, list):
                    for ep in batch_result:
                        ep_uuid = getattr(ep, 'uuid_', None) or getattr(ep, 'uuid', None)
                        if ep_uuid:
                            episode_uuids.append(ep_uuid)
                
                # 避免请求过快
                time.sleep(1)
                
            except Exception as e:
                if progress_callback:
                    progress_callback(t('progress.batchFailed', batch=batch_num, error=str(e)), 0)
                raise
        
        return episode_uuids
    
    def _wait_for_episodes(
        self,
        episode_uuids: List[str],
        progress_callback: Optional[Callable] = None,
        timeout: int = 600
    ):
        """等待所有 episode 处理完成（通过查询每个 episode 的 processed 状态）"""
        if not episode_uuids:
            if progress_callback:
                progress_callback(t('progress.noEpisodesWait'), 1.0)
            return
        
        start_time = time.time()
        pending_episodes = set(episode_uuids)
        completed_count = 0
        total_episodes = len(episode_uuids)
        
        if progress_callback:
            progress_callback(t('progress.waitingEpisodes', count=total_episodes), 0)
        
        while pending_episodes:
            if time.time() - start_time > timeout:
                if progress_callback:
                    progress_callback(
                        t('progress.episodesTimeout', completed=completed_count, total=total_episodes),
                        completed_count / total_episodes
                    )
                break
            
            # 检查每个 episode 的处理状态
            for ep_uuid in list(pending_episodes):
                try:
                    episode = self.client.graph.episode.get(uuid_=ep_uuid)
                    is_processed = getattr(episode, 'processed', False)
                    
                    if is_processed:
                        pending_episodes.remove(ep_uuid)
                        completed_count += 1
                        
                except Exception as e:
                    # 忽略单个查询错误，继续
                    pass
            
            elapsed = int(time.time() - start_time)
            if progress_callback:
                progress_callback(
                    t('progress.zepProcessing', completed=completed_count, total=total_episodes, pending=len(pending_episodes), elapsed=elapsed),
                    completed_count / total_episodes if total_episodes > 0 else 0
                )
            
            if pending_episodes:
                time.sleep(3)  # 每3秒检查一次
        
        if progress_callback:
            progress_callback(t('progress.processingComplete', completed=completed_count, total=total_episodes), 1.0)
    
    def _get_graph_info(self, graph_id: str) -> GraphInfo:
        """获取图谱信息"""
        # 获取节点（分页）
        nodes = fetch_all_nodes(self.client, graph_id)

        # 获取边（分页）
        edges = fetch_all_edges(self.client, graph_id)

        # 统计实体类型
        entity_types = set()
        for node in nodes:
            if node.labels:
                for label in node.labels:
                    if label not in ["Entity", "Node"]:
                        entity_types.add(label)

        return GraphInfo(
            graph_id=graph_id,
            node_count=len(nodes),
            edge_count=len(edges),
            entity_types=list(entity_types)
        )
    
    def _generate_edge_fact(self, source_name: str, target_name: str, relation_name: str) -> str:
        """
        Gera uma descricao factual para uma edge quando o campo 'fact' esta vazio.
        
        Primeiro tenta uma heuristica simples. Se o resultado for muito generico,
        usa o LLM para gerar uma frase mais especifica.
        
        Args:
            source_name: Nome do no origem
            target_name: Nome do no destino
            relation_name: Nome da relacao
            
        Returns:
            Frase factual descrevendo a relacao
        """
        if not source_name or not target_name or not relation_name:
            return ""
        
        # Heuristica simples: transformar relacao em frase factual
        relation_lower = relation_name.lower().replace("_", " ")
        heuristic_fact = f"{source_name} {relation_lower} {target_name}."
        
        # Se a heuristica parece razoavel (nao muito generica), retorna ela
        if len(heuristic_fact) > 20 and relation_lower not in ("related to", "connected to", "linked to"):
            return heuristic_fact.capitalize()
        
        # Caso contrario, tenta usar LLM para gerar um fato melhor
        try:
            from ..utils.llm_client import LLMClient
            llm = LLMClient()
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Voce e um assistente que gera frases factuais curtas e claras. "
                        "Dado uma entidade origem, uma entidade destino e uma relacao, "
                        "gere UMA frase factual em portugues descrevendo essa relacao. "
                        "Maximo 25 palavras. Sem adjetivos poeticos. Apenas a frase, nada mais."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Origem: {source_name}\nDestino: {target_name}\nRelacao: {relation_name}\n\nGere a frase factual:",
                },
            ]
            response = llm.chat(messages, temperature=0.3, max_tokens=100)
            if response:
                fact = response.strip().strip('"').strip("'")
                if len(fact) > 10:
                    return fact
        except Exception as e:
            logger.warning(f"[GraphBuilder] LLM fact generation failed: {e}")
        
        # Fallback final: retorna a heuristica mesmo que generica
        return heuristic_fact.capitalize()

    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """
        获取完整图谱数据（包含详细信息）
        
        Args:
            graph_id: 图谱ID
            
        Returns:
            包含nodes和edges的字典，包括时间信息、属性等详细数据
        """
        nodes = fetch_all_nodes(self.client, graph_id)
        edges = fetch_all_edges(self.client, graph_id)

        # 创建节点映射用于获取节点名称
        node_map = {}
        for node in nodes:
            node_map[node.uuid_] = node.name or ""
        
        nodes_data = []
        for node in nodes:
            # 获取创建时间
            created_at = getattr(node, 'created_at', None)
            if created_at:
                created_at = str(created_at)
            
            nodes_data.append({
                "uuid": node.uuid_,
                "name": node.name,
                "labels": node.labels or [],
                "summary": node.summary or "",
                "attributes": node.attributes or {},
                "created_at": created_at,
            })
        
        edges_data = []
        for edge in edges:
            # 获取时间信息
            created_at = getattr(edge, 'created_at', None)
            valid_at = getattr(edge, 'valid_at', None)
            invalid_at = getattr(edge, 'invalid_at', None)
            expired_at = getattr(edge, 'expired_at', None)
            
            # 获取 episodes
            episodes = getattr(edge, 'episodes', None) or getattr(edge, 'episode_ids', None)
            if episodes and not isinstance(episodes, list):
                episodes = [str(episodes)]
            elif episodes:
                episodes = [str(e) for e in episodes]
            
            # 获取 fact_type
            fact_type = getattr(edge, 'fact_type', None) or edge.name or ""
            
            # Garantir que 'fact' esteja preenchido
            source_name = node_map.get(edge.source_node_uuid, "")
            target_name = node_map.get(edge.target_node_uuid, "")
            fact = edge.fact or ""
            if not fact:
                fact = self._generate_edge_fact(source_name, target_name, edge.name or "")
            
            edges_data.append({
                "uuid": edge.uuid_,
                "name": edge.name or "",
                "fact": fact,
                "fact_type": fact_type,
                "source_node_uuid": edge.source_node_uuid,
                "target_node_uuid": edge.target_node_uuid,
                "source_node_name": source_name,
                "target_node_name": target_name,
                "attributes": edge.attributes or {},
                "created_at": str(created_at) if created_at else None,
                "valid_at": str(valid_at) if valid_at else None,
                "invalid_at": str(invalid_at) if invalid_at else None,
                "expired_at": str(expired_at) if expired_at else None,
                "episodes": episodes or [],
            })
        
        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }
    
    def delete_graph(self, graph_id: str):
        """删除图谱"""
        self.client.graph.delete(graph_id=graph_id)
