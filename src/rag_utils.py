# rag_utils.py
"""
RAG Tab 工具类和公共函数
提供数据库管理、文件操作、缓存等功能
"""

import os
import json
import glob
import streamlit as st
from typing import Dict, List, Set, Optional, Tuple
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma


class ChromaDBManager:
    """Chroma数据库管理类，提供连接复用和缓存功能"""
    
    def __init__(self, db_dir: str, embed_model: str = "text-embedding-3-large"):
        self.db_dir = db_dir
        self.embed_model = embed_model
        self._db_instance = None
        self._embedding_function = None
    
    @property
    def embedding_function(self):
        """获取embedding函数，使用缓存"""
        if self._embedding_function is None:
            self._embedding_function = OpenAIEmbeddings(model=self.embed_model)
        return self._embedding_function
    
    @property
    def db(self):
        """获取数据库实例，使用缓存"""
        if self._db_instance is None:
            try:
                self._db_instance = Chroma(
                    persist_directory=self.db_dir,
                    embedding_function=self.embedding_function,
                    collection_name="literature_chunks"
                )
            except Exception as e:
                st.error(f"数据库连接失败: {e}")
                return None
        return self._db_instance
    
    def get_embedding_count(self) -> int:
        """获取embedding数量"""
        try:
            if self.db is None:
                return 0
            ids = self.db._collection.get()["ids"]
            return len([i for i in ids if i and len(i) > 0])  # 过滤空ID
        except Exception as e:
            st.error(f"获取embedding数量失败: {e}")
            return 0
    
    def get_existing_ids(self) -> Set[str]:
        """获取现有的embedding IDs"""
        try:
            if self.db is None:
                return set()
            return set(self.db._collection.get()["ids"])
        except Exception as e:
            st.error(f"获取现有IDs失败: {e}")
            return set()
    
    def close(self):
        """关闭数据库连接"""
        if self._db_instance:
            self._db_instance = None
        self._embedding_function = None


