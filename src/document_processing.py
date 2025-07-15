# document_processing.py
"""
重构后的文档处理模块
将原来的 process_documents 拆分为多个独立的功能模块
支持可选的深度清洗功能
"""

import datetime
import os
import json
import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, NamedTuple

import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt', quiet=True)

from langchain.schema import Document
from langchain.document_loaders import (
    PyMuPDFLoader, TextLoader, UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader
)
from langchain.text_splitter import CharacterTextSplitter

# ============================================================================
# 常量定义
# ============================================================================

SUPPORTED_EXTENSIONS = {
    ".pdf": PyMuPDFLoader,
    ".txt": TextLoader,
    ".text": TextLoader,
    ".docx": UnstructuredWordDocumentLoader,
    ".doc": UnstructuredWordDocumentLoader,
    ".xls": UnstructuredExcelLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".html": UnstructuredHTMLLoader,
    ".htm": UnstructuredHTMLLoader,
    ".md": UnstructuredMarkdownLoader,
    ".markdown": UnstructuredMarkdownLoader,
}

DEFAULT_DEEP_CLEAN_CONFIG = {
    "min_ref_lines": 2,
    "max_nonmatch_lines": 7,
    "remove_authors": True,
    "remove_references": True,
    "remove_citations": True,
    "remove_page_numbers": True,
    "normalize_whitespace": True,
}

# Standard chunking methods (English only)
CHUNKING_METHODS = {
    "by_page": "by_page",
    "by_sentence": "by_sentence", 
    "by_paragraph": "by_paragraph",
    "fixed_size": "fixed_size"
}

# Clean levels
CLEAN_LEVELS = {
    "basic": "basic",
    "deep": "deep"
}



# ============================================================================
# 数据类定义
# ============================================================================

class ProcessingStats(NamedTuple):
    """处理统计信息"""
    total_files: int
    processed_files: int
    skipped_files: int
    failed_files: int
    total_chunks: int

class ProcessingResult(NamedTuple):
    """单文件处理结果"""
    success: bool
    chunks: List[Document]
    error: Optional[str] = None

# ============================================================================
# 文件管理器
# ============================================================================

