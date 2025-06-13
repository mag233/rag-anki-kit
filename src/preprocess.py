# preprocess.py
import datetime
import os
import json
import hashlib
import logging
import re
from pathlib import Path

import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt', quiet=True)

from langchain.schema import Document
from langchain_community.document_loaders import (
    PyMuPDFLoader, TextLoader, UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader
)
from langchain.text_splitter import CharacterTextSplitter

# 只用 PyMuPDFLoader 解析 PDF
SUPPORTED_EXTENSIONS = {
    ".pdf": PyMuPDFLoader,
    ".txt": TextLoader,
    ".text": TextLoader,  # 新增
    ".docx": UnstructuredWordDocumentLoader,
    ".doc": UnstructuredWordDocumentLoader,
    ".xls": UnstructuredExcelLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".html": UnstructuredHTMLLoader,
    ".htm": UnstructuredHTMLLoader,
    ".md": UnstructuredMarkdownLoader,
    ".markdown": UnstructuredMarkdownLoader,
}

def process_documents(
    input_folder: str,
    output_folder: str,
    extract_tables: bool = True,
    extract_images: bool = True,
    extract_meta: bool = True,
    chunking_method: str = "按句子",
    chunk_size: int = 400,
    chunk_overlap: int = 50,
    force_reprocess: bool = False,
):
    """
    加载 input_folder 下所有支持文件，按 chunking_method 分块。
    如果 force_reprocess=True，会清空旧 chunks 并重跑所有文件。
    """

    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    chunks_folder    = output_folder / "chunks"
    tables_folder    = output_folder / "tables"
    images_folder    = output_folder / "images"
    equations_folder = output_folder / "equations"
    structure_folder = output_folder / "structure"
    manifest_path    = output_folder / "manifest.json"

    # 确保输出目录存在
    for d in [chunks_folder, tables_folder, images_folder, equations_folder, structure_folder]:
        d.mkdir(parents=True, exist_ok=True)

    # 如果强制重跑，清空旧 chunks 和 manifest
    if force_reprocess:
        for f in chunks_folder.glob("*_chunks.json"):
            try: f.unlink()
            except: pass
        manifest = {}
    else:
        # 读旧 manifest
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        else:
            manifest = {}

    # 统计信息
    total_files = 0
    processed_files = 0
    skipped_files = 0
    failed_files = 0

    # 遍历所有文件
    file_list = list(os.listdir(input_folder))
    total_files = len(file_list)
    print(f"[Chunk] Found {total_files} files in {input_folder}")

    for idx, file in enumerate(file_list, 1):
        src = input_folder / file
        ext = src.suffix.lower()
        loader_cls = SUPPORTED_EXTENSIONS.get(ext)
        if not loader_cls:
            print(f"[Chunk] [{idx}/{total_files}] Skipping unsupported file: {file}")
            skipped_files += 1
            continue

        # 计算文件 hash，判断是否需要处理
        current_hash = hashlib.md5(src.read_bytes()).hexdigest()
        prev = manifest.get(file, {})
        if not force_reprocess and prev.get("hash") == current_hash:
            print(f"[Chunk] [{idx}/{total_files}] Skipping unchanged file: {file}")
            skipped_files += 1
            continue

        print(f"[Chunk] [{idx}/{total_files}] Processing {file} ...")
        try:
            loader = loader_cls(str(src))
            docs = loader.load()
        except Exception as e:
            logging.error(f"Failed to load {file}: {e}")
            print(f"[Chunk] [{idx}/{total_files}] Failed to process {file}: {e}")
            failed_files += 1
            continue

        # 简单清洗：去掉 PDF 软换行、Markdown 多空行
        if ext == ".pdf":
            SOFT = re.compile(r"-\s*\n")
            MULTI = re.compile(r"\s+")
            for doc in docs:
                t = doc.page_content.replace("•", "")
                t = SOFT.sub("", t)
                t = MULTI.sub(" ", t)
                doc.page_content = t
        if ext in {".md", ".markdown"}:
            for doc in docs:
                # 去除多余空行，保留段落结构
                doc.page_content = re.sub(r"\n{3,}", "\n\n", doc.page_content)

        # —— 分块逻辑 —— 
        chunks = []
        if chunking_method == "按页":
            # PyMuPDFLoader 默认按页拆文档
            chunks = docs

        elif chunking_method == "按句子":
            for doc in docs:
                for i, sent in enumerate(sent_tokenize(doc.page_content)):
                    chunks.append(Document(
                        page_content=sent,
                        metadata={**doc.metadata, "chunk_id": f"{src.stem}_sent{i}"}
                    ))

        elif chunking_method == "按段落":
            for doc in docs:
                # 针对 Excel 文件，按单行分割
                if ext in {".xls", ".xlsx"}:
                    paras = doc.page_content.split("\n")
                else:
                    paras = doc.page_content.split("\n\n")
                for i, para in enumerate(paras):
                    para = para.strip()
                    if para:  # 跳过空段
                        chunks.append(Document(
                            page_content=para,
                            metadata={**doc.metadata, "chunk_id": f"{src.stem}_para{i}"}
                        ))

        else:  # 固定长度
            splitter = CharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            chunks = splitter.split_documents(docs)

        # 修正：为所有 chunk 自动补全 chunk_id，防止为空
        for idx, chunk in enumerate(chunks):
            if not chunk.metadata.get("chunk_id") or not str(chunk.metadata.get("chunk_id")).strip():
                chunk.metadata["chunk_id"] = f"{src.stem}_chunk{idx}"

        logging.info(f"[Chunk] {file}: {len(chunks)} chunks generated.")
        print(f"[Chunk] [{idx}/{total_files}] {file}: {len(chunks)} chunks generated.")

        # 写出 chunks JSON
        out = []
        for chunk in chunks:
            out.append({
                "chunk_id": chunk.metadata.get("chunk_id", ""),
                "chunk_text": chunk.page_content,
                "metadata": chunk.metadata
            })
        (chunks_folder / f"{src.stem}_chunks.json")\
            .write_text(json.dumps(out, ensure_ascii=False, indent=2),
                        encoding="utf-8")

        # 更新 manifest
        manifest[file] = {
            "hash": current_hash,
            "n_chunks": len(chunks),
            "last_processed": datetime.datetime.now().isoformat(),
            "chunk_method": chunking_method  # 新增字段
        }

        processed_files += 1

    # 保存 manifest
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print(f"[Chunk] Done. Total: {total_files}, Processed: {processed_files}, Skipped: {skipped_files}, Failed: {failed_files}")
    logging.info(f"[Chunk] Done. Total: {total_files}, Processed: {processed_files}, Skipped: {skipped_files}, Failed: {failed_files}")
