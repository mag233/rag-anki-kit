"""
LitMap Tab - Knowledge Graph Generation from Research Literature

This module provides a Streamlit interface for building and visualizing
knowledge graphs from research papers using the LitMap feature.
"""

import os
import re
import streamlit as st
import pandas as pd
from typing import Dict, Any, List
import tempfile
import json
import datetime

# Import LitMap modules
from knowledge_graph import EntityRelationExtractor, KnowledgeGraphBuilder, KnowledgeGraphVisualizer
from knowledge_graph.utils import (
    save_extraction_results, load_extraction_results,
    create_summary_dataframes, filter_by_confidence,
    get_most_connected_entities
)
from literature import load_all_chunks
from lang_utils import get_text
from litmap import (
    load_chunk_status, load_all_chunks_from_folder, sync_chunk_status,
    get_processing_stats, start_full_reprocess, save_chunk_status,
    update_processed_chunks_status, clear_database_files, 
    create_fresh_chunk_status, save_extraction_data, load_extraction_data,
    dedup_items, merge_and_save_data, load_custom_types,
    get_all_entity_and_relation_types, get_last_processed_times,
    get_chunks_to_process
)


@st.cache_data(show_spinner=False)
def cached_load_all_chunks(chunks_folder):
    """Cached version of load_all_chunks for better performance."""
    return load_all_chunks(chunks_folder)


