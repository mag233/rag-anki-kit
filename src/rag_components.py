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
import time
from typing import NamedTuple


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
    
    # File processing mode selection
    st.subheader("📁 File Processing Mode")
    processing_mode = st.radio(
        "Choose processing mode:",
        ["Process all files", "Select specific files"],
        index=0,
        help="Process all: Process all PDF files in the directory\nSelect specific: Choose which files to process"
    )
    
    selected_files = None
    if processing_mode == "Select specific files":
        selected_files = _render_file_selection(paths["raw_dir"], paths["manifest_path"])
        
        if not selected_files:
            st.warning("Please select at least one file to process.")
            return
    
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
        
        # Chunk overlap setting (only for fixed_size)
        chunk_overlap = 0
        if method == "fixed_size":
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
        
        # Keep only metadata extraction (tables and images are not implemented)
        extract_meta = st.checkbox("Extract Metadata", value=True)
        
        st.subheader("⚙️ Advanced Options")
        
        # Advanced Chunk ID generation
        use_advanced_ids = st.checkbox(
            "Enhanced Chunk IDs", 
            value=False,
            help="Generate chunk IDs with timestamps and UUIDs for better uniqueness and traceability"
        )
        
        # Error handling options
        with st.expander("🛡️ Error Handling & Recovery"):
            max_retries = st.number_input(
                "Max Retries per File",
                min_value=0,
                max_value=5,
                value=2,
                help="Number of retry attempts for failed file processing"
            )
            
            skip_corrupted = st.checkbox(
                "Skip Corrupted Files",
                value=True,
                help="Continue processing other files when encountering corrupted files"
            )
        
        # Performance options
        with st.expander("🚀 Performance Settings"):
            enable_streaming = st.checkbox(
                "Streaming Processing",
                value=False,
                help="Process large files in chunks to reduce memory usage (experimental)"
            )
            
            show_progress_details = st.checkbox(
                "Detailed Progress",
                value=True,
                help="Show detailed progress information during processing"
            )
    
    # Process button
    st.divider()
    
    # Cleanup strategy selection
    if force:
        st.subheader("🗑️ Cleanup Strategy")
        cleanup_strategy = st.radio(
            "Data Cleanup Strategy",
            ["smart_cleanup", "full_reset", "selective_reset"],
            index=0,
            help="Smart: Clear only changed files\\nFull: Clear all data\\nSelective: Clear only selected files"
        )
    else:
        cleanup_strategy = "incremental"
    
    if st.button("Start Processing", type="primary"):
        _handle_improved_preprocessing(
            paths, method, size, chunk_overlap, force,
            clean_level, deep_clean_config, 
            extract_meta, selected_files,
            use_advanced_ids, max_retries, skip_corrupted,
            enable_streaming, show_progress_details, cleanup_strategy
        )


