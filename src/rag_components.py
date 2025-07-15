# rag_components.py
"""
RAG Tab UI组件模块
将UI组件分离，提高代码可维护性
"""

import os
import streamlit as st
from typing import Dict, List, Optional
from rag_utils import (
    ChromaDBManager, 
    FileManager, 
    ProjectManager, 
    UploadManager,
    get_embedding_model
)
from document_processing import process_documents
from embed import create_or_update_embeddings
from processing_config import (
    get_chunking_methods_for_ui,
    get_cleaning_levels_for_ui,
    normalize_chunking_method,
    normalize_cleaning_level,
    get_display_text
)


def render_project_selection(projects_dir: str, text: Dict) -> Optional[str]:
    """渲染项目选择和创建界面"""
    project_manager = ProjectManager(projects_dir)
    projects = project_manager.get_projects()
    
    # 项目选择
    idx = 1 if projects else 0
    selected = st.selectbox(
        text["select_project"], 
        [text["new_project"]] + projects, 
        index=idx, 
        key="rag_project"
    )
    
    # 新建项目
    if selected == text["new_project"]:
        project_name = st.text_input(text["project_name_placeholder"])
        if st.button(text["create_btn"]) and project_name:
            if project_manager.create_project(project_name.strip()):
                st.success(text["success"].format(name=project_name))
                st.rerun()
        return None
    
    return selected


def render_file_upload(upload_manager: UploadManager, text: Dict) -> List[str]:
    """渲染文件上传界面"""
    st.markdown(text["step1_title"])
    
    uploaded_files = st.file_uploader(
        text["uploader_label"],
        type=["pdf", "md", "markdown", "text", "txt", "docx", "xlsx", "html"],
        accept_multiple_files=True
    )
    
    # 处理上传逻辑
    last_uploaded_files = st.session_state.get('last_uploaded_files', [])
    current_upload_names = [f.name for f in uploaded_files] if uploaded_files else []
    
    new_files = []
    
    if uploaded_files and current_upload_names != last_uploaded_files:
        new_files, actually_uploaded = upload_manager.handle_file_upload(
            uploaded_files, 
            last_uploaded_files
        )
        
        st.session_state['last_uploaded_files'] = current_upload_names
        
        if new_files:
            st.success(text["upload_success"].format(files=", ".join(new_files)))
        elif not actually_uploaded:
            pass  # 没有新文件写入且没有新冲突，不提示
        else:
            st.info(text["no_new_file"])
    
    elif not uploaded_files:
        st.session_state['last_uploaded_files'] = []
        st.caption(text["please_upload"])
    
    return new_files


def render_status_dashboard(db_manager: ChromaDBManager, file_manager: FileManager, text: Dict):
    """渲染状态仪表板"""
    st.divider()
    st.markdown(text["status_title"])
    
    # 显示embedding模型
    embed_model = get_embedding_model()
    st.info(text["embed_model"].format(model=embed_model))
    
    # 刷新按钮
    if st.button("🔄 " + text.get("refresh_stats", "Refresh Status"), key="refresh_stats_btn"):
        # 清理缓存并刷新
        from rag_utils import clear_cache
        clear_cache()
        st.rerun()
    
    # 数据指标
    col1, col2 = st.columns(2)
    
    with col1:
        chunk_count = file_manager.get_chunk_count()
        st.metric(text.get("chunk_count_metric", "Chunk Count"), chunk_count)
    
    with col2:
        embed_count = db_manager.get_embedding_count()
        st.metric(text.get("embed_count_metric", "Embedding Count"), embed_count)
    
    # 进度条
    progress = (embed_count / chunk_count) if chunk_count > 0 else 0.0
    st.progress(progress, text=text["progress_label"])


