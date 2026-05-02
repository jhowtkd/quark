"""
OASIS模拟管理器
管理Twitter和Reddit双平台并行模拟
使用预设脚本 + LLM智能生成配置参数
"""

import os
import json
import shutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import Counter

from ..config import Config
from ..utils.logger import get_logger
from .zep_entity_reader import ZepEntityReader, FilteredEntities
from .oasis_profile_generator import OasisProfileGenerator, OasisAgentProfile
from .simulation_config_generator import SimulationConfigGenerator, SimulationParameters
from ..utils.locale import t

logger = get_logger('futuria.simulation')


class SimulationStatus(str, Enum):
    """模拟状态"""
    CREATED = "created"
    PREPARING = "preparing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"      # 模拟被手动停止
    COMPLETED = "completed"  # 模拟自然完成
    FAILED = "failed"


class PlatformType(str, Enum):
    """平台类型"""
    TWITTER = "twitter"
    REDDIT = "reddit"


@dataclass
class SimulationState:
    """模拟状态"""
    simulation_id: str
    project_id: str
    graph_id: str
    
    # 平台启用状态
    enable_twitter: bool = True
    enable_reddit: bool = True
    
    # 状态
    status: SimulationStatus = SimulationStatus.CREATED
    
    # 准备阶段数据
    entities_count: int = 0
    profiles_count: int = 0
    entity_types: List[str] = field(default_factory=list)
    
    # 配置生成信息
    config_generated: bool = False
    config_reasoning: str = ""
    
    # 运行时数据
    current_round: int = 0
    twitter_status: str = "not_started"
    reddit_status: str = "not_started"
    degraded_mode: bool = False
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 错误信息
    error: Optional[str] = None
    
    # 用户资料档案 (perfil de analise, opcional)
    profile: str = "generico"
    
    # 实体类型质量指标
    unknown_entity_count: int = 0
    resolved_entity_count: int = 0
    entity_type_distribution: Dict[str, int] = field(default_factory=dict)
    quality_flags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """完整状态字典（内部使用）"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "enable_twitter": self.enable_twitter,
            "enable_reddit": self.enable_reddit,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "config_generated": self.config_generated,
            "config_reasoning": self.config_reasoning,
            "current_round": self.current_round,
            "twitter_status": self.twitter_status,
            "reddit_status": self.reddit_status,
            "degraded_mode": self.degraded_mode,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
            "profile": self.profile,
            "unknown_entity_count": self.unknown_entity_count,
            "resolved_entity_count": self.resolved_entity_count,
            "entity_type_distribution": self.entity_type_distribution,
            "quality_flags": self.quality_flags,
        }
    
    def to_simple_dict(self) -> Dict[str, Any]:
        """简化状态字典（API返回使用）"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "config_generated": self.config_generated,
            "error": self.error,
            "profile": self.profile,
            "unknown_entity_count": self.unknown_entity_count,
            "resolved_entity_count": self.resolved_entity_count,
            "quality_flags": self.quality_flags,
        }