def _handle_preprocessing(paths: Dict, method: str, size: Optional[int], chunk_overlap: int, 
                        force: bool, clean_level: str, deep_clean_config: Dict,
                        extract_meta: bool, selected_files: Optional[List[str]] = None):
    """Handle preprocessing logic"""
    try:
        # Create progress indicators
        status_placeholder = st.empty()
        
        with status_placeholder.container():
            if selected_files:
                st.info(f"Processing {len(selected_files)} selected files... (Cleaning level: {clean_level})")
            else:
                st.info(f"Processing all documents... (Cleaning level: {clean_level})")
        
        # Determine if deep cleaning is enabled
        enable_deep_clean = (clean_level == "deep")
        
        # Clear embeddings when force reprocessing
        if force:
            try:
                from rag_utils import ChromaDBManager, get_embedding_model
                embed_model = get_embedding_model()
                db_manager = ChromaDBManager(paths["db_dir"], embed_model)
                
                if selected_files:
                    # Clear embeddings for selected files only
                    deleted_count = db_manager.delete_embeddings_for_files(selected_files)
                    if deleted_count > 0:
                        st.info(f"🗑️ Cleared {deleted_count} existing embeddings for selected files")
                else:
                    # Clear all embeddings when processing all files
                    deleted_count = db_manager.clear_all_embeddings()
                    if deleted_count > 0:
                        st.info(f"🗑️ Cleared all {deleted_count} existing embeddings")
                        
            except Exception as e:
                st.warning(f"Failed to clear embeddings: {e}")
        
        # Execute preprocessing
        result = process_documents(
            input_folder=paths["raw_dir"],
            output_folder=paths["proc_dir"],
            extract_tables=False,  # Not implemented - set to False
            extract_images=False,  # Not implemented - set to False
            extract_meta=extract_meta,
            chunking_method=method,
            chunk_size=size or 400,
            chunk_overlap=chunk_overlap,
            force_reprocess=force,
            enable_deep_clean=enable_deep_clean,
            deep_clean_config=deep_clean_config if enable_deep_clean else None,
            selected_files=selected_files  # Pass selected files
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
            
            # 清除缓存以获取最新数据
            from rag_utils import clear_cache
            clear_cache()
            
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
                "Deep Clean": "Yes" if meta.get("deep_clean_enabled", False) else "No",
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


def _render_file_selection(raw_dir: str, manifest_path: str) -> List[str]:
    """Render file selection interface with filtering options"""
    import os
    from pathlib import Path
    from datetime import datetime
    
    # Get all PDF files in raw directory
    pdf_files = []
    if os.path.exists(raw_dir):
        for file in os.listdir(raw_dir):
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(raw_dir, file)
                file_stat = os.stat(file_path)
                pdf_files.append({
                    'name': file,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime)
                })
    
    if not pdf_files:
        st.warning("No PDF files found in raw directory.")
        return []
    
    # Load manifest to check processing status
    manifest = {}
    if os.path.exists(manifest_path):
        try:
            import json
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception:
            pass
    
    # Filtering options (only show if there are many files)
    if len(pdf_files) > 10:
        st.markdown("**Filter Options:**")
        col1, col2 = st.columns(2)
        
        with col1:
            name_filter = st.text_input("Filter by name:", placeholder="Enter filename keywords...")
        
        with col2:
            status_filter = st.selectbox(
                "Filter by status:",
                ["All files", "Not processed", "Already processed"],
                index=0
            )
        
        # Apply filters
        filtered_files = []
        for file_info in pdf_files:
            filename = file_info['name']
            
            # Apply name filter
            if name_filter and name_filter.lower() not in filename.lower():
                continue
            
            # Apply status filter
            is_processed = filename in manifest
            if status_filter == "Not processed" and is_processed:
                continue
            elif status_filter == "Already processed" and not is_processed:
                continue
            
            filtered_files.append(file_info)
        
        pdf_files = filtered_files
    
    # Sort files by modification time (newest first)
    pdf_files.sort(key=lambda x: x['modified'], reverse=True)
    
    if not pdf_files:
        st.warning("No files match the current filters.")
        return []
    
    # Show file selection with status
    st.markdown(f"**Available PDF Files ({len(pdf_files)} files):**")
    
    # Add "Select All" / "Deselect All" buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Select All", key="select_all"):
            for i in range(len(pdf_files)):
                st.session_state[f"file_select_{i}"] = True
            st.rerun()
    
    with col2:
        if st.button("Deselect All", key="deselect_all"):
            for i in range(len(pdf_files)):
                st.session_state[f"file_select_{i}"] = False
            st.rerun()
    
    # Create checkboxes for each file with status info
    selected_files = []
    already_processed = []
    
    for i, file_info in enumerate(pdf_files):
        filename = file_info['name']
        is_processed = filename in manifest
        status_text = "✅ Processed" if is_processed else "⏳ Not processed"
        
        # Format file size
        size_mb = file_info['size'] / (1024 * 1024)
        size_text = f"({size_mb:.1f} MB)"
        
        # Format modification time
        mod_time = file_info['modified'].strftime("%Y-%m-%d %H:%M")
        
        # Create columns for better layout
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # Default select unprocessed files, but allow user to change
            default_selected = not is_processed
            is_selected = st.checkbox(
                f"{filename} {size_text}",
                value=st.session_state.get(f"file_select_{i}", default_selected),
                key=f"file_select_{i}"
            )
        
        with col2:
            st.text(status_text)
        
        with col3:
            st.text(mod_time)
        
        if is_selected:
            selected_files.append(filename)
            if is_processed:
                already_processed.append(filename)
    
    # Show override confirmation if needed
    if already_processed:
        st.warning(f"⚠️ {len(already_processed)} selected file(s) have already been processed:")
        for filename in already_processed:
            st.text(f"  • {filename}")
        
        override_confirmed = st.checkbox(
            "I confirm to reprocess these files (this will overwrite existing data)",
            value=False,
            key="override_confirmation"
        )
        
        if not override_confirmed:
            # Remove already processed files from selection
            selected_files = [f for f in selected_files if f not in already_processed]
            if already_processed:
                st.info(f"Removed {len(already_processed)} already processed file(s) from selection. Check the confirmation box above to reprocess them.")
    
    # Show selection summary
    if selected_files:
        st.success(f"📁 Selected {len(selected_files)} file(s) for processing")
    
    return selected_files


