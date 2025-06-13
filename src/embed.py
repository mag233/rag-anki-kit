# embed.py
import os
import json
import hashlib
import logging
import threading
import argparse
import sys
from pathlib import Path
from typing import Optional, Set, List, Dict, Any, Union
from datetime import datetime

import openai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Thread lock for database operations
_db_lock = threading.Lock()

# OpenAI 配置（保持不变）
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key, base_url="https://xiaoai.plus/v1")
embed_model = "text-embedding-3-large"

def _compute_chunk_hash(chunk: Dict[str, Any]) -> str:
    """Compute hash for chunk content to detect changes."""
    content = f"{chunk.get('chunk_text', '')}{chunk.get('metadata', {})}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def _get_existing_chunk_ids(db) -> Set[str]:
    """Get all existing chunk IDs from the database."""
    try:
        existing_data = db._collection.get()
        return set(existing_data.get("ids", []))
    except Exception as e:
        logger.warning(f"Could not retrieve existing chunk IDs: {e}")
        return set()

def _get_existing_chunk_hashes(db) -> Dict[str, str]:
    """Get existing chunk ID to hash mapping from database metadata."""
    try:
        existing_data = db._collection.get(include=["metadatas"])
        chunk_hashes = {}
        ids = existing_data.get("ids", [])
        metadatas = existing_data.get("metadatas", [])
        
        for chunk_id, metadata in zip(ids, metadatas):
            if metadata and "content_hash" in metadata:
                chunk_hashes[chunk_id] = metadata["content_hash"]
        
        return chunk_hashes
    except Exception as e:
        logger.warning(f"Could not retrieve existing chunk hashes: {e}")
        return {}

