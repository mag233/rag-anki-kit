"""
Knowledge Graph Builder

This module constructs NetworkX graphs from extracted entities and relations,
with enhanced deduplication and graph analysis capabilities.
"""

import networkx as nx
from typing import List, Dict, Any, Set
from collections import defaultdict
import yaml
from pathlib import Path
from .entity_optimizer import create_entity_optimizer


class KnowledgeGraphBuilder:
    """Builds and manages knowledge graphs using NetworkX with enhanced entity optimization."""
    
    def __init__(self, config_path: str = None, enable_semantic: bool = False, similarity_threshold: float = 0.85):
        """
        Initialize the graph builder with configuration.
        
        Args:
            config_path: Path to configuration file
            enable_semantic: Enable semantic similarity for Phase 2 optimization
            similarity_threshold: Threshold for semantic similarity matching
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.graph = nx.MultiDiGraph()
        self.entity_counts = defaultdict(int)
        self.relation_counts = defaultdict(int)
        
        # Initialize entity optimizer with Phase 1 (always enabled) and optional Phase 2
        self.entity_optimizer = create_entity_optimizer(
            enable_semantic=enable_semantic,
            similarity_threshold=similarity_threshold
        )
    
    def optimize_entities(self, entities: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Optimize entities using the entity optimizer (Phase 1 + optional Phase 2).
        
        Args:
            entities: List of raw entities
            
        Returns:
            Tuple of (optimized_entities, optimization_stats)
        """
        return self.entity_optimizer.optimize_entities(entities)
    
    # Legacy method for backward compatibility
    def normalize_entity_name(self, name: str) -> str:
        """Legacy method - use entity_optimizer instead."""
        return self.entity_optimizer.normalize_entity_name(name)
    
    def deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Legacy method - use optimize_entities instead for better results."""
        optimized_entities, _ = self.optimize_entities(entities)
        return optimized_entities
    
    def add_entities(self, entities: List[Dict[str, Any]]) -> None:
        """
        Add entities to the knowledge graph.
        
        Args:
            entities: List of entities to add
        """
        deduplicated_entities = self.deduplicate_entities(entities)
        
        for entity in deduplicated_entities:
            name = entity.get('name', '')
            entity_type = entity.get('type', 'unknown')
            
            if not name:
                continue
            
            # Add node with attributes (avoiding duplicate 'type' keyword)
            node_attrs = {
                'node_type': entity_type,
                'frequency': self.entity_counts[name] + 1,
                'source_papers': entity.get('source_paper', ''),
                'doi': entity.get('doi', ''),
                'description': entity.get('description', ''),
                'confidence': entity.get('confidence', 0.0)
            }
            
            self.graph.add_node(name, **node_attrs)
            
            self.entity_counts[name] += 1
    
    def add_relations(self, relations: List[Dict[str, Any]]) -> None:
        """
        Add relations to the knowledge graph.
        
        Args:
            relations: List of relations (triples) to add
        """
        for relation in relations:
            source = relation.get('subject', relation.get('source', ''))
            target = relation.get('object', relation.get('target', ''))
            relation_type = relation.get('relation_type', relation.get('relation', ''))
            
            if not (source and target and relation_type):
                continue
            
            # Ensure both nodes exist
            if source not in self.graph:
                self.graph.add_node(source, node_type='unknown')
            if target not in self.graph:
                self.graph.add_node(target, node_type='unknown')
            
            # Add edge with attributes (avoiding conflicts)
            edge_attrs = {
                'relation': relation_type,
                'weight': 1.0,
                'confidence': relation.get('confidence', 0.0),
                'evidence': relation.get('evidence', ''),
                'source_chunk': relation.get('source_chunk', ''),
                'source_paper': relation.get('source_paper', ''),
                'doi': relation.get('doi', '')
            }
            
            self.graph.add_edge(source, target, **edge_attrs)
            
            self.relation_counts[relation_type] += 1
    
    def build_graph(self, entities: List[Dict[str, Any]], 
                   relations: List[Dict[str, Any]]) -> nx.MultiDiGraph:
        """
        Build complete knowledge graph from entities and relations.
        
        Args:
            entities: List of extracted entities
            relations: List of extracted relations
            
        Returns:
            NetworkX MultiDiGraph
        """
        print(f"Building graph with {len(entities)} entities and {len(relations)} relations")
        
        # Clear existing graph
        self.graph.clear()
        self.entity_counts.clear()
        self.relation_counts.clear()
        
        # Add entities and relations
        self.add_entities(entities)
        self.add_relations(relations)
        
        print(f"Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        
        return self.graph
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics."""
        stats = {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'is_connected': nx.is_weakly_connected(self.graph),
        }
        
        # Node type distribution
        type_counts = defaultdict(int)
        for node, data in self.graph.nodes(data=True):
            type_counts[data.get('node_type', 'unknown')] += 1
        stats['node_types'] = dict(type_counts)
        
        # Relation type distribution
        relation_counts = defaultdict(int)
        for u, v, data in self.graph.edges(data=True):
            relation_counts[data.get('relation', 'unknown')] += 1
        stats['relation_types'] = dict(relation_counts)
        
        # Centrality measures (for top nodes)
        if self.graph.number_of_nodes() > 0:
            degree_centrality = nx.degree_centrality(self.graph)
            top_nodes = sorted(degree_centrality.items(), 
                             key=lambda x: x[1], reverse=True)[:10]
            stats['top_central_nodes'] = top_nodes
        
        return stats
    
    def filter_graph(self, min_degree: int = 1, 
                    entity_types: List[str] = None,
                    relation_types: List[str] = None) -> nx.MultiDiGraph:
        """
        Filter graph based on various criteria.
        
        Args:
            min_degree: Minimum node degree
            entity_types: Allowed entity types
            relation_types: Allowed relation types
            
        Returns:
            Filtered NetworkX graph
        """
        filtered_graph = self.graph.copy()
        
        # Filter by node degree
        if min_degree > 1:
            low_degree_nodes = [node for node, degree in filtered_graph.degree() 
                              if degree < min_degree]
            filtered_graph.remove_nodes_from(low_degree_nodes)
        
        # Filter by entity types
        if entity_types:
            nodes_to_remove = [node for node, data in filtered_graph.nodes(data=True)
                             if data.get('node_type') not in entity_types]
            filtered_graph.remove_nodes_from(nodes_to_remove)
        
        # Filter by relation types
        if relation_types:
            edges_to_remove = [(u, v, k) for u, v, k, data in filtered_graph.edges(keys=True, data=True)
                             if data.get('relation') not in relation_types]
            filtered_graph.remove_edges_from(edges_to_remove)
        
        return filtered_graph
    
    def export_graph(self, filepath: str, format: str = 'gexf') -> None:
        """
        Export graph to various formats.
        
        Args:
            filepath: Output file path
            format: Export format ('gexf', 'graphml', 'gml')
        """
        if format == 'gexf':
            nx.write_gexf(self.graph, filepath)
        elif format == 'graphml':
            nx.write_graphml(self.graph, filepath)
        elif format == 'gml':
            nx.write_gml(self.graph, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"Graph exported to {filepath}")
