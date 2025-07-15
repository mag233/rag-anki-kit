import os
import json
import streamlit as st
from document_processing import process_documents
from retrieve import initialize_chroma, search
from embed import create_or_update_embeddings, generate_embedding
from summarize import summarize_chunks, call_llm_with_prompt
from literature import (
    standardize_query,
    load_all_chunks,
    find_chunk_by_id,
    build_chunk_text,
)
from lang_utils import get_text  # 新增

@st.cache_data(show_spinner=False)
def cached_load_all_chunks(chunks_folder):
    from literature import load_all_chunks
    return load_all_chunks(chunks_folder)

def render_literature_tab(PROJECTS_DIR, lang):
    text = get_text(lang)["literature_tab"]

    st.header(text["header"])

    # Step 1: 项目选择
    st.markdown(text["step1_title"])
    st.info(text["step1_info"])
    projects = [d for d in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, d))]
    selected_project = st.selectbox(
        text["select_project"],
        options=projects,
        key="literature_project"
    )

    if not selected_project:
        st.warning(text["no_project"])
        return

    # 各路径
    project_path = os.path.join(PROJECTS_DIR, selected_project)
    chroma_db_folder = os.path.join(project_path, "vectorstore", "chroma_db")
    chunks_folder = os.path.join(project_path, "processed", "chunks")

    if not os.path.exists(chroma_db_folder):
        st.warning(text["no_db_warning"])
        return

    # 模型选择
    st.markdown("### " + text["select_model"])
    col_model, col_temp = st.columns([2,1])
    with col_temp:
        temperature = st.slider(
            text["temperature"],
            min_value=0.0, max_value=2.0, value=0.7, step=0.1,
            help=text["temp_help"]
        )
    with col_model:
        previous_model = st.session_state.get('selected_model', None)
        model_choice = st.radio(
            text["select_model"],
            options=text["model_options"],
            horizontal=True
        )
        # 当模型改变时，清除之前的优化结果
        if previous_model != model_choice:
            st.session_state['litrev_last_query'] = ""
            st.session_state['litrev_std_query'] = ""
            st.session_state['selected_model'] = model_choice
            print(f"[Model] Model changed from {previous_model} to {model_choice}, clearing cached queries")
        
        # 只在模型确实改变时才打印，避免频繁的日志输出
        # print(f"[Model] Using model: {model_choice}, temperature: {temperature}")

    # Step 2: 输入检索问题
    st.markdown(text["step2_title"])
    st.info(text["step2_info"])

    # 输入框
    query = st.text_input(text["query_input"], key="literature_query_input")
    
    # 优化按钮放在输入框下方
    optimize_btn = st.button(
        "✨ " + text["optimized_prompt"].split(":")[0],
        type="secondary",
        help=text.get("optimize_help", "Use AI to optimize your query for better retrieval"),
        key="lit_optimize_btn"
    )

    # 初始化session state
    if 'litrev_confirmed_query' not in st.session_state:
        st.session_state['litrev_confirmed_query'] = ""
    if 'litrev_optimized_query' not in st.session_state:
        st.session_state['litrev_optimized_query'] = ""
    if 'litrev_is_optimized' not in st.session_state:
        st.session_state['litrev_is_optimized'] = False
    if 'litrev_cached_model' not in st.session_state:
        st.session_state['litrev_cached_model'] = ""

    # 处理用户输入确认逻辑
    if query and query != st.session_state.get('litrev_last_input', ""):
        # 用户输入了新内容，重置状态
        st.session_state['litrev_confirmed_query'] = query
        st.session_state['litrev_optimized_query'] = ""
        st.session_state['litrev_is_optimized'] = False
        st.session_state['litrev_last_input'] = query
        print(f"[Query] User confirmed new query: {query}")

    # 处理优化按钮点击
    if optimize_btn and query:
        cached_model = st.session_state.get('litrev_cached_model', "")
        
        # 检查是否需要重新优化
        if (st.session_state['litrev_optimized_query'] == "" or 
            st.session_state['litrev_confirmed_query'] != query or 
            cached_model != model_choice):
            
            with st.spinner(text["optimizing"]):
                print(f"[Prompt] Optimizing query using {model_choice} model...")
                print(f"[Prompt] Original query: {query}")
                optimized = standardize_query(query, model=model_choice)
                print(f"[Prompt] Optimized query: {optimized}")
                
                # 更新状态
                st.session_state['litrev_confirmed_query'] = query
                st.session_state['litrev_optimized_query'] = optimized
                st.session_state['litrev_is_optimized'] = True
                st.session_state['litrev_cached_model'] = model_choice
        else:
            # 使用缓存的优化结果
            st.session_state['litrev_is_optimized'] = True

    # 确定最终使用的查询
    if st.session_state['litrev_is_optimized'] and st.session_state['litrev_optimized_query']:
        std_query = st.session_state['litrev_optimized_query']
        display_query = std_query
        query_type = "optimized"
    elif st.session_state['litrev_confirmed_query']:
        std_query = st.session_state['litrev_confirmed_query']
        display_query = std_query
        query_type = "original"
    else:
        std_query = ""
        display_query = ""
        query_type = ""

    # 显示当前使用的查询
    if display_query:
        if query_type == "optimized":
            st.info(f"✨ **{text['optimized_prompt'].split(':')[0]} ({model_choice}):**\n\n{display_query}")
        else:
            st.info(f"📝 **{text.get('current_query', 'Current Query')}:**\n\n{display_query}")

    # Step 3: 编辑摘要模板
    st.markdown(text["step3_title"])
    st.info(text["step3_info"])

    col1, col2 = st.columns(2)
    default_template_structured = text["default_structured"]
    default_template_direct = text["default_direct"]

    with col1:
        st.markdown(text["structured_review"])
        template_structured = st.text_area(text["structured_template"], default_template_structured, height=200, key="structured_template")
    with col2:
        st.markdown(text["direct_answer"])
        template_direct = st.text_area(text["direct_template"], default_template_direct, height=200, key="direct_template")

    template_option = st.radio(
        text["choose_template"],
        options=[text["structured"], text["direct"]],
        index=0,
        horizontal=True
    )
    custom_template = template_structured if template_option == text["structured"] else template_direct

    # Step 4: 检索参数设置与检索
    st.markdown(text["step4_title"])
    st.info(text["step4_info"])
    relevance_threshold = st.slider(
        text["relevance_threshold"],
        min_value=0.0, max_value=1.1, value=0.85, step=0.01,
        help=text["relevance_help"]
    )
    num_chunks = st.slider(text["num_chunks"], min_value=5, max_value=50, value=15)

    # 确保retrieval按键始终显示，只要有查询内容
    run_retrieval_btn = st.button(text["run_retrieval"], disabled=not std_query)
    
    if std_query and run_retrieval_btn:
        st.info(text["retrieving"])
        print(f"[INFO] search params: query={std_query}, top_k={num_chunks}, db={chroma_db_folder}, relevance_threshold={relevance_threshold}")
        db = initialize_chroma(chroma_db_folder)
        results = search(std_query, num_chunks, db, relevance_threshold)
        print(f"[INFO] search returned {len(results)} results")
        st.success(text["chunks_found"].format(n=len(results)))
        all_chunks = cached_load_all_chunks(chunks_folder)
        chunk_texts = []
        for result in results:
            chunk_id = result["chunk_id"]
            entry = find_chunk_by_id(all_chunks, chunk_id)
            if entry:
                chunk_texts.append(build_chunk_text(entry))
            else:
                chunk_texts.append({
                    "chunk_id": chunk_id,
                    "chunk_text": "[Not found]" if lang == "English" else "未找到",
                    "source": "unknown" if lang == "English" else "未知",
                    "doi": "",
                    "title": "",
                    "author": "",
                    "journal": "",
                    "year": "",
                    "keywords": ""
                })
        st.session_state.chunks = chunk_texts

    # Step 5: 生成摘要
    st.markdown(text["step5_title"])
    st.info(text["step5_info"])
    
    # tokens setting only
    max_tokens = st.number_input(
        text["max_tokens"],
        min_value=500, max_value=128000, value=3000, step=500,
        help=text["max_tokens_help"]
    )
    log_metrics = st.checkbox(text["log_metrics"])
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    if 'chunks' in st.session_state and st.button(text["generate_summary"]):
        chunks = st.session_state.chunks
        if chunks:
            st.info(text["summarizing"])
            dynamic_template = custom_template.format(context="{context}", query=std_query)
            basic_prompt = text["basic_prompt"].format(context="{context}", query=std_query, delimiter="#####")
            final_prompt = basic_prompt + dynamic_template
            summary, processing_time, token_consumption = summarize_chunks(
                chunks, final_prompt, model=model_choice, api_key=api_key,
                max_tokens=max_tokens, base_url=base_url, log_metrics=log_metrics, temperature=temperature
            )
            if summary:
                st.write(summary)
                if log_metrics:
                    st.write(text["show_time"].format(time=processing_time))
                    st.write(text["show_tokens"].format(tokens=token_consumption))
            else:
                st.warning(text["summary_fail"])
        else:
            st.warning(text["no_chunks"])
