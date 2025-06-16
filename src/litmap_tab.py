"""
LitMap Tab - Knowledge Graph Generation from Research Literature

This module provides a Streamlit interface for building and visualizing
knowledge graphs from research papers using the LitMap feature.
"""

import os
import streamlit as st
import pandas as pd
from typing import Dict, Any, List
import tempfile

# Import LitMap modules
from knowledge_graph import EntityRelationExtractor, KnowledgeGraphBuilder, KnowledgeGraphVisualizer
from knowledge_graph.utils import (
    save_extraction_results, load_extraction_results,
    create_summary_dataframes, filter_by_confidence,
    get_most_connected_entities
)
from literature import load_all_chunks
from lang_utils import get_text


@st.cache_data(show_spinner=False)
def cached_load_all_chunks(chunks_folder):
    """Cached version of load_all_chunks for better performance."""
    return load_all_chunks(chunks_folder)


def render_litmap_tab(PROJECTS_DIR: str, lang: str) -> None:
    """Render the LitMap knowledge graph tab."""
    text = get_text(lang)["litmap_tab"]
    
    st.header(text["header"])
    st.info(text["description"])
    
    # Step 1: 项目选择 (following same pattern as other tabs)
    st.markdown("### " + text["step1_title"])
    st.info(text["step1_info"])
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
    
    # Step 2: 配置设置
    st.markdown("### " + text["step2_title"])
    st.info(text["step2_info"])
    
    with st.expander("❓ " + text["step2_help_title"], expanded=False):
        st.markdown(text["step2_help_content"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_chunks = st.slider(
            text["max_chunks"],
            min_value=5, max_value=100, value=20,
            help=text["max_chunks_help"]
        )
        
        confidence_threshold = st.slider(
            text["confidence_threshold"],
            min_value=0.0, max_value=1.0, value=0.6, step=0.1,
            help=text["confidence_help"]
        )
    
    with col2:
        enable_deduplication = st.checkbox(
            text["enable_deduplication"],
            value=True,
            help=text["deduplication_help"]
        )
        
        physics_enabled = st.checkbox(
            text["physics_enabled"],
            value=True,
            help=text["physics_help"]
        )
    
    # Step 3: 实体和关系类型选择
    st.markdown("### " + text["step3_title"])
    st.info(text["step3_info"])
    
    with st.expander("❓ " + text["step3_help_title"], expanded=False):
        st.markdown(text["step3_help_content"])
    
    # Load configuration for available types
    try:
        extractor = EntityRelationExtractor()
        available_entity_types = extractor.config['ENTITY_TYPES']
        available_relation_types = extractor.config['RELATION_TYPES']
        
        col_entities, col_relations = st.columns(2)
        
        with col_entities:
            selected_entity_types = st.multiselect(
                text["entity_types"],
                options=available_entity_types,
                default=available_entity_types,
                help=text["entity_types_help"]
            )
        
        with col_relations:
            selected_relation_types = st.multiselect(
                text["relation_types"],
                options=available_relation_types,
                default=available_relation_types,
                help=text["relation_types_help"]
            )
    
    except Exception as e:
        st.error(f"Configuration loading error: {e}")
        return
    
    # Step 4: 知识图谱生成
    st.markdown("### " + text["step4_title"])
    st.info(text["step4_info"])
    
    with st.expander("❓ " + text["step4_help_title"], expanded=False):
        st.markdown(text["step4_help_content"])
    
    # Check for existing extraction results
    entities_file = os.path.join(litmap_folder, f"{selected_project}_entities.json")
    relations_file = os.path.join(litmap_folder, f"{selected_project}_relations.json")
    
    has_existing_results = os.path.exists(entities_file) and os.path.exists(relations_file)
    
    if has_existing_results:
        st.success(text["existing_results_found"])
        
        # 显示现有结果信息
        try:
            existing_entities, existing_relations = load_extraction_results(entities_file, relations_file)
            col_exist1, col_exist2 = st.columns(2)
            
            with col_exist1:
                st.metric("已提取实体数", len(existing_entities))
            with col_exist2:
                st.metric("已提取关系数", len(existing_relations))
        except:
            pass
        
        col_load, col_regenerate = st.columns(2)
        
        with col_load:
            load_existing = st.button(
                "📁 " + text["load_existing"],
                type="primary",
                help=text["load_existing_help"]
            )
        
        with col_regenerate:
            regenerate = st.button(
                "🔄 " + text["regenerate"],
                type="secondary",
                help=text["regenerate_help"]
            )
    else:
        load_existing = False
        regenerate = st.button(
            "🚀 " + text["generate_knowledge_graph"],
            type="primary",
            help=text["generate_help"]
        )
    
    # Process chunks and generate/load knowledge graph
    entities, relations = [], []
    
    if load_existing:
        try:
            entities, relations = load_extraction_results(entities_file, relations_file)
            st.success(text["loaded_existing_results"])
        except Exception as e:
            st.error(f"Error loading existing results: {e}")
            return
    
    elif regenerate:
        try:
            # 初始化进度跟踪
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            with status_placeholder.container():
                st.info("🔄 " + text.get("initializing_extraction", "Initializing extraction..."))
            
            # 加载chunks
            all_chunks = cached_load_all_chunks(chunks_folder)
            
            if not all_chunks:
                st.warning(text["no_chunks_found"])
                return
            
            # 限制chunks数量
            process_chunks = all_chunks[:max_chunks] if max_chunks else all_chunks
            
            with status_placeholder.container():
                st.info(f"📚 " + text["processing_chunks"].format(n=len(process_chunks)))
            
            # 初始化extractor
            extractor = EntityRelationExtractor()
            extractor.reset_stats()
            
            # 显示预估信息
            estimated_cost = len(process_chunks) * 0.002  # rough estimate
            with status_placeholder.container():
                st.info(f"📊 预估处理: {len(process_chunks)} 个分块, 大约需要 {len(process_chunks)*2} 分钟, 预估费用 ${estimated_cost:.3f}")
            
            # 定义进度回调函数
            def update_progress(progress_info):
                current = progress_info['current']
                total = progress_info['total']
                chunk_id = progress_info['chunk_id']
                entities_found = progress_info['entities_found']
                relations_found = progress_info['relations_found']
                stats = progress_info['stats']
                
                # 更新进度条
                progress_percentage = current / total
                with progress_placeholder.container():
                    st.progress(progress_percentage, 
                              text=f"处理进度: {current}/{total} ({progress_percentage:.1%})")
                
                # 更新状态信息
                with status_placeholder.container():
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("当前Chunk", f"{current}/{total}")
                        st.text(f"ID: {chunk_id[:15]}...")
                    
                    with col2:
                        st.metric("本次发现", f"实体: {entities_found}")
                        st.text(f"关系: {relations_found}")
                    
                    with col3:
                        st.metric("累计统计", f"实体: {stats['total_entities']}")
                        st.text(f"关系: {stats['total_relations']}")
                    
                    with col4:
                        st.metric("资源消耗", f"API: {stats['total_api_calls']}")
                        st.text(f"Token: {stats['total_tokens_used']}")
                        
                        # 计算实时成本
                        current_cost = stats['total_tokens_used'] * 0.00015 / 1000
                        st.text(f"费用: ${current_cost:.4f}")
            
            # 执行提取
            entities, relations = extractor.extract_from_chunks(
                process_chunks, 
                max_chunks=max_chunks,
                progress_callback=update_progress
            )
            
            # 保存结果
            save_extraction_results(entities, relations, litmap_folder, selected_project)
            
            # 获取最终统计
            final_stats = extractor.get_stats()
            
            # 清除进度显示
            progress_placeholder.empty()
            
            # 显示完成状态
            with status_placeholder.container():
                st.success("✅ " + text["extraction_complete"].format(
                    entities=len(entities), 
                    relations=len(relations)
                ))
                
                # 详细统计报告
                with st.expander("📊 详细处理报告", expanded=True):
                    col_stats1, col_stats2, col_stats3 = st.columns(3)
                    
                    with col_stats1:
                        st.markdown("**📈 处理统计**")
                        st.metric("总Chunks", final_stats['total_chunks'])
                        st.metric("成功处理", final_stats['successful_chunks'])
                        st.metric("处理失败", final_stats['failed_chunks'])
                        success_rate = (final_stats['successful_chunks'] / final_stats['total_chunks'] * 100) if final_stats['total_chunks'] > 0 else 0
                        st.metric("成功率", f"{success_rate:.1f}%")
                    
                    with col_stats2:
                        st.markdown("**🎯 提取结果**")
                        st.metric("实体总数", final_stats['total_entities'])
                        st.metric("关系总数", final_stats['total_relations'])
                        avg_entities = final_stats['total_entities'] / final_stats['successful_chunks'] if final_stats['successful_chunks'] > 0 else 0
                        st.metric("平均实体/Chunk", f"{avg_entities:.1f}")
                    
                    with col_stats3:
                        st.markdown("**💰 资源消耗**")
                        st.metric("API调用次数", final_stats['total_api_calls'])
                        st.metric("Token消耗", final_stats['total_tokens_used'])
                        st.metric("处理时间", f"{final_stats['processing_time']:.1f}秒")
                        
                        # 估算成本（基于GPT-4o-mini价格）
                        input_cost = final_stats['total_tokens_used'] * 0.00015 / 1000  # $0.15/1M tokens
                        st.metric("估算成本", f"${input_cost:.4f}")
                    
                    # 错误报告
                    if final_stats['errors']:
                        st.markdown("**⚠️ 错误报告**")
                        error_expander = st.expander(f"查看 {len(final_stats['errors'])} 个错误")
                        with error_expander:
                            for i, error in enumerate(final_stats['errors'][:10]):  # 只显示前10个错误
                                st.text(f"{i+1}. {error}")
                            if len(final_stats['errors']) > 10:
                                st.text(f"... 还有 {len(final_stats['errors']) - 10} 个错误")
        
        except Exception as e:
            st.error(f"❌ 提取过程发生错误: {e}")
            return
    
    # Display results if we have them
    if entities or relations:
        
        # Apply confidence filtering
        if confidence_threshold > 0:
            filtered_entities, filtered_relations = filter_by_confidence(
                entities, relations, confidence_threshold
            )
        else:
            filtered_entities, filtered_relations = entities, relations
        
        # Create summary statistics
        st.markdown("### " + text["step5_title"])
        
        col_stats1, col_stats2 = st.columns(2)
        
        with col_stats1:
            st.metric(text["total_entities"], len(filtered_entities))
            st.metric(text["total_relations"], len(filtered_relations))
        
        with col_stats2:
            if entities:
                avg_entity_confidence = sum(e.get('confidence', 0) for e in filtered_entities) / len(filtered_entities)
                st.metric(text["avg_entity_confidence"], f"{avg_entity_confidence:.3f}")
            
            if relations:
                avg_relation_confidence = sum(r.get('confidence', 0) for r in filtered_relations) / len(filtered_relations)
                st.metric(text["avg_relation_confidence"], f"{avg_relation_confidence:.3f}")
        
        # Summary tables
        summary_dfs = create_summary_dataframes(filtered_entities, filtered_relations)
        
        col_table1, col_table2 = st.columns(2)
        
        with col_table1:
            st.markdown("#### " + text["entity_summary"])
            if not summary_dfs['entities'].empty:
                st.dataframe(summary_dfs['entities'], use_container_width=True)
            else:
                st.info(text["no_entities"])
        
        with col_table2:
            st.markdown("#### " + text["relation_summary"])
            if not summary_dfs['relations'].empty:
                st.dataframe(summary_dfs['relations'], use_container_width=True)
            else:
                st.info(text["no_relations"])
        
        # Most connected entities
        if filtered_relations:
            st.markdown("#### " + text["most_connected"])
            connected_entities = get_most_connected_entities(filtered_relations, top_n=10)
            connected_df = pd.DataFrame(connected_entities)
            st.dataframe(connected_df, use_container_width=True)
        
        # Step 6: 知识图谱可视化
        st.markdown("### " + text["step6_title"])
        
        if filtered_entities and filtered_relations:
            try:
                # Build graph
                with st.spinner(text["building_graph"]):
                    builder = KnowledgeGraphBuilder()
                    graph = builder.build_graph(filtered_entities, filtered_relations)
                    
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
                
                # Visualization options
                viz_type = st.radio(
                    text["visualization_type"],
                    options=[text["interactive_network"], text["static_plotly"], text["statistics_dashboard"]],
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
                
                elif viz_type == text["static_plotly"]:
                    # Plotly static network  
                    with st.spinner(text["creating_visualization"]):
                        fig = visualizer.create_plotly_network(graph, layout='spring')
                        st.plotly_chart(fig, use_container_width=True)
                
                else:  # Statistics dashboard
                    with st.spinner(text["creating_dashboard"]):
                        dashboard_figs = visualizer.create_statistics_dashboard(graph)
                        
                        for title, fig in dashboard_figs.items():
                            st.plotly_chart(fig, use_container_width=True)
                
                # Export options
                st.markdown("### " + text["export_options"])
                
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
            st.warning(text["insufficient_data"])
    
    else:
        st.info(text["select_project_and_configure"])
