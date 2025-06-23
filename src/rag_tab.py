# rag_tab.py
import os
import json
import streamlit as st
from preprocess import process_documents
from embed import create_or_update_embeddings
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
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
            st.rerun()

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
        # 只在本次上传动作（即ups变化时且有新文件写入时）查重和提示，不在刷新或其它动作时重复提示
        last_uploaded_files = st.session_state.get('last_uploaded_files', [])
        current_upload_names = [f.name for f in ups] if ups else []
        # 只有当上传文件列表发生变化且有新文件写入时才处理上传逻辑
        if ups and current_upload_names != last_uploaded_files:
            exist = set(os.listdir(raw_dir))
            uploaded_names = set()
            actually_uploaded = False
            for f in ups:
                if f.name in exist and f.name not in last_uploaded_files:
                    # 只对本次新上传且已存在的文件提示
                    st.warning(text["already_exists"].format(name=f.name))
                elif f.name not in exist and f.name not in uploaded_names:
                    with open(os.path.join(raw_dir, f.name), "wb") as fw:
                        fw.write(f.getbuffer())
                    new_files.append(f.name)
                    uploaded_names.add(f.name)
                    actually_uploaded = True
            st.session_state['last_uploaded_files'] = current_upload_names
            if new_files:
                st.success(text["upload_success"].format(files=", ".join(new_files)))
            elif not actually_uploaded:
                # 没有新文件写入且没有新冲突，不提示任何内容
                pass
            else:
                st.info(text["no_new_file"])
        elif not ups:
            st.session_state['last_uploaded_files'] = []
            st.caption(text["please_upload"])
        # 如果有文件但不是新上传，什么都不提示

        # —— 各类数据展示（仪表板） —— 
        st.divider()
        st.markdown(text["status_title"])
        embed_model = os.getenv("EMBED_MODEL", "text-embedding-3-large")
        st.info(text["embed_model"].format(model=embed_model))

        # 刷新按钮
        if st.button("🔄 " + text.get("refresh_stats", "Refresh Status"), key="refresh_stats_btn"):
            st.rerun()

        # chunks 数量
        chunk_count = sum(
            len(json.load(open(os.path.join(chunks_dir, fn), "r", encoding="utf-8")))
            for fn in os.listdir(chunks_dir) if fn.endswith("_chunks.json")
        )
        st.metric(text.get("chunk_count_metric", "Chunk Count"), chunk_count)

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
        st.metric(text.get("embed_count_metric", "Embedding Count"), embed_count)

        # 进度条
        prog = (embed_count / chunk_count) if chunk_count else 0.0
        st.progress(prog, text=text["progress_label"])

        # manifest 表格（已移除，避免与健康检查重复）
        # st.markdown(text["manifest_title"])
        # if os.path.exists(manifest_fp):
        #     mf = json.load(open(manifest_fp, "r", encoding="utf-8"))
        #     rows = []
        #     for fn, m in mf.items():
        #         stem = os.path.splitext(fn)[0]
        #         rows.append({
        #             text["manifest_col_file"]: fn,
        #             text["manifest_col_nchunks"]: m.get("n_chunks", "-"),
        #             text["manifest_col_chunkmethod"]: m.get("chunk_method", "-"),
        #             text["manifest_col_last"]: m.get("last_processed", "-")
        #         })
        #     st.dataframe(
        #         rows,
        #         hide_index=True,
        #         use_container_width=True,
        #         height=350
        #     )
        # else:
        #     st.info(text["no_manifest"])

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
        mode = st.radio(text["embed_mode"], text["embed_modes"], index=0)
        stems = {os.path.splitext(f)[0] for f in new_files}
        embed_status_placeholder = st.empty()
        embed_progress_placeholder = st.empty()
        if st.button(text["start_embed"]):
            duplicate_ids = []
            try:
                # 选项逻辑修正：
                only = None
                if mode == text["embed_modes"][1]:  # Only new chunks
                    try:
                        db = Chroma(
                            persist_directory=db_dir,
                            embedding_function=OpenAIEmbeddings(model=embed_model),
                            collection_name="literature_chunks"
                        )
                        existing_ids = set(db._collection.get()["ids"])
                    except Exception as e:
                        embed_status_placeholder.error(f"[Chroma Error] {e}")
                        embed_progress_placeholder.empty()
                        return
                    import glob
                    import json as _json
                    import os as _os
                    only = set()
                    for fn in glob.glob(_os.path.join(chunks_dir, "*_chunks.json")):
                        with open(fn, "r", encoding="utf-8") as f:
                            arr = _json.load(f)
                        if any(c.get("chunk_id", "") not in existing_ids for c in arr if c.get("chunk_id", "")):
                            only.add(os.path.splitext(os.path.basename(fn))[0])
                    if not only:
                        embed_status_placeholder.info(text.get("no_new_chunks_to_embed", "No new chunks to embed."))
                        embed_progress_placeholder.empty()
                        return
                # UI: 显示处理中
                with embed_status_placeholder.container():
                    st.info(text.get("embedding_in_progress", "Embedding in progress..."))
                try:
                    import glob
                    import json as _json
                    import os as _os
                    filtered = []
                    # 只处理需要的文件
                    chunk_files = list(glob.glob(_os.path.join(chunks_dir, "*_chunks.json")))
                    if only is not None:
                        # 修正：确保不会出现双 _chunks 后缀
                        chunk_files = [
                            os.path.join(chunks_dir, (fn[:-7] if fn.endswith('_chunks') else fn) + "_chunks.json")
                            for fn in only
                        ]
                    total_files = len(chunk_files)
                    if total_files == 0:
                        embed_progress_placeholder.empty()
                        embed_status_placeholder.info(text.get("no_new_chunks_to_embed", "No new chunks to embed."))
                        return
                    for idx, fn in enumerate(chunk_files):
                        try:
                            with open(fn, "r", encoding="utf-8") as f:
                                arr = _json.load(f)
                            arr = [c for c in arr if c.get("chunk_id", "").strip()]
                            if len(arr) == 0:
                                continue
                            with open(fn, "w", encoding="utf-8") as f:
                                _json.dump(arr, f, ensure_ascii=False, indent=2)
                            filtered.append(fn)
                            embed_progress_placeholder.progress((idx+1)/total_files, text=f"{idx+1}/{total_files} {os.path.basename(fn)}")
                        except Exception as file_e:
                            embed_status_placeholder.error(f"[File Error] {fn}: {file_e}")
                    try:
                        create_or_update_embeddings(chunks_dir, db_dir, only_files=only)
                        embed_progress_placeholder.empty()
                        embed_status_placeholder.success(text["embed_success"])
                    except Exception as embed_e:
                        embed_progress_placeholder.empty()
                        embed_status_placeholder.error(f"[Embedding Error] {embed_e}")
                except ValueError as ve:
                    embed_progress_placeholder.empty()
                    msg = str(ve)
                    if "Expected IDs to be unique" in msg:
                        import re
                        dup_match = re.findall(r"found duplicates of: ([^ ]+)", msg)
                        duplicate_ids.extend(dup_match)
                        embed_status_placeholder.warning(text["duplicate_ids"].format(ids=", ".join(duplicate_ids)))
                        embed_status_placeholder.info(text["partial_embed"])
                    elif "Empty ID" in msg or "ID must have at least one character" in msg:
                        embed_status_placeholder.error("有分块ID为空，请检查原始文档或分块逻辑。")
                    else:
                        embed_status_placeholder.error(text["embed_fail"].format(err=ve))
                except Exception as e:
                    embed_progress_placeholder.empty()
                    embed_status_placeholder.error(text["embed_fail"].format(err=e))
            except Exception as e:
                embed_progress_placeholder.empty()
                embed_status_placeholder.error(text["embed_fail"].format(err=e))

        # —— Manifest 健康检查 —— 
        st.divider()
        st.markdown(text["manifest_check_title"])
        if os.path.exists(manifest_fp):
            mf = json.load(open(manifest_fp, "r", encoding="utf-8"))
            missing = [k for k, v in mf.items() if v.get("n_chunks", 0) == 0]
            # 只显示manifest独有的详细健康信息，增加embedding状态
            details = []
            # 获取所有embedding的chunk名集合
            try:
                db = Chroma(
                    persist_directory=db_dir,
                    embedding_function=OpenAIEmbeddings(model=embed_model),
                    collection_name="literature_chunks"
                )
                embed_ids = set(db._collection.get()["ids"])
            except:
                embed_ids = set()
            for k, v in mf.items():
                n_chunks = v.get("n_chunks", 0)
                # 判断embedding覆盖率
                if n_chunks and isinstance(n_chunks, int) and n_chunks > 0:
                    # 期望embedding的id前缀为stem
                    stem = os.path.splitext(k)[0]
                    embed_count = len([eid for eid in embed_ids if eid.startswith(stem)])
                    embed_status = f"{embed_count}/{n_chunks} ({embed_count/n_chunks:.0%})" if n_chunks else "-"
                else:
                    embed_status = "-"
                details.append({
                    text["manifest_col_file"]: k,
                    text["manifest_col_chunkmethod"]: v.get("chunk_method", "-"),
                    text["manifest_col_last"]: v.get("last_processed", "-"),
                    "Error": v.get("error", "-"),
                    "Has Chunks": n_chunks > 0,
                    "Embedding Status": embed_status
                })
            st.dataframe(details, hide_index=True, use_container_width=True)
            if missing:
                st.warning(text["missing_chunks"].format(files=", ".join(missing)))
            else:
                st.success(text["all_chunked"])
        else:
            st.info(text["no_manifest"])
