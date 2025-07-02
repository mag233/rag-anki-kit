"""
Knowledge Graph Visualizer

This module creates interactive visualizations of knowledge graphs
using Pyvis, Plotly, and other visualization libraries.
"""

import networkx as nx
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from pyvis.network import Network
import pandas as pd
from collections import defaultdict
import math


class KnowledgeGraphVisualizer:
    """Creates interactive visualizations of knowledge graphs."""
    
    def __init__(self, config_path: str = None):
        """Initialize the visualizer with configuration."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def create_pyvis_network(self, graph: nx.MultiDiGraph,
                           height: str = "600px",
                           width: str = "100%",
                           physics: bool = True) -> Network:
        """
        Create interactive Pyvis network visualization.
        
        Args:
            graph: NetworkX graph to visualize
            height: HTML height of the visualization
            width: HTML width of the visualization  
            physics: Enable physics simulation
            
        Returns:
            Pyvis Network object
        """
        net = Network(height=height, width=width, directed=True)
        # --- 强制 vis.js 使用自定义 tooltip 而不是浏览器原生 title ---
        net.set_options("""
        var options = {
          "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "dragNodes": true,
            "navigationButtons": true,
            "keyboard": true
          },
          "nodes": {
            "shape": "dot",
            "font": { "multi": true }
          },
          "physics": {
            "enabled": %s,
            "stabilization": {"iterations": 100},
            "barnesHut": {
              "gravitationalConstant": -30000,
              "centralGravity": 0.2,
              "springLength": 180,
              "springConstant": 0.04,
              "damping": 0.09,
              "avoidOverlap": 1
            }
          },
          "edges": {
            "smooth": {
              "type": "dynamic"
            },
            "arrows": {
              "to": {"enabled": true, "scaleFactor": 1.2}
            }
          },
          "manipulation": false,
          "layout": {
            "improvedLayout": true
          },
          "fullscreen": {
            "enabled": true,
            "button": true
          }
        }
        """ % ("true" if physics else "false"))
        
        # Node colors from config
        node_colors = self.config['VISUALIZATION']['node_colors']
        edge_colors = self.config['VISUALIZATION']['edge_colors']
        
        # Add nodes
        for node, data in graph.nodes(data=True):
            node_type = data.get('node_type', 'concept')
            color = node_colors.get(node_type, '#95A5A6')
            degree = graph.degree(node)
            size = max(10, min(50, 10 + degree * 3))
            # 简洁tooltip：只显示置信度和DOI（如有），不显示label/type/degree/description/source_papers
            tooltip_parts = []
            if 'confidence' in data:
                tooltip_parts.append(f"Confidence: {data['confidence']:.2f}")
            if data.get('doi'):
                tooltip_parts.append(f"DOI: {data['doi']}")
            title = " | ".join(tooltip_parts) if tooltip_parts else ""
            net.add_node(
                node,
                label=node,
                color=color,
                size=size,
                title=title,
                type=node_type
            )
        
        # Add edges
        for u, v, data in graph.edges(data=True):
            relation = data.get('relation', 'relates_to')
            color = edge_colors.get(relation, '#95A5A6')
            # 边tooltip只显示关系类型
            net.add_edge(
                u, v,
                label=relation,
                color=color,
                title=relation
            )
        
        return net
    
    def create_plotly_network(self, graph: nx.MultiDiGraph,
                            layout: str = 'spring', 
                            node_font_size: int = 14, 
                            node_spacing: int = 200, 
                            show_labels: bool = True) -> go.Figure:
        """
        Create Plotly network visualization.
        
        Args:
            graph: NetworkX graph to visualize
            layout: Layout algorithm ('spring', 'circular', 'kamada_kawai')
            node_font_size: Font size for node labels
            node_spacing: Spacing between nodes (affects layout scale/repulsion)
            show_labels: Whether to show node labels
            
        Returns:
            Plotly Figure object
        """
        # Generate layout positions
        if layout == 'spring':
            pos = nx.spring_layout(graph, k=1, iterations=50)
        elif layout == 'circular':
            pos = nx.circular_layout(graph)
        elif layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(graph)
        else:
            pos = nx.spring_layout(graph)
        
        # Prepare node traces by type
        node_colors = self.config['VISUALIZATION']['node_colors']
        edge_colors = self.config['VISUALIZATION']['edge_colors']
        
        node_traces = {}
        for node_type in set(data.get('node_type', 'concept') for _, data in graph.nodes(data=True)):
            node_traces[node_type] = {
                'x': [], 'y': [], 'text': [], 'hovertext': [],
                'name': node_type, 'color': node_colors.get(node_type, '#95A5A6')
            }
        
        # Add nodes to traces
        for node, data in graph.nodes(data=True):
            x, y = pos[node]
            node_type = data.get('node_type', 'concept')
            degree = graph.degree(node)
            
            node_traces[node_type]['x'].append(x)
            node_traces[node_type]['y'].append(y)
            node_traces[node_type]['text'].append(node)
            node_traces[node_type]['hovertext'].append(
                f"{node}<br>Type: {node_type}<br>Connections: {degree}"
            )
        
        # Create edge traces
        edge_x = []
        edge_y = []
        
        for u, v in graph.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y, mode='lines',
            line=dict(width=0.5, color='#888'),
            hoverinfo='none', showlegend=False
        )
        
        # Create figure
        fig = go.Figure()
        
        # Add edge trace
        fig.add_trace(edge_trace)
        
        # Add node traces
        for node_type, trace_data in node_traces.items():
            if trace_data['x']:  # Only add if there are nodes of this type
                fig.add_trace(go.Scatter(
                    x=trace_data['x'], y=trace_data['y'],
                    mode='markers+text',
                    marker=dict(
                        size=10,
                        color=trace_data['color'],
                        line=dict(width=2, color='white')
                    ),
                    text=trace_data['text'],
                    textposition='middle center',
                    hovertext=trace_data['hovertext'],
                    hoverinfo='text',
                    name=node_type,
                    textfont=dict(size=node_font_size)  # Apply node font size
                ))
        
        # Update layout
        fig.update_layout(
            title="Knowledge Graph Visualization",
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ dict(
                text="Interactive Knowledge Graph",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom',
                font=dict(color='#888', size=14)
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        return fig
    
    def create_statistics_dashboard(self, graph: nx.MultiDiGraph) -> Dict[str, go.Figure]:
        """
        Create an enhanced dashboard with meaningful research-focused visualizations.
        
        Args:
            graph: NetworkX graph to analyze
            
        Returns:
            Dictionary of enhanced Plotly figures
        """
        figures = {}
        
        # 1. Enhanced Entity Type Distribution with gradients
        type_counts = defaultdict(int)
        type_confidences = defaultdict(list)
        
        for node, data in graph.nodes(data=True):
            entity_type = data.get('node_type') or data.get('type') or 'unknown'
            type_counts[entity_type] += 1
            confidence = data.get('confidence', 0.0)
            type_confidences[entity_type].append(confidence)
        
        if type_counts:
            # Calculate average confidence per type
            avg_confidences = {t: sum(confs)/len(confs) for t, confs in type_confidences.items()}
            
            # Create enhanced donut chart with confidence indicators
            colors = [self.config['VISUALIZATION']['node_colors'].get(t, '#95A5A6') for t in type_counts.keys()]
            
            fig_types = go.Figure(data=[go.Pie(
                labels=list(type_counts.keys()),
                values=list(type_counts.values()),
                hole=0.4,
                marker_colors=colors,
                textinfo='label+percent+value',
                textfont_size=12,
                hovertemplate='<b>%{label}</b><br>' +
                             'Count: %{value}<br>' +
                             'Percentage: %{percent}<br>' +
                             'Avg Confidence: %{customdata:.2f}<extra></extra>',
                customdata=[avg_confidences[t] for t in type_counts.keys()]
            )])
            
            fig_types.update_layout(
                title={
                    'text': "🎯 Entity Type Distribution & Confidence",
                    'x': 0.5,
                    'font': {'size': 16, 'color': '#2C3E50'}
                },
                font=dict(family="Arial", size=12),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=50, b=20)
            )
            figures['entity_types'] = fig_types
        
        # 2. Relationship Network Analysis with insights
        relation_counts = defaultdict(int)
        relation_confidences = defaultdict(list)
        
        for u, v, data in graph.edges(data=True):
            relation_type = data.get('relation', 'unknown')
            relation_counts[relation_type] += 1
            confidence = data.get('confidence', 0.0)
            relation_confidences[relation_type].append(confidence)
        
        if relation_counts:
            # Enhanced horizontal bar chart with confidence bands
            relation_types = list(relation_counts.keys())
            counts = list(relation_counts.values())
            avg_confs = [sum(relation_confidences[rt])/len(relation_confidences[rt]) for rt in relation_types]
            
            # Sort by count for better visualization
            sorted_data = sorted(zip(relation_types, counts, avg_confs), key=lambda x: x[1], reverse=True)
            relation_types, counts, avg_confs = zip(*sorted_data)
            
            colors = [self.config['VISUALIZATION']['edge_colors'].get(rt, '#95A5A6') for rt in relation_types]
            
            fig_relations = go.Figure()
            
            # Main bars
            fig_relations.add_trace(go.Bar(
                y=relation_types,
                x=counts,
                orientation='h',
                marker_color=colors,
                text=[f'{c} (conf: {ac:.2f})' for c, ac in zip(counts, avg_confs)],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>' +
                             'Count: %{x}<br>' +
                             'Avg Confidence: %{customdata:.2f}<extra></extra>',
                customdata=avg_confs
            ))
            
            fig_relations.update_layout(
                title={
                    'text': "🔗 Relationship Types & Strength Analysis",
                    'x': 0.5,
                    'font': {'size': 16, 'color': '#2C3E50'}
                },
                xaxis_title="Number of Relationships",
                yaxis_title="Relationship Type",
                plot_bgcolor='rgba(248,249,250,0.8)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Arial", size=11),
                margin=dict(l=150, r=20, t=50, b=40)
            )
            figures['relation_types'] = fig_relations
        
        # 3. Network Topology Analysis
        if graph.number_of_nodes() > 0:
            # Convert MultiDiGraph to simple Graph for centrality calculations
            simple_graph = nx.Graph(graph)
            
            # Calculate various centrality measures
            try:
                degree_centrality = nx.degree_centrality(simple_graph)
                betweenness_centrality = nx.betweenness_centrality(simple_graph)
                closeness_centrality = nx.closeness_centrality(simple_graph)
            except:
                # Fallback for disconnected components
                degree_centrality = {node: graph.degree(node) / max(1, graph.number_of_nodes() - 1) 
                                   for node in graph.nodes()}
                betweenness_centrality = degree_centrality.copy()
                closeness_centrality = degree_centrality.copy()
            
            # Get top nodes by different metrics
            top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            top_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            top_closeness = sorted(closeness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Create multi-metric centrality comparison
            if top_degree:
                fig_centrality = go.Figure()
                
                nodes, degree_vals = zip(*top_degree)
                between_vals = [betweenness_centrality.get(node, 0) for node in nodes]
                close_vals = [closeness_centrality.get(node, 0) for node in nodes]
                
                # Normalize values for comparison
                max_degree = max(degree_vals) if degree_vals else 1
                max_between = max(between_vals) if between_vals else 1
                max_close = max(close_vals) if close_vals else 1
                
                fig_centrality.add_trace(go.Bar(
                    name='Degree Centrality',
                    x=nodes,
                    y=[v/max_degree for v in degree_vals],
                    marker_color='rgba(55, 128, 191, 0.7)',
                    hovertemplate='<b>%{x}</b><br>Degree Centrality: %{customdata:.3f}<extra></extra>',
                    customdata=degree_vals
                ))
                
                fig_centrality.add_trace(go.Bar(
                    name='Betweenness Centrality',
                    x=nodes,
                    y=[v/max_between for v in between_vals],
                    marker_color='rgba(255, 153, 51, 0.7)',
                    hovertemplate='<b>%{x}</b><br>Betweenness Centrality: %{customdata:.3f}<extra></extra>',
                    customdata=between_vals
                ))
                
                fig_centrality.add_trace(go.Bar(
                    name='Closeness Centrality',
                    x=nodes,
                    y=[v/max_close for v in close_vals],
                    marker_color='rgba(50, 171, 96, 0.7)',
                    hovertemplate='<b>%{x}</b><br>Closeness Centrality: %{customdata:.3f}<extra></extra>',
                    customdata=close_vals
                ))
                
                fig_centrality.update_layout(
                    title={
                        'text': "🌟 Key Entities: Multi-Dimensional Centrality Analysis",
                        'x': 0.5,
                        'font': {'size': 16, 'color': '#2C3E50'}
                    },
                    xaxis_title="Entities",
                    yaxis_title="Normalized Centrality Score",
                    barmode='group',
                    plot_bgcolor='rgba(248,249,250,0.8)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Arial", size=11),
                    margin=dict(l=60, r=20, t=60, b=100),
                    xaxis={'tickangle': 45},
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                figures['centrality_analysis'] = fig_centrality
        
        # 4. Research Impact & Knowledge Density Analysis
        if graph.number_of_nodes() > 0:
            # Convert MultiDiGraph to simple Graph for clustering analysis
            simple_graph = nx.Graph()
            simple_graph.add_nodes_from(graph.nodes(data=True))
            simple_graph.add_edges_from(graph.edges(data=False))  # Remove edge data for simplicity
            
            # Analyze knowledge clusters and research impact
            degrees = [d for n, d in graph.degree()]
            try:
                clustering_coeffs = list(nx.clustering(simple_graph).values()) if simple_graph.number_of_nodes() > 1 else [0]
            except:
                clustering_coeffs = [0] * simple_graph.number_of_nodes()
            
            # Create knowledge density scatter plot
            node_data = []
            for node, data in graph.nodes(data=True):
                degree = graph.degree(node)
                confidence = data.get('confidence', 0.0)
                entity_type = data.get('node_type', 'unknown')
                try:
                    clustering_coeff = nx.clustering(simple_graph, node) if simple_graph.number_of_nodes() > 1 else 0
                except:
                    clustering_coeff = 0
                
                node_data.append({
                    'node': node,
                    'degree': degree,
                    'confidence': confidence,
                    'type': entity_type,
                    'clustering': clustering_coeff
                })
            
            if node_data:
                import numpy as np
                df_nodes = pd.DataFrame(node_data)
                
                # Check data variance and add jittering if needed for better visualization
                confidence_variance = df_nodes['confidence'].var()
                degree_variance = df_nodes['degree'].var()
                
                # Add slight jittering for overlapping points (especially if low variance)
                if confidence_variance < 0.01:  # Very low variance in confidence
                    jitter_conf = np.random.normal(0, 0.005, len(df_nodes))
                    df_nodes['confidence_plot'] = df_nodes['confidence'] + jitter_conf
                else:
                    df_nodes['confidence_plot'] = df_nodes['confidence']
                
                if degree_variance < 1:  # Very low variance in degree
                    jitter_deg = np.random.normal(0, 0.1, len(df_nodes))
                    df_nodes['degree_plot'] = df_nodes['degree'] + jitter_deg
                else:
                    df_nodes['degree_plot'] = df_nodes['degree']
                
                # Normalize clustering coefficient for better marker sizing
                max_clustering = df_nodes['clustering'].max() if df_nodes['clustering'].max() > 0 else 1
                min_clustering = df_nodes['clustering'].min()
                
                # Create a more meaningful size scale based on clustering + degree
                df_nodes['impact_score'] = (
                    0.6 * (df_nodes['degree'] / df_nodes['degree'].max()) + 
                    0.4 * (df_nodes['clustering'] / max_clustering if max_clustering > 0 else 0)
                )
                df_nodes['size_normalized'] = df_nodes['impact_score'].apply(
                    lambda x: max(8, min(25, x * 20 + 8))
                )
                
                # Create enhanced scatter plot with better data distribution
                fig_impact = go.Figure()
                
                # Define distinct colors for better visibility
                type_colors = {}
                default_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
                
                # Group by entity type for better legend and coloring
                for i, entity_type in enumerate(df_nodes['type'].unique()):
                    type_data = df_nodes[df_nodes['type'] == entity_type]
                    
                    # Use config colors if available, otherwise use default palette
                    color = self.config['VISUALIZATION']['node_colors'].get(
                        entity_type, 
                        default_colors[i % len(default_colors)]
                    )
                    type_colors[entity_type] = color
                    
                    fig_impact.add_trace(go.Scatter(
                        x=type_data['degree_plot'],
                        y=type_data['confidence_plot'],
                        mode='markers',
                        marker=dict(
                            size=type_data['size_normalized'],
                            color=color,
                            opacity=0.75,
                            line=dict(width=1.5, color='white'),
                            sizemode='diameter'
                        ),
                        name=f'{entity_type} ({len(type_data)})',
                        text=type_data['node'],
                        hovertemplate='<b>%{text}</b><br>' +
                                     'Type: ' + entity_type + '<br>' +
                                     'Connections: %{customdata[0]}<br>' +
                                     'Confidence: %{customdata[1]:.3f}<br>' +
                                     'Clustering: %{customdata[2]:.3f}<br>' +
                                     'Impact Score: %{customdata[3]:.3f}<extra></extra>',
                        customdata=list(zip(
                            type_data['degree'], 
                            type_data['confidence'], 
                            type_data['clustering'],
                            type_data['impact_score']
                        ))
                    ))
                
                # Calculate more robust axis ranges
                x_range = [
                    max(0, df_nodes['degree_plot'].min() - 0.5),
                    df_nodes['degree_plot'].max() + 0.5
                ]
                y_range = [
                    max(0, df_nodes['confidence_plot'].min() - 0.02),
                    min(1, df_nodes['confidence_plot'].max() + 0.02)
                ]
                
                # Update layout with improved scaling and appearance
                fig_impact.update_layout(
                    title={
                        'text': "📈 Research Impact Matrix: Entity Connectivity vs. AI Confidence",
                        'x': 0.5,
                        'font': {'size': 16, 'color': '#2C3E50'}
                    },
                    xaxis_title="Number of Connections (Research Centrality)",
                    yaxis_title="AI Extraction Confidence",
                    plot_bgcolor='rgba(248,249,250,0.9)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Arial", size=11),
                    margin=dict(l=70, r=20, t=70, b=50),
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=1.02,
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor="rgba(128,128,128,0.3)",
                        borderwidth=1
                    ),
                    xaxis=dict(
                        range=x_range,
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='rgba(128,128,128,0.2)',
                        zeroline=True,
                        zerolinecolor='rgba(128,128,128,0.3)'
                    ),
                    yaxis=dict(
                        range=y_range,
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='rgba(128,128,128,0.2)',
                        zeroline=False
                    )
                )
                
                # Add meaningful reference lines using quartiles for better distribution
                q1_degree = df_nodes['degree'].quantile(0.25)
                q3_degree = df_nodes['degree'].quantile(0.75)
                q1_confidence = df_nodes['confidence'].quantile(0.25)
                q3_confidence = df_nodes['confidence'].quantile(0.75)
                
                # Add quartile lines for better interpretation
                fig_impact.add_vline(
                    x=q3_degree,
                    line_dash="dot",
                    line_color="rgba(100,100,100,0.6)",
                    line_width=1
                )
                
                fig_impact.add_hline(
                    y=q3_confidence,
                    line_dash="dot",
                    line_color="rgba(100,100,100,0.6)",
                    line_width=1
                )
                
                # Add interpretive quadrant annotations with better positioning
                max_x, max_y = x_range[1], y_range[1]
                min_x, min_y = x_range[0], y_range[0]
                
                # Top-right: High confidence, high connectivity
                fig_impact.add_annotation(
                    text="🌟 Research Stars<br><i>High confidence & well-connected</i>",
                    x=max_x * 0.75,
                    y=max_y * 0.95,
                    showarrow=False,
                    font=dict(size=10, color="#2E8B57"),
                    bgcolor="rgba(46,139,87,0.1)",
                    bordercolor="rgba(46,139,87,0.4)",
                    borderwidth=1,
                    borderpad=4
                )
                
                # Top-left: High confidence, low connectivity
                fig_impact.add_annotation(
                    text="💎 Hidden Gems<br><i>High confidence, underexplored</i>",
                    x=min_x + (max_x - min_x) * 0.25,
                    y=max_y * 0.95,
                    showarrow=False,
                    font=dict(size=10, color="#4169E1"),
                    bgcolor="rgba(65,105,225,0.1)",
                    bordercolor="rgba(65,105,225,0.4)",
                    borderwidth=1,
                    borderpad=4
                )
                
                # Bottom-right: Low confidence, high connectivity
                if min_y < max_y * 0.6:  # Only show if there's enough space
                    fig_impact.add_annotation(
                        text="🔍 Review Targets<br><i>Well-connected but uncertain</i>",
                        x=max_x * 0.75,
                        y=min_y + (max_y - min_y) * 0.15,
                        showarrow=False,
                        font=dict(size=10, color="#CD853F"),
                        bgcolor="rgba(205,133,63,0.1)",
                        bordercolor="rgba(205,133,63,0.4)",
                        borderwidth=1,
                        borderpad=4
                    )
                
                # Add size legend explanation
                fig_impact.add_annotation(
                    text="<i>Marker size = Impact Score<br>(combination of connectivity + clustering)</i>",
                    x=0.02,
                    y=0.02,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=9, color="#666"),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="rgba(128,128,128,0.3)",
                    borderwidth=1
                )
                
                figures['research_impact'] = fig_impact
        
        # 5. Knowledge Gap Analysis
        if relation_counts:
            # Identify potential research gaps and opportunities
            total_possible_relations = len(type_counts) * (len(type_counts) - 1)
            actual_relation_types = len(relation_counts)
            
            # Create gap analysis summary
            gap_metrics = {
                'Relation Density': len(relation_counts) / max(1, total_possible_relations) * 100,
                'Entity Coverage': (len([n for n, d in graph.degree() if d > 0]) / max(1, graph.number_of_nodes())) * 100,
                'Knowledge Connectivity': (sum(degrees) / max(1, len(degrees))) if degrees else 0,
                'Research Breadth': len(type_counts),
                'Relationship Diversity': len(relation_counts)
            }
            
            fig_gaps = go.Figure()
            
            metrics = list(gap_metrics.keys())
            values = list(gap_metrics.values())
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
            
            fig_gaps.add_trace(go.Bar(
                x=values,
                y=metrics,
                orientation='h',
                marker_color=colors,
                text=[f'{v:.1f}' for v in values],
                textposition='auto'
            ))
            
            fig_gaps.update_layout(
                title={
                    'text': "🔍 Knowledge Graph Completeness & Research Opportunities",
                    'x': 0.5,
                    'font': {'size': 16, 'color': '#2C3E50'}
                },
                xaxis_title="Score / Count",
                plot_bgcolor='rgba(248,249,250,0.8)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Arial", size=11),
                margin=dict(l=150, r=20, t=60, b=40)
            )
            
            figures['knowledge_gaps'] = fig_gaps
        
        return figures
    
    def export_visualization(self, net: Network, filepath: str) -> None:
        """
        Export Pyvis network to HTML file.
        
        Args:
            net: Pyvis Network object
            filepath: Output HTML file path
        """
        net.save_graph(filepath)
        print(f"Visualization saved to {filepath}")
    
    def get_subgraph_around_node(self, graph: nx.MultiDiGraph, 
                                center_node: str, radius: int = 2) -> nx.MultiDiGraph:
        """
        Extract subgraph around a specific node.
        
        Args:
            graph: Full NetworkX graph
            center_node: Central node for subgraph
            radius: Distance radius for subgraph
            
        Returns:
            Subgraph NetworkX object
        """
        if center_node not in graph:
            return nx.MultiDiGraph()
        
        # Get nodes within radius
        subgraph_nodes = set([center_node])
        for r in range(radius):
            new_nodes = set()
            for node in subgraph_nodes:
                new_nodes.update(graph.neighbors(node))
                new_nodes.update(graph.predecessors(node))
            subgraph_nodes.update(new_nodes)
        
        return graph.subgraph(subgraph_nodes).copy()
