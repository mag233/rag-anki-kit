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
        Create dashboard with graph statistics visualizations.
        
        Args:
            graph: NetworkX graph to analyze
            
        Returns:
            Dictionary of Plotly figures
        """
        figures = {}
        
        # Node type distribution (fix: use node_type, fallback to type, then unknown)
        type_counts = defaultdict(int)
        for node, data in graph.nodes(data=True):
            entity_type = data.get('node_type') or data.get('type') or 'unknown'
            type_counts[entity_type] += 1
        
        if type_counts:
            fig_types = px.pie(
                values=list(type_counts.values()),
                names=list(type_counts.keys()),
                title="Entity Type Distribution",
                color_discrete_map=self.config['VISUALIZATION']['node_colors']
            )
            figures['entity_types'] = fig_types
        
        # Relation type distribution
        relation_counts = defaultdict(int)
        for u, v, data in graph.edges(data=True):
            relation_counts[data.get('relation', 'unknown')] += 1
        
        if relation_counts:
            fig_relations = px.bar(
                x=list(relation_counts.keys()),
                y=list(relation_counts.values()),
                title="Relation Type Distribution",
                labels={'x': 'Relation Type', 'y': 'Count'}
            )
            figures['relation_types'] = fig_relations
        
        # Degree distribution
        degrees = [d for n, d in graph.degree()]
        if degrees:
            fig_degree = px.histogram(
                x=degrees,
                title="Node Degree Distribution",
                labels={'x': 'Degree', 'y': 'Count'},
                nbins=min(20, max(degrees))
            )
            figures['degree_distribution'] = fig_degree
        
        # Top central nodes
        if graph.number_of_nodes() > 0:
            centrality = nx.degree_centrality(graph)
            top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:15]
            
            if top_nodes:
                nodes, centrality_values = zip(*top_nodes)
                fig_centrality = px.bar(
                    x=list(centrality_values),
                    y=list(nodes),
                    orientation='h',
                    title="Top Central Nodes (Degree Centrality)",
                    labels={'x': 'Centrality', 'y': 'Node'}
                )
                fig_centrality.update_layout(height=400)
                figures['centrality'] = fig_centrality
        
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
