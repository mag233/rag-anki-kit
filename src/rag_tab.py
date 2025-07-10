# rag_tab.py
"""
重构后的RAG标签页模块
使用模块化设计，提高代码可维护性和性能
"""

import os
import streamlit as st
from lang_utils import get_text
from rag_utils import (
    ChromaDBManager, 
    FileManager, 
    ProjectManager, 
    UploadManager,
    get_embedding_model
)
from rag_components import (
    render_project_selection,
    render_file_upload,
    render_status_dashboard,
    render_preprocessing_section,
    render_embedding_section,
    render_health_check
)


def render_rag_tab(PROJECTS_DIR, lang):
    """渲染RAG标签页的主函数"""
    text = get_text(lang)["rag_tab"]
    st.header(text["header"])
    
    # 项目选择和创建
    selected_project = render_project_selection(PROJECTS_DIR, text)
    
    if selected_project:
        _render_project_interface(PROJECTS_DIR, selected_project, text)


def _render_project_interface(projects_dir: str, project_name: str, text: dict):
    """渲染项目界面"""
    try:
        # 获取项目路径
        project_manager = ProjectManager(projects_dir)
        paths = project_manager.get_project_paths(project_name)
        
        # 确保目录存在
        for directory in [paths["raw_dir"], paths["chunks_dir"], paths["db_dir"]]:
            os.makedirs(directory, exist_ok=True)
        
        # 初始化管理器
        embed_model = get_embedding_model()
        db_manager = ChromaDBManager(paths["db_dir"], embed_model)
        file_manager = FileManager(paths["chunks_dir"], paths["manifest_path"])
        upload_manager = UploadManager(paths["raw_dir"])
        
        # 渲染各个界面组件
        new_files = render_file_upload(upload_manager, text)
        render_status_dashboard(db_manager, file_manager, text)
        render_preprocessing_section(paths, text)
        render_embedding_section(db_manager, file_manager, text)
        render_health_check(db_manager, file_manager, text)
        
        # 清理资源
        db_manager.close()
        
    except Exception as e:
        st.error(f"渲染项目界面失败: {e}")


# 保持向后兼容性的旧版本接口
def render_rag_tab_legacy(PROJECTS_DIR, lang):
    """旧版本接口，用于向后兼容"""
    return render_rag_tab(PROJECTS_DIR, lang)