def render_preprocessing_section(paths: Dict, text: Dict):
    """Render preprocessing interface with fine-grained controls"""
    st.divider()
    st.markdown("### Step 2: Document Processing")
    
    # Create two columns layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Document Processing Options")
        
        # Chunking method selection (English only)
        chunking_methods = ["by_sentence", "by_paragraph", "by_page", "fixed_size"]
        method = st.selectbox("Chunking Method:", chunking_methods, index=0)
        
        # Chunk size setting (only for fixed_size)
        size = None
        if method == "fixed_size":
            size = st.number_input(
                "Chunk Size (characters)", 
                min_value=50, 
                max_value=2000, 
                value=400, 
                step=50
            )
        
        # Chunk overlap setting
        chunk_overlap = st.number_input(
            "Chunk Overlap (tokens)",
            min_value=0,
            max_value=200,
            value=50,
            step=10,
            help="Overlap between adjacent chunks helps maintain context continuity"
        )
        
        # Force reprocess option
        force = st.checkbox("Force full reprocessing", value=False)
    
    with col2:
        st.subheader("🧹 Cleaning Options")
        
        # Cleaning level selection (English only)
        clean_level = st.radio(
            "Cleaning Level",
            ["basic", "deep"],
            index=0,
            help="Basic: Standard text cleaning\\nDeep: Remove references, footnotes, page numbers etc."
        )
        
        # Deep clean detailed options (only show when deep cleaning is selected)
        deep_clean_config = {}
        if clean_level == "deep":
            st.markdown("**Deep Cleaning Options:**")
            deep_clean_config = {
                'remove_references': st.checkbox("Remove References", value=True),
                'remove_authors': st.checkbox("Remove Author Info", value=True),
                'remove_citations': st.checkbox("Remove Citations", value=True),
                'remove_page_numbers': st.checkbox("Remove Page Numbers", value=True),
                'normalize_whitespace': st.checkbox("Normalize Whitespace", value=True)
            }
        
        # Extraction options
        st.markdown("**Extraction Options:**")
        extract_tables = st.checkbox("Extract Tables", value=True)
        extract_images = st.checkbox("Extract Images", value=True)
        extract_meta = st.checkbox("Extract Metadata", value=True)
    
    # Process button
    st.divider()
    if st.button("Start Processing", type="primary"):
        _handle_preprocessing(
            paths, method, size, chunk_overlap, force,
            clean_level, deep_clean_config, 
            extract_tables, extract_images, extract_meta
        )


def _handle_preprocessing(paths: Dict, method: str, size: Optional[int], chunk_overlap: int, 
                        force: bool, clean_level: str, deep_clean_config: Dict,
                        extract_tables: bool, extract_images: bool, extract_meta: bool):
    """Handle preprocessing logic"""
    try:
        # Create progress indicators
        status_placeholder = st.empty()
        
        with status_placeholder.container():
            st.info(f"Processing documents... (Cleaning level: {clean_level})")
        
        # Determine if deep cleaning is enabled
        enable_deep_clean = (clean_level == "deep")
        
        # Execute preprocessing
        result = process_documents(
            input_folder=paths["raw_dir"],
            output_folder=paths["proc_dir"],
            extract_tables=extract_tables,
            extract_images=extract_images,
            extract_meta=extract_meta,
            chunking_method=method,
            chunk_size=size or 400,
            chunk_overlap=chunk_overlap,
            force_reprocess=force,
            enable_deep_clean=enable_deep_clean,
            deep_clean_config=deep_clean_config if enable_deep_clean else None
        )
        
        # Clear cache to get latest data
        from rag_utils import clear_cache
        clear_cache()
        
        # Show detailed results
        status_placeholder.success("Processing completed!")
        
        # Show processing statistics
        st.info(f"📊 Processing Statistics:\\n"
               f"- Total files: {result.total_files}\\n"
               f"- Processed: {result.processed_files}\\n"
               f"- Skipped: {result.skipped_files}\\n"
               f"- Failed: {result.failed_files}\\n"
               f"- Total chunks: {result.total_chunks}")
        
        # Show post-processing statistics
        _show_processing_stats(paths)
        
    except Exception as e:
        st.error(f"Processing failed: {str(e)}")


