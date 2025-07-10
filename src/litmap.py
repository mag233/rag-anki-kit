"""
LitMap Business Logic Module

This module contains the core business logic for LitMap knowledge graph processing,
separated from the UI components for better maintainability.
"""

import os
import json
import datetime
import glob
from typing import Dict, Any, List, Tuple, Optional

from knowledge_graph import EntityRelationExtractor


def load_chunk_status(status_file: str) -> Dict[str, Any]:
    """Load or initialize chunk status metadata."""
    if os.path.exists(status_file):
        with open(status_file, "r", encoding="utf-8") as f:
            loaded_status = json.load(f)
            # Ensure all entries have required fields for backward compatibility
            for cid, status_data in loaded_status.items():
                if not isinstance(status_data, dict):
                    loaded_status[cid] = {
                        "status": "pending", 
                        "last_processed_at": None, 
                        "confidence_score": None
                    }
                else:
                    # Ensure all required fields exist
                    status_data.setdefault("status", "pending")
                    status_data.setdefault("last_processed_at", None)
                    status_data.setdefault("confidence_score", None)
            return loaded_status
    else:
        return {}


def load_all_chunks_from_folder(chunks_folder: str) -> Tuple[List[Dict], List[str], List[str]]:
    """Load all chunks from the chunks folder and return chunks, their IDs, and file paths."""
    chunk_files = glob.glob(os.path.join(chunks_folder, "*_chunks.json"))
    all_chunks = []
    chunk_ids = []
    
    for fn in chunk_files:
        with open(fn, "r", encoding="utf-8") as f:
            arr = json.load(f)
            all_chunks.extend(arr)
            chunk_ids.extend([c.get("chunk_id") for c in arr if c.get("chunk_id")])
    
    return all_chunks, chunk_ids, chunk_files


def sync_chunk_status(chunk_status: Dict[str, Any], chunk_ids: List[str]) -> Dict[str, Any]:
    """Sync metadata with current chunks - add new chunks as pending, remove missing."""
    # Add new chunks as pending
    for cid in chunk_ids:
        if cid not in chunk_status:
            chunk_status[cid] = {
                "status": "pending",
                "last_processed_at": None,
                "confidence_score": None
            }
    
    # Remove missing chunks
    for cid in list(chunk_status.keys()):
        if cid not in chunk_ids:
            del chunk_status[cid]
    
    return chunk_status


def get_processing_stats(chunk_status: Dict[str, Any], chunk_ids: List[str]) -> Dict[str, int]:
    """Calculate processing statistics."""
    total_chunks = len(chunk_ids)
    n_processed = len([cid for cid in chunk_ids if chunk_status.get(cid, {}).get("status") == "processed"])
    n_pending = total_chunks - n_processed
    
    return {
        "total_chunks": total_chunks,
        "n_processed": n_processed,
        "n_pending": n_pending
    }


def start_full_reprocess(
    chunk_status: Dict[str, Any], 
    status_file: str, 
    litmap_folder: str, 
    selected_project: str
) -> None:
    """Start full reprocessing mode - reset all chunk status and delete existing data."""
    # 1. Reset all chunk status
    for cid in chunk_status:
        chunk_status[cid]["status"] = "pending"
        chunk_status[cid]["last_processed_at"] = None
        chunk_status[cid]["confidence_score"] = None
    
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(chunk_status, f, ensure_ascii=False, indent=2)
    
    # 2. Delete existing data files
    entities_file = os.path.join(litmap_folder, f"{selected_project}_entities.json")
    relations_file = os.path.join(litmap_folder, f"{selected_project}_relations.json")
    temp_entities_file = os.path.join(litmap_folder, f"{selected_project}_new_entities.tmp.json")
    temp_relations_file = os.path.join(litmap_folder, f"{selected_project}_new_relations.tmp.json")
    
    for file_path in [entities_file, relations_file, temp_entities_file, temp_relations_file]:
        if os.path.exists(file_path):
            os.remove(file_path)


def save_chunk_status(status_file: str, chunk_status: Dict[str, Any]) -> None:
    """Save chunk status to file."""
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(chunk_status, f, ensure_ascii=False, indent=2)