def render_litmap_tab(PROJECTS_DIR: str, lang: str) -> None:
    def clean_title(title):
        # Remove leading markdown headers like ###, ##, # and whitespace
        return re.sub(r"^#+\\s*", "", title).strip()
    """Render the LitMap knowledge graph tab."""
    text = get_text(lang)["litmap_tab"]
    
    st.header(text["header"])
    st.info(text["description"])
    st.divider()
    st.subheader(clean_title(text['step1_title']))
    st.caption(text["step1_info"])
    projects = [d for d in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, d))]
    
    if not projects:
        st.warning(text["no_projects"])
        return
    
    selected_project = st.selectbox(
        text["select_project"],
        options=projects,
        key="litmap_project"
    )
    
    if not selected_project:
        st.warning(text["no_project"])
        return

    # 初始化 session_state，防止 KeyError
    if 'litmap_entities' not in st.session_state:
        st.session_state['litmap_entities'] = []
    if 'litmap_relations' not in st.session_state:
        st.session_state['litmap_relations'] = []
    if 'litmap_loaded_project' not in st.session_state:
        st.session_state['litmap_loaded_project'] = None

    # 只有在切换项目时清空 session_state
    if st.session_state['litmap_loaded_project'] != selected_project:
        st.session_state['litmap_entities'] = []
        st.session_state['litmap_relations'] = []
        st.session_state['litmap_loaded_project'] = selected_project
    
    project_path = os.path.join(PROJECTS_DIR, selected_project)
    chunks_folder = os.path.join(project_path, "processed", "chunks")
    chroma_db_folder = os.path.join(project_path, "vectorstore", "chroma_db")
    litmap_folder = os.path.join(project_path, "litmap")
    
    # Create litmap folder if it doesn't exist
    os.makedirs(litmap_folder, exist_ok=True)
    
    # Check if chunks exist (same pattern as literature_tab)
    if not os.path.exists(chunks_folder):
        st.warning(text["no_chunks_warning"])
        return
    
    st.divider()
    st.subheader(clean_title(text['step2_title']))
    st.caption(text["step2_info"])

    # --- Knowledge Graph Chunk Processing State Management ---
    status_file = os.path.join(litmap_folder, "kg_chunk_status.json")
    # Load all chunks from chunks folder
    all_chunks, chunk_ids, chunk_files = load_all_chunks_from_folder(chunks_folder)
    now = datetime.datetime.now().isoformat()

    chunk_status = load_chunk_status(status_file)

    # Sync metadata with current chunks using business logic
    chunk_status = sync_chunk_status(chunk_status, chunk_ids)
    
    # Get processing statistics
    stats = get_processing_stats(chunk_status, chunk_ids)
    total_chunks = stats["total_chunks"]
    n_processed = stats["n_processed"] 
    n_pending = stats["n_pending"]

    # --- Processing Information ---
    with st.expander("ℹ️ Processing Information", expanded=False):
        st.write(f"Available chunk files: {len(chunk_files)} files")
        st.write(f"Total chunk IDs: {len(chunk_ids)}")
        st.write(f"Total chunks: {total_chunks}")
        st.write(f"Processed: {n_processed}")
        st.write(f"Pending: {n_pending}")
        if chunk_status:
            last_processed = chunk_status.get('last_processed_at', 'Never')
            st.write(f"Last processed: {last_processed}")

    # --- UI: Progress Bar and Controls ---
    st.markdown(f"**{text.get('progress_label', 'Progress')}: {n_processed} / {total_chunks} ({(n_processed/total_chunks*100 if total_chunks else 0):.1f}%)**")
    st.progress(n_processed/total_chunks if total_chunks else 0.0)

    # Show last processed time
    last_processed_times = [
        chunk_status.get(cid, {}).get("last_processed_at") 
        for cid in chunk_ids 
        if chunk_status.get(cid, {}).get("last_processed_at")
    ]
    if last_processed_times:
        last_time = max(last_processed_times)
        st.info(text.get("last_processed_at", "Last processed at") + f": {last_time}")

    # --- Chunk processing parameters (must be defined before action logic) ---
    col1, col2 = st.columns(2)
    with col1:
        max_chunks = st.slider(
            text.get("max_chunks", "Maximum Chunks to Process"),
            min_value=5, max_value=100, value=20,
            help=text.get("max_chunks_help", "How many chunks to process at once.")
        )
        confidence_threshold = st.slider(
            text.get("confidence_threshold", "Confidence Threshold"),
            min_value=0.0, max_value=1.0, value=0.6, step=0.1,
            help=text.get("confidence_help", "Minimum confidence for entities/relations.")
        )
    with col2:
        enable_deduplication = st.checkbox(
            text.get("enable_deduplication", "Enable Entity Deduplication"),
            value=True,
            help=text.get("deduplication_help", "Remove duplicate entities.")
        )
        physics_enabled = st.checkbox(
            text.get("physics_enabled", "Enable Physics Simulation"),
            value=True,
            help=text.get("physics_help", "Use physics for network visualization.")
        )

    # --- Advanced Entity Optimization Settings ---
    with st.expander(text.get("advanced_optimization", "🔧 Advanced Entity Optimization")):
        st.caption(text.get("optimization_description", 
            "Entity optimization uses two phases: Phase 1 (linguistic normalization) is always enabled, "
            "while Phase 2 (semantic similarity) is optional and computationally intensive."))
        
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            enable_semantic = st.checkbox(
                text.get("enable_semantic", "Enable Semantic Similarity (Phase 2)"),
                value=False,
                help=text.get("semantic_help", 
                    "Use AI models to detect semantically similar entities (e.g., 'ML' and 'machine learning'). "
                    "Requires sentence-transformers package and increases processing time.")
            )
            
            # New option for extraction strategy
            use_improved_extraction = st.checkbox(
                text.get("improved_extraction", "Enable Improved Extraction (Pre-normalization)"),
                value=True,
                help=text.get("improved_extraction_help",
                    "Normalize entities during extraction instead of post-processing. "
                    "This reduces inconsistencies at the source and improves efficiency.")
            )
            
        with col_opt2:
            similarity_threshold = st.slider(
                text.get("similarity_threshold", "Semantic Similarity Threshold"),
                min_value=0.70, max_value=0.95, value=0.85, step=0.05,
                disabled=not enable_semantic,
                help=text.get("threshold_help", 
                    "Higher values = more conservative merging. Recommended: 0.80-0.90")
            )
        
        if enable_semantic:
            st.info(text.get("semantic_warning", 
                "⚠️ Semantic similarity will increase processing time significantly. "
                "Consider testing with a small number of chunks first."))
        
        if use_improved_extraction:
            st.info(text.get("improved_extraction_info",
                "✨ Improved extraction applies normalization during entity extraction, "
                "resulting in more consistent entities from the start."))
        
        # Display what Phase 1 does
        st.write("**" + text.get("phase1_features", "Phase 1 (Always Enabled)") + ":**")
        phase1_desc = text.get("phase1_description", 
            "• Normalizes singular/plural forms (e.g., 'systematic reviews' → 'systematic review')\n"
            "• Expands abbreviations (e.g., 'ML' → 'machine learning')\n"
            "• Standardizes punctuation and word order\n"
            "• Removes duplicate entities with exact name matches")
        
        if use_improved_extraction:
            phase1_desc += text.get("phase1_extraction_note", 
                "\n• **Applied during extraction** for maximum efficiency")
        else:
            phase1_desc += text.get("phase1_postprocess_note",
                "\n• **Applied after extraction** as post-processing")
            
        st.write(phase1_desc)
        
        if enable_semantic:
            st.write("**" + text.get("phase2_features", "Phase 2 (Semantic Similarity)") + ":**")
            st.write(text.get("phase2_description", 
                "• Detects semantically similar entities using AI embeddings\n"
                "• Merges entities with similar meanings but different expressions\n"
                "• Maintains entity source and confidence information"))

    # --- Entity/Relation type list (must be before UI controls) ---
    # Initialize extractor before using its config
    extractor = EntityRelationExtractor(use_improved_extraction=use_improved_extraction)
    
    # Load custom types and get all available types
    custom_entity_types, custom_relation_types = load_custom_types(litmap_folder)
    all_entity_types, all_relation_types = get_all_entity_and_relation_types(
        extractor, custom_entity_types, custom_relation_types
    )

    # --- UI: Entity/Relation type selection (must be before action logic) ---
    col_entities, col_relations = st.columns(2)
    with col_entities:
        selected_entity_types = st.multiselect(
            text.get("entity_types", "Select Entity Types"),
            options=all_entity_types,
            default=all_entity_types,
            help=text.get("entity_types_help", "Choose which entity types to extract.")
        )
        # Optional: custom entity types
        if st.checkbox(text.get("enable_entity_custom", "Enable custom entity types"), value=False):
            custom_entity_types = st.text_area(
                text.get("custom_entity_types", "Custom entity types (comma separated)"),
                value="",
                help=text.get("custom_entity_types_help", "Enter custom entity types, comma separated.")
            )
            if custom_entity_types:
                custom_entity_types = [et.strip() for et in custom_entity_types.split(",") if et.strip()]
                selected_entity_types = list(set(selected_entity_types) | set(custom_entity_types))
    with col_relations:
        selected_relation_types = st.multiselect(
            text.get("relation_types", "Select Relation Types"),
            options=all_relation_types,
            default=all_relation_types,
            help=text.get("relation_types_help", "Choose which relation types to extract.")
        )
        # Optional: custom relation types
        if st.checkbox(text.get("enable_relation_custom", "Enable custom relation types"), value=False):
            custom_relation_types = st.text_area(
                text.get("custom_relation_types", "Custom relation types (comma separated)"),
                value="",
                help=text.get("custom_relation_types_help", "Enter custom relation types, comma separated.")
            )
            if custom_relation_types:
                custom_relation_types = [rt.strip() for rt in custom_relation_types.split(",") if rt.strip()]
                selected_relation_types = list(set(selected_relation_types) | set(custom_relation_types))

    # --- Determine which chunks to process ---
    # 未处理的chunks（用于增量处理）
    unprocessed_cids = [cid for cid in chunk_ids if chunk_status.get(cid, {}).get("status") != "processed"]
    
    # 根据模式确定要显示和处理的chunks
    # 对于选择性重处理，我们允许选择任何chunks（已处理或未处理）
    available_cids = chunk_ids[:max_chunks]  # 选择前N个chunks用于选择性重处理
    unprocessed_next_cids = unprocessed_cids[:max_chunks]  # 用于增量处理
    
    # 准备chunk数据
    next_chunks = [c for c in all_chunks if c.get("chunk_id") in available_cids]  # 选择性重处理用
    unprocessed_next_chunks = [c for c in all_chunks if c.get("chunk_id") in unprocessed_next_cids]  # 增量处理用

    # --- Action buttons ---
    col_reprocess, col_select, col_continue, col_dryrun, col_clear = st.columns([1,1,1,1,1])
    with col_reprocess:
        # 添加确认对话框
        if 'show_reprocess_confirm' not in st.session_state:
            st.session_state['show_reprocess_confirm'] = False
        
        if st.button(text.get("reprocess_all", "Reprocess All"), key="kg_reprocess_all", help=text.get("reprocess_all_help", "Reset all chunk status and reprocess all data from scratch.")):
            st.session_state['show_reprocess_confirm'] = True
        
        # 添加警告说明
        st.caption("⚠️ " + text.get("reprocess_all_warning", "Will process ALL chunks (ignores the limit above) and delete existing data."))
            
        if st.session_state.get('show_reprocess_confirm'):
            st.warning("⚠️ " + text.get("reprocess_warning", "This will delete all existing data and reprocess everything from scratch. Continue?"))
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ " + text.get("yes_reprocess", "Yes, Reprocess All"), key="confirm_reprocess"):
                    st.session_state['reprocess_mode'] = 'full'
                    st.session_state['show_reprocess_confirm'] = False
                    # 立即开始全量重处理
                    start_full_reprocess(chunk_status, status_file, litmap_folder, selected_project)
                    # 设置 UI 状态
                    st.session_state["litmap_status"] = "processing"
                    st.session_state["litmap_progress"] = text.get("initializing_full_reprocess", "Starting full reprocessing from scratch...")
                    st.session_state["litmap_errors"] = []
                    st.session_state['litmap_view_mode'] = 'direct'  # 直接替换模式
                    # 清空相关session state
                    for k in ["litmap_stats", "litmap_entities", "litmap_relations", "litmap_new_entities", "litmap_new_relations"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()
            with col_no:
                if st.button("❌ " + text.get("cancel", "Cancel"), key="cancel_reprocess"):
                    st.session_state['show_reprocess_confirm'] = False
                    st.rerun()
    
    with col_select:
        reprocess_select = st.button(
            text.get("reprocess_select", "Reprocess Select"), 
            key="kg_reprocess_select", 
            help=text.get("reprocess_select_help", "Reprocess only the selected chunks (respects chunk limit above) and merge with existing data.")
        )
        # 添加说明
        st.caption("🔄 " + text.get("reprocess_select_info", f"Will reprocess {min(max_chunks, len(available_cids))} chunks and merge results."))
    
    with col_continue:
        continue_from_last = st.button(text.get("continue_from_last", "Continue from Last"), key="kg_continue_from_last", help=text.get("continue_from_last_help", "Only process unprocessed chunks, keep history."))
        # 添加说明
        st.caption("ℹ️ " + text.get("continue_from_last_info", "Respects the chunk limit above and preserves existing data."))
    with col_dryrun:
        dry_run = st.checkbox(text.get("dry_run", "Dry Run (Preview Only)"), value=False, key="kg_dry_run")
    with col_clear:
        clear_status = st.button(text.get("clear_status", "Clear Status"), key="kg_clear_status", help=text.get("clear_status_help", "Clear progress and stats display."))

    # Action logic
    if continue_from_last:
        st.session_state["litmap_status"] = "processing"
        st.session_state["litmap_progress"] = text.get("initializing_extraction", "Initializing extraction...")
        st.session_state["litmap_errors"] = []
        st.session_state["reprocess_mode"] = "incremental"  # 增量处理模式
    elif reprocess_select:
        # 选择性重处理模式
        st.session_state["litmap_status"] = "processing" 
        st.session_state["litmap_progress"] = text.get("initializing_select_reprocess", "Initializing selective reprocessing...")
        st.session_state["litmap_errors"] = []
        st.session_state["reprocess_mode"] = "selective"  # 选择性重处理模式
    elif clear_status:
        for k in ["litmap_status", "litmap_progress", "litmap_stats", "litmap_errors"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

    # Progress/Stats/Errors display (always visible if not idle)
    if st.session_state.get("litmap_status") == "processing":
        st.info(st.session_state.get("litmap_progress", ""))
    if st.session_state.get("litmap_status") == "done":
        stats = st.session_state.get("litmap_stats", {})
        st.success(text.get("extraction_complete", "Extraction complete: {entities} entities, {relations} relations.").format(
            entities=stats.get('entities', 0),
            relations=stats.get('relations', 0)
        ))
        # Optionally show more stats here
    if st.session_state.get("litmap_status") == "error":
        errors = st.session_state.get("litmap_errors", [])
        if errors:
            st.error("\n".join(errors))

    # --- Main processing logic (only run if status is 'processing') ---
    if st.session_state.get("litmap_status") == "processing":
        try:
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            # 根据处理模式决定要处理的chunks
            reprocess_mode = st.session_state.get("reprocess_mode", "incremental")
            
            if reprocess_mode == "full":
                # 全量重处理：处理所有chunks，不分批
                process_chunks = all_chunks
                with status_placeholder.container():
                    st.info(text.get("full_reprocessing", "🔄 Full reprocessing: Processing all {n} chunks...").format(n=len(process_chunks)))
            elif reprocess_mode == "selective":
                # 选择性重处理：清空数据库并从头处理指定数量的chunks
                process_chunks = next_chunks  # 使用max_chunks限制数量
                if not process_chunks:
                    st.session_state["litmap_status"] = "idle"
                    st.warning(text.get("no_chunks_to_reprocess", "No chunks available for selective reprocessing."))
                    return
                
                # === 清空数据库：删除所有实体和关系文件 ===
                entities_file = os.path.join(litmap_folder, f"{selected_project}_entities.json")
                relations_file = os.path.join(litmap_folder, f"{selected_project}_relations.json")
                
                # 清空主数据文件
                if os.path.exists(entities_file):
                    os.remove(entities_file)
                if os.path.exists(relations_file):
                    os.remove(relations_file)
                
                # 清空临时文件
                temp_new_entities_path = os.path.join(litmap_folder, f"{selected_project}_new_entities.tmp.json")
                temp_new_relations_path = os.path.join(litmap_folder, f"{selected_project}_new_relations.tmp.json")
                if os.path.exists(temp_new_entities_path):
                    os.remove(temp_new_entities_path)
                if os.path.exists(temp_new_relations_path):
                    os.remove(temp_new_relations_path)
                
                # === 重置所有chunks的状态（从头开始） ===
                # 创建全新的chunk_status，所有chunks都设为pending
                fresh_chunk_status = {}
                for chunk in all_chunks:
                    cid = chunk.get("chunk_id")
                    if cid:
                        fresh_chunk_status[cid] = {
                            "status": "pending",
                            "last_processed_at": None,
                            "confidence_score": None
                        }
                
                # 保存全新的状态文件
                with open(status_file, "w", encoding="utf-8") as f:
                    json.dump(fresh_chunk_status, f, ensure_ascii=False, indent=2)
                
                # 更新本地变量以使用新状态
                chunk_status = fresh_chunk_status
                
                # 清空session state中的数据
                st.session_state['litmap_entities'] = []
                st.session_state['litmap_relations'] = []
                st.session_state['litmap_new_entities'] = []
                st.session_state['litmap_new_relations'] = []
                
                with status_placeholder.container():
                    st.info(text.get("selective_reprocessing", "🔄 Selective reprocessing: Processing {n} selected chunks from scratch...").format(n=len(process_chunks)))
            else:
                # 增量处理：只处理未处理的chunks，分批处理
                process_chunks = unprocessed_next_chunks
                if not process_chunks:
                    st.session_state["litmap_status"] = "idle"
                    st.warning(text.get("no_unprocessed_chunks", "No unprocessed chunks to process."))
                    return
                with status_placeholder.container():
                    st.info(text.get("processing_chunks", "📝 Incremental processing: Processing {n} chunks...").format(n=len(process_chunks)))
            
            extractor = EntityRelationExtractor(use_improved_extraction=use_improved_extraction)
            extractor.reset_stats()
            estimated_cost = len(process_chunks) * 0.002
            with status_placeholder.container():
                st.info(text.get('estimated_processing', 'Estimated processing: {n} chunks, estimated time {t} minutes, estimated cost ${c}').format(
                    n=len(process_chunks),
                    t=len(process_chunks)*2,
                    c=f"{estimated_cost:.3f}"
                ))
            def update_progress(progress_info):
                current = progress_info['current']
                total = progress_info['total']
                progress_percentage = current / total
                msg = text.get("processing_progress", "Progress: {current}/{total} ({percent:.1%})").format(
                    current=current, total=total, percent=progress_percentage)
                st.session_state['litmap_progress'] = msg
                with progress_placeholder.container():
                    st.progress(progress_percentage, text=msg)
            
            # 对于全量重处理，使用更大的max_chunks值或None来处理所有chunks
            max_chunks_to_use = None if reprocess_mode == "full" else max_chunks
            
            entities, relations = extractor.extract_from_chunks(
                process_chunks, 
                max_chunks=max_chunks_to_use,
                progress_callback=update_progress
            )
            # --- FIX: Always load and update the full status file, only update processed chunks ---
            # Load the full status file again to avoid overwriting previous progress
            full_chunk_status = load_chunk_status(status_file)
            for c in process_chunks:
                cid = c.get("chunk_id")
                if cid:
                    full_chunk_status[cid] = {
                        "status": "processed",
                        "last_processed_at": datetime.datetime.now().isoformat(),
                        "confidence_score": None
                    }
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(full_chunk_status, f, ensure_ascii=False, indent=2)
            chunk_status = full_chunk_status  # for UI update

            # 根据处理模式决定数据保存方式
            if reprocess_mode == "full":
                # 全量重处理：直接替换历史数据
                entities_file = os.path.join(litmap_folder, f"{selected_project}_entities.json")
                relations_file = os.path.join(litmap_folder, f"{selected_project}_relations.json")
                
                with open(entities_file, "w", encoding="utf-8") as f:
                    json.dump(entities, f, ensure_ascii=False, indent=2)
                with open(relations_file, "w", encoding="utf-8") as f:
                    json.dump(relations, f, ensure_ascii=False, indent=2)
                
                # 直接加载到主session state
                st.session_state['litmap_entities'] = entities
                st.session_state['litmap_relations'] = relations
                st.session_state['litmap_view_mode'] = 'history'  # 查看历史数据（即新处理的数据）
                
                # 清空临时数据
                st.session_state['litmap_new_entities'] = []
                st.session_state['litmap_new_relations'] = []
                
                with status_placeholder.container():
                    st.success(f"✅ " + text.get("full_reprocess_complete", "Full reprocessing complete! Processed {n} entities and {r} relations.").format(n=len(entities), r=len(relations)))
            elif reprocess_mode == "selective":
                # 选择性重处理：直接保存到主数据库（已清空数据库）
                entities_file = os.path.join(litmap_folder, f"{selected_project}_entities.json")
                relations_file = os.path.join(litmap_folder, f"{selected_project}_relations.json")
                
                with open(entities_file, "w", encoding="utf-8") as f:
                    json.dump(entities, f, ensure_ascii=False, indent=2)
                with open(relations_file, "w", encoding="utf-8") as f:
                    json.dump(relations, f, ensure_ascii=False, indent=2)
                
                # 直接加载到主session state
                st.session_state['litmap_entities'] = entities
                st.session_state['litmap_relations'] = relations
                st.session_state['litmap_view_mode'] = 'history'  # 查看主数据
                
                # 清空临时数据
                st.session_state['litmap_new_entities'] = []
                st.session_state['litmap_new_relations'] = []
                
                with status_placeholder.container():
                    st.success(f"✅ " + text.get("selective_complete", "Selective reprocessing complete! Processed {n} entities and {r} relations from {c} chunks.").format(n=len(entities), r=len(relations), c=len(process_chunks)))
            else:
                # 增量处理：放入新数据区域，等待预览合并
                st.session_state['litmap_new_entities'] = entities
                st.session_state['litmap_new_relations'] = relations
                st.session_state['litmap_view_mode'] = 'new'  # 查看新数据
                
                with status_placeholder.container():
                    st.success(f"✅ " + text.get("incremental_complete", "Incremental processing complete! Found {n} new entities and {r} new relations. Please review and merge.").format(n=len(entities), r=len(relations)))

            final_stats = extractor.get_stats()
            st.session_state['litmap_stats'] = {
                'entities': len(entities),
                'relations': len(relations),
                'total_chunks': final_stats.get('total_chunks', 0),
                'successful_chunks': final_stats.get('successful_chunks', 0),
                'failed_chunks': final_stats.get('failed_chunks', 0),
                'total_entities': final_stats.get('total_entities', 0),
                'total_relations': final_stats.get('total_relations', 0),
                'processing_time': final_stats.get('processing_time', 0),
                'errors': final_stats.get('errors', [])
            }
            st.session_state['litmap_errors'] = final_stats.get('errors', [])
            st.session_state['litmap_status'] = "done"
            progress_placeholder.empty()
            status_placeholder.empty()
            
            # 重新运行页面以更新UI显示
            st.rerun()
        except Exception as e:
            st.session_state['litmap_errors'] = [text.get("extraction_error", "Extraction error") + f": {e}"]
            st.session_state['litmap_status'] = "error"
            st.error(st.session_state['litmap_errors'][0])
            return

    st.divider()
    st.subheader(clean_title(text['step3_title']))
    st.caption(text["step3_info"])

    # 初始化 session_state
    if 'litmap_new_entities' not in st.session_state:
        st.session_state['litmap_new_entities'] = []
    if 'litmap_new_relations' not in st.session_state:
        st.session_state['litmap_new_relations'] = []
    if 'litmap_view_mode' not in st.session_state:
        st.session_state['litmap_view_mode'] = 'history'  # 'new' or 'history'
    if 'litmap_merge_pending' not in st.session_state:
        st.session_state['litmap_merge_pending'] = False

    # 新增：每次处理新chunk后自动保存到临时文件，防止session_state丢失
    temp_new_entities_path = os.path.join(litmap_folder, f"{selected_project}_new_entities.tmp.json")
    temp_new_relations_path = os.path.join(litmap_folder, f"{selected_project}_new_relations.tmp.json")
    if st.session_state.get('litmap_new_entities'):
        with open(temp_new_entities_path, "w", encoding="utf-8") as f:
            json.dump(st.session_state['litmap_new_entities'], f, ensure_ascii=False, indent=2)
    if st.session_state.get('litmap_new_relations'):
        with open(temp_new_relations_path, "w", encoding="utf-8") as f:
            json.dump(st.session_state['litmap_new_relations'], f, ensure_ascii=False, indent=2)

    # --- Step 3: Data Review & Merge Controls (soft-coded English) ---
    col_preview, col_load_history, col_merge = st.columns(3)
    
    # 检查是否有新数据需要合并
    has_new_data = (
        len(st.session_state.get('litmap_new_entities', [])) > 0 or 
        len(st.session_state.get('litmap_new_relations', [])) > 0 or
        os.path.exists(temp_new_entities_path) or
        os.path.exists(temp_new_relations_path)
    )
    
    with col_preview:
        preview_new = st.button(
            text.get("preview_new_data", "Preview New Data"), 
            key="preview_new_data",
            disabled=not has_new_data
        )
    with col_load_history:
        load_history = st.button(text.get("load_history_data", "Load All History"), key="load_history_data")
    with col_merge:
        merge_button = st.button(
            text.get("merge_new_data", "Merge New Data to Main DB"), 
            key="merge_new_data",
            disabled=not has_new_data,
            help=text.get("merge_help", "Only available when there is new data to merge") if not has_new_data else None
        )
        if merge_button and has_new_data:
            st.session_state['litmap_merge_pending'] = True
            st.rerun()
        
        # 添加状态说明
        if not has_new_data:
            st.caption("💡 " + text.get("no_new_data_to_merge", "No new data to merge"))
        else:
            st.caption("📥 " + text.get("new_data_ready", "New data ready to merge"))

    # 处理按钮逻辑
    entities_path = os.path.join(litmap_folder, f"{selected_project}_entities.json")
    relations_path = os.path.join(litmap_folder, f"{selected_project}_relations.json")

    # 1. 预览新数据（仅显示新处理结果，不影响历史）
    if preview_new:
        st.session_state['litmap_view_mode'] = 'new'
        st.info(text["showing_new_data"])

    # 2. 加载历史数据（从磁盘读取，覆盖 session_state，切换为历史视图）
    if load_history:
        if os.path.exists(entities_path):
            with open(entities_path, "r", encoding="utf-8") as f:
                st.session_state['litmap_entities'] = json.load(f)
        else:
            st.session_state['litmap_entities'] = []
        if os.path.exists(relations_path):
            with open(relations_path, "r", encoding="utf-8") as f:
                st.session_state['litmap_relations'] = json.load(f)
        else:
            st.session_state['litmap_relations'] = []
        st.session_state['litmap_view_mode'] = 'history'
        st.session_state['litmap_new_entities'] = []
        st.session_state['litmap_new_relations'] = []
        st.success(text["history_loaded"])
        st.rerun()

    # 3. 合并新数据到主数据库（去重，写入磁盘，切换为历史视图）
    if st.session_state.get('litmap_merge_pending', False):
        st.session_state['litmap_merge_pending'] = False  # 重置
        
        # 合并前强制从磁盘加载历史数据，防止 session_state 被清空
        if os.path.exists(entities_path):
            with open(entities_path, "r", encoding="utf-8") as f:
                disk_entities = json.load(f)
        else:
            disk_entities = []
        if os.path.exists(relations_path):
            with open(relations_path, "r", encoding="utf-8") as f:
                disk_relations = json.load(f)
        else:
            disk_relations = []
        
        # 新增：合并时优先从临时文件读取新数据，防止session_state丢失
        if os.path.exists(temp_new_entities_path):
            with open(temp_new_entities_path, "r", encoding="utf-8") as f:
                new_entities = json.load(f)
        else:
            new_entities = st.session_state.get('litmap_new_entities', [])
        if os.path.exists(temp_new_relations_path):
            with open(temp_new_relations_path, "r", encoding="utf-8") as f:
                new_relations = json.load(f)
        else:
            new_relations = st.session_state.get('litmap_new_relations', [])
        # 合并并去重
        # 合并
        all_entities = disk_entities + new_entities
        all_relations = disk_relations + new_relations
        
        # 去重 (使用业务逻辑模块的函数)
        all_entities = dedup_items(all_entities, 'entity')
        all_relations = dedup_items(all_relations, 'relation')
        
        # 保存
        with open(entities_path, "w", encoding="utf-8") as f:
            json.dump(all_entities, f, ensure_ascii=False, indent=2)
        with open(relations_path, "w", encoding="utf-8") as f:
            json.dump(all_relations, f, ensure_ascii=False, indent=2)
        st.session_state['litmap_entities'] = all_entities
        st.session_state['litmap_relations'] = all_relations
        st.session_state['litmap_new_entities'] = []
        st.session_state['litmap_new_relations'] = []
        st.session_state['litmap_view_mode'] = 'history'
        # 合并后清理临时文件
        if os.path.exists(temp_new_entities_path):
            os.remove(temp_new_entities_path)
        if os.path.exists(temp_new_relations_path):
            os.remove(temp_new_relations_path)
        msg = f"新数据已合并到主数据库并保存！共{len(all_entities)}个实体，{len(all_relations)}条关系。"
        print(f"DEBUG: 合并完成 - 实体: {len(all_entities)}, 关系: {len(all_relations)}")
        print(f"DEBUG: session_state更新后 - 实体: {len(st.session_state['litmap_entities'])}, 关系: {len(st.session_state['litmap_relations'])}")
        st.success(msg)
        st.rerun()
    
    # --- 选择数据源：新 or 历史 ---
    if st.session_state.get('litmap_view_mode') == 'new':
        entities = st.session_state.get('litmap_new_entities', [])
        relations = st.session_state.get('litmap_new_relations', [])
        st.info(text["showing_new_data"])
        print(f"DEBUG: 显示新数据 - 实体: {len(entities)}, 关系: {len(relations)}")
    else:
        entities = st.session_state.get('litmap_entities', [])
        relations = st.session_state.get('litmap_relations', [])
        st.info(text["showing_history_data"])
        print(f"DEBUG: 显示历史数据 - 实体: {len(entities)}, 关系: {len(relations)}")
        print(f"DEBUG: view_mode = {st.session_state.get('litmap_view_mode')}")

    # --- step 4/5: 后续统计和可视化全部用 entities/relations 变量 ---
    st.divider()
    if entities or relations:
        st.subheader(clean_title(text['step4_title']))
        col_stats1, col_stats2 = st.columns(2)
        with col_stats1:
            st.metric(text["total_entities"], len(entities))
            st.metric(text["total_relations"], len(relations))
        with col_stats2:
            if entities:
                avg_entity_confidence = sum(e.get('confidence', 0) for e in entities) / len(entities)
                st.metric(text["avg_entity_confidence"], f"{avg_entity_confidence:.3f}")
            if relations:
                avg_relation_confidence = sum(r.get('confidence', 0) for r in relations) / len(relations)
                st.metric(text["avg_relation_confidence"], f"{avg_relation_confidence:.3f}")
        # Most connected entities (enhanced with comprehensive analysis)
        if relations and entities:
            st.subheader(clean_title(text['most_connected']))
            
            connected_entities = get_most_connected_entities(relations, entities, top_n=10)
            
            if connected_entities and any(e['entity'] for e in connected_entities):
                # Create tabs for different views
                tab1, tab2 = st.tabs([
                    text.get("detailed_table", "📊 Detailed Analysis"), 
                    text.get("summary_cards", "📋 Summary Cards")
                ])
                
                with tab1:
                    # Create a more informative dataframe
                    display_data = []
                    for entity in connected_entities:
                        display_data.append({
                            text.get("entity_name", "Entity"): entity['entity'],
                            text.get("entity_type", "Type"): entity['type'],
                            text.get("total_connections", "Total Connections"): entity['total_connections'],
                            text.get("as_source", "As Source"): entity['as_source'],
                            text.get("as_target", "As Target"): entity['as_target'],
                            text.get("unique_partners", "Unique Partners"): entity['unique_partners'],
                            text.get("relation_diversity", "Relation Types"): entity['relation_diversity'],
                            text.get("avg_confidence", "Avg Confidence"): f"{entity['avg_confidence']:.3f}",
                            text.get("influence_score", "Influence Score"): f"{entity['influence_score']:.2f}"
                        })
                    
                    connected_df = pd.DataFrame(display_data)
                    st.dataframe(connected_df, use_container_width=True)
                
                with tab2:
                    # Create visually appealing cards for top entities
                    for i, entity in enumerate(connected_entities[:6]):  # Show top 6 in cards
                        with st.container():
                            # Color coding based on influence score
                            influence = entity['influence_score']
                            if influence >= 10:
                                color = "🔥"
                                border_color = "#FF6B6B"
                            elif influence >= 5:
                                color = "⭐"
                                border_color = "#4ECDC4"
                            else:
                                color = "📍"
                                border_color = "#95A5A6"
                            
                            # Create custom styled container
                            st.markdown(f"""
                            <div style="
                                border: 2px solid {border_color}; 
                                border-radius: 10px; 
                                padding: 15px; 
                                margin: 10px 0;
                                background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(248,249,250,0.9));
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            ">
                                <h4 style="margin: 0; color: #2C3E50;">
                                    {color} <strong>{entity['entity']}</strong>
                                    <span style="float: right; font-size: 0.8em; color: #7F8C8D;">
                                        {text.get('influence_score', 'Influence')}: {entity['influence_score']:.1f}
                                    </span>
                                </h4>
                                <p style="margin: 5px 0; color: #7F8C8D; font-style: italic;">
                                    <strong>{text.get('entity_type', 'Type')}:</strong> {entity['type']}
                                </p>
                                {f'<p style="margin: 5px 0; color: #5D6D7E; font-size: 0.9em;">{entity["description"]}</p>' if entity.get('description') else ''}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Metrics in columns
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric(
                                    text.get("total_connections", "Connections"), 
                                    entity['total_connections']
                                )
                            with col2:
                                st.metric(
                                    text.get("unique_partners", "Partners"), 
                                    entity['unique_partners']
                                )
                            with col3:
                                st.metric(
                                    text.get("relation_diversity", "Rel. Types"), 
                                    entity['relation_diversity']
                                )
                            with col4:
                                st.metric(
                                    text.get("avg_confidence", "Confidence"), 
                                    f"{entity['avg_confidence']:.3f}"
                                )
                            
                            # Show relationship types as tags
                            if entity.get('relation_types'):
                                st.markdown("**" + text.get("relation_types", "Relationship Types") + ":**")
                                relation_tags = " ".join([
                                    f'<span style="background-color: #E8F4FD; color: #1B4F72; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin: 2px;">{rel_type}</span>'
                                    for rel_type in entity['relation_types'][:5]  # Show max 5 types
                                ])
                                if len(entity['relation_types']) > 5:
                                    relation_tags += f' <span style="color: #7F8C8D; font-size: 0.8em;">+{len(entity["relation_types"]) - 5} more</span>'
                                st.markdown(relation_tags, unsafe_allow_html=True)
                            
                            st.markdown("---")
                
                # Add explanatory section
                with st.expander(text.get("most_connected_explanation", "📊 Understanding Most Connected Entities")):
                    st.markdown(text.get("connected_entities_help", """
                    **Influence Score**: Combination of total connections weighted by average confidence
                    - **Total Connections**: How many relationships this entity participates in
                    - **As Source/Target**: Direction of relationships (active vs passive role)
                    - **Unique Partners**: Number of different entities connected to
                    - **Relation Diversity**: Number of different relationship types
                    - **Avg Confidence**: Average AI confidence in entity extraction
                    
                    Entities with high influence scores are typically central concepts, key methodologies, or important research topics in your literature.
                    
                    **Color Coding:**
                    - 🔥 **High Impact** (Score ≥ 10): Core research concepts
                    - ⭐ **Moderate Impact** (Score 5-10): Important supporting concepts  
                    - 📍 **Emerging** (Score < 5): Specific or niche concepts
                    """))
            else:
                st.info(text.get("no_connected_entities", "No connected entities found."))
        st.divider()
        st.subheader(clean_title(text['step5_title']))
        print(f"DEBUG: 可视化检查 - 实体: {len(entities)}, 关系: {len(relations)}")
        if entities and relations:
            print("DEBUG: 开始构建知识图谱可视化")
            try:
                # Build graph with optimization settings
                with st.spinner(text["building_graph"]):
                    builder = KnowledgeGraphBuilder(
                        enable_semantic=enable_semantic,
                        similarity_threshold=similarity_threshold
                    )
                    graph = builder.build_graph(entities, relations)
                    
                    # Filter graph if needed
                    if selected_entity_types or selected_relation_types:
                        graph = builder.filter_graph(
                            min_degree=1,
                            entity_types=selected_entity_types if selected_entity_types else None,
                            relation_types=selected_relation_types if selected_relation_types else None
                        )
                
                # Graph statistics
                stats = builder.get_graph_statistics()
                
                col_graph_stats1, col_graph_stats2, col_graph_stats3 = st.columns(3)
                
                with col_graph_stats1:
                    st.metric(text["graph_nodes"], stats['num_nodes'])
                
                with col_graph_stats2:
                    st.metric(text["graph_edges"], stats['num_edges'])
                
                with col_graph_stats3:
                    st.metric(text["graph_density"], f"{stats['density']:.3f}")
                
                # Visualization options (remove Static Network Plot)
                viz_type = st.radio(
                    text["visualization_type"],
                    options=[text["interactive_network"], text["statistics_dashboard"]],
                    horizontal=True
                )
                visualizer = KnowledgeGraphVisualizer()
                if viz_type == text["interactive_network"]:
                    # Pyvis interactive network
                    with st.spinner(text["creating_visualization"]):
                        net = visualizer.create_pyvis_network(
                            graph, 
                            height="600px", 
                            physics=physics_enabled
                        )
                        # Save to temporary file and display
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                            temp_path = f.name
                            net.save_graph(temp_path)
                        # Read and display HTML
                        with open(temp_path, 'r') as f:
                            html_content = f.read()
                        st.components.v1.html(html_content, height=650)
                        # Cleanup
                        os.unlink(temp_path)
                else:  # Statistics dashboard
                    with st.spinner(text["creating_dashboard"]):
                        dashboard_figs = visualizer.create_statistics_dashboard(graph)
                        for title, fig in dashboard_figs.items():
                            st.plotly_chart(fig, use_container_width=True)
                
                # Export options
                st.subheader(clean_title(text['export_options']))
                
                col_exp1, col_exp2 = st.columns(2)
                
                with col_exp1:
                    if st.button(text["export_graph_data"]):
                        export_path = os.path.join(litmap_folder, f"{selected_project}_graph.gexf")
                        builder.export_graph(export_path, format='gexf')
                        st.success(text["graph_exported"].format(path=export_path))
                
                with col_exp2:
                    if st.button(text["export_visualization"]):
                        net = visualizer.create_pyvis_network(graph, physics=physics_enabled)
                        export_path = os.path.join(litmap_folder, f"{selected_project}_visualization.html")
                        visualizer.export_visualization(net, export_path)
                        st.success(text["visualization_exported"].format(path=export_path))
                
            except Exception as e:
                st.error(f"Visualization error: {e}")
        
        else:
            print(f"DEBUG: 数据不足，无法创建可视化 - 实体: {len(entities)}, 关系: {len(relations)}")
            if len(entities) == 0 and len(relations) == 0:
                st.warning(text["insufficient_data"] + " (没有实体和关系数据)")
            elif len(entities) == 0:
                st.warning(text["insufficient_data"] + " (没有实体数据)")
            elif len(relations) == 0:
                st.warning(text["insufficient_data"] + " (没有关系数据)")
            else:
                st.warning(text["insufficient_data"])
    
    else:
        st.info(text["select_project_and_configure"])
