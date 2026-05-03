"""
图谱相关API路由
采用项目上下文机制，服务端持久化状态
"""

import os
import threading
from flask import request, jsonify
from pydantic import ValidationError as PydanticValidationError

from ..schemas.graph import (
    OntologyGenerateFromTextRequest,
    GraphBuildRequest,
)
from ..utils.response import success_response, error_response, validation_error_response

from . import graph_bp
from ..config import Config
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilderService
from ..services.simulation_manager import SimulationManager
from ..services.text_processor import TextProcessor
from ..services.graph_orchestrator import GraphOrchestratorService
from ..utils.file_parser import FileParser
from ..utils.logger import get_logger
from ..utils.locale import t, get_locale, set_locale
from ..models.task import TaskManager, TaskStatus
from ..models.project import ProjectManager, ProjectStatus
from ..services.graph_backend import GraphBackendFactory

# 获取日志器
logger = get_logger('futuria.api')


# ============== 项目管理接口 ==============

@graph_bp.route('/project/<project_id>', methods=['GET'])
def get_project(project_id: str):
    """
    获取项目详情
    """
    project = ProjectManager.get_project(project_id)
    
    if not project:
        return jsonify({
            "success": False,
            "error": t('api.projectNotFound', id=project_id)
        }), 404

    return jsonify({
        "success": True,
        "data": project.to_dict()
    })


@graph_bp.route('/project/list', methods=['GET'])
def list_projects():
    """
    列出所有项目
    """
    limit = request.args.get('limit', 50, type=int)
    projects = ProjectManager.list_projects(limit=limit)
    
    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in projects],
        "count": len(projects)
    })


@graph_bp.route('/project/<project_id>', methods=['DELETE'])
def delete_project(project_id: str):
    """
    删除项目
    """
    success = ProjectManager.delete_project(project_id)
    
    if not success:
        return jsonify({
            "success": False,
            "error": t('api.projectDeleteFailed', id=project_id)
        }), 404

    return jsonify({
        "success": True,
        "message": t('api.projectDeleted', id=project_id)
    })


@graph_bp.route('/project/<project_id>/reset', methods=['POST'])
def reset_project(project_id: str):
    """
    重置项目状态（用于重新构建图谱）
    """
    project = ProjectManager.get_project(project_id)
    
    if not project:
        return jsonify({
            "success": False,
            "error": t('api.projectNotFound', id=project_id)
        }), 404

    # 重置到本体已生成状态
    if project.ontology:
        project.status = ProjectStatus.ONTOLOGY_GENERATED
    else:
        project.status = ProjectStatus.CREATED
    
    project.graph_id = None
    project.graph_build_task_id = None
    project.error = None
    ProjectManager.save_project(project)

    SimulationManager().clear_project_graph_references(project_id)
    
    return jsonify({
        "success": True,
        "message": t('api.projectReset', id=project_id),
        "data": project.to_dict()
    })


# ============== 接口1：上传文件并生成本体 ==============