class FileManager:
    """文件管理类，提供文件操作和缓存功能"""
    
    def __init__(self, chunks_dir: str, manifest_path: str):
        self.chunks_dir = chunks_dir
        self.manifest_path = manifest_path
        self._chunk_files_cache = None
        self._manifest_cache = None
    
    def get_chunk_files(self) -> List[str]:
        """获取所有chunk文件路径"""
        return get_chunk_files_cached(self.chunks_dir)
    
    def get_chunk_count(self) -> int:
        """获取chunk总数"""
        return get_chunk_count_cached(self.chunks_dir)
    
    def get_manifest(self) -> Dict:
        """获取manifest数据"""
        return get_manifest_cached(self.manifest_path)
    
    def get_files_with_new_chunks(self, existing_ids: Set[str]) -> Set[str]:
        """获取包含新chunk的文件名（不含扩展名）"""
        files_with_new_chunks = set()
        
        try:
            for chunk_file in self.get_chunk_files():
                with open(chunk_file, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                
                # 检查是否有新的chunk
                has_new_chunks = any(
                    chunk.get("chunk_id", "") not in existing_ids 
                    for chunk in chunks 
                    if chunk.get("chunk_id", "")
                )
                
                if has_new_chunks:
                    filename = os.path.basename(chunk_file)
                    # 正确提取文件stem：移除_chunks.json后缀
                    file_stem = filename.replace("_chunks.json", "")
                    files_with_new_chunks.add(file_stem)
        
        except Exception as e:
            st.error(f"检查新chunk失败: {e}")
        
        return files_with_new_chunks
    
    def clean_chunk_files(self, chunk_files: List[str]) -> List[str]:
        """清理chunk文件，移除空ID的chunk"""
        cleaned_files = []
        
        for chunk_file in chunk_files:
            try:
                with open(chunk_file, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                
                # 过滤空ID的chunk
                cleaned_chunks = [
                    chunk for chunk in chunks 
                    if chunk.get("chunk_id", "").strip()
                ]
                
                if cleaned_chunks:
                    # 写回清理后的数据
                    with open(chunk_file, "w", encoding="utf-8") as f:
                        json.dump(cleaned_chunks, f, ensure_ascii=False, indent=2)
                    cleaned_files.append(chunk_file)
            
            except Exception as e:
                st.error(f"清理文件 {chunk_file} 失败: {e}")
        
        return cleaned_files


class ProjectManager:
    """项目管理类"""
    
    def __init__(self, projects_dir: str):
        self.projects_dir = projects_dir
    
    def get_projects(self) -> List[str]:
        """获取所有项目列表"""
        try:
            return [
                d for d in os.listdir(self.projects_dir) 
                if os.path.isdir(os.path.join(self.projects_dir, d))
            ]
        except Exception as e:
            st.error(f"获取项目列表失败: {e}")
            return []
    
    def create_project(self, project_name: str) -> bool:
        """创建新项目"""
        try:
            # 验证项目名称
            if not project_name or not project_name.strip():
                st.error("项目名称不能为空")
                return False
            
            # 检查项目是否已存在
            if project_name in self.get_projects():
                st.error(f"项目 {project_name} 已存在")
                return False
            
            # 创建项目目录结构
            project_path = os.path.join(self.projects_dir, project_name)
            directories = [
                os.path.join(project_path, "raw_pdfs"),
                os.path.join(project_path, "processed", "chunks"),
                os.path.join(project_path, "vectorstore", "chroma_db")
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
            
            return True
        
        except Exception as e:
            st.error(f"创建项目失败: {e}")
            return False
    
    def get_project_paths(self, project_name: str) -> Dict[str, str]:
        """获取项目的所有路径"""
        base_path = os.path.join(self.projects_dir, project_name)
        
        return {
            "base": base_path,
            "raw_dir": os.path.join(base_path, "raw_pdfs"),
            "proc_dir": os.path.join(base_path, "processed"),
            "chunks_dir": os.path.join(base_path, "processed", "chunks"),
            "db_dir": os.path.join(base_path, "vectorstore", "chroma_db"),
            "manifest_path": os.path.join(base_path, "processed", "manifest.json")
        }


class UploadManager:
    """文件上传管理类"""
    
    def __init__(self, raw_dir: str):
        self.raw_dir = raw_dir
    
    def handle_file_upload(self, uploaded_files, last_uploaded_files: List[str]) -> Tuple[List[str], bool]:
        """
        处理文件上传
        返回: (新上传的文件名列表, 是否有文件被上传)
        """
        if not uploaded_files:
            return [], False
        
        current_upload_names = [f.name for f in uploaded_files]
        
        # 只有当上传文件列表发生变化时才处理
        if current_upload_names == last_uploaded_files:
            return [], False
        
        try:
            existing_files = set(os.listdir(self.raw_dir))
            uploaded_names = set()
            new_files = []
            actually_uploaded = False
            
            for file in uploaded_files:
                if file.name in existing_files and file.name not in last_uploaded_files:
                    # 只对本次新上传且已存在的文件提示
                    st.warning(f"文件 {file.name} 已存在")
                elif file.name not in existing_files and file.name not in uploaded_names:
                    # 安全地写入文件
                    file_path = os.path.join(self.raw_dir, file.name)
                    with open(file_path, "wb") as fw:
                        fw.write(file.getbuffer())
                    new_files.append(file.name)
                    uploaded_names.add(file.name)
                    actually_uploaded = True
            
            return new_files, actually_uploaded
        
        except Exception as e:
            st.error(f"文件上传失败: {e}")
            return [], False


@st.cache_data(ttl=300)  # 缓存5分钟
def get_chunk_files_cached(chunks_dir: str) -> List[str]:
    """获取chunk文件的缓存版本"""
    try:
        return glob.glob(os.path.join(chunks_dir, "*_chunks.json"))
    except Exception:
        return []

@st.cache_data(ttl=300)  # 缓存5分钟
def get_chunk_count_cached(chunks_dir: str) -> int:
    """获取chunk数量的缓存版本"""
    try:
        total_count = 0
        for chunk_file in get_chunk_files_cached(chunks_dir):
            with open(chunk_file, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                total_count += len(chunks)
        return total_count
    except Exception:
        return 0

@st.cache_data(ttl=300)  # 缓存5分钟
def get_manifest_cached(manifest_path: str) -> Dict:
    """获取manifest数据的缓存版本"""
    try:
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception:
        return {}


def get_embedding_model() -> str:
    """获取embedding模型名称"""
    return os.getenv("EMBED_MODEL", "text-embedding-3-large")


def clear_cache():
    """清理所有缓存"""
    st.cache_data.clear()
