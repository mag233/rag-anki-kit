"""
Utility functions for LitMap knowledge graph module
"""

from typing import List, Dict, Any
import json
import pandas as pd


def save_extraction_results(entities: List[Dict], relations: List[Dict], 
                          output_dir: str, project_name: str) -> Dict[str, str]:
    """
    Save extraction results to JSON files.
    
    Args:
        entities: List of extracted entities
        relations: List of extracted relations
        output_dir: Output directory path
        project_name: Project name for file naming
        
    Returns:
        Dictionary with file paths
    """
    import os
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Construct file paths for entities and relations
    entities_file = os.path.join(output_dir, f"{project_name}_entities.json")
    relations_file = os.path.join(output_dir, f"{project_name}_relations.json")
    
    # Save entities to JSON
    with open(entities_file, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    
    # Save relations to JSON
    with open(relations_file, 'w', encoding='utf-8') as f:
        json.dump(relations, f, ensure_ascii=False, indent=2)
    
    return {
        'entities_file': entities_file,
        'relations_file': relations_file
    }


def load_extraction_results(entities_file: str, relations_file: str) -> tuple:
    """
    Load previously saved extraction results from JSON files.
    
    Args:
        entities_file: Path to entities JSON file
        relations_file: Path to relations JSON file
        
    Returns:
        Tuple of (entities, relations)
    """
    try:
        # Load entities from file, or return empty list if not found
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities = json.load(f)
    except FileNotFoundError:
        entities = []
    
    try:
        # Load relations from file, or return empty list if not found
        with open(relations_file, 'r', encoding='utf-8') as f:
            relations = json.load(f)
    except FileNotFoundError:
        relations = []
    
    return entities, relations


def create_summary_dataframes(entities: List[Dict], relations: List[Dict]) -> Dict[str, pd.DataFrame]:
    """
    Create summary DataFrames for display in UI or analysis.
    
    Args:
        entities: List of extracted entities
        relations: List of extracted relations
        
    Returns:
        Dictionary containing summary DataFrames
    """
    # Entities summary: group by type, count names, average confidence
    entities_df = pd.DataFrame(entities)
    if not entities_df.empty:
        entities_summary = entities_df.groupby('type').agg({
            'name': 'count',
            'confidence': 'mean'
        }).round(3)
        entities_summary.columns = ['Count', 'Avg Confidence']
    else:
        entities_summary = pd.DataFrame()
    
    # Relations summary: group by relation type, count sources, average confidence
    relations_df = pd.DataFrame(relations)
    if not relations_df.empty:
        relations_summary = relations_df.groupby('relation').agg({
            'source': 'count',
            'confidence': 'mean'
        }).round(3)
        relations_summary.columns = ['Count', 'Avg Confidence']
    else:
        relations_summary = pd.DataFrame()
    
    return {
        'entities': entities_summary,           # Summary by entity type
        'relations': relations_summary,         # Summary by relation type
        'entities_detail': entities_df,         # Full entity details
        'relations_detail': relations_df        # Full relation details
    }


def filter_by_confidence(entities: List[Dict], relations: List[Dict], 
                        min_confidence: float = 0.5) -> tuple:
    """
    Filter entities and relations by confidence threshold.
    
    Args:
        entities: List of entities
        relations: List of relations
        min_confidence: Minimum confidence threshold
        
    Returns:
        Tuple of filtered (entities, relations)
    """
    # Only keep entities and relations with confidence >= min_confidence
    filtered_entities = [e for e in entities if e.get('confidence', 0) >= min_confidence]
    filtered_relations = [r for r in relations if r.get('confidence', 0) >= min_confidence]
    
    return filtered_entities, filtered_relations


def get_most_connected_entities(relations: List[Dict], entities: List[Dict] = None, top_n: int = 10) -> List[Dict]:
    """
    Get entities with the most connections and comprehensive analysis metrics.
    
    Args:
        relations: List of relations
        entities: List of entities (optional, for additional metadata)
        top_n: Number of top entities to return
        
    Returns:
        List of most connected entities with detailed analysis
    """
    from collections import defaultdict
    
    # Create entity lookup for metadata
    entity_lookup = {}
    if entities:
        for entity in entities:
            name = entity.get('name', '')
            entity_lookup[name] = entity
    
    # Analyze connections and relationships
    entity_stats = defaultdict(lambda: {
        'total_connections': 0,
        'as_source': 0,
        'as_target': 0,
        'relation_types': set(),
        'unique_partners': set(),
        'avg_confidence': 0.0,
        'confidence_scores': []
    })
    
    for relation in relations:
        # Support both 'subject'/'object' and 'source'/'target' field names
        source = relation.get('subject', '') or relation.get('source', '')
        target = relation.get('object', '') or relation.get('target', '')
        relation_type = relation.get('relation_type', '') or relation.get('relation', '')
        confidence = relation.get('confidence', 0.0)
        
        if source:
            stats = entity_stats[source]
            stats['total_connections'] += 1
            stats['as_source'] += 1
            stats['relation_types'].add(relation_type)
            stats['unique_partners'].add(target)
            stats['confidence_scores'].append(confidence)
            
        if target:
            stats = entity_stats[target]
            stats['total_connections'] += 1
            stats['as_target'] += 1
            stats['relation_types'].add(relation_type)
            stats['unique_partners'].add(source)
            stats['confidence_scores'].append(confidence)
    
    # Calculate final metrics and prepare results
    results = []
    for entity_name, stats in entity_stats.items():
        if not entity_name:
            continue
            
        # Calculate average confidence
        if stats['confidence_scores']:
            stats['avg_confidence'] = sum(stats['confidence_scores']) / len(stats['confidence_scores'])
        
        # Get entity metadata
        entity_info = entity_lookup.get(entity_name, {})
        entity_type = entity_info.get('type', 'unknown')
        description = entity_info.get('description', '')
        
        # Calculate influence score (combination of connections and confidence)
        influence_score = stats['total_connections'] * (stats['avg_confidence'] + 0.5)
        
        result = {
            'entity': entity_name,
            'type': entity_type,
            'description': description[:100] + '...' if len(description) > 100 else description,
            'total_connections': stats['total_connections'],
            'as_source': stats['as_source'],
            'as_target': stats['as_target'],
            'unique_partners': len(stats['unique_partners']),
            'relation_diversity': len(stats['relation_types']),
            'avg_confidence': round(stats['avg_confidence'], 3),
            'influence_score': round(influence_score, 2),
            'relation_types': list(stats['relation_types'])
        }
        results.append(result)
    
    # Sort by influence score (connections weighted by confidence)
    results.sort(key=lambda x: x['influence_score'], reverse=True)
    
    return results[:top_n]
