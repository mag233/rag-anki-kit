import os
import streamlit as st
import pandas as pd
from anki import (
    standardize_query_with_llm_anki,
    generate_anki_cards_llm,
    export_llm_cards_to_csv,
    parse_csv_to_table,
)
from lang_utils import get_text  # 新增

def render_anki_tab(PROJECTS_DIR, lang):
    text = get_text(lang)["anki_tab"]

    st.header(text["header"])

    # 1. 读取所有项目
    projects = [d for d in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, d))]
    if not projects:
        st.warning(text["no_projects"])
        return

    selected_project = st.selectbox(
        text["select_project"],
        options=projects,
        help=text["select_project_help"]
    )
    if not selected_project:
        st.warning(text["please_select_project"])
        return

    project_path = os.path.join(PROJECTS_DIR, selected_project)
    chunks_folder = os.path.join(project_path, "processed", "chunks")
    chroma_db_folder = os.path.join(project_path, "vectorstore", "chroma_db")

    if not (os.path.isdir(chunks_folder) and os.path.isdir(chroma_db_folder)):
        st.warning(text["preprocess_warning"])
        return

    st.info(text["using_llm"])

    col1, col2 = st.columns(2)
    with col1:
        card_type = st.radio(
            text["card_type"],
            [text["qa"], text["cloze"]],
            help=text["card_type_help"]
        ).lower()
        num_cards = st.slider(
            text["num_cards"],
            1, 25, 5,
            help=text["num_cards_help"]
        )
    with col2:
        difficulty = st.select_slider(
            text["difficulty"],
            text["difficulty_options"],
            value=text["difficulty_default"],
            help=text["difficulty_help"]
        )
        detail_level = st.select_slider(
            text["detail_level"],
            text["detail_level_options"],
            value=text["detail_level_default"],
            help=text["detail_level_help"]
        )

    query = st.text_area(
        text["query_input"],
        help=text["query_help"],
        key="anki_query_input"
    )

    # 优化按钮放在输入框下方
    optimize_btn = st.button(
        "✨ " + text.get("optimize_prompt", "Optimize Query"),
        type="secondary",
        help=text.get("optimize_help", "Use AI to optimize your query for better retrieval"),
        key="anki_optimize_btn"
    )

    # 初始化session state
    if 'anki_confirmed_query' not in st.session_state:
        st.session_state['anki_confirmed_query'] = ""
    if 'anki_optimized_query' not in st.session_state:
        st.session_state['anki_optimized_query'] = ""
    if 'anki_is_optimized' not in st.session_state:
        st.session_state['anki_is_optimized'] = False

    # 处理用户输入确认逻辑
    if query and query != st.session_state.get('anki_last_input', ""):
        # 用户输入了新内容，重置状态
        st.session_state['anki_confirmed_query'] = query
        st.session_state['anki_optimized_query'] = ""
        st.session_state['anki_is_optimized'] = False
        st.session_state['anki_last_input'] = query
        print(f"[Anki Query] User confirmed new query: {query}")

    # 处理优化按钮点击
    if optimize_btn and query:
        # 检查是否需要重新优化
        if (st.session_state['anki_optimized_query'] == "" or 
            st.session_state['anki_confirmed_query'] != query):
            
            with st.spinner(text.get("optimizing", "Optimizing query...")):
                print(f"[Anki Prompt] Optimizing query...")
                print(f"[Anki Prompt] Original query: {query}")
                optimized = standardize_query_with_llm_anki(query, optimize=True)
                print(f"[Anki Prompt] Optimized query: {optimized}")
                
                # 更新状态
                st.session_state['anki_confirmed_query'] = query
                st.session_state['anki_optimized_query'] = optimized
                st.session_state['anki_is_optimized'] = True
        else:
            # 使用缓存的优化结果
            st.session_state['anki_is_optimized'] = True

    # 确定最终使用的查询
    if st.session_state['anki_is_optimized'] and st.session_state['anki_optimized_query']:
        std_query = st.session_state['anki_optimized_query']
        display_query = std_query
        query_type = "optimized"
    elif st.session_state['anki_confirmed_query']:
        std_query = st.session_state['anki_confirmed_query']
        display_query = std_query
        query_type = "original"
    else:
        std_query = ""
        display_query = ""
        query_type = ""

    # 显示当前使用的查询
    if display_query:
        if query_type == "optimized":
            st.info(f"✨ **{text.get('optimized_query', 'Optimized Query')}:**\n\n{display_query}")
        else:
            st.info(f"📝 **{text.get('current_query', 'Current Query')}:**\n\n{display_query}")

    col_k, col_rel = st.columns(2)
    with col_k:
        top_k = st.slider(
            text["top_k"],
            min_value=5, max_value=50, value=10,
            help=text["top_k_help"]
        )
    with col_rel:
        relevance_threshold = st.slider(
            text["relevance_threshold"],
            min_value=0.0, max_value=1.1, value=0.85, step=0.01,
            help=text["relevance_threshold_help"]
        )

    if st.button(text["retrieve_chunks"]):
        if not std_query:
            st.warning(text["please_enter_query"])
            return
        # 只显示正在检索的信息，不重复显示query
        with st.spinner(text.get("retrieving", "Retrieving relevant chunks...")):
            from retrieve import initialize_chroma, search
            db = initialize_chroma(chroma_db_folder)
            results = search(std_query, top_k, db, relevance_threshold)
            st.session_state["anki_retrieved_chunks"] = results
        
        st.success(text["chunks_retrieved"].format(n=len(results)))
        if results:
            st.info(text.get("preview_chunks", "Preview of retrieved chunks:"))
            for i, chunk in enumerate(results[:5]):
                st.markdown(text["chunk_id"].format(idx=i+1, src=chunk.get('source', '')))
                st.code(chunk.get("chunk_id", ""))
                st.text(chunk.get("distance", ""))
        else:
            st.info(text["no_chunks_found"])

    if st.button(text["generate_cards"]):
        retrieved_chunks = st.session_state.get("anki_retrieved_chunks", [])
        if not std_query:
            st.warning(text["please_enter_query"])
            return
        if not retrieved_chunks:
            st.warning(text["please_retrieve_chunks"])
            return
        try:
            with st.spinner(text["generating_cards"]):
                llm_response = generate_anki_cards_llm(
                    query=std_query,
                    project_folder=project_path,
                    card_type=card_type,
                    difficulty=difficulty,
                    detail_level=detail_level,
                    num_cards=num_cards,
                    top_k=top_k,
                    relevance_threshold=relevance_threshold,
                    optimize_prompt=True  # 总是使用优化
                )
                st.subheader(text["llm_output"])
                rows = parse_csv_to_table(llm_response)
                
                # 显示调试信息
                with st.expander("🔍 调试信息 (Debug Info)", expanded=False):
                    st.text(f"LLM返回内容长度: {len(llm_response)} 字符")
                    st.text(f"解析出的行数: {len(rows)}")
                    if rows:
                        st.text(f"每行列数: {[len(row) for row in rows]}")
                        for i, row in enumerate(rows[:3]):  # 只显示前3行
                            st.text(f"行 {i+1}: {row}")
                    st.text("原始LLM输出:")
                    st.code(llm_response[:1000] + "..." if len(llm_response) > 1000 else llm_response)
                
                if rows:
                    # 确保表格有正确的列标题
                    if card_type.lower() == "qa" or card_type == text["qa"].lower():
                        headers = [text.get("question", "Question"), text.get("answer", "Answer"), text.get("extra_info", "Extra Info")]
                        
                        # 创建DataFrame以更好地显示表格
                        df_data = []
                        for i, row in enumerate(rows):
                            if len(row) >= 3:
                                df_data.append([row[0], row[1], row[2]])
                            elif len(row) == 2:
                                df_data.append([row[0], row[1], ""])
                            elif len(row) == 1:
                                df_data.append([row[0], "", ""])
                            else:
                                st.warning(f"第 {i+1} 行格式不正确: {row}")
                        
                        if df_data:
                            df = pd.DataFrame(df_data, columns=headers)
                            st.dataframe(df, use_container_width=True)
                            st.success(f"✅ 成功生成 {len(df_data)} 张卡片")
                        else:
                            st.error("无法解析任何有效的卡片数据")
                            st.table(rows)
                    else:
                        # Cloze类型直接显示
                        st.table(rows)
                else:
                    st.error("LLM没有返回有效的CSV格式数据")
                    st.info(text["no_content_preview"])

                st.session_state["anki_llm_response"] = llm_response
        except Exception as e:
            st.error(text["error_generating"].format(err=e))

    llm_response = st.session_state.get("anki_llm_response", "")
    if llm_response:
        if st.button(text["export_csv"]):
            output_path = os.path.join(project_path, "anki_cards")
            os.makedirs(output_path, exist_ok=True)
            csv_path = export_llm_cards_to_csv(llm_response, output_path)
            st.success(text["csv_saved"].format(path=csv_path))
            with open(csv_path, 'r', encoding='utf-8') as f:
                csv_data = f.read()
            st.download_button(
                text["download_cards"],
                csv_data,
                file_name=os.path.basename(csv_path),
                mime='text/csv'
            )