def _show_processing_stats(paths: Dict):
    """Show post-processing statistics"""
    try:
        # Re-create manager instances to get latest data
        embed_model = get_embedding_model()
        db_manager = ChromaDBManager(paths["db_dir"], embed_model)
        file_manager = FileManager(paths["chunks_dir"], paths["manifest_path"])
        
        chunk_count = file_manager.get_chunk_count()
        embed_count = db_manager.get_embedding_count()
        
        st.info(f"Total Chunks: {chunk_count}")
        st.info(f"Total Embeddings: {embed_count}")
        
        progress = (embed_count / chunk_count) if chunk_count > 0 else 0.0
        st.progress(progress, text="Embedding Progress")
        
        # Show manifest table
        _show_manifest_table(file_manager)
        
    except Exception as e:
        st.error(f"Failed to show statistics: {e}")


def _show_manifest_table(file_manager: FileManager):
    """Show manifest table"""
    try:
        manifest = file_manager.get_manifest()
        if not manifest:
            return
        
        rows = []
        for filename, meta in manifest.items():
            rows.append({
                "File": filename,
                "Chunks": meta.get("n_chunks", "-"),
                "Chunk Method": meta.get("chunk_method", "-"),
                "Deep Clean": meta.get("deep_clean_enabled", False),
                "Last Processed": meta.get("last_processed", "-")
            })
        
        st.dataframe(
            rows,
            hide_index=True,
            use_container_width=True,
            height=350
        )
        
    except Exception as e:
        st.error(f"Failed to show manifest table: {e}")
        st.error(f"显示manifest表格失败: {e}")


def render_embedding_section(db_manager: ChromaDBManager, file_manager: FileManager, text: Dict):
    """渲染嵌入生成界面"""
    st.divider()
    st.markdown(text["step3_title"])
    
    # 嵌入模式选择
    mode = st.radio(text["embed_mode"], text["embed_modes"], index=0)
    
    # 状态占位符
    embed_status_placeholder = st.empty()
    embed_progress_placeholder = st.empty()
    
    # 开始嵌入按钮
    if st.button(text["start_embed"]):
        _handle_embedding(db_manager, file_manager, mode, text, embed_status_placeholder, embed_progress_placeholder)


def _handle_embedding(db_manager: ChromaDBManager, file_manager: FileManager, mode: str, text: Dict, 
                     status_placeholder, progress_placeholder):
    """处理嵌入逻辑"""
    try:
        # 确定处理范围
        only_files = None
        if mode == text["embed_modes"][1]:  # Only new chunks
            only_files = _get_files_with_new_chunks(db_manager, file_manager, text, status_placeholder, progress_placeholder)
            if only_files is None:  # 出错或没有新chunks
                return
        
        # 显示处理状态
        with status_placeholder.container():
            st.info(text.get("embedding_in_progress", "Embedding in progress..."))
        
        # 清理文件并显示进度
        _process_and_clean_files(file_manager, only_files, progress_placeholder)
        
        # 执行嵌入
        try:
            create_or_update_embeddings(
                file_manager.chunks_dir, 
                db_manager.db_dir, 
                only_files=only_files
            )
            progress_placeholder.empty()
            status_placeholder.success(text["embed_success"])
            
        except Exception as embed_error:
            progress_placeholder.empty()
            _handle_embedding_error(embed_error, text, status_placeholder)
            
    except Exception as e:
        progress_placeholder.empty()
        status_placeholder.error(text["embed_fail"].format(err=str(e)))


def _get_files_with_new_chunks(db_manager: ChromaDBManager, file_manager: FileManager, text: Dict,
                              status_placeholder, progress_placeholder) -> Optional[set]:
    """获取包含新chunks的文件"""
    try:
        existing_ids = db_manager.get_existing_ids()
        if not existing_ids:
            # 如果没有现有的embeddings，返回None表示处理所有文件
            return None
        
        files_with_new_chunks = file_manager.get_files_with_new_chunks(existing_ids)
        
        if not files_with_new_chunks:
            status_placeholder.info(text.get("no_new_chunks_to_embed", "No new chunks to embed."))
            progress_placeholder.empty()
            return None
        
        return files_with_new_chunks
        
    except Exception as e:
        status_placeholder.error(f"检查新chunks失败: {e}")
        progress_placeholder.empty()
        return None


