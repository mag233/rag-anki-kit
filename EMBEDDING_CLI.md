# Embedding Management CLI

This document describes the enhanced embedding management system and CLI interface for the RAG Anki Kit.

## Overview

The embedding system has been completely rewritten with advanced features including:
- **Incremental vs Force Processing**: Choose between updating only new/changed content or reprocessing everything
- **Hash-based Deduplication**: Automatically detect content changes and skip unchanged chunks
- **Administrative Functions**: Clear embeddings by document, chunk IDs, or timestamp
- **Thread Safety**: Safe concurrent operations with proper locking
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **CLI Interface**: Command-line tools for all operations

## CLI Usage

### Basic Embedding Creation

```bash
# Create embeddings for all chunks (incremental mode)
python embed.py create /path/to/chunks /path/to/database

# Force reprocess all chunks (ignore existing)
python embed.py create /path/to/chunks /path/to/database --force

# Process only specific files
python embed.py create /path/to/chunks /path/to/database --only-files file1 file2

# Disable hash-based deduplication
python embed.py create /path/to/chunks /path/to/database --no-dedup
```

### Administrative Commands

```bash
# Clear all embeddings (requires confirmation)
python embed.py clear-all /path/to/database --confirm

# Clear embeddings for a specific document
python embed.py clear-document /path/to/database "document_name.pdf" --confirm

# Clear specific chunk embeddings
python embed.py clear-chunks /path/to/database chunk_id1 chunk_id2 --confirm

# Clear embeddings created before a timestamp
python embed.py clear-before /path/to/database "2023-12-01T00:00:00" --confirm

# Show database statistics
python embed.py stats /path/to/database
```

## API Usage

### Python API

```python
from embed import create_or_update_embeddings, get_database_stats, clear_all_embeddings

# Create/update embeddings
result = create_or_update_embeddings(
    chunks_folder="/path/to/chunks",
    persist_directory="/path/to/database",
    only_files={"file1", "file2"},  # Optional: specific files only
    force_reprocess=False,  # Default: incremental mode
    enable_deduplication=True  # Default: use hash-based deduplication
)
print(f"Processed: {result['processed']}, Skipped: {result['skipped']}")

# Get database statistics
stats = get_database_stats("/path/to/database")
print(f"Total embeddings: {stats['total_embeddings']}")

# Clear all embeddings (be careful!)
success = clear_all_embeddings("/path/to/database", confirm=True)
```

## Features

### Processing Modes

1. **Incremental Mode** (default): Only processes new or changed chunks
   - Skips existing embeddings unless content has changed
   - Uses hash-based change detection
   - Efficient for regular updates

2. **Force Reprocess Mode**: Reprocesses all chunks regardless of existing state
   - Useful when changing embedding models or parameters
   - Overwrites all existing embeddings
   - Use with `--force` flag or `force_reprocess=True`

### Hash-based Deduplication

- Computes MD5 hash of chunk content and metadata
- Stores hash in embedding metadata
- Automatically detects content changes
- Skips unchanged chunks in incremental mode
- Can be disabled with `--no-dedup` or `enable_deduplication=False`

### Thread Safety

- Uses threading locks for database operations
- Safe for concurrent access
- Prevents data corruption during parallel operations

### Logging

The system provides comprehensive logging at different levels:
- **INFO**: Processing progress and statistics
- **DEBUG**: Detailed operation information
- **WARNING**: Non-critical issues and skipped operations
- **ERROR**: Critical failures

## Database Statistics

The `stats` command provides detailed information about your embedding database:

```
Database Statistics:
  total_embeddings: 73
  database_path: /path/to/database
  documents: ['doc1.pdf', 'doc2.md', ...]
  has_timestamps: 73
  has_hashes: 73
  unique_documents: 4
```

## Safety Features

- **Confirmation Required**: Destructive operations require `--confirm` flag
- **Validation**: Input validation for paths and parameters
- **Error Handling**: Graceful error handling and recovery
- **Backup Recommendation**: Always backup your database before major operations

## Integration with Streamlit App

The enhanced embedding system integrates seamlessly with the Streamlit application:
- Real-time status updates during processing
- Automatic detection of new files
- Progress monitoring and error reporting
- Consistent behavior between CLI and GUI

## Best Practices

1. **Regular Backups**: Backup your vector database before major operations
2. **Incremental Updates**: Use incremental mode for regular document updates
3. **Monitor Logs**: Check logs for processing issues and performance
4. **Test First**: Test commands with small datasets before bulk operations
5. **Confirmation**: Always use `--confirm` for destructive operations

## Troubleshooting

### Common Issues

1. **Empty Chunk IDs**: Ensure all chunks have valid, non-empty IDs
2. **Duplicate IDs**: Check for duplicate chunk IDs in your data
3. **Permission Errors**: Verify read/write permissions for database directory
4. **Memory Issues**: Use smaller batch sizes for large datasets

### Error Recovery

- Failed operations are logged with detailed error messages
- Partial failures allow continuation with remaining chunks
- Database remains in consistent state even after failures
