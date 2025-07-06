"""
Entity Optimizer for Knowledge Graph

This module provides advanced entity normalization and deduplication
with configurable semantic similarity detection.
"""

import re
import json
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import logging

# Optional imports for semantic similarity (Phase 2)
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    logging.warning("sentence-transformers not available. Semantic similarity disabled.")


class EntityOptimizer:
    """Advanced entity optimization with normalization and semantic deduplication."""
    
    def __init__(self, enable_semantic: bool = False, similarity_threshold: float = 0.85):
        """
        Initialize the entity optimizer.
        
        Args:
            enable_semantic: Enable semantic similarity detection (Phase 2)
            similarity_threshold: Threshold for semantic similarity matching
        """
        self.enable_semantic = enable_semantic and SEMANTIC_AVAILABLE
        self.similarity_threshold = similarity_threshold
        
        # Initialize semantic model if enabled
        self.semantic_model = None
        if self.enable_semantic:
            try:
                # Use a lightweight model for better performance
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                logging.info("Semantic similarity model loaded successfully")
            except Exception as e:
                logging.warning(f"Failed to load semantic model: {e}")
                self.enable_semantic = False
        
        # Common abbreviation mappings
        self.abbreviations = {
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'nlp': 'natural language processing',
            'cv': 'computer vision',
            'dl': 'deep learning',
            'nn': 'neural network',
            'cnn': 'convolutional neural network',
            'rnn': 'recurrent neural network',
            'lstm': 'long short-term memory',
            'gpt': 'generative pre-trained transformer',
            'bert': 'bidirectional encoder representations from transformers',
            'covid': 'covid-19',
            'sars': 'severe acute respiratory syndrome',
            'mri': 'magnetic resonance imaging',
            'ct': 'computed tomography',
            'dna': 'deoxyribonucleic acid',
            'rna': 'ribonucleic acid',
            'pcr': 'polymerase chain reaction',
            'who': 'world health organization',
            'fda': 'food and drug administration',
            'nih': 'national institutes of health'
        }
        
        # Pluralization patterns - more specific patterns first
        # Be careful not to match singular words that end in 's'
        self.plural_patterns = [
            (r'ies$', 'y'),      # studies -> study
            (r'ves$', 'f'),      # leaves -> leaf  
            (r'oes$', 'o'),      # heroes -> hero
            (r'ses$', 's'),      # analyses -> analysis (must come before 'es' pattern)
            (r'ches$', 'ch'),    # approaches -> approach
            (r'shes$', 'sh'),    # wishes -> wish
            (r'xes$', 'x'),      # indexes -> index
            (r'([^s])es$', r'\1'),  # approaches -> approach, but not "analyses" or words ending in "ses"
            (r'([^aeiou])s$', r'\1'),  # methods -> method, but not "analysis", "focus", etc.
        ]
        
        # Irregular plurals
        self.irregular_plurals = {
            'children': 'child',
            'people': 'person',
            'men': 'man',
            'women': 'woman',
            'feet': 'foot',
            'teeth': 'tooth',
            'mice': 'mouse',
            'geese': 'goose',
            'data': 'datum',
            'criteria': 'criterion',
            'phenomena': 'phenomenon',
            'analyses': 'analysis',
            'meta-analyses': 'meta-analysis',  # Add compound forms
            'syntheses': 'synthesis',
            'hypotheses': 'hypothesis',
            'diagnoses': 'diagnosis',
            'prognoses': 'prognosis',
            'techniques': 'technique',  # Add common research terms
            'approaches': 'approach',
            'procedures': 'procedure',
            'strategies': 'strategy'
        }

    def normalize_entity_name(self, name: str) -> str:
        """
        Phase 1: Enhanced entity name normalization.
        
        Args:
            name: Raw entity name
            
        Returns:
            Normalized entity name
        """
        if not name or not isinstance(name, str):
            return ""
        
        # Step 1: Basic cleaning
        normalized = name.strip().lower()
        
        # Step 2: Remove excessive whitespace and punctuation
        normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces -> single space
        normalized = re.sub(r'[^\w\s\-]', '', normalized)  # Remove special chars except hyphens
        normalized = re.sub(r'\-+', '-', normalized)  # Multiple hyphens -> single hyphen
        normalized = normalized.strip('-')  # Remove leading/trailing hyphens
        
        # Step 3: Handle word order standardization for compound terms
        normalized = self._standardize_word_order(normalized)
        
        # Step 4: Expand abbreviations
        normalized = self._expand_abbreviations(normalized)
        
        # Step 5: Singularize (convert plurals to singular)
        normalized = self._singularize(normalized)
        
        # Step 6: Final cleanup
        normalized = normalized.strip()
        
        return normalized

    def _standardize_word_order(self, text: str) -> str:
        """Standardize word order for common compound terms."""
        # Common patterns to standardize
        patterns = [
            (r'\b(machine learning|ml)\s+(model|algorithm|method)\b', r'machine learning \2'),
            (r'\b(deep learning|dl)\s+(model|network|algorithm)\b', r'deep learning \2'),
            (r'\b(neural network|nn)\s+(model|architecture)\b', r'neural network \2'),
            (r'\b(natural language|nl)\s+processing\b', 'natural language processing'),
            (r'\b(artificial intelligence|ai)\s+(system|model)\b', r'artificial intelligence \2'),
        ]
        
        result = text
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result

    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations."""
        words = text.split()
        expanded_words = []
        
        for word in words:
            # Check if word is an abbreviation
            if word in self.abbreviations:
                expanded_words.append(self.abbreviations[word])
            else:
                expanded_words.append(word)
        
        return ' '.join(expanded_words)

    def _singularize(self, text: str) -> str:
        """Convert plural forms to singular."""
        words = text.split()
        singularized_words = []
        
        for word in words:
            # Handle possessive forms by removing them and normalizing to non-possessive
            # e.g., "children's health" -> "child health" 
            if word.endswith("'s"):
                word = word[:-2]  # Remove 's
            elif word.endswith("s'"):
                word = word[:-2]  # Remove s'
            
            # Check irregular plurals first
            if word in self.irregular_plurals:
                singularized = self.irregular_plurals[word]
                singularized_words.append(singularized)
                continue
            
            # Apply pattern-based singularization
            singularized = word
            for plural_pattern, singular_ending in self.plural_patterns:
                if re.search(plural_pattern, word):
                    singularized = re.sub(plural_pattern, singular_ending, word)
                    break
            
            singularized_words.append(singularized)
        
        return ' '.join(singularized_words)

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Phase 2: Calculate semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        if not self.enable_semantic or not self.semantic_model:
            return 0.0
        
        try:
            embeddings = self.semantic_model.encode([text1, text2])
            similarity = float(np.dot(embeddings[0], embeddings[1]) / 
                             (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])))
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            logging.warning(f"Semantic similarity calculation failed: {e}")
            return 0.0

    def should_merge_entities(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if two entities should be merged.
        
        Args:
            entity1: First entity
            entity2: Second entity
            
        Returns:
            Tuple of (should_merge, reason)
        """
        name1 = entity1.get('name', '')
        name2 = entity2.get('name', '')
        type1 = entity1.get('type', '')
        type2 = entity2.get('type', '')
        
        # Must be same type to merge
        if type1 != type2:
            return False, "different_types"
        
        # Phase 1: Exact match after normalization
        norm1 = self.normalize_entity_name(name1)
        norm2 = self.normalize_entity_name(name2)
        
        if norm1 == norm2:
            return True, "exact_match"
        
        # Phase 2: Semantic similarity (if enabled)
        if self.enable_semantic:
            similarity = self.calculate_semantic_similarity(norm1, norm2)
            if similarity >= self.similarity_threshold:
                return True, f"semantic_similarity_{similarity:.3f}"
        
        return False, "no_match"

    def merge_entity_data(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge data from two entities, keeping the best information.
        
        Args:
            primary: Primary entity to keep
            secondary: Secondary entity to merge into primary
            
        Returns:
            Merged entity data
        """
        merged = primary.copy()
        
        # Keep higher confidence score
        if secondary.get('confidence', 0) > primary.get('confidence', 0):
            merged['confidence'] = secondary['confidence']
        
        # Merge descriptions (keep longer one)
        primary_desc = primary.get('description', '')
        secondary_desc = secondary.get('description', '')
        if len(secondary_desc) > len(primary_desc):
            merged['description'] = secondary_desc
        
        # Merge source information
        if 'source_chunks' not in merged:
            merged['source_chunks'] = []
        
        # Add source chunks from both entities
        for source_key in ['source_chunk', 'source_chunks']:
            for entity in [primary, secondary]:
                if source_key in entity:
                    source_data = entity[source_key]
                    if isinstance(source_data, list):
                        merged['source_chunks'].extend(source_data)
                    else:
                        merged['source_chunks'].append(source_data)
        
        # Remove duplicates from source chunks
        merged['source_chunks'] = list(set(merged['source_chunks']))
        
        # Track merge history
        if 'merged_from' not in merged:
            merged['merged_from'] = []
        merged['merged_from'].append(secondary.get('name', ''))
        
        return merged

    def optimize_entities(self, entities: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Optimize a list of entities using normalization and deduplication.
        
        Args:
            entities: List of raw entities
            
        Returns:
            Tuple of (optimized_entities, optimization_stats)
        """
        if not entities:
            return [], {"original_count": 0, "optimized_count": 0, "merges": 0}
        
        original_count = len(entities)
        optimization_stats = {
            "original_count": original_count,
            "merges": 0,
            "merge_reasons": defaultdict(int)
        }
        
        # Track entities by normalized name and type
        entity_groups = defaultdict(list)
        
        # Group entities by normalized name and type for Phase 1
        for entity in entities:
            norm_name = self.normalize_entity_name(entity.get('name', ''))
            entity_type = entity.get('type', '')
            key = f"{norm_name}|{entity_type}"
            entity_groups[key].append(entity)
        
        optimized_entities = []
        
        # Phase 1: Merge exact matches after normalization
        for group in entity_groups.values():
            if len(group) == 1:
                optimized_entities.append(group[0])
            else:
                # Merge all entities in this group
                primary = group[0]
                for secondary in group[1:]:
                    primary = self.merge_entity_data(primary, secondary)
                    optimization_stats["merges"] += 1
                    optimization_stats["merge_reasons"]["exact_match"] += 1
                
                optimized_entities.append(primary)
        
        # Phase 2: Semantic similarity merging (if enabled)
        if self.enable_semantic and len(optimized_entities) > 1:
            optimized_entities = self._semantic_merge_pass(optimized_entities, optimization_stats)
        
        optimization_stats["optimized_count"] = len(optimized_entities)
        
        return optimized_entities, dict(optimization_stats)

    def _semantic_merge_pass(self, entities: List[Dict[str, Any]], stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform semantic similarity merging pass."""
        if not self.enable_semantic:
            return entities
        
        merged_entities = []
        processed_indices = set()
        
        for i, entity1 in enumerate(entities):
            if i in processed_indices:
                continue
            
            current_entity = entity1
            
            # Look for similar entities to merge with
            for j, entity2 in enumerate(entities[i+1:], i+1):
                if j in processed_indices:
                    continue
                
                should_merge, reason = self.should_merge_entities(current_entity, entity2)
                if should_merge and reason.startswith("semantic_similarity"):
                    current_entity = self.merge_entity_data(current_entity, entity2)
                    processed_indices.add(j)
                    stats["merges"] += 1
                    stats["merge_reasons"][reason] += 1
            
            merged_entities.append(current_entity)
            processed_indices.add(i)
        
        return merged_entities


def create_entity_optimizer(enable_semantic: bool = False, similarity_threshold: float = 0.85) -> EntityOptimizer:
    """
    Factory function to create an EntityOptimizer instance.
    
    Args:
        enable_semantic: Enable semantic similarity detection
        similarity_threshold: Threshold for semantic similarity
        
    Returns:
        EntityOptimizer instance
    """
    return EntityOptimizer(enable_semantic=enable_semantic, similarity_threshold=similarity_threshold)