def _process_and_clean_files(file_manager: FileManager, only_files: Optional[set], progress_placeholder):
    """处理和清理文件"""
    try:
        chunk_files = file_manager.get_chunk_files()
        
        if only_files is not None:
            # 只处理指定的文件
            chunk_files = [
                os.path.join(file_manager.chunks_dir, f"{filename}_chunks.json")
                for filename in only_files
                if os.path.exists(os.path.join(file_manager.chunks_dir, f"{filename}_chunks.json"))
            ]
        
        total_files = len(chunk_files)
        if total_files == 0:
            progress_placeholder.empty()
            return
        
        # 清理文件并显示进度
        for idx, chunk_file in enumerate(chunk_files):
            progress_placeholder.progress(
                (idx + 1) / total_files, 
                text=f"{idx + 1}/{total_files} {os.path.basename(chunk_file)}"
            )
        
        # 执行文件清理
        file_manager.clean_chunk_files(chunk_files)
        
    except Exception as e:
        st.error(f"处理文件失败: {e}")


def _handle_embedding_error(error: Exception, text: Dict, status_placeholder):
    """处理嵌入错误"""
    error_msg = str(error)
    
    if "Expected IDs to be unique" in error_msg:
        import re
        dup_match = re.findall(r"found duplicates of: ([^ ]+)", error_msg)
        if dup_match:
            status_placeholder.warning(text["duplicate_ids"].format(ids=", ".join(dup_match)))
            status_placeholder.info(text["partial_embed"])
        else:
            status_placeholder.error("发现重复ID，但无法解析具体信息")
    
    elif "Empty ID" in error_msg or "ID must have at least one character" in error_msg:
        status_placeholder.error("有分块ID为空，请检查原始文档或分块逻辑。")
    
    else:
        status_placeholder.error(text["embed_fail"].format(err=error_msg))


def render_health_check(db_manager: ChromaDBManager, file_manager: FileManager, text: Dict):
    """渲染健康检查界面"""
    st.divider()
    st.markdown(text["manifest_check_title"])
    
    try:
        manifest = file_manager.get_manifest()
        if not manifest:
            st.info(text["no_manifest"])
            return
        
        # 获取embedding信息
        embed_ids = db_manager.get_existing_ids()
        
        # 构建详细信息
        details = []
        missing_files = []
        
        for filename, meta in manifest.items():
            n_chunks = meta.get("n_chunks", 0)
            
            # 计算embedding覆盖率
            if n_chunks and isinstance(n_chunks, int) and n_chunks > 0:
                stem = os.path.splitext(filename)[0]
                embed_count = len([eid for eid in embed_ids if eid.startswith(stem)])
                embed_status = f"{embed_count}/{n_chunks} ({embed_count/n_chunks:.0%})" if n_chunks else "-"
            else:
                embed_status = "-"
                if n_chunks == 0:
                    missing_files.append(filename)
            
            details.append({
                text["manifest_col_file"]: filename,
                text["manifest_col_chunkmethod"]: meta.get("chunk_method", "-"),
                text["manifest_col_last"]: meta.get("last_processed", "-"),
                "Error": meta.get("error", "-"),
                "Has Chunks": n_chunks > 0,
                "Embedding Status": embed_status
            })
        
        # 显示详细信息表格
        st.dataframe(details, hide_index=True, use_container_width=True)
        
        # 显示健康状态
        if missing_files:
            st.warning(text["missing_chunks"].format(files=", ".join(missing_files)))
        else:
            st.success(text["all_chunked"])
            
    except Exception as e:
        st.error(f"健康检查失败: {e}")