def create_or_update_embeddings(
    chunks_folder: str, 
    persist_directory: str, 
    only_files: Optional[Set[str]] = None,
    force_reprocess: bool = False,
    enable_deduplication: bool = True
) -> Dict[str, int]:
    """
    Create or update embeddings with enhanced processing modes.
    
    Args:
        chunks_folder: Directory containing chunk JSON files
        persist_directory: Chroma database save path
        only_files: If specified, only process files with these stems (no extension)
        force_reprocess: If True, reprocess all chunks regardless of existing state
        enable_deduplication: If True, use hash-based deduplication
    
    Returns:
        Dict with processing statistics: {'processed': int, 'skipped': int, 'errors': int}
    """
    with _db_lock:
        logger.info(f"Starting embedding process - folder: {chunks_folder}, force: {force_reprocess}")
        
        # Import here to avoid circular imports
        from langchain_openai import OpenAIEmbeddings
        from langchain_chroma import Chroma

        # Collect all chunk files
        chunk_files = [
            fn for fn in os.listdir(chunks_folder)
            if fn.endswith("_chunks.json") and (
                only_files is None or 
                any(os.path.splitext(fn)[0].replace("_chunks", "") in only_files for stem in only_files)
            )
        ]
        
        logger.info(f"Found {len(chunk_files)} chunk files to process")
        
        # Load all chunks
        all_chunks = []
        for fn in chunk_files:
            try:
                with open(os.path.join(chunks_folder, fn), "r", encoding="utf-8") as f:
                    file_chunks = json.load(f)
                    all_chunks.extend(file_chunks)
                    logger.debug(f"Loaded {len(file_chunks)} chunks from {fn}")
            except Exception as e:
                logger.error(f"Error loading chunks from {fn}: {e}")

        if not all_chunks:
            logger.warning("No chunks found to process")
            return {'processed': 0, 'skipped': 0, 'errors': 0}

        # Initialize embeddings and database
        embeddings = OpenAIEmbeddings(model=embed_model)
        db = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name="literature_chunks"
        )

        # Get existing data for incremental processing
        existing_ids = set()
        existing_hashes = {}
        
        if not force_reprocess:
            existing_ids = _get_existing_chunk_ids(db)
            if enable_deduplication:
                existing_hashes = _get_existing_chunk_hashes(db)
            logger.info(f"Found {len(existing_ids)} existing embeddings")

        # Process chunks with deduplication
        chunks_to_process = []
        skipped_count = 0
        duplicate_ids = set()
        seen_ids = set()

        for chunk in all_chunks:
            chunk_id = chunk.get("chunk_id", "")
            
            # Skip chunks with empty or duplicate IDs
            if not chunk_id or chunk_id in seen_ids:
                if chunk_id in seen_ids:
                    duplicate_ids.add(chunk_id)
                skipped_count += 1
                continue
            
            seen_ids.add(chunk_id)
            
            # Skip if not forcing reprocess and chunk exists
            if not force_reprocess and chunk_id in existing_ids:
                # Check hash-based deduplication if enabled
                if enable_deduplication:
                    current_hash = _compute_chunk_hash(chunk)
                    existing_hash = existing_hashes.get(chunk_id)
                    
                    if existing_hash == current_hash:
                        logger.debug(f"Skipping unchanged chunk: {chunk_id}")
                        skipped_count += 1
                        continue
                    else:
                        logger.debug(f"Content changed for chunk: {chunk_id}")
                else:
                    logger.debug(f"Skipping existing chunk: {chunk_id}")
                    skipped_count += 1
                    continue
            
            # Add content hash to metadata if deduplication is enabled
            if enable_deduplication:
                chunk_copy = chunk.copy()
                if "metadata" not in chunk_copy:
                    chunk_copy["metadata"] = {}
                chunk_copy["metadata"]["content_hash"] = _compute_chunk_hash(chunk)
                chunk_copy["metadata"]["last_updated"] = datetime.now().isoformat()
                chunks_to_process.append(chunk_copy)
            else:
                chunks_to_process.append(chunk)

        if duplicate_ids:
            logger.warning(f"Skipped duplicate chunk_ids: {', '.join(list(duplicate_ids)[:10])}")

        # Process chunks in batches
        processed_count = 0
        error_count = 0
        batch_size = 100
        
        logger.info(f"Processing {len(chunks_to_process)} chunks in batches of {batch_size}")
        
        for i in range(0, len(chunks_to_process), batch_size):
            batch = chunks_to_process[i:i + batch_size]
            try:
                texts = [c["chunk_text"] for c in batch]
                metadatas = [c.get("metadata", {}) for c in batch]
                ids = [c["chunk_id"] for c in batch]
                
                if force_reprocess:
                    # Delete existing embeddings for these IDs first
                    try:
                        db._collection.delete(ids=ids)
                        logger.debug(f"Deleted existing embeddings for batch starting at index {i}")
                    except Exception as e:
                        logger.debug(f"No existing embeddings to delete: {e}")
                
                db.add_texts(texts, metadatas=metadatas, ids=ids)
                processed_count += len(batch)
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(chunks_to_process) + batch_size - 1)//batch_size}")
                
            except Exception as e:
                logger.error(f"Error processing batch starting at index {i}: {e}")
                error_count += len(batch)

        logger.info(f"Embedding process completed - Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")
        logger.info(f"Database persisted to {persist_directory}")
        
        return {
            'processed': processed_count,
            'skipped': skipped_count, 
            'errors': error_count
        }

def generate_embedding(text, model=embed_model, api_key=None, base_url=None):
    """
    用 OpenAI API 生成一个文本的 embedding。
    返回 embedding 向量（list of float）或 None。
    """
    _api_key = api_key or os.getenv("OPENAI_API_KEY")
    _base_url = base_url or "https://xiaoai.plus/v1"
    try:
        _client = openai.OpenAI(api_key=_api_key, base_url=_base_url)
        response = _client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None

