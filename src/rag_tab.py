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

        # —— 各类数据展示（仪表板） —— 
        st.divider()
        st.markdown(text["status_title"])
        embed_model = os.getenv("EMBED_MODEL", "text-embedding-3-large")
        st.info(text["embed_model"].format(model=embed_model))

        # chunks 数量
        chunk_count = sum(
            len(json.load(open(os.path.join(chunks_dir, fn), "r", encoding="utf-8")))
            for fn in os.listdir(chunks_dir) if fn.endswith("_chunks.json")
        )
        st.info(text["chunk_count"].format(n=chunk_count))

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
        # 语言化“现有”前缀
        if "现有" in text.get("embed_count", "") or "Current" in text.get("embed_count", ""):
            st.info(text["embed_count"].format(n=embed_count))
        else:
            prefix = "现有" if lang == "中文" else "Current "
            st.info(prefix + text["embed_count"].format(n=embed_count))

        prog = (embed_count / chunk_count) if chunk_count else 0.0
        st.progress(prog, text=text["progress_label"])

        # manifest 表格
        st.markdown(text["manifest_title"])
        if os.path.exists(manifest_fp):
            mf = json.load(open(manifest_fp, "r", encoding="utf-8"))
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
        else:
            st.info(text["no_manifest"])

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
        if st.button(text["start_embed"]):
            duplicate_ids = []
            try:
                only = stems if mode.endswith(text["only_new_chunks"]) else None
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
                    create_or_update_embeddings(chunks_dir, db_dir, only_files=only)
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