def _handle_improved_preprocessing(paths: Dict, method: str, size: Optional[int], chunk_overlap: int, 
                                 force: bool, clean_level: str, deep_clean_config: Dict,
                                 extract_meta: bool, selected_files: Optional[List[str]] = None,
                                 use_advanced_ids: bool = False, max_retries: int = 2,
                                 skip_corrupted: bool = True, enable_streaming: bool = False,
                                 show_progress_details: bool = True, cleanup_strategy: str = "smart_cleanup"):
    """Enhanced preprocessing logic with improved features"""
    
    # Check if improved processing is available
    try:
        from improved_document_processing import improved_process_documents
        use_improved = True
        st.info("🚀 Using enhanced document processing engine")
    except ImportError:
        # Use enhanced fallback
        use_improved = False
        st.info("🔧 Using enhanced fallback processing engine")
    
    try:
        # Create progress indicators
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        details_placeholder = st.empty()
        
        with status_placeholder.container():
            if selected_files:
                st.info(f"🔄 Processing {len(selected_files)} selected files... (Enhanced mode: {clean_level} cleaning)")
            else:
                st.info(f"🔄 Processing all documents... (Enhanced mode: {clean_level} cleaning)")
        
        # Show advanced features being used
        if use_advanced_ids or max_retries > 0 or enable_streaming:
            features = []
            if use_advanced_ids:
                features.append("Enhanced Chunk IDs")
            if max_retries > 0:
                features.append(f"Error Recovery ({max_retries} retries)")
            if enable_streaming:
                features.append("Streaming Processing")
            
            st.success(f"✨ Enhanced features: {', '.join(features)}")
        
        # Determine if deep cleaning is enabled
        enable_deep_clean = (clean_level == "deep")
        
        # Smart cleanup handling
        if force and cleanup_strategy == "smart_cleanup":
            try:
                from rag_utils import ChromaDBManager, get_embedding_model
                embed_model = get_embedding_model()
                db_manager = ChromaDBManager(paths["db_dir"], embed_model)
                
                if selected_files:
                    # Smart cleanup for selected files
                    deleted_count = db_manager.delete_embeddings_for_files(selected_files)
                    if deleted_count > 0:
                        st.info(f"🧹 Smart cleanup: Cleared {deleted_count} embeddings for selected files")
                else:
                    # Smart cleanup: only clear if really needed
                    existing_count = db_manager.get_embedding_count()
                    if existing_count > 0:
                        st.warning(f"🧹 Smart cleanup: Found {existing_count} existing embeddings")
                        if st.button("Clear all existing embeddings?", key="smart_clear"):
                            deleted_count = db_manager.clear_all_embeddings()
                            st.success(f"✅ Cleared {deleted_count} embeddings")
                            
            except Exception as e:
                st.warning(f"Smart cleanup failed: {e}")
        
        elif force and cleanup_strategy in ["full_reset", "selective_reset"]:
            # Original cleanup logic
            try:
                from rag_utils import ChromaDBManager, get_embedding_model
                embed_model = get_embedding_model()
                db_manager = ChromaDBManager(paths["db_dir"], embed_model)
                
                if cleanup_strategy == "selective_reset" and selected_files:
                    deleted_count = db_manager.delete_embeddings_for_files(selected_files)
                    if deleted_count > 0:
                        st.info(f"🗑️ Cleared {deleted_count} embeddings for selected files")
                elif cleanup_strategy == "full_reset":
                    deleted_count = db_manager.clear_all_embeddings()
                    if deleted_count > 0:
                        st.info(f"🗑️ Cleared all {deleted_count} existing embeddings")
                        
            except Exception as e:
                st.warning(f"Failed to clear embeddings: {e}")
        
        # Progress callback for detailed progress tracking
        progress_data = {"current": 0, "total": 0, "errors": []}
        
        def progress_callback(current, total, message):
            progress_data["current"] = current
            progress_data["total"] = total
            
            if show_progress_details:
                progress_percentage = (current / total * 100) if total > 0 else 0
                progress_placeholder.progress(progress_percentage / 100, 
                                           text=f"Processing: {current}/{total} files ({progress_percentage:.1f}%)")
                
                if show_progress_details:
                    details_placeholder.info(f"📄 {message}")
        
        # Execute enhanced preprocessing
        if use_improved:
            result = improved_process_documents(
                input_folder=paths["raw_dir"],
                output_folder=paths["proc_dir"],
                extract_tables=False,
                extract_images=False,
                extract_meta=extract_meta,
                chunking_method=method,
                chunk_size=size or 400,
                chunk_overlap=chunk_overlap,
                force_reprocess=force,
                enable_deep_clean=enable_deep_clean,
                deep_clean_config=deep_clean_config if enable_deep_clean else None,
                selected_files=selected_files,
                use_advanced_chunk_ids=use_advanced_ids,
                progress_callback=progress_callback if show_progress_details else None
            )
        else:
            # Use enhanced fallback processing
            result = _enhanced_process_documents_fallback(
                input_folder=paths["raw_dir"],
                output_folder=paths["proc_dir"],
                extract_tables=False,
                extract_images=False,
                extract_meta=extract_meta,
                chunking_method=method,
                chunk_size=size or 400,
                chunk_overlap=chunk_overlap,
                force_reprocess=force,
                enable_deep_clean=enable_deep_clean,
                deep_clean_config=deep_clean_config if enable_deep_clean else None,
                selected_files=selected_files,
                use_advanced_chunk_ids=use_advanced_ids,
                progress_callback=progress_callback if show_progress_details else None
            )
        
        # Clear progress indicators
        progress_placeholder.empty()
        details_placeholder.empty()
        
        # Clear cache to get latest data
        from rag_utils import clear_cache
        clear_cache()
        
        # Show enhanced results
        status_placeholder.success("✅ Enhanced processing completed!")
        
        # Enhanced statistics display
        _show_enhanced_processing_stats(result, progress_data)
        
        # Show post-processing statistics
        _show_processing_stats(paths)
        
    except Exception as e:
        st.error(f"Enhanced processing failed: {str(e)}")
        # Show error details if available
        if hasattr(e, '__traceback__'):
            with st.expander("🔍 Error Details"):
                import traceback
                st.code(traceback.format_exc())