def main():
    """CLI interface for embedding management."""
    parser = argparse.ArgumentParser(description="Embedding Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create embeddings command
    create_parser = subparsers.add_parser("create", help="Create or update embeddings")
    create_parser.add_argument("chunks_folder", help="Path to chunks folder")
    create_parser.add_argument("db_path", help="Path to database")
    create_parser.add_argument("--force", action="store_true", help="Force reprocess all chunks")
    create_parser.add_argument("--no-dedup", action="store_true", help="Disable hash-based deduplication")
    create_parser.add_argument("--only-files", nargs="*", help="Process only these file stems")
    
    # Clear all command
    clear_all_parser = subparsers.add_parser("clear-all", help="Clear all embeddings")
    clear_all_parser.add_argument("db_path", help="Path to database")
    clear_all_parser.add_argument("--confirm", action="store_true", help="Confirm the operation")
    
    # Clear by document command
    clear_doc_parser = subparsers.add_parser("clear-document", help="Clear embeddings for a document")
    clear_doc_parser.add_argument("db_path", help="Path to database")
    clear_doc_parser.add_argument("document_id", help="Document ID to clear")
    clear_doc_parser.add_argument("--confirm", action="store_true", help="Confirm the operation")
    
    # Clear by chunk IDs command
    clear_chunks_parser = subparsers.add_parser("clear-chunks", help="Clear specific chunk embeddings")
    clear_chunks_parser.add_argument("db_path", help="Path to database")
    clear_chunks_parser.add_argument("chunk_ids", nargs="+", help="Chunk IDs to clear")
    clear_chunks_parser.add_argument("--confirm", action="store_true", help="Confirm the operation")
    
    # Clear by timestamp command
    clear_time_parser = subparsers.add_parser("clear-before", help="Clear embeddings before timestamp")
    clear_time_parser.add_argument("db_path", help="Path to database")
    clear_time_parser.add_argument("timestamp", help="ISO timestamp (e.g., 2023-12-01T00:00:00)")
    clear_time_parser.add_argument("--confirm", action="store_true", help="Confirm the operation")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.add_argument("db_path", help="Path to database")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "create":
        only_files = set(args.only_files) if args.only_files else None
        result = create_or_update_embeddings(
            args.chunks_folder,
            args.db_path,
            only_files=only_files,
            force_reprocess=args.force,
            enable_deduplication=not args.no_dedup
        )
        print(f"Results: {result}")
        
    elif args.command == "clear-all":
        if not args.confirm:
            print("WARNING: This will delete ALL embeddings. Use --confirm to proceed.")
            return
        success = clear_all_embeddings(args.db_path, confirm=True)
        print(f"Clear all operation: {'Success' if success else 'Failed'}")
        
    elif args.command == "clear-document":
        if not args.confirm:
            print("WARNING: This will delete embeddings for the specified document. Use --confirm to proceed.")
            return
        success = clear_embeddings_by_document(args.db_path, args.document_id, confirm=True)
        print(f"Clear document operation: {'Success' if success else 'Failed'}")
        
    elif args.command == "clear-chunks":
        if not args.confirm:
            print("WARNING: This will delete the specified chunk embeddings. Use --confirm to proceed.")
            return
        success = clear_embeddings_by_chunk_ids(args.db_path, args.chunk_ids, confirm=True)
        print(f"Clear chunks operation: {'Success' if success else 'Failed'}")
        
    elif args.command == "clear-before":
        if not args.confirm:
            print("WARNING: This will delete embeddings before the specified timestamp. Use --confirm to proceed.")
            return
        success = clear_embeddings_by_timestamp(args.db_path, args.timestamp, confirm=True)
        print(f"Clear by timestamp operation: {'Success' if success else 'Failed'}")
        
    elif args.command == "stats":
        stats = get_database_stats(args.db_path)
        print("Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

# ...existing code...

def clear_all_embeddings(persist_directory: str, confirm: bool = False) -> bool:
    """
    Clear all embeddings and chunks from the database.
    
    Args:
        persist_directory: Chroma database path
        confirm: Safety confirmation flag
    
    Returns:
        True if successful, False otherwise
    """
    if not confirm:
        logger.warning("clear_all_embeddings called without confirmation - operation aborted")
        return False
    
    with _db_lock:
        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_chroma import Chroma
            
            logger.info(f"Clearing all embeddings from {persist_directory}")
            
            embeddings = OpenAIEmbeddings(model=embed_model)
            db = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings,
                collection_name="literature_chunks"
            )
            
            # Get all IDs and delete them
            existing_data = db._collection.get()
            all_ids = existing_data.get("ids", [])
            
            if all_ids:
                db._collection.delete(ids=all_ids)
                logger.info(f"Cleared {len(all_ids)} embeddings from database")
            else:
                logger.info("No embeddings found to clear")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all embeddings: {e}")
            return False

def clear_embeddings_by_document(
    persist_directory: str, 
    document_id: str, 
    confirm: bool = False
) -> bool:
    """
    Clear embeddings for a specific document.
    
    Args:
        persist_directory: Chroma database path
        document_id: Document identifier to clear
        confirm: Safety confirmation flag
    
    Returns:
        True if successful, False otherwise
    """
    if not confirm:
        logger.warning("clear_embeddings_by_document called without confirmation - operation aborted")
        return False
    
    with _db_lock:
        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_chroma import Chroma
            
            logger.info(f"Clearing embeddings for document: {document_id}")
            
            embeddings = OpenAIEmbeddings(model=embed_model)
            db = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings,
                collection_name="literature_chunks"
            )
            
            # Get all data to filter by document
            existing_data = db._collection.get(include=["metadatas"])
            ids_to_delete = []
            
            ids = existing_data.get("ids", [])
            metadatas = existing_data.get("metadatas", [])
            
            for chunk_id, metadata in zip(ids, metadatas):
                if metadata and metadata.get("source", "").find(document_id) != -1:
                    ids_to_delete.append(chunk_id)
            
            if ids_to_delete:
                db._collection.delete(ids=ids_to_delete)
                logger.info(f"Cleared {len(ids_to_delete)} embeddings for document {document_id}")
            else:
                logger.info(f"No embeddings found for document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing embeddings for document {document_id}: {e}")
            return False