@graph_bp.route('/ontology/generate', methods=['POST'])
def generate_ontology():
    """
    接口1：上传文件，分析生成本体定义
    
    请求方式：multipart/form-data
    
    参数：
        files: 上传的文件（PDF/MD/TXT），可多个
        simulation_requirement: 模拟需求描述（必填）
        project_name: 项目名称（可选）
        additional_context: 额外说明（可选）
        
    返回：
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "ontology": {
                    "entity_types": [...],
                    "edge_types": [...],
                    "analysis_summary": "..."
                },
                "files": [...],
                "total_text_length": 12345
            }
        }
    """
    try:
        logger.info("=== 开始生成本体定义 ===")
        
        # 获取参数
        simulation_requirement = request.form.get('simulation_requirement', '')
        project_name = request.form.get('project_name', 'Unnamed Project')
        additional_context = request.form.get('additional_context', '')
        
        logger.debug(f"项目名称: {project_name}")
        logger.debug(f"模拟需求: {simulation_requirement[:100]}...")
        
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationRequirement')
            }), 400
        
        # 获取上传的文件
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or all(not f.filename for f in uploaded_files):
            return jsonify({
                "success": False,
                "error": t('api.requireFileUpload')
            }), 400
        
        # 创建项目
        project = ProjectManager.create_project(name=project_name)
        project.simulation_requirement = simulation_requirement
        logger.info(f"创建项目: {project.project_id}")
        
        # 保存文件并提取文本
        document_texts = []
        all_text = ""
        
        for file in uploaded_files:
            if file and file.filename and GraphOrchestratorService.allowed_file(file.filename):
                # 保存文件到项目目录
                file_info = ProjectManager.save_file_to_project(
                    project.project_id, 
                    file, 
                    file.filename
                )
                project.files.append({
                    "filename": file_info["original_filename"],
                    "size": file_info["size"]
                })
                
                # 提取文本
                text = FileParser.extract_text(file_info["path"])
                text = TextProcessor.preprocess_text(text)
                document_texts.append(text)
                all_text += f"\n\n=== {file_info['original_filename']} ===\n{text}"
        
        if not document_texts:
            ProjectManager.delete_project(project.project_id)
            return jsonify({
                "success": False,
                "error": t('api.noDocProcessed')
            }), 400
        
        # 保存提取的文本
        project.total_text_length = len(all_text)
        ProjectManager.save_extracted_text(project.project_id, all_text)
        logger.info(f"文本提取完成，共 {len(all_text)} 字符")
        
        # 生成本体
        logger.info("调用 LLM 生成本体定义...")
        generator = OntologyGenerator()
        ontology = generator.generate(
            document_texts=document_texts,
            simulation_requirement=simulation_requirement,
            additional_context=additional_context if additional_context else None
        )
        
        # 保存本体到项目
        entity_count = len(ontology.get("entity_types", []))
        edge_count = len(ontology.get("edge_types", []))
        logger.info(f"本体生成完成: {entity_count} 个实体类型, {edge_count} 个关系类型")
        
        project.ontology = {
            "entity_types": ontology.get("entity_types", []),
            "edge_types": ontology.get("edge_types", [])
        }
        project.analysis_summary = ontology.get("analysis_summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        ProjectManager.save_project(project)
        logger.info(f"=== 本体生成完成 === 项目ID: {project.project_id}")
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project.project_id,
                "project_name": project.name,
                "ontology": project.ontology,
                "analysis_summary": project.analysis_summary,
                "files": project.files,
                "total_text_length": project.total_text_length,
                "chunk_size": project.chunk_size,
                "chunk_overlap": project.chunk_overlap,
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500


@graph_bp.route('/health/llm', methods=['GET'])
def get_llm_health():
    """Return LLM provider status and current active provider."""
    from ..utils.llm_client import LLMClient
    try:
        client = LLMClient()
        return jsonify({
            "success": True,
            "data": {
                "providers": client.get_provider_status(),
                "current_provider": client.current_provider_name,
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


# ============== 接口2：基于已有文本生成本体 ==============

@graph_bp.route('/ontology/generate-from-text/<project_id>', methods=['POST'])
def generate_ontology_from_text(project_id: str):
    """
    接口2：读取已提取文本，生成本体定义
    
    用于research-only项目的本体生成（无文件上传场景）。
    
    请求（JSON）：
        {
            "simulation_requirement": "模拟需求描述（必填）",
            "additional_context": "额外说明（可选）"
        }
        
    返回：
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "ontology": {...},
                "analysis_summary": "...",
                "text_char_count": 12345
            }
        }
    """
    try:
        import time
        start_time = time.time()
        
        logger.info(f"=== 开始从已有文本生成本体 === project_id={project_id}")
        
        # 解析请求
        data = request.get_json() or {}
        try:
            req = OntologyGenerateFromTextRequest.model_validate(data)
        except PydanticValidationError as exc:
            return validation_error_response(
                [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()]
            )
        
        simulation_requirement = req.simulation_requirement
        additional_context = req.additional_context
        
        if not simulation_requirement:
            return error_response(t('api.requireSimulationRequirement'), 400)
        
        # 获取项目
        project = ProjectManager.get_project(project_id)
        if not project:
            return error_response(t('api.projectNotFound', id=project_id), 404)
        
        # 获取已提取的文本
        text = ProjectManager.get_extracted_text(project_id)
        if not text or not text.strip():
            return error_response(t('api.textNotFound'), 400)
        
        text_char_count = len(text)
        logger.info(f"文本读取完成: {text_char_count} 字符, project_id={project_id}")
        
        # 更新项目simulation_requirement
        project.simulation_requirement = simulation_requirement
        
        # 截断文本用于本体生成（5万字限制）
        max_len = OntologyGenerator.MAX_TEXT_LENGTH_FOR_LLM
        truncated_text = text[:max_len] if len(text) > max_len else text
        document_texts = [truncated_text]
        
        # 生成本体
        logger.info("调用 LLM 生成本体定义...")
        generator = OntologyGenerator()
        ontology = generator.generate(
            document_texts=document_texts,
            simulation_requirement=simulation_requirement,
            additional_context=additional_context if additional_context else None
        )
        
        # 保存本体到项目
        entity_count = len(ontology.get("entity_types", []))
        edge_count = len(ontology.get("edge_types", []))
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"本体生成完成: project_id={project_id}, "
            f"text_char_count={text_char_count}, "
            f"entity_count={entity_count}, "
            f"edge_count={edge_count}, "
            f"generation_time_ms={generation_time_ms}"
        )
        
        project.ontology = {
            "entity_types": ontology.get("entity_types", []),
            "edge_types": ontology.get("edge_types", [])
        }
        project.analysis_summary = ontology.get("analysis_summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        ProjectManager.save_project(project)
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project.project_id,
                "ontology": project.ontology,
                "analysis_summary": project.analysis_summary,
                "text_char_count": text_char_count,
                "entity_count": entity_count,
                "edge_count": edge_count,
                "generation_time_ms": generation_time_ms,
            }
        })
        
    except Exception as e:
        return error_response(str(e), 500)


# ============== 接口3：构建图谱 ==============

@graph_bp.route('/build', methods=['POST'])
def build_graph():
    """
    接口2：根据project_id构建图谱
    """
    try:
        logger.info("=== 开始构建图谱 ===")
        data = request.get_json() or {}
        try:
            req = GraphBuildRequest.model_validate(data)
        except PydanticValidationError as exc:
            return validation_error_response(
                [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()]
            )
        
        project_id = req.project_id
        preview = req.preview
        force = req.force
        logger.debug(f"请求参数: project_id={project_id}")
        
        if not project_id:
            return error_response(t('api.requireProjectId'), 400)
        
        project = ProjectManager.get_project(project_id)
        if not project:
            return error_response(t('api.projectNotFound', id=project_id), 404)
        if project.status == ProjectStatus.CREATED:
            return error_response(t('api.ontologyNotGenerated'), 400)
        if project.status == ProjectStatus.GRAPH_BUILDING and not force:
            return jsonify({"success": False, "error": t('api.graphBuilding'), "task_id": project.graph_build_task_id}), 400
        
        if force and project.status in [ProjectStatus.GRAPH_BUILDING, ProjectStatus.FAILED, ProjectStatus.GRAPH_COMPLETED]:
            project.status = ProjectStatus.ONTOLOGY_GENERATED
            project.graph_id = None
            project.graph_build_task_id = None
            project.error = None
        
        graph_name = req.graph_name or project.name or 'FUTUR.IA Graph'
        try:
            chunk_size, chunk_overlap = GraphOrchestratorService.normalize_chunk_settings(
                req.chunk_size, req.chunk_overlap, project
            )
        except ValueError as exc:
            return error_response(str(exc), 400)
        
        project.chunk_size = chunk_size
        project.chunk_overlap = chunk_overlap
        text = ProjectManager.get_extracted_text(project_id)
        if not text:
            return error_response(t('api.textNotFound'), 400)
        ontology = project.ontology
        if not ontology:
            return error_response(t('api.ontologyNotFound'), 400)
        
        ontology_guardrails = GraphBuilderService.analyze_ontology_guardrails(ontology)
        if preview:
            estimate = TextProcessor.estimate_ingestion_cost(text=text, chunk_size=chunk_size, overlap=chunk_overlap)
            return jsonify({"success": True, "data": {"project_id": project_id, "graph_name": graph_name, "chunk_size": chunk_size, "chunk_overlap": chunk_overlap, "ontology_guardrails": ontology_guardrails, **estimate}})
        if not ontology_guardrails["can_build"]:
            return jsonify({"success": False, "error": "Ontology must be fixed before building the graph.", "ontology_guardrails": ontology_guardrails}), 400
        if not Config.ZEP_API_KEY:
            return error_response(t('api.zepApiKeyMissing'), 500)
        
        if GraphOrchestratorService.should_skip_rebuild(project, text, ontology, force):
            return jsonify({"success": True, "data": {"project_id": project_id, "message": t('api.buildSkippedNoChanges'), "skipped": True}})
        
        use_incremental, changed_chunks, new_chunk_signatures = GraphOrchestratorService.compute_incremental_plan(project, text, chunk_size, chunk_overlap, force)
        if use_incremental and changed_chunks:
            builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
            task_id = builder.incremental_build_graph_async(graph_id=project.graph_id, chunks=changed_chunks, batch_size=3)
            project.status = ProjectStatus.GRAPH_BUILDING
            project.graph_build_task_id = task_id
            project.chunk_signatures = new_chunk_signatures
            ProjectManager.save_project(project)
            return jsonify({"success": True, "data": {"project_id": project_id, "task_id": task_id, "message": t('api.graphBuildStarted', taskId=task_id), "incremental": True}})
        
        task_manager = TaskManager()
        task_id = task_manager.create_task(f"构建图谱: {graph_name}")
        logger.info(f"创建图谱构建任务: task_id={task_id}, project_id={project_id}")
        project.status = ProjectStatus.GRAPH_BUILDING
        project.graph_build_task_id = task_id
        ProjectManager.save_project(project)
        current_locale = get_locale()
        thread = threading.Thread(target=GraphOrchestratorService.run_build_task, args=(project_id, task_id, graph_name, chunk_size, chunk_overlap, text, ontology, project, task_manager, current_locale), daemon=True)
        thread.start()
        return jsonify({"success": True, "data": {"project_id": project_id, "task_id": task_id, "message": t('api.graphBuildStarted', taskId=task_id)}})
    except Exception as e:
        return error_response(str(e), 500)


# ============== 任务查询接口 ==============

@graph_bp.route('/task/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """
    查询任务状态
    """
    task = TaskManager().get_task(task_id)
    
    if not task:
        return jsonify({
            "success": False,
            "error": t('api.taskNotFound', id=task_id)
        }), 404
    
    return jsonify({
        "success": True,
        "data": task.to_dict()
    })


@graph_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """
    列出所有任务
    """
    tasks = TaskManager().list_tasks()
    
    return jsonify({
        "success": True,
        "data": [t.to_dict() for t in tasks],
        "count": len(tasks)
    })


# ============== 图谱数据接口 ==============

@graph_bp.route('/data/<graph_id>', methods=['GET'])
def get_graph_data(graph_id: str):
    """
    获取图谱数据（节点和边）
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": t('api.zepApiKeyMissing')
            }), 500
        
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_data = builder.get_graph_data(graph_id)
        
        return jsonify({
            "success": True,
            "data": graph_data,
            "degraded_mode": False
        })
        
    except Exception as e:
        err_str = str(e)
        if 'Rate limit' in err_str or '429' in err_str:
            return jsonify({
                "success": False,
                "error": "Zep API rate limit exceeded. Please wait a minute and try again."
            }), 429
        if 'not found' in err_str.lower() or '404' in err_str:
            return jsonify({
                "success": False,
                "error": "Graph not found in Zep. It may have been deleted or not created yet."
            }), 404
        short_err = err_str.split('\n')[0][:200] if '\n' in err_str else err_str[:200]
        return jsonify({
            "success": False,
            "error": short_err
        }), 500