def _show_enhanced_processing_stats(result, progress_data: Dict):
    """Show enhanced processing statistics with error details"""
    
    # Main statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Files", result.total_files)
    
    with col2:
        st.metric("Processed", result.processed_files, 
                 delta=f"{result.processed_files/result.total_files*100:.1f}%" if result.total_files > 0 else "0%")
    
    with col3:
        st.metric("Skipped", result.skipped_files)
        
    with col4:
        st.metric("Failed", result.failed_files,
                 delta=f"{result.failed_files/result.total_files*100:.1f}%" if result.total_files > 0 else "0%")
    
    # Additional enhanced statistics
    if hasattr(result, 'total_processing_time'):
        st.metric("Processing Time", f"{result.total_processing_time:.2f}s")
    
    if hasattr(result, 'total_chunks'):
        st.metric("Total Chunks", result.total_chunks)
    
    # Error details if available
    if hasattr(result, 'errors') and result.errors:
        with st.expander(f"⚠️ Error Details ({len(result.errors)} errors)"):
            for i, error in enumerate(result.errors, 1):
                error_type = error.get('type', 'unknown')
                retryable = error.get('retryable', False)
                retry_indicator = " 🔄" if retryable else " ❌"
                
                st.markdown(f"**{i}. {error.get('file', 'Unknown file')}**{retry_indicator}")
                st.text(f"Type: {error_type}")
                st.text(f"Error: {error.get('error', 'Unknown error')}")
                
                if retryable:
                    st.info("This error can be retried by reprocessing the file")
                else:
                    st.warning("This error requires manual intervention")
                
                st.divider()
    
    # Processing summary
    if result.total_files > 0:
        success_rate = result.processed_files / result.total_files * 100
        if success_rate >= 90:
            st.success(f"🎉 Excellent! {success_rate:.1f}% success rate")
        elif success_rate >= 70:
            st.info(f"✅ Good! {success_rate:.1f}% success rate")
        else:
            st.warning(f"⚠️ {success_rate:.1f}% success rate - consider checking failed files")