def clear_embeddings_by_chunk_ids(
    persist_directory: str, 
    chunk_ids: List[str], 
    confirm: bool = False
) -> bool:
    """
    Clear specific embeddings by chunk IDs.
    
    Args:
        persist_directory: Chroma database path
        chunk_ids: List of chunk IDs to clear
        confirm: Safety confirmation flag
    
    Returns:
        True if successful, False otherwise
    """
    if not confirm:
        logger.warning("clear_embeddings_by_chunk_ids called without confirmation - operation aborted")
        return False
    
    with _db_lock:
        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_chroma import Chroma
            
            logger.info(f"Clearing {len(chunk_ids)} specific chunk embeddings")
            
            embeddings = OpenAIEmbeddings(model=embed_model)
            db = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings,
                collection_name="literature_chunks"
            )
            
            # Filter existing IDs
            existing_data = db._collection.get()
            existing_ids = set(existing_data.get("ids", []))
            ids_to_delete = [cid for cid in chunk_ids if cid in existing_ids]
            
            if ids_to_delete:
                db._collection.delete(ids=ids_to_delete)
                logger.info(f"Cleared {len(ids_to_delete)} embeddings")
            else:
                logger.info("No matching embeddings found to clear")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing specific embeddings: {e}")
            return False

def clear_embeddings_by_timestamp(
    persist_directory: str, 
    before_timestamp: str, 
    confirm: bool = False
) -> bool:
    """
    Clear embeddings created before a specific timestamp.
    
    Args:
        persist_directory: Chroma database path
        before_timestamp: ISO format timestamp (e.g., "2023-12-01T00:00:00")
        confirm: Safety confirmation flag
    
    Returns:
        True if successful, False otherwise
    """
    if not confirm:
        logger.warning("clear_embeddings_by_timestamp called without confirmation - operation aborted")
        return False
    
    with _db_lock:
        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_chroma import Chroma
            from datetime import datetime
            
            threshold_dt = datetime.fromisoformat(before_timestamp.replace('Z', '+00:00'))
            logger.info(f"Clearing embeddings created before: {threshold_dt}")
            
            embeddings = OpenAIEmbeddings(model=embed_model)
            db = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings,
                collection_name="literature_chunks"
            )
            
            # Get all data to filter by timestamp
            existing_data = db._collection.get(include=["metadatas"])
            ids_to_delete = []
            
            ids = existing_data.get("ids", [])
            metadatas = existing_data.get("metadatas", [])
            
            for chunk_id, metadata in zip(ids, metadatas):
                if metadata and "last_updated" in metadata:
                    try:
                        chunk_dt = datetime.fromisoformat(metadata["last_updated"])
                        if chunk_dt < threshold_dt:
                            ids_to_delete.append(chunk_id)
                    except ValueError:
                        # Skip chunks with invalid timestamps
                        continue
            
            if ids_to_delete:
                db._collection.delete(ids=ids_to_delete)
                logger.info(f"Cleared {len(ids_to_delete)} embeddings created before {threshold_dt}")
            else:
                logger.info(f"No embeddings found created before {threshold_dt}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing embeddings by timestamp: {e}")
            return False