class SimulationManager:
    """
    模拟管理器
    
    核心功能：
    1. 从Zep图谱读取实体并过滤
    2. 生成OASIS Agent Profile
    3. 使用LLM智能生成模拟配置参数
    4. 准备预设脚本所需的所有文件
    """
    
    # 模拟数据存储目录 — 使用 Config 中的集中配置，避免相对路径脆弱性
    SIMULATION_DATA_DIR = Config.OASIS_SIMULATION_DATA_DIR
    
    def __init__(self, observability_client: Any = None):
        # 确保目录存在
        os.makedirs(self.SIMULATION_DATA_DIR, exist_ok=True)

        # 内存中的模拟状态缓存
        self._simulations: Dict[str, SimulationState] = {}
        self.observability_client = observability_client
    
    def _get_simulation_dir(self, simulation_id: str) -> str:
        """获取模拟数据目录"""
        sim_dir = os.path.join(self.SIMULATION_DATA_DIR, simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        return sim_dir
    
    def _save_simulation_state(self, state: SimulationState, observation: Any = None):
        """保存模拟状态到文件"""
        sim_dir = self._get_simulation_dir(state.simulation_id)
        state_file = os.path.join(sim_dir, "state.json")

        state.updated_at = datetime.now().isoformat()

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)

        self._simulations[state.simulation_id] = state

        if observation is not None:
            observation.update(
                output={
                    "status": state.status.value,
                    "simulation_id": state.simulation_id,
                }
            )
    
    def _load_simulation_state(self, simulation_id: str) -> Optional[SimulationState]:
        """从文件加载模拟状态"""
        if simulation_id in self._simulations:
            return self._simulations[simulation_id]
        
        sim_dir = self._get_simulation_dir(simulation_id)
        state_file = os.path.join(sim_dir, "state.json")
        
        if not os.path.exists(state_file):
            return None
        
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        normalized_reasoning = SimulationConfigGenerator()._normalize_reasoning_text(
            data.get("config_reasoning", ""),
            "Configuração ajustada ao público e ao ritmo esperado da discussão.",
        )

        state = SimulationState(
            simulation_id=simulation_id,
            project_id=data.get("project_id", ""),
            graph_id=data.get("graph_id", ""),
            enable_twitter=data.get("enable_twitter", True),
            enable_reddit=data.get("enable_reddit", True),
            status=SimulationStatus(data.get("status", "created")),
            entities_count=data.get("entities_count", 0),
            profiles_count=data.get("profiles_count", 0),
            entity_types=data.get("entity_types", []),
            config_generated=data.get("config_generated", False),
            config_reasoning=normalized_reasoning,
            current_round=data.get("current_round", 0),
            twitter_status=data.get("twitter_status", "not_started"),
            reddit_status=data.get("reddit_status", "not_started"),
            degraded_mode=data.get("degraded_mode", False),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            error=data.get("error"),
            profile=data.get("profile", "generico"),
            unknown_entity_count=data.get("unknown_entity_count", 0),
            resolved_entity_count=data.get("resolved_entity_count", 0),
            entity_type_distribution=data.get("entity_type_distribution", {}),
            quality_flags=data.get("quality_flags", []),
        )
        
        self._simulations[simulation_id] = state
        return state
    
    def create_simulation(
        self,
        project_id: str,
        graph_id: str,
        enable_twitter: bool = True,
        enable_reddit: bool = True,
        profile: str = "generico",
        observation: Any = None,
    ) -> SimulationState:
        """
        创建新的模拟

        Args:
            project_id: 项目ID
            graph_id: Zep图谱ID
            enable_twitter: 是否启用Twitter模拟
            enable_reddit: 是否启用Reddit模拟
            profile: 用户资料档案 (marketing, direito, economia, saude, generico)
            observation: Observability span for tracing

        Returns:
            SimulationState
        """
        import uuid
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"

        span = None
        if observation is not None:
            span = observation.start_span(
                name="simulation_manager.create_simulation",
                metadata={
                    "simulation_id": simulation_id,
                    "project_id": project_id,
                    "graph_id": graph_id,
                    "enable_twitter": enable_twitter,
                    "enable_reddit": enable_reddit,
                    "profile": profile,
                },
            )
            span.update(input={"project_id": project_id, "graph_id": graph_id})

        try:
            state = SimulationState(
                simulation_id=simulation_id,
                project_id=project_id,
                graph_id=graph_id,
                enable_twitter=enable_twitter,
                enable_reddit=enable_reddit,
                status=SimulationStatus.CREATED,
                profile=profile,
            )

            self._save_simulation_state(state)
            logger.info(f"创建模拟: {simulation_id}, project={project_id}, graph={graph_id}, profile={profile}")

            if span is not None:
                span.update(output={"status": state.status.value})
                span.end()

            return state
        except Exception as e:
            if span is not None:
                span.update(status_message=str(e))
                span.end()
            raise
    
    def prepare_simulation(
        self,
        simulation_id: str,
        simulation_requirement: str,
        document_text: str,
        defined_entity_types: Optional[List[str]] = None,
        use_llm_for_profiles: bool = True,
        progress_callback: Optional[callable] = None,
        parallel_profile_count: int = 3,
        observation: Any = None,
    ) -> SimulationState:
        """
        准备模拟环境（全程自动化）— delegates to OasisPreparationService.
        """
        from .oasis_preparation_service import OasisPreparationService

        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"模拟不存在: {simulation_id}")

        try:
            state.status = SimulationStatus.PREPARING
            self._save_simulation_state(state)

            from .graph_backend import GraphBackendFactory
            graph_backend = GraphBackendFactory.create()
            state.degraded_mode = graph_backend.is_degraded()

            sim_dir = self._get_simulation_dir(simulation_id)
            prep_service = OasisPreparationService()
            state = prep_service.prepare(
                simulation_id=simulation_id,
                simulation_requirement=simulation_requirement,
                document_text=document_text,
                state=state,
                sim_dir=sim_dir,
                defined_entity_types=defined_entity_types,
                use_llm_for_profiles=use_llm_for_profiles,
                progress_callback=progress_callback,
                parallel_profile_count=parallel_profile_count,
            )

            self._save_simulation_state(state)
            logger.info(f"模拟准备完成: {simulation_id}, "
                       f"entities={state.entities_count}, profiles={state.profiles_count}")
            return state

        except Exception as e:
            logger.exception(f"Simulation manager error: {simulation_id}, error={e}")
            state.status = SimulationStatus.FAILED
            state.error = str(e)
            self._save_simulation_state(state)
            raise
    
    def get_simulation(self, simulation_id: str) -> Optional[SimulationState]:
        """获取模拟状态"""
        return self._load_simulation_state(simulation_id)
    
    def list_simulations(self, project_id: Optional[str] = None) -> List[SimulationState]:
        """列出所有模拟"""
        simulations = []
        
        if os.path.exists(self.SIMULATION_DATA_DIR):
            for sim_id in os.listdir(self.SIMULATION_DATA_DIR):
                # 跳过隐藏文件（如 .DS_Store）和非目录文件
                sim_path = os.path.join(self.SIMULATION_DATA_DIR, sim_id)
                if sim_id.startswith('.') or not os.path.isdir(sim_path):
                    continue
                
                state = self._load_simulation_state(sim_id)
                if state:
                    if project_id is None or state.project_id == project_id:
                        simulations.append(state)
        
        return simulations

    def clear_project_graph_references(self, project_id: str) -> int:
        """清理指定项目下所有模拟的 graph_id 引用。"""
        cleared = 0

        for state in self.list_simulations(project_id=project_id):
            if state.graph_id:
                state.graph_id = ""
                self._save_simulation_state(state)
                cleared += 1

        return cleared
    
    def get_profiles(self, simulation_id: str, platform: str = "reddit") -> List[Dict[str, Any]]:
        """获取模拟的Agent Profile"""
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"模拟不存在: {simulation_id}")
        
        sim_dir = self._get_simulation_dir(simulation_id)
        profile_path = os.path.join(sim_dir, f"{platform}_profiles.json")
        
        if not os.path.exists(profile_path):
            return []
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_simulation_config(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """获取模拟配置"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        config["generation_reasoning"] = SimulationConfigGenerator()._normalize_reasoning_text(
            config.get("generation_reasoning", ""),
            "Configuração ajustada ao público e ao ritmo esperado da discussão.",
        )
        return config
    
    def get_run_instructions(self, simulation_id: str) -> Dict[str, str]:
        """获取运行说明"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts'))
        
        return {
            "simulation_dir": sim_dir,
            "scripts_dir": scripts_dir,
            "config_file": config_path,
            "commands": {
                "twitter": f"python {scripts_dir}/run_twitter_simulation.py --config {config_path}",
                "reddit": f"python {scripts_dir}/run_reddit_simulation.py --config {config_path}",
                "parallel": f"python {scripts_dir}/run_parallel_simulation.py --config {config_path}",
            },
            "instructions": (
                f"1. Activate environment: conda activate futuria\n"
                f"2. Run simulation (scripts at {scripts_dir}):\n"
                f"   - Run Twitter only: python {scripts_dir}/run_twitter_simulation.py --config {config_path}\n"
                f"   - Run Reddit only: python {scripts_dir}/run_reddit_simulation.py --config {config_path}\n"
                f"   - Run both platforms in parallel: python {scripts_dir}/run_parallel_simulation.py --config {config_path}"
            )
        }