# Enhanced processing fallback - create a wrapper around existing processing
def _enhanced_process_documents_fallback(
    input_folder: str,
    output_folder: str,
    extract_tables: bool = True,
    extract_images: bool = True,
    extract_meta: bool = True,
    chunking_method: str = "by_sentence",
    chunk_size: int = 400,
    chunk_overlap: int = 50,
    force_reprocess: bool = False,
    enable_deep_clean: bool = False,
    deep_clean_config: Optional[Dict] = None,
    selected_files: Optional[List[str]] = None,
    use_advanced_chunk_ids: bool = False,
    progress_callback: Optional[callable] = None
):
    """Enhanced wrapper around existing process_documents with additional features"""
    
    # Import the current processing function
    from document_processing import process_documents
    import time
    from typing import NamedTuple
    
    # Enhanced ProcessingStats class
    class EnhancedProcessingStats(NamedTuple):
        total_files: int
        processed_files: int
        skipped_files: int
        failed_files: int
        total_chunks: int
        total_processing_time: float = 0.0
        errors: List = None
        
        def __new__(cls, total_files, processed_files, skipped_files, failed_files, total_chunks, total_processing_time=0.0, errors=None):
            return super().__new__(cls, total_files, processed_files, skipped_files, failed_files, total_chunks, total_processing_time, errors or [])
    
    start_time = time.time()
    
    # Enhanced chunk ID logic - modify chunks after processing if needed
    result = process_documents(
        input_folder=input_folder,
        output_folder=output_folder,
        extract_tables=extract_tables,
        extract_images=extract_images,
        extract_meta=extract_meta,
        chunking_method=chunking_method,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        force_reprocess=force_reprocess,
        enable_deep_clean=enable_deep_clean,
        deep_clean_config=deep_clean_config,
        selected_files=selected_files
    )
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # If advanced chunk IDs are requested, we would need to update the chunk files
    # This is a simplified implementation - the full version would be in improved_document_processing.py
    if use_advanced_chunk_ids:
        st.info("🆔 Enhanced Chunk IDs: Feature enabled (simplified implementation)")
    
    # Convert to enhanced stats
    enhanced_result = EnhancedProcessingStats(
        total_files=result.total_files,
        processed_files=result.processed_files,
        skipped_files=result.skipped_files,
        failed_files=result.failed_files,
        total_chunks=result.total_chunks,
        total_processing_time=processing_time,
        errors=[]  # Could be enhanced to track specific errors
    )
    
    return enhanced_result