def remove_duplicates(persist_directory: str) -> int:
    """
    Remove duplicate embeddings based on content hash.
    
    Args:
        persist_directory: Chroma database path
    
    Returns:
        Number of duplicates removed
    """
    try:
        from langchain_openai import OpenAIEmbeddings
        from langchain_chroma import Chroma
        
        embeddings = OpenAIEmbeddings(model=embed_model)
        db = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name="literature_chunks"
        )
        
        existing_data = db._collection.get(include=["metadatas"])
        ids = existing_data.get("ids", [])
        metadatas = existing_data.get("metadatas", [])
        
        # Track hashes and find duplicates
        hash_to_ids = {}
        duplicates_to_remove = []
        
        for chunk_id, metadata in zip(ids, metadatas):
            if metadata and "content_hash" in metadata:
                content_hash = metadata["content_hash"]
                if content_hash in hash_to_ids:
                    # Found duplicate - mark for removal
                    duplicates_to_remove.append(chunk_id)
                    logger.info(f"Found duplicate chunk: {chunk_id} (hash: {content_hash[:8]}...)")
                else:
                    hash_to_ids[content_hash] = chunk_id
        
        # Remove duplicates
        if duplicates_to_remove:
            logger.info(f"Removing {len(duplicates_to_remove)} duplicate embeddings...")
            db._collection.delete(ids=duplicates_to_remove)
            logger.info(f"Successfully removed {len(duplicates_to_remove)} duplicates")
            return len(duplicates_to_remove)
        else:
            logger.info("No duplicates found")
            return 0
            
    except Exception as e:
        logger.error(f"Error removing duplicates: {e}")
        raise e

def get_database_stats(persist_directory: str) -> Dict[str, Any]:
    """
    Get comprehensive statistics about the embedding database.
    
    Args:
        persist_directory: Chroma database path
    
    Returns:
        Dictionary with detailed database statistics
    """
    try:
        from langchain_openai import OpenAIEmbeddings
        from langchain_chroma import Chroma
        
        embeddings = OpenAIEmbeddings(model=embed_model)
        db = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name="literature_chunks"
        )
        
        existing_data = db._collection.get(include=["metadatas", "documents"])
        ids = existing_data.get("ids", [])
        metadatas = existing_data.get("metadatas", [])
        documents = existing_data.get("documents", [])
        
        stats = {
            "total_embeddings": len(ids),
            "database_path": persist_directory,
            "embedding_model": embed_model,
            "last_updated": "N/A",
            "documents": set(),
            "has_timestamps": 0,
            "has_hashes": 0,
            "content_lengths": [],
            "id_lengths": []
        }
        
        # Analyze metadata and content
        latest_timestamp = None
        for i, (chunk_id, metadata) in enumerate(zip(ids, metadatas)):
            # Track ID lengths
            stats["id_lengths"].append(len(chunk_id))
            
            # Track document content lengths
            if i < len(documents) and documents[i]:
                stats["content_lengths"].append(len(documents[i]))
            
            if metadata:
                # Track unique documents
                if "source" in metadata:
                    source_path = metadata["source"]
                    doc_name = os.path.basename(source_path)
                    stats["documents"].add(doc_name)
                
                # Track timestamps
                if "last_updated" in metadata:
                    stats["has_timestamps"] += 1
                    timestamp_str = metadata["last_updated"]
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if latest_timestamp is None or timestamp > latest_timestamp:
                            latest_timestamp = timestamp
                    except:
                        pass
                
                # Track content hashes
                if "content_hash" in metadata:
                    stats["has_hashes"] += 1
        
        # Calculate averages
        stats["avg_id_length"] = sum(stats["id_lengths"]) / len(stats["id_lengths"]) if stats["id_lengths"] else 0
        stats["avg_content_length"] = sum(stats["content_lengths"]) / len(stats["content_lengths"]) if stats["content_lengths"] else 0
        
        # Format last updated
        if latest_timestamp:
            stats["last_updated"] = latest_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Finalize document stats
        stats["unique_documents"] = len(stats["documents"])
        stats["documents"] = list(stats["documents"])
        
        # Clean up working data
        del stats["id_lengths"]
        del stats["content_lengths"]
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {
            "error": str(e),
            "total_embeddings": 0,
            "unique_documents": 0,
            "embedding_model": embed_model,
            "last_updated": "Error",
            "has_hashes": False
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        # Legacy behavior for backward compatibility
        BASE = Path(__file__).parent
        CHUNKS = BASE / "data" / "processed" / "chunks"
        DB_DIR = BASE / "data" / "vectorstore" / "chroma_db"
        if CHUNKS.exists():
            create_or_update_embeddings(str(CHUNKS), str(DB_DIR))
        else:
            print("Usage: python embed.py <command> [options]")
            print("Run 'python embed.py -h' for help")
