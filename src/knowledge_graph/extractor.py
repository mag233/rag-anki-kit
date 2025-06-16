"""
Entity and Relation Extractor for Knowledge Graphs

This module extracts entities and relationships from research paper chunks
using OpenAI's GPT models with structured prompts.
"""

import os
import json
import yaml
from typing import List, Dict, Any, Tuple, Callable, Optional
from openai import OpenAI
from pathlib import Path
import time


class EntityRelationExtractor:
    """Extracts entities and relations from research text using GPT models."""
    
    def __init__(self, config_path: str = None):
        """Initialize the extractor with configuration."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        )
        
        # Load extraction prompts
        prompts_dir = Path(__file__).parent / "prompts"
        with open(prompts_dir / "entity_extraction.txt", 'r') as f:
            self.entity_prompt = f.read()
        with open(prompts_dir / "relation_extraction.txt", 'r') as f:
            self.relation_prompt = f.read()
        
        # Statistics tracking
        self.stats = {
            'total_chunks': 0,
            'successful_chunks': 0,
            'failed_chunks': 0,
            'total_entities': 0,
            'total_relations': 0,
            'total_tokens_used': 0,
            'total_api_calls': 0,
            'errors': [],
            'processing_time': 0.0
        }
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text chunk.
        
        Args:
            text: Research paper text chunk
            
        Returns:
            List of extracted entities with type and properties
        """
        try:
            self.stats['total_api_calls'] += 1
            
            prompt = self.entity_prompt.format(
                text=text,
                entity_types=", ".join(self.config['ENTITY_TYPES'])
            )
            
            response = self.client.chat.completions.create(
                model=self.config['EXTRACTION']['model'],
                messages=[
                    {"role": "system", "content": "You are a research entity extraction expert. Always respond with valid JSON only. No explanations, no markdown formatting, no code blocks."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config['EXTRACTION']['temperature'],
                max_tokens=self.config['EXTRACTION']['max_tokens']
            )
            
            # Track token usage
            if hasattr(response, 'usage') and response.usage:
                self.stats['total_tokens_used'] += response.usage.total_tokens
            
            result = response.choices[0].message.content
            
            # Clean the response - remove markdown formatting if present
            if result.strip().startswith('```'):
                # Remove code block formatting
                lines = result.strip().split('\n')
                start_idx = 1 if lines[0].startswith('```') else 0
                end_idx = len(lines) - 1 if lines[-1].strip() == '```' else len(lines)
                result = '\n'.join(lines[start_idx:end_idx])
            
            # Try to parse JSON
            entities = json.loads(result.strip())
            
            # Validate structure
            if not isinstance(entities, list):
                print(f"Warning: Expected list, got {type(entities)}")
                return []
            
            # Validate each entity
            valid_entities = []
            for entity in entities:
                if isinstance(entity, dict) and 'name' in entity and 'type' in entity:
                    valid_entities.append(entity)
                else:
                    print(f"Warning: Invalid entity structure: {entity}")
            
            self.stats['total_entities'] += len(valid_entities)
            return valid_entities
            
        except json.JSONDecodeError as e:
            error_msg = f"Entity extraction JSON error: {e}"
            print(error_msg)
            print(f"Response was: {result[:200]}...")
            self.stats['errors'].append(error_msg)
            return []
        except Exception as e:
            error_msg = f"Entity extraction error: {e}"
            print(error_msg)
            self.stats['errors'].append(error_msg)
            return []
    
    def extract_relations(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract relations between entities from text.
        
        Args:
            text: Research paper text chunk
            entities: List of previously extracted entities
            
        Returns:
            List of extracted relations (triples)
        """
        try:
            # Skip if no entities
            if not entities:
                return []
            
            self.stats['total_api_calls'] += 1
            entity_list = [f"{e['name']} ({e['type']})" for e in entities]
            
            prompt = self.relation_prompt.format(
                text=text,
                entities="\n".join(entity_list),
                relation_types=", ".join(self.config['RELATION_TYPES'])
            )
            
            response = self.client.chat.completions.create(
                model=self.config['EXTRACTION']['model'],
                messages=[
                    {"role": "system", "content": "You are a research relationship extraction expert. Always respond with valid JSON only. No explanations, no markdown formatting, no code blocks."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config['EXTRACTION']['temperature'],
                max_tokens=self.config['EXTRACTION']['max_tokens']
            )
            
            # Track token usage
            if hasattr(response, 'usage') and response.usage:
                self.stats['total_tokens_used'] += response.usage.total_tokens
            
            result = response.choices[0].message.content
            
            # Clean the response - remove markdown formatting if present
            if result.strip().startswith('```'):
                # Remove code block formatting
                lines = result.strip().split('\n')
                start_idx = 1 if lines[0].startswith('```') else 0
                end_idx = len(lines) - 1 if lines[-1].strip() == '```' else len(lines)
                result = '\n'.join(lines[start_idx:end_idx])
            
            # Try to parse JSON
            relations = json.loads(result.strip())
            
            # Validate structure
            if not isinstance(relations, list):
                print(f"Warning: Expected list, got {type(relations)}")
                return []
            
            # Validate each relation and standardize field names
            valid_relations = []
            for relation in relations:
                if (isinstance(relation, dict) and 
                    'source' in relation and 
                    'target' in relation and 
                    'relation' in relation):
                    # Standardize field names for consistency
                    standardized_relation = {
                        'subject': relation['source'],
                        'object': relation['target'], 
                        'relation_type': relation['relation'],
                        'confidence': relation.get('confidence', 0.0),
                        'evidence': relation.get('evidence', '')
                    }
                    valid_relations.append(standardized_relation)
                else:
                    print(f"Warning: Invalid relation structure: {relation}")
            
            self.stats['total_relations'] += len(valid_relations)
            return valid_relations
            
        except json.JSONDecodeError as e:
            error_msg = f"Relation extraction JSON error: {e}"
            print(error_msg)
            print(f"Response was: {result[:200]}...")
            self.stats['errors'].append(error_msg)
            return []
        except Exception as e:
            error_msg = f"Relation extraction error: {e}"
            print(error_msg)
            self.stats['errors'].append(error_msg)
            return []
    
    def extract_from_chunk(self, chunk: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract entities and relations from a single text chunk.
        
        Args:
            chunk: Text chunk with metadata
            
        Returns:
            Tuple of (entities, relations)
        """
        text = chunk.get('chunk_text', chunk.get('text', ''))
        chunk_id = chunk.get('chunk_id', '')
        
        if not text:
            self.stats['failed_chunks'] += 1
            return [], []
        
        print(f"Extracting from chunk: {chunk_id}")
        
        chunk_success = True
        try:
            # Extract entities first
            entities = self.extract_entities(text)
            
            # Add source metadata to entities
            for entity in entities:
                entity['source_chunk'] = chunk_id
                entity['source_paper'] = chunk.get('title', 'Unknown')
                entity['doi'] = chunk.get('doi', '')
            
            # Extract relations
            relations = self.extract_relations(text, entities)
            
            # Add source metadata to relations
            for relation in relations:
                relation['source_chunk'] = chunk_id
                relation['source_paper'] = chunk.get('title', 'Unknown')
                relation['doi'] = chunk.get('doi', '')
            
            if entities or relations:
                self.stats['successful_chunks'] += 1
            else:
                self.stats['failed_chunks'] += 1
                chunk_success = False
            
            return entities, relations
            
        except Exception as e:
            error_msg = f"Chunk processing error for {chunk_id}: {e}"
            print(error_msg)
            self.stats['errors'].append(error_msg)
            self.stats['failed_chunks'] += 1
            return [], []
    
    def extract_from_chunks(self, chunks: List[Dict[str, Any]], 
                          max_chunks: int = None,
                          progress_callback: Optional[Callable] = None) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract entities and relations from multiple chunks.
        
        Args:
            chunks: List of text chunks
            max_chunks: Maximum number of chunks to process
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (all_entities, all_relations)
        """
        start_time = time.time()
        all_entities = []
        all_relations = []
        
        process_chunks = chunks[:max_chunks] if max_chunks else chunks
        self.stats['total_chunks'] = len(process_chunks)
        
        for i, chunk in enumerate(process_chunks):
            print(f"Processing chunk {i+1}/{len(process_chunks)}")
            
            entities, relations = self.extract_from_chunk(chunk)
            all_entities.extend(entities)
            all_relations.extend(relations)
            
            # Progress callback
            if progress_callback:
                progress = {
                    'current': i + 1,
                    'total': len(process_chunks),
                    'chunk_id': chunk.get('chunk_id', ''),
                    'entities_found': len(entities),
                    'relations_found': len(relations),
                    'stats': self.get_stats()
                }
                progress_callback(progress)
        
        self.stats['processing_time'] = time.time() - start_time
        return all_entities, all_relations
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current extraction statistics."""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset extraction statistics."""
        self.stats = {
            'total_chunks': 0,
            'successful_chunks': 0,
            'failed_chunks': 0,
            'total_entities': 0,
            'total_relations': 0,
            'total_tokens_used': 0,
            'total_api_calls': 0,
            'errors': [],
            'processing_time': 0.0
        }