def update_processed_chunks_status(
    process_chunks: List[Dict], 
    status_file: str
) -> None:
    """Update status for processed chunks."""
    # Load the full status file again to avoid overwriting previous progress
    full_chunk_status = load_chunk_status(status_file)
    
    for c in process_chunks:
        cid = c.get("chunk_id")
        if cid:
            full_chunk_status[cid] = {
                "status": "processed",
                "last_processed_at": datetime.datetime.now().isoformat(),
                "confidence_score": None
            }
    
    save_chunk_status(status_file, full_chunk_status)


def clear_database_files(litmap_folder: str, selected_project: str) -> None:
    """Clear main database files for selective reprocessing."""
    entities_file = os.path.join(litmap_folder, f"{selected_project}_entities.json")
    relations_file = os.path.join(litmap_folder, f"{selected_project}_relations.json")
    
    # Clear main data files
    if os.path.exists(entities_file):
        os.remove(entities_file)
    if os.path.exists(relations_file):
        os.remove(relations_file)
    
    # Clear temporary files
    temp_new_entities_path = os.path.join(litmap_folder, f"{selected_project}_new_entities.tmp.json")
    temp_new_relations_path = os.path.join(litmap_folder, f"{selected_project}_new_relations.tmp.json")
    if os.path.exists(temp_new_entities_path):
        os.remove(temp_new_entities_path)
    if os.path.exists(temp_new_relations_path):
        os.remove(temp_new_relations_path)


def create_fresh_chunk_status(all_chunks: List[Dict]) -> Dict[str, Any]:
    """Create fresh chunk status for selective reprocessing."""
    fresh_chunk_status = {}
    for chunk in all_chunks:
        cid = chunk.get("chunk_id")
        if cid:
            fresh_chunk_status[cid] = {
                "status": "pending",
                "last_processed_at": None,
                "confidence_score": None
            }
    return fresh_chunk_status


def save_extraction_data(
    entities: List[Dict], 
    relations: List[Dict], 
    litmap_folder: str, 
    selected_project: str,
    mode: str = "main"
) -> None:
    """Save extraction data to files."""
    if mode == "main":
        entities_file = os.path.join(litmap_folder, f"{selected_project}_entities.json")
        relations_file = os.path.join(litmap_folder, f"{selected_project}_relations.json")
    else:  # temporary
        entities_file = os.path.join(litmap_folder, f"{selected_project}_new_entities.tmp.json")
        relations_file = os.path.join(litmap_folder, f"{selected_project}_new_relations.tmp.json")
    
    with open(entities_file, "w", encoding="utf-8") as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    with open(relations_file, "w", encoding="utf-8") as f:
        json.dump(relations, f, ensure_ascii=False, indent=2)


def load_extraction_data(
    litmap_folder: str, 
    selected_project: str,
    mode: str = "main"
) -> Tuple[List[Dict], List[Dict]]:
    """Load extraction data from files."""
    if mode == "main":
        entities_file = os.path.join(litmap_folder, f"{selected_project}_entities.json")
        relations_file = os.path.join(litmap_folder, f"{selected_project}_relations.json")
    else:  # temporary
        entities_file = os.path.join(litmap_folder, f"{selected_project}_new_entities.tmp.json")
        relations_file = os.path.join(litmap_folder, f"{selected_project}_new_relations.tmp.json")
    
    entities = []
    relations = []
    
    if os.path.exists(entities_file):
        with open(entities_file, "r", encoding="utf-8") as f:
            entities = json.load(f)
    
    if os.path.exists(relations_file):
        with open(relations_file, "r", encoding="utf-8") as f:
            relations = json.load(f)
    
    return entities, relations