@graph_bp.route('/info/<graph_id>', methods=['GET'])
def get_graph_info(graph_id: str):
    """
    获取图谱基本信息（节点数、边数、实体类型、fidelidade）
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": t('api.zepApiKeyMissing')
            }), 500
        
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_info = builder._get_graph_info(graph_id)
        fidelity = builder.analyze_graph_actor_fidelity(graph_id)
        
        return jsonify({
            "success": True,
            "data": {
                **graph_info.to_dict(),
                "fidelity_score": fidelity["fidelity_score"],
            }
        })
        
    except Exception as e:
        err_str = str(e)
        if 'not found' in err_str.lower() or '404' in err_str:
            return jsonify({
                "success": False,
                "error": "Graph not found in Zep."
            }), 404
        short_err = err_str.split('\n')[0][:200] if '\n' in err_str else err_str[:200]
        return jsonify({
            "success": False,
            "error": short_err
        }), 500


@graph_bp.route('/fidelity/<graph_id>', methods=['GET'])
def get_graph_fidelity(graph_id: str):
    """
    获取图谱Actor Fidelity分析
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": t('api.zepApiKeyMissing')
            }), 500
        
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        result = builder.analyze_graph_actor_fidelity(graph_id)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        err_str = str(e)
        if 'not found' in err_str.lower() or '404' in err_str:
            return jsonify({
                "success": False,
                "error": "Graph not found in Zep."
            }), 404
        short_err = err_str.split('\n')[0][:200] if '\n' in err_str else err_str[:200]
        return jsonify({
            "success": False,
            "error": short_err
        }), 500


@graph_bp.route('/delete/<graph_id>', methods=['DELETE'])
def delete_graph(graph_id: str):
    """
    删除Zep图谱
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": t('api.zepApiKeyMissing')
            }), 500
        
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        builder.delete_graph(graph_id)
        
        return jsonify({
            "success": True,
            "message": t('api.graphDeleted', id=graph_id)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            
        }), 500
