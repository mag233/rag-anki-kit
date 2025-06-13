# rag_tab.py
import os
import json
import streamlit as st
from preprocess import process_documents
from embed import create_or_update_embeddings
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from lang_utils import get_text  # 新增

def render_rag_tab(PROJECTS_DIR, lang):
    text = get_text(lang)["rag_tab"]

    st.header(text["header"])

    # —— 项目选择与新建 —— 
    projects = [d for d in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, d))]
    idx = 1 if projects else 0
    selected = st.selectbox(text["select_project"], [text["new_project"]] + projects, index=idx, key="rag_project")

    if selected == text["new_project"]:
        nm = st.text_input(text["project_name_placeholder"])
        if st.button(text["create_btn"]) and nm:
            p = os.path.join(PROJECTS_DIR, nm)
            os.makedirs(os.path.join(p, "raw_pdfs"), exist_ok=True)
            os.makedirs(os.path.join(p, "processed", "chunks"), exist_ok=True)
            os.makedirs(os.path.join(p, "vectorstore", "chroma_db"), exist_ok=True)
            st.success(text["success"].format(name=nm))
            st.experimental_rerun()

    # 确保有已选项目
    if selected and selected != text["new_project"]:
        # 路径
        base        = os.path.join(PROJECTS_DIR, selected)
        raw_dir     = os.path.join(base, "raw_pdfs")
        proc_dir    = os.path.join(base, "processed")
        chunks_dir  = os.path.join(proc_dir, "chunks")
        db_dir      = os.path.join(base, "vectorstore", "chroma_db")
        manifest_fp = os.path.join(proc_dir, "manifest.json")

        for d in [raw_dir, chunks_dir, db_dir]:
            os.makedirs(d, exist_ok=True)

        # —— 步骤1：上传文件 —— 
        st.markdown(text["step1_title"])
        ups = st.file_uploader(
            text["uploader_label"],
            type=["pdf","md","markdown","text","txt","docx","xlsx","html"], accept_multiple_files=True
        )
        new_files = []
        if ups:
            exist = set(os.listdir(raw_dir))
            for f in ups:
                if f.name in exist:
                    st.warning(text["already_exists"].format(name=f.name))
                else:
                    with open(os.path.join(raw_dir, f.name), "wb") as fw:
                        fw.write(f.getbuffer())
                    new_files.append(f.name)
            if new_files:
                st.success(text["upload_success"].format(files=", ".join(new_files)))
            else:
                st.info(text["no_new_file"])
        else:
            st.caption(text["please_upload"])

        # —— 嵌入数据库概览 ——
        st.divider()
        
        # Header with aligned refresh button
        header_col1, header_col2 = st.columns([4, 1])
        with header_col1:
            st.markdown(f"### 📊 {text['db_overview']}")
        with header_col2:
            refresh_clicked = st.button(
                "🔄", 
                help=text["refresh_stats"],
                key="refresh_db_stats"
            )
        
        # Get embedding model and counts
        embed_model = os.getenv("EMBED_MODEL", "text-embedding-3-large")
        
        # chunks 数量
        chunk_count = sum(
            len(json.load(open(os.path.join(chunks_dir, fn), "r", encoding="utf-8")))
            for fn in os.listdir(chunks_dir) if fn.endswith("_chunks.json")
        )
        
        # embeddings 数量
        try:
            db = Chroma(
                persist_directory=db_dir,
                embedding_function=OpenAIEmbeddings(model=embed_model),
                collection_name="literature_chunks"
            )
            embed_count = len([i for i in db._collection.get()["ids"] if i and len(i) > 0])  # 过滤空ID
        except:
            embed_count = 0
        
        # Get advanced stats if refresh clicked or cached
        if refresh_clicked:
            try:
                from embed import get_database_stats
                stats = get_database_stats(db_dir)
                st.session_state.db_stats = stats
            except Exception as e:
                st.error(f"{text['stats_error']} {e}")
        
        # Display embedding model at the top
        st.markdown(
            f'<p style="font-size: 14px; color: #6b7280; margin: 0;">{text["embedding_model"]}</p>'
            f'<p style="font-size: 16px; font-weight: 600; color: #111827; margin: 0 0 16px 0;">{embed_model}</p>',
            unsafe_allow_html=True
        )
        
        # Main metrics in 3-column layout
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.markdown(
                f'<p style="font-size: 14px; color: #6b7280; margin: 0;">{text["total_chunks"]}</p>'
                f'<p style="font-size: 32px; font-weight: bold; color: #111827; margin: 0; line-height: 1;">{chunk_count:,}</p>',
                unsafe_allow_html=True
            )
        
        with metric_col2:
            st.markdown(
                f'<p style="font-size: 14px; color: #6b7280; margin: 0;">{text["embedded_chunks"]}</p>'
                f'<p style="font-size: 32px; font-weight: bold; color: #111827; margin: 0; line-height: 1;">{embed_count:,}</p>',
                unsafe_allow_html=True
            )
        
        with metric_col3:
            # Get document count from stats if available, otherwise calculate from manifest
            doc_count = 0
            if hasattr(st.session_state, 'db_stats') and st.session_state.db_stats:
                doc_count = st.session_state.db_stats.get('unique_documents', 0)
            elif os.path.exists(manifest_fp):
                mf = json.load(open(manifest_fp, "r", encoding="utf-8"))
                doc_count = len(mf)
            
            st.markdown(
                f'<p style="font-size: 14px; color: #6b7280; margin: 0;">{text["document_count"]}</p>'
                f'<p style="font-size: 32px; font-weight: bold; color: #111827; margin: 0; line-height: 1;">{doc_count:,}</p>',
                unsafe_allow_html=True
            )
        
        # Progress bar
        progress_value = (embed_count / chunk_count) if chunk_count else 0.0
        progress_text = f"{embed_count}/{chunk_count} " + text["chunks_embedded"]
        st.progress(progress_value, text=progress_text)
        
        # Expandable details section
        if hasattr(st.session_state, 'db_stats') and st.session_state.db_stats:
            stats = st.session_state.db_stats
            with st.expander(text["details"], expanded=False):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown(
                        f'<p style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">{text["last_updated"]}</p>'
                        f'<p style="font-size: 13px; color: #374151; margin: 0 0 12px 0;">{stats.get("last_updated", "N/A")}</p>'
                        f'<p style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">{text["avg_content_length"]}</p>'
                        f'<p style="font-size: 13px; color: #374151; margin: 0;">{stats.get("avg_content_length", 0):.0f} chars</p>',
                        unsafe_allow_html=True
                    )
                
                with detail_col2:
                    dedup_status = text["dedup_enabled"] if stats.get('has_hashes', False) else text["dedup_disabled"]
                    st.markdown(
                        f'<p style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">{text["dedup_status"]}</p>'
                        f'<p style="font-size: 13px; color: #374151; margin: 0;">{dedup_status}</p>',
                        unsafe_allow_html=True
                    )

        # Database Operations Section
        st.markdown("---")
        st.markdown(f"#### 🔧 {text['db_operations']}")
        
        # Operations in 2-column layout
        op_col1, op_col2 = st.columns(2)
        
        with op_col1:
            # Health Check
            if st.button(
                f"🏥 {text['db_health_check']}",
                help=text["check_db"],
                use_container_width=True
            ):
                try:
                    db = Chroma(
                        persist_directory=db_dir,
                        embedding_function=OpenAIEmbeddings(model=embed_model),
                        collection_name="literature_chunks"
                    )
                    collection_info = db._collection.get()
                    total_embeddings = len(collection_info.get("ids", []))
                    st.success(f"{text['db_healthy']} {total_embeddings} {text['db_healthy_embeddings']}")
                except Exception as e:
                    st.error(f"{text['db_connection_failed']} {e}")
            
            # Remove Duplicates
            if st.button(
                f"🧹 {text['remove_duplicates']}",
                help=text["remove_duplicates_help"],
                use_container_width=True
            ):
                try:
                    from embed import remove_duplicates
                    removed_count = remove_duplicates(db_dir)
                    if removed_count > 0:
                        st.success(f"{text['duplicates_removed']} {removed_count} {text['duplicates_count']}")
                        # Clear cached stats to force refresh
                        if hasattr(st.session_state, 'db_stats'):
                            del st.session_state.db_stats
                    else:
                        st.info(text["no_duplicates"])
                except Exception as e:
                    st.error(f"{text['remove_duplicates_failed']} {e}")
        
        with op_col2:
            # Danger Zone - Clear All
            st.markdown(
                f"<div style='background: #fee2e2; border: 1px solid #fecaca; border-radius: 8px; padding: 12px;'>"
                f"<h5 style='color: #dc2626; margin: 0 0 8px 0;'>⚠️ {text['danger_zone']}</h5>"
                f"<p style='font-size: 13px; color: #7f1d1d; margin: 0 0 12px 0;'>{text['irreversible_warning']}</p>",
                unsafe_allow_html=True
            )
            
            # Confirmation checkbox
            confirm_clear = st.checkbox(
                text["confirm_clear_all"],
                key="confirm_clear_all"
            )
            
            # Clear All button
            clear_all_disabled = not confirm_clear
            if st.button(
                f"🗑️ {text['clear_all_embeddings']}",
                help=text["clear_all_help"],
                disabled=clear_all_disabled,
                use_container_width=True
            ):
                if confirm_clear:
                    try:
                        from embed import clear_all_embeddings
                        success = clear_all_embeddings(db_dir, confirm=True)
                        if success:
                            st.success(text["clear_success"])
                            # Clear cached stats
                            if hasattr(st.session_state, 'db_stats'):
                                del st.session_state.db_stats
                            # Reset confirmation
                            st.session_state.confirm_clear_all = False
                        else:
                            st.error(text["clear_failed"])
                    except Exception as e:
                        st.error(f"{text['clear_failed_error']} {e}")
            
            st.markdown("</div>", unsafe_allow_html=True)

        # —— 步骤2：预处理文件（分块） —— 
        st.divider()
        st.markdown(text["step2_title"])

        method = st.selectbox(text["chunk_method"], text["chunk_methods"], index=0)
        if method == text["chunk_length"]:
            size = st.number_input(text["chunk_length_label"], min_value=50, max_value=2000, value=400, step=50)
        else:
            size = None

        force = st.checkbox(
            text["force_reprocess"], value=False
        )

        if st.button(text["start_preprocess"]):
            try:
                process_documents(
                    raw_dir,
                    proc_dir,
                    extract_tables=True,
                    extract_images=True,
                    extract_meta=True,
                    chunking_method=method,
                    chunk_size=size or 400,
                    chunk_overlap=50,
                    force_reprocess=force
                )
                st.success(text["preprocess_success"])
                # 刷新
                if os.path.exists(manifest_fp):
                    mf = json.load(open(manifest_fp, "r", encoding="utf-8"))
                else:
                    mf = {}
                chunk_count = sum(
                    len(json.load(open(os.path.join(chunks_dir, fn), "r", encoding="utf-8")))
                    for fn in os.listdir(chunks_dir) if fn.endswith("_chunks.json")
                )
                try:
                    db = Chroma(
                        persist_directory=db_dir,
                        embedding_function=OpenAIEmbeddings(model=embed_model),
                        collection_name="literature_chunks"
                    )
                    embed_count = len(db._collection.get()["ids"])
                except:
                    embed_count = 0
                st.info(text["chunk_count"].format(n=chunk_count))
                st.info(text["embed_count"].format(n=embed_count))
                prog = (embed_count / chunk_count) if chunk_count else 0.0
                st.progress(prog, text=text["progress_label"])
                # manifest 表
                rows = []
                for fn, m in mf.items():
                    stem = os.path.splitext(fn)[0]
                    rows.append({
                        text["manifest_col_file"]: fn,
                        text["manifest_col_nchunks"]: m.get("n_chunks", "-"),
                        text["manifest_col_chunkmethod"]: m.get("chunk_method", "-"),
                        text["manifest_col_last"]: m.get("last_processed", "-")
                    })
                st.dataframe(
                    rows,
                    hide_index=True,
                    use_container_width=True,
                    height=350
                )
            except Exception as e:
                st.error(text["preprocess_fail"].format(err=e))

        # —— 步骤3：生成/更新嵌入 —— 
        st.divider()
        st.markdown(text["step3_title"])
        
        # 嵌入模式选择，增加更详细的说明
        mode = st.radio(
            text["embed_mode"], 
            text["embed_modes"], 
            index=0,
            help=text["mode_help_only_new"] if text["embed_modes"][0].endswith(("new chunks", "新增分块")) else text["mode_help_embed_all"]
        )
        
        # 高级选项
        with st.expander(f"🔧 {text['advanced_options']}", expanded=False):
            force_reprocess = st.checkbox(
                text["force_reprocess_embed"],
                value=False,
                help=text["force_reprocess_embed_help"]
            )
            enable_deduplication = st.checkbox(
                text["enable_deduplication"],
                value=True,
                help=text["enable_deduplication_help"]
            )
        
        stems = {os.path.splitext(f)[0] for f in new_files}
        
        # 显示当前状态信息
        col1, col2 = st.columns([2, 1])
        with col1:
            start_embed_clicked = st.button(text["start_embed"])
        
        with col2:
            # 显示实时状态
            pending_chunks = max(0, chunk_count - embed_count)
            if pending_chunks > 0:
                st.warning(f"{text['pending_embed']} {pending_chunks}")
            else:
                st.success(f"{text['complete_embed']} ✅")
        
        if start_embed_clicked:
            duplicate_ids = []
            try:
                # 确定处理模式
                if mode.endswith(text["only_new_chunks"]):
                    # "仅新增分块"模式：处理当前会话上传的文件，如果没有则智能检测需要嵌入的文件
                    actual_force_reprocess = force_reprocess  # 使用用户设置的强制重新处理选项
                    if stems:
                        only = stems
                        st.info(f"{text['processing_session_files']} {', '.join(stems)}")
                    else:
                        # 如果没有新上传文件，智能检测需要嵌入的chunk
                        st.info(text["auto_detect_chunks"])
                        only = None  # 让embedding函数的增量逻辑处理
                else:
                    # "全部重新生成"模式：处理所有文件，强制重新处理所有分块
                    only = None
                    actual_force_reprocess = True  # 全部重新生成模式自动启用强制重新处理
                    st.info(text["processing_all_chunks"])
                
                try:
                    # 过滤掉空ID的chunk文件
                    import glob
                    import json as _json
                    import os as _os
                    filtered = []
                    for fn in glob.glob(_os.path.join(chunks_dir, "*_chunks.json")):
                        with open(fn, "r", encoding="utf-8") as f:
                            arr = _json.load(f)
                        arr = [c for c in arr if c.get("chunk_id", "").strip()]
                        if len(arr) == 0:
                            continue
                        with open(fn, "w", encoding="utf-8") as f:
                            _json.dump(arr, f, ensure_ascii=False, indent=2)
                        filtered.append(fn)
                    create_or_update_embeddings(
                        chunks_dir, 
                        db_dir, 
                        only_files=only,
                        force_reprocess=actual_force_reprocess,
                        enable_deduplication=enable_deduplication
                    )
                    st.success(text["embed_success"])
                except ValueError as ve:
                    msg = str(ve)
                    if "Expected IDs to be unique" in msg:
                        import re
                        dup_match = re.findall(r"found duplicates of: ([^ ]+)", msg)
                        duplicate_ids.extend(dup_match)
                        st.warning(text["duplicate_ids"].format(ids=", ".join(duplicate_ids)))
                        st.info(text["partial_embed"])
                    elif "Empty ID" in msg or "ID must have at least one character" in msg:
                        st.error("有分块ID为空，请检查原始文档或分块逻辑。")
                    else:
                        st.error(text["embed_fail"].format(err=ve))
                except Exception as e:
                    st.error(text["embed_fail"].format(err=e))
            except Exception as e:
                st.error(text["embed_fail"].format(err=e))

        # —— Manifest 健康检查 —— 
        st.divider()
        st.markdown(text["manifest_check_title"])
        if os.path.exists(manifest_fp):
            mf = json.load(open(manifest_fp, "r", encoding="utf-8"))
            missing = [k for k, v in mf.items() if v.get("n_chunks", 0) == 0]
            if missing:
                st.warning(text["missing_chunks"].format(files=", ".join(missing)))
            else:
                st.success(text["all_chunked"])