def dedup_items(items: List[Dict], item_type: str) -> List[Dict]:
    """Robust deduplication for entities and relations."""
    seen = set()
    result = []
    for item in items:
        if item_type == 'entity':
            # For entities, use name + type as key
            key = (item.get('name', '').lower(), item.get('type', '').lower())
        else:  # relation
            # For relations, use subject + object + relation_type as key
            # Handle both 'subject'/'object' and 'source'/'target' formats
            subject = item.get('subject') or item.get('source', '')
            obj = item.get('object') or item.get('target', '')
            rel_type = item.get('relation_type') or item.get('type', '')
            key = (subject.lower(), obj.lower(), rel_type.lower())
        
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def merge_and_save_data(
    litmap_folder: str, 
    selected_project: str
) -> Tuple[List[Dict], List[Dict]]:
    """Merge new data with existing data, deduplicate, and save."""
    # Load existing data from disk
    disk_entities, disk_relations = load_extraction_data(litmap_folder, selected_project, mode="main")
    
    # Load new data from temporary files
    new_entities, new_relations = load_extraction_data(litmap_folder, selected_project, mode="temp")
    
    # Merge and deduplicate
    all_entities = disk_entities + new_entities
    all_relations = disk_relations + new_relations
    
    all_entities = dedup_items(all_entities, 'entity')
    all_relations = dedup_items(all_relations, 'relation')
    
    # Save merged data
    save_extraction_data(all_entities, all_relations, litmap_folder, selected_project, mode="main")
    
    # Clean up temporary files
    temp_entities_path = os.path.join(litmap_folder, f"{selected_project}_new_entities.tmp.json")
    temp_relations_path = os.path.join(litmap_folder, f"{selected_project}_new_relations.tmp.json")
    
    if os.path.exists(temp_entities_path):
        os.remove(temp_entities_path)
    if os.path.exists(temp_relations_path):
        os.remove(temp_relations_path)
    
    return all_entities, all_relations


def load_custom_types(litmap_folder: str) -> Tuple[List[str], List[str]]:
    """Load custom entity and relation types from file."""
    custom_types_file = os.path.join(litmap_folder, "custom_types.json")
    
    if os.path.exists(custom_types_file):
        with open(custom_types_file, "r", encoding="utf-8") as f:
            custom_types = json.load(f)
        custom_entity_types = custom_types.get("customEntityTypes", [])
        custom_relation_types = custom_types.get("customRelationTypes", [])
    else:
        custom_entity_types = []
        custom_relation_types = []
    
    return custom_entity_types, custom_relation_types


def get_all_entity_and_relation_types(
    extractor: EntityRelationExtractor, 
    custom_entity_types: List[str], 
    custom_relation_types: List[str]
) -> Tuple[List[str], List[str]]:
    """Get all available entity and relation types including custom ones."""
    # Default types
    default_entity_types = extractor.config['ENTITY_TYPES'] + [
        'gene', 'protein', 'chemical', 'symptom', 'biomarker'
    ]
    default_entity_types = list(dict.fromkeys(default_entity_types))
    
    default_relation_types = extractor.config['RELATION_TYPES'] + [
        'interacts_with', 'associated_with', 'expresses', 'inhibits', 'induces', 'encodes'
    ]
    default_relation_types = list(dict.fromkeys(default_relation_types))
    
    # Merge custom types
    all_entity_types = default_entity_types + [t for t in custom_entity_types if t not in default_entity_types]
    all_relation_types = default_relation_types + [t for t in custom_relation_types if t not in default_relation_types]
    
    return all_entity_types, all_relation_types


def get_last_processed_times(chunk_status: Dict[str, Any], chunk_ids: List[str]) -> List[str]:
    """Get list of last processed times for chunks that have been processed."""
    last_processed_times = [
        chunk_status.get(cid, {}).get("last_processed_at") 
        for cid in chunk_ids 
        if chunk_status.get(cid, {}).get("last_processed_at")
    ]
    return last_processed_times


def get_chunks_to_process(
    all_chunks: List[Dict], 
    chunk_ids: List[str], 
    chunk_status: Dict[str, Any], 
    max_chunks: int,
    mode: str = "incremental"
) -> List[Dict]:
    """Get chunks to process based on the processing mode."""
    if mode == "full":
        # Full reprocessing: process all chunks
        return all_chunks
    elif mode == "selective":
        # Selective reprocessing: process first N chunks
        available_cids = chunk_ids[:max_chunks]
        return [c for c in all_chunks if c.get("chunk_id") in available_cids]
    else:  # incremental
        # Incremental processing: process only unprocessed chunks
        unprocessed_cids = [cid for cid in chunk_ids if chunk_status.get(cid, {}).get("status") != "processed"]
        unprocessed_next_cids = unprocessed_cids[:max_chunks]
        return [c for c in all_chunks if c.get("chunk_id") in unprocessed_next_cids]
