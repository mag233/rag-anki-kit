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
    
    os.makedirs(output_dir, exist_ok=True)
    
    entities_file = os.path.join(output_dir, f"{project_name}_entities.json")
    relations_file = os.path.join(output_dir, f"{project_name}_relations.json")
    
    with open(entities_file, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    
    with open(relations_file, 'w', encoding='utf-8') as f:
        json.dump(relations, f, ensure_ascii=False, indent=2)
    
    return {
        'entities_file': entities_file,
        'relations_file': relations_file
    }


def load_extraction_results(entities_file: str, relations_file: str) -> tuple:
    """
    Load previously saved extraction results.
    
    Args:
        entities_file: Path to entities JSON file
        relations_file: Path to relations JSON file
        
    Returns:
        Tuple of (entities, relations)
    """
    try:
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities = json.load(f)
    except FileNotFoundError:
        entities = []
    
    try:
        with open(relations_file, 'r', encoding='utf-8') as f:
            relations = json.load(f)
    except FileNotFoundError:
        relations = []
    
    return entities, relations


def create_summary_dataframes(entities: List[Dict], relations: List[Dict]) -> Dict[str, pd.DataFrame]:
    """
    Create summary DataFrames for display.
    
    Args:
        entities: List of extracted entities
        relations: List of extracted relations
        
    Returns:
        Dictionary containing summary DataFrames
    """
    # Entities summary
    entities_df = pd.DataFrame(entities)
    if not entities_df.empty:
        entities_summary = entities_df.groupby('type').agg({
            'name': 'count',
            'confidence': 'mean'
        }).round(3)
        entities_summary.columns = ['Count', 'Avg Confidence']
    else:
        entities_summary = pd.DataFrame()
    
    # Relations summary
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
        'entities': entities_summary,
        'relations': relations_summary,
        'entities_detail': entities_df,
        'relations_detail': relations_df
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
    filtered_entities = [e for e in entities if e.get('confidence', 0) >= min_confidence]
    filtered_relations = [r for r in relations if r.get('confidence', 0) >= min_confidence]
    
    return filtered_entities, filtered_relations


def get_most_connected_entities(relations: List[Dict], top_n: int = 10) -> List[Dict]:
    """
    Get entities with the most connections.
    
    Args:
        relations: List of relations
        top_n: Number of top entities to return
        
    Returns:
        List of most connected entities with counts
    """
    from collections import defaultdict
    
    entity_counts = defaultdict(int)
    
    for relation in relations:
        entity_counts[relation.get('source', '')] += 1
        entity_counts[relation.get('target', '')] += 1
    
    # Sort by count and return top N
    sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
    
    return [{'entity': entity, 'connections': count} for entity, count in sorted_entities[:top_n]]