class FileManager:
    """文件管理器：负责目录创建、manifest管理、文件hash计算等"""
    
    def __init__(self, input_folder: str, output_folder: str):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.chunks_folder = self.output_folder / "chunks"
        self.tables_folder = self.output_folder / "tables"
        self.images_folder = self.output_folder / "images"
        self.equations_folder = self.output_folder / "equations"
        self.structure_folder = self.output_folder / "structure"
        self.manifest_path = self.output_folder / "manifest.json"
    
    def setup_directories(self):
        """创建必要的目录结构"""
        for folder in [self.chunks_folder, self.tables_folder, 
                      self.images_folder, self.equations_folder, self.structure_folder]:
            folder.mkdir(parents=True, exist_ok=True)
    
    def load_manifest(self) -> Dict:
        """加载manifest文件"""
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {}
    
    def save_manifest(self, manifest: Dict):
        """保存manifest文件"""
        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件hash"""
        return hashlib.md5(file_path.read_bytes()).hexdigest()
    
    def should_process_file(self, file_path: Path, manifest: Dict, force: bool) -> bool:
        """判断是否需要处理文件"""
        if force:
            return True
        
        current_hash = self.calculate_file_hash(file_path)
        prev = manifest.get(file_path.name, {})
        return prev.get("hash") != current_hash
    
    def save_chunks(self, chunks: List[Document], file_stem: str):
        """保存分块结果"""
        out = []
        for chunk in chunks:
            out.append({
                "chunk_id": chunk.metadata.get("chunk_id", ""),
                "chunk_text": chunk.page_content,
                "metadata": chunk.metadata
            })
        
        output_file = self.chunks_folder / f"{file_stem}_chunks.json"
        output_file.write_text(
            json.dumps(out, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def clear_old_chunks_if_needed(self, force: bool):
        """如果强制重处理，清空旧chunks"""
        if force:
            for f in self.chunks_folder.glob("*_chunks.json"):
                try:
                    f.unlink()
                except:
                    pass

# ============================================================================
# 文档提取器
# ============================================================================

class DocumentExtractor:
    """文档提取器：负责从各种格式的文件中提取文档内容"""
    
    def __init__(self, supported_extensions: Dict[str, Any] = None):
        self.supported_extensions = supported_extensions or SUPPORTED_EXTENSIONS
    
    def is_supported(self, file_path: Path) -> bool:
        """检查文件是否支持"""
        return file_path.suffix.lower() in self.supported_extensions
    
    def extract_documents(self, file_path: Path) -> List[Document]:
        """提取文档内容"""
        ext = file_path.suffix.lower()
        loader_cls = self.supported_extensions.get(ext)
        
        if not loader_cls:
            raise ValueError(f"Unsupported file type: {ext}")
        
        try:
            loader = loader_cls(str(file_path))
            docs = loader.load()
            return docs
        except Exception as e:
            raise RuntimeError(f"Failed to load {file_path.name}: {e}")

# ============================================================================
# 文档清洗器
# ============================================================================

class DocumentCleaner:
    """文档清洗器：支持基础清洗和可选的深度清洗"""
    
    def __init__(self, enable_deep_clean: bool = False, deep_clean_config: Optional[Dict] = None):
        self.enable_deep_clean = enable_deep_clean
        self.config = deep_clean_config or DEFAULT_DEEP_CLEAN_CONFIG
    
    def clean_documents(self, docs: List[Document], file_extension: str) -> List[Document]:
        """清洗文档的主入口"""
        if self.enable_deep_clean:
            return self._deep_clean_documents(docs, file_extension)
        else:
            return self._basic_clean_documents(docs, file_extension)
    
    def _basic_clean_documents(self, docs: List[Document], file_extension: str) -> List[Document]:
        """基础清洗：原有的清洗逻辑"""
        if file_extension == ".pdf":
            return self._clean_pdf_basic(docs)
        elif file_extension in {".md", ".markdown"}:
            return self._clean_markdown_basic(docs)
        return docs
    
    def _clean_pdf_basic(self, docs: List[Document]) -> List[Document]:
        """基础PDF清洗：去软换行等"""
        SOFT = re.compile(r"-\s*\n")
        MULTI = re.compile(r"\s+")
        
        for doc in docs:
            t = doc.page_content.replace("•", "")
            t = SOFT.sub("", t)
            t = MULTI.sub(" ", t)
            doc.page_content = t
        return docs
    
    def _clean_markdown_basic(self, docs: List[Document]) -> List[Document]:
        """基础Markdown清洗：去多余空行"""
        for doc in docs:
            doc.page_content = re.sub(r"\n{3,}", "\n\n", doc.page_content)
        return docs
    
    def _deep_clean_documents(self, docs: List[Document], file_extension: str) -> List[Document]:
        """深度清洗：使用深度清洗管道"""
        for doc in docs:
            doc.page_content = self._deep_clean_pipeline(doc.page_content)
        return docs
    
    def _deep_clean_pipeline(self, text: str) -> str:
        """深度清洗管道（来自deep_clean.py）"""
        logging.debug("=== 开始深度清洗管道 ===")
        
        # 1. 统一空白字符
        if self.config.get("normalize_whitespace", True):
            text = self._unify_spaces(text)
            text = self._normalize_whitespace(text)
        
        # 2. 删除作者信息
        if self.config.get("remove_authors", True):
            text = self._remove_authors_from_intro(text)
        
        # 3. 删除参考文献
        if self.config.get("remove_references", True):
            before = len(text.split('\n'))
            text = self._remove_references_section(
                text, 
                self.config.get("min_ref_lines", 2),
                self.config.get("max_nonmatch_lines", 7)
            )
            after = len(text.split('\n'))
            logging.debug(f"[DeepClean] 行数 {before} → {after}")
        
        # 4. 删除引用标记
        if self.config.get("remove_citations", True):
            text = re.sub(r'\[\d+\]', '', text)
            text = re.sub(r'\(\s*\d+\s*\)', '', text)
            text = re.sub(r'(?P<t>.+?)\s+\d{1,2}(?=[\.,]?$)', r'\1', text)
            logging.debug("[DeepClean] 引用标记清洗完成")
        
        # 5. 删除页码
        if self.config.get("remove_page_numbers", True):
            text = re.sub(r'^\s*(Page\s*\d+|第\s*\d+\s*页|\d+)\s*$',
                         '', text, flags=re.MULTILINE)
            logging.debug("[DeepClean] 页码清洗完成")
        
        # 6. 最后清理
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = '\n'.join([l for l in text.split('\n') if l.strip()])
        
        logging.debug("=== 深度清洗管道结束 ===")
        return text.strip()
    
    def _unify_spaces(self, text: str) -> str:
        """统一各种空白字符"""
        # 把常见的非 ASCII 空白都替换成普通空格
        text = text.replace('\u3000', ' ')  # 全角空格
        text = text.replace('\u00A0', ' ')  # 不换行空格
        for cp in range(0x2002, 0x200B):   # 各种窄空格
            text = text.replace(chr(cp), ' ')
        # 将控制字符替换为普通空格
        text = re.sub(r'[\t\v\f\u2028\u2029]', ' ', text)
        # 压缩连续空格
        text = re.sub(r' {2,}', ' ', text)
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """规范化空白和断行"""
        # 删除零宽空格等
        text = text.replace('\u3000', ' ').replace('\u200b', '')
        # 合并多行换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 非段落分隔的单换行 -> 空格
        text = re.sub(r'(?<!\n)(?<![。！？.!?])\n(?!\n)', ' ', text)
        # 拼回被连字符拆分的单词
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        # 每行去除首尾空白
        lines = [ln.strip() for ln in text.split('\n')]
        # 合并多个空格
        lines = [re.sub(r' {2,}', ' ', ln) for ln in lines]
        return "\n".join(lines)
    
    def _remove_authors_from_intro(self, text: str) -> str:
        """删除开头的作者/单位信息"""
        lines = text.split('\n')
        for idx, line in enumerate(lines):
            if re.match(r'^\s*前言\b', line) or re.match(r'^\s*目\s*录\b', line):
                logging.debug(f"[DeepClean] 匹配到第{idx}行'{line.strip()}'，删除前{idx}行")
                return '\n'.join(lines[idx:])
        for idx, line in enumerate(lines):
            if re.search(r'\bAbstract\b|\b摘要\b|\bINTRODUCTION\b', line, re.IGNORECASE):
                logging.debug(f"[DeepClean] 匹配到第{idx}行'{line.strip()}'，删除前{idx}行")
                return '\n'.join(lines[idx:])
        logging.debug("[DeepClean] 未匹配到作者起点")
        return text
    
    def _remove_references_section(self, text: str, min_ref_lines: int = 1, max_nonmatch_lines: int = 7) -> str:
        """删除尾部参考文献区块"""
        lines = text.split('\n')
        n = len(lines)
        matched = nonmatch = 0
        boundary = n
        
        # 参考文献行正则
        ref_re = re.compile(
            r"""(?x) ^\s*
            (?:
              \[\d+\]                         # [123]
            | \[J\]\.?                        # [J] 或 [J].
            | \[M\]\.?                        # [M] 或 [M].
            | \d{1,4}[\.）]\s+                # 123. 或 123)
            | \d{4}(?:年|;)\s*\d+             # 2020年22 或 2020;22
            | \d{4}[:,]\d{1,4}                # 2015:1234 或 2015,1234
            | doi[:：]\S+                     # doi:10.1000/xyz
            | https?://\S+                    # http://...
            | [A-Za-z]{2,}(?:[A-Za-z0-9\-,']+),   # 作者名
            | [A-Z][A-Za-z0-9\-\'&, ]{10,}\.\s+[A-Z]  # 期刊名
            | [\u4e00-\u9fa5]{2,}(?:,|，|、).{5,}?[\.。]\s*[\u4e00-\u9fa5A-Za-z] # 中文引用
            | .+?,\s*\d{4},\s*\d{1,4}:\d{1,5}(?:-\d{1,5})?  # 期刊格式
            )
            """,
            re.IGNORECASE
        )
        
        logging.debug(f"[DeepClean] 文本共 {n} 行，开始扫描参考文献")
        for i in range(n - 1, -1, -1):
            line = lines[i]
            if ref_re.match(line):
                matched += 1
                nonmatch = 0
                if matched >= min_ref_lines:
                    boundary = i
            else:
                if matched >= min_ref_lines:
                    nonmatch += 1
                    if nonmatch >= max_nonmatch_lines:
                        boundary = i + nonmatch
                        break
        
        if boundary < n:
            logging.debug(f"[DeepClean] 删除参考文献区间 [{boundary}, {n}) 共 {n - boundary} 行")
            return '\n'.join(lines[:boundary])
        else:
            logging.debug("[DeepClean] 未检测到参考文献区块")
            return text

# ============================================================================
# 文档分块器
# ============================================================================

class DocumentChunker:
    """文档分块器：负责将文档按不同策略分块"""
    
    def chunk_documents(self, docs: List[Document], method: str, file_stem: str, 
                       file_extension: str, chunk_size: int = 400, 
                       chunk_overlap: int = 50) -> List[Document]:
        """Document chunking with standardized English method names"""
        # Standard English method identifiers only
        if method == "by_page":
            return self._chunk_by_page(docs)
        elif method == "by_sentence":
            return self._chunk_by_sentence(docs, file_stem)
        elif method == "by_paragraph":
            return self._chunk_by_paragraph(docs, file_stem, file_extension)
        elif method == "fixed_size":
            return self._chunk_by_size(docs, chunk_size, chunk_overlap)
        else:
            # Default to fixed_size for unknown methods
            return self._chunk_by_size(docs, chunk_size, chunk_overlap)
    
    def _chunk_by_page(self, docs: List[Document]) -> List[Document]:
        """Chunk by page"""
        return docs
    
    def _chunk_by_sentence(self, docs: List[Document], file_stem: str) -> List[Document]:
        """Chunk by sentence"""
        chunks = []
        for doc in docs:
            for i, sent in enumerate(sent_tokenize(doc.page_content)):
                chunks.append(Document(
                    page_content=sent,
                    metadata={**doc.metadata, "chunk_id": f"{file_stem}_sent{i}"}
                ))
        return chunks
    
    def _chunk_by_paragraph(self, docs: List[Document], file_stem: str, file_extension: str) -> List[Document]:
        """Chunk by paragraph"""
        chunks = []
        for doc in docs:
            # For Excel files, split by lines
            if file_extension in {".xls", ".xlsx"}:
                paras = doc.page_content.split("\n")
            else:
                paras = doc.page_content.split("\n\n")
            
            for i, para in enumerate(paras):
                para = para.strip()
                if para:  # Skip empty paragraphs
                    chunks.append(Document(
                        page_content=para,
                        metadata={**doc.metadata, "chunk_id": f"{file_stem}_para{i}"}
                    ))
        return chunks
    
    def _chunk_by_size(self, docs: List[Document], chunk_size: int, chunk_overlap: int) -> List[Document]:
        """Chunk by fixed size"""
        splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return splitter.split_documents(docs)
    
    def _ensure_chunk_ids(self, chunks: List[Document], file_stem: str):
        """Ensure all chunks have chunk_id"""
        for idx, chunk in enumerate(chunks):
            if not chunk.metadata.get("chunk_id") or not str(chunk.metadata.get("chunk_id")).strip():
                chunk.metadata["chunk_id"] = f"{file_stem}_chunk{idx}"
    
    def _chunk_by_paragraph(self, docs: List[Document], file_stem: str, file_extension: str) -> List[Document]:
        """Chunk by paragraph"""
        chunks = []
        for doc in docs:
            # For Excel files, split by lines
            if file_extension in {".xls", ".xlsx"}:
                paras = doc.page_content.split("\n")
            else:
                paras = doc.page_content.split("\n\n")
            
            for i, para in enumerate(paras):
                para = para.strip()
                if para:  # Skip empty paragraphs
                    chunks.append(Document(
                        page_content=para,
                        metadata={**doc.metadata, "chunk_id": f"{file_stem}_para{i}"}
                    ))
        return chunks
    
    def _chunk_by_size(self, docs: List[Document], chunk_size: int, chunk_overlap: int) -> List[Document]:
        """Chunk by fixed size"""
        splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return splitter.split_documents(docs)
    
# ============================================================================
# Document Processing Pipeline
# ============================================================================

class DocumentProcessingPipeline:
    """文档处理管道：组合各个处理组件"""
    
    def __init__(self, input_folder: str, output_folder: str):
        self.file_manager = FileManager(input_folder, output_folder)
        self.extractor = DocumentExtractor()
        self.cleaner = None  # 在process时创建
        self.chunker = DocumentChunker()
    
    def process_single_file(self, file_path: Path, chunking_config: Dict) -> ProcessingResult:
        """处理单个文件的完整流程"""
        try:
            # 1. 提取文档
            docs = self.extractor.extract_documents(file_path)
            
            # 2. 清洗文档
            file_extension = file_path.suffix.lower()
            docs = self.cleaner.clean_documents(docs, file_extension)
            
            # 3. 分块文档
            chunks = self.chunker.chunk_documents(
                docs=docs,
                method=chunking_config["method"],
                file_stem=file_path.stem,
                file_extension=file_extension,
                chunk_size=chunking_config.get("chunk_size", 400),
                chunk_overlap=chunking_config.get("chunk_overlap", 50)
            )
            
            # 4. 确保chunk_id
            self.chunker._ensure_chunk_ids(chunks, file_path.stem)
            
            return ProcessingResult(success=True, chunks=chunks)
            
        except Exception as e:
            logging.error(f"Failed to process {file_path.name}: {e}")
            return ProcessingResult(success=False, chunks=[], error=str(e))
    
    def process_documents(self, 
                         chunking_method: str = "by_sentence",
                         chunk_size: int = 400,
                         chunk_overlap: int = 50,
                         force_reprocess: bool = False,
                         enable_deep_clean: bool = False,
                         deep_clean_config: Optional[Dict] = None,
                         extract_tables: bool = True,
                         extract_images: bool = True,
                         extract_meta: bool = True) -> ProcessingStats:
        """处理所有文档的主入口函数"""
        
        # 初始化组件
        self.cleaner = DocumentCleaner(enable_deep_clean, deep_clean_config)
        
        # 设置目录和配置
        self.file_manager.setup_directories()
        self.file_manager.clear_old_chunks_if_needed(force_reprocess)
        
        # 加载manifest
        manifest = {} if force_reprocess else self.file_manager.load_manifest()
        
        # 分块配置
        chunking_config = {
            "method": chunking_method,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap
        }
        
        # 统计信息
        stats = ProcessingStats(0, 0, 0, 0, 0)
        total_chunks = 0
        
        # 处理文件
        file_list = list(self.file_manager.input_folder.iterdir())
        stats = stats._replace(total_files=len(file_list))
        
        print(f"[Processing] Found {len(file_list)} files in {self.file_manager.input_folder}")
        
        for idx, file_path in enumerate(file_list, 1):
            if not self.extractor.is_supported(file_path):
                print(f"[Processing] [{idx}/{len(file_list)}] Skipping unsupported file: {file_path.name}")
                stats = stats._replace(skipped_files=stats.skipped_files + 1)
                continue
            
            # 检查是否需要处理
            if not self.file_manager.should_process_file(file_path, manifest, force_reprocess):
                print(f"[Processing] [{idx}/{len(file_list)}] Skipping unchanged file: {file_path.name}")
                stats = stats._replace(skipped_files=stats.skipped_files + 1)
                continue
            
            print(f"[Processing] [{idx}/{len(file_list)}] Processing {file_path.name} ...")
            
            # 处理文件
            result = self.process_single_file(file_path, chunking_config)
            
            if result.success:
                # 保存chunks
                self.file_manager.save_chunks(result.chunks, file_path.stem)
                
                # 更新manifest
                current_hash = self.file_manager.calculate_file_hash(file_path)
                manifest[file_path.name] = {
                    "hash": current_hash,
                    "n_chunks": len(result.chunks),
                    "last_processed": datetime.datetime.now().isoformat(),
                    "chunk_method": chunking_method,
                    "deep_clean_enabled": enable_deep_clean
                }
                
                total_chunks += len(result.chunks)
                stats = stats._replace(processed_files=stats.processed_files + 1)
                
                print(f"[Processing] [{idx}/{len(file_list)}] {file_path.name}: {len(result.chunks)} chunks generated.")
                logging.info(f"[Processing] {file_path.name}: {len(result.chunks)} chunks generated.")
                
            else:
                stats = stats._replace(failed_files=stats.failed_files + 1)
                print(f"[Processing] [{idx}/{len(file_list)}] Failed to process {file_path.name}: {result.error}")
        
        # 保存manifest
        self.file_manager.save_manifest(manifest)
        
        # 更新统计信息
        stats = stats._replace(total_chunks=total_chunks)
        
        print(f"[Processing] Done. Total: {stats.total_files}, Processed: {stats.processed_files}, "
              f"Skipped: {stats.skipped_files}, Failed: {stats.failed_files}, Total chunks: {stats.total_chunks}")
        logging.info(f"[Processing] Done. Total: {stats.total_files}, Processed: {stats.processed_files}, "
                    f"Skipped: {stats.skipped_files}, Failed: {stats.failed_files}, Total chunks: {stats.total_chunks}")
        
        return stats

# ============================================================================
# 向后兼容的函数接口
# ============================================================================

def process_documents(
    input_folder: str,
    output_folder: str,
    extract_tables: bool = True,
    extract_images: bool = True,
    extract_meta: bool = True,
    chunking_method: str = "by_sentence",
    chunk_size: int = 400,
    chunk_overlap: int = 50,
    force_reprocess: bool = False,
    enable_deep_clean: bool = False,
    deep_clean_config: Optional[Dict] = None,
) -> ProcessingStats:
    """
    Backward compatible document processing function
    
    Args:
        input_folder: Input folder path
        output_folder: Output folder path  
        extract_tables: Whether to extract tables (for compatibility)
        extract_images: Whether to extract images (for compatibility)
        extract_meta: Whether to extract metadata (for compatibility)
        chunking_method: Chunking method ("by_sentence", "by_paragraph", "by_page", "fixed_size")
        chunk_size: Chunk size (used for fixed_size method)
        chunk_overlap: Chunk overlap (used for fixed_size method)
        force_reprocess: Whether to force reprocessing
        enable_deep_clean: Whether to enable deep cleaning
        deep_clean_config: Deep cleaning configuration
    
    Returns:
        ProcessingStats: Processing statistics
    """
    pipeline = DocumentProcessingPipeline(input_folder, output_folder)
    return pipeline.process_documents(
        chunking_method=chunking_method,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        force_reprocess=force_reprocess,
        enable_deep_clean=enable_deep_clean,
        deep_clean_config=deep_clean_config,
        extract_tables=extract_tables,
        extract_images=extract_images,
        extract_meta=extract_meta
    )
