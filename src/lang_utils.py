# src/lang_utils.py

def get_text(lang):
    return {
        "tab_titles": {
            "RAG": "RAG 数据库管理" if lang == "中文" else "RAG Database",
            "Literature": "文献综述 + 问答数据库" if lang == "中文" else "Literature Review PLUS Database Q&A",
            "Anki": "Anki 记忆卡片" if lang == "中文" else "Anki Cards",
            "LitMap": "LitMap 知识图谱" if lang == "中文" else "LitMap Knowledge Graph",
        },
        "rag_tab": {
            "header": "RAG：项目与文件管理" if lang == "中文" else "RAG: Project and File Management",
            "select_project": "选择项目：" if lang == "中文" else "Select Project:",
            "new_project": "新建项目" if lang == "中文" else "New Project",
            "project_name_placeholder": "请输入新项目名称：" if lang == "中文" else "Enter new project name:",
            "create_btn": "创建项目" if lang == "中文" else "Create Project",
            "success": "✅ 项目 {name} 创建成功！" if lang == "中文" else "✅ Project {name} created successfully!",

            "step1_title": "### 步骤1：上传文件" if lang == "中文" else "### Step 1: Upload Files",
            "uploader_label": "上传 PDF/MD/DOCX/XLSX/HTML" if lang == "中文" else "Upload PDF/MD/DOCX/XLSX/HTML",
            "already_exists": "'{name}' 已存在。" if lang == "中文" else "'{name}' already exists.",
            "upload_success": "已上传: {files}" if lang == "中文" else "Uploaded: {files}",
            "no_new_file": "无新文件。" if lang == "中文" else "No new files.",
            "please_upload": "请上传文件。" if lang == "中文" else "Please upload files.",

            "db_overview": "数据库概览" if lang == "中文" else "Database Overview",
            "refresh_stats": "刷新统计信息" if lang == "中文" else "Refresh Statistics",
            "embedding_model": "嵌入模型" if lang == "中文" else "Embedding Model",
            "total_chunks": "总分块数" if lang == "中文" else "Total Chunks",
            "embedded_chunks": "已嵌入分块" if lang == "中文" else "Embedded Chunks",
            "document_count": "文档数量" if lang == "中文" else "Document Count",
            "chunks_embedded": "分块已嵌入" if lang == "中文" else "chunks embedded",
            "details": "详细信息" if lang == "中文" else "Details",
            "last_updated": "最后更新" if lang == "中文" else "Last Updated",
            "avg_content_length": "平均内容长度" if lang == "中文" else "Average Content Length",
            "dedup_status": "去重状态" if lang == "中文" else "Deduplication Status",
            "dedup_enabled": "已启用" if lang == "中文" else "Enabled",
            "dedup_disabled": "未启用" if lang == "中文" else "Disabled",
            "db_operations": "数据库操作" if lang == "中文" else "Database Operations",
            "db_health_check": "健康检查" if lang == "中文" else "Health Check",
            "check_db": "检查数据库连接和完整性" if lang == "中文" else "Check database connection and integrity",
            "db_healthy": "数据库健康，包含" if lang == "中文" else "Database is healthy, contains",
            "db_healthy_embeddings": "个嵌入向量" if lang == "中文" else "embeddings",
            "db_connection_failed": "数据库连接失败:" if lang == "中文" else "Database connection failed:",
            "remove_duplicates": "清理重复项" if lang == "中文" else "Remove Duplicates",
            "remove_duplicates_help": "删除重复的嵌入向量以优化存储" if lang == "中文" else "Remove duplicate embeddings to optimize storage",
            "duplicates_removed": "已删除" if lang == "中文" else "Removed",
            "duplicates_count": "个重复项" if lang == "中文" else "duplicates",
            "no_duplicates": "未发现重复项" if lang == "中文" else "No duplicates found",
            "remove_duplicates_failed": "清理重复项失败:" if lang == "中文" else "Failed to remove duplicates:",
            "danger_zone": "危险区域" if lang == "中文" else "Danger Zone",
            "irreversible_warning": "以下操作不可逆，请谨慎操作" if lang == "中文" else "The following operations are irreversible, please proceed with caution",
            "confirm_clear_all": "我确认要清空所有嵌入向量" if lang == "中文" else "I confirm to clear all embeddings",
            "clear_all_embeddings": "清空所有嵌入" if lang == "中文" else "Clear All Embeddings",
            "clear_all_help": "删除所有嵌入向量，保留文档和分块" if lang == "中文" else "Delete all embeddings while keeping documents and chunks",
            "clear_success": "所有嵌入已清空" if lang == "中文" else "All embeddings cleared",
            "clear_failed": "清空失败" if lang == "中文" else "Clear operation failed",
            "clear_failed_error": "清空操作失败:" if lang == "中文" else "Clear operation failed:",
            "stats_error": "获取统计信息失败:" if lang == "中文" else "Failed to get statistics:",

            "step2_title": "### 步骤2：预处理文件（分块）" if lang == "中文" else "### Step 2: Preprocess Files (Chunking)",
            "chunk_method": "分块方式：" if lang == "中文" else "Chunking method:",
            "chunk_methods": ["按句子","按段落","按页","固定长度"] if lang == "中文" else ["By Sentence","By Paragraph","By Page","Fixed Length"],
            "chunk_length": "固定长度" if lang == "中文" else "Fixed Length",
            "chunk_length_label": "分块长度（字符）" if lang == "中文" else "Chunk length (chars)",
            "force_reprocess": "强制全部重新预处理（忽略 hash，适用于参数变更或修复）" if lang == "中文" else "Force full reprocessing (ignore hash; for param change/fix)",
            "start_preprocess": "开始预处理" if lang == "中文" else "Start Preprocessing",
            "preprocess_success": "预处理完成！" if lang == "中文" else "Preprocessing complete!",
            "preprocess_fail": "预处理失败: {err}" if lang == "中文" else "Preprocessing failed: {err}",

            "step3_title": "### 步骤3：生成/更新向量" if lang == "中文" else "### Step 3: Create/Update Embeddings",
            "embed_mode": "向量生成方式：" if lang == "中文" else "Embedding mode:",
            "embed_modes": ["全部重新生成向量","仅新增分块"] if lang == "中文" else ["Embed all","Only new chunks"],
            "only_new_chunks": "仅新增分块" if lang == "中文" else "Only new chunks",
            "mode_help_only_new": "仅处理新上传或未嵌入的分块，节省时间和成本" if lang == "中文" else "Only process newly uploaded or unembedded chunks to save time and cost",
            "mode_help_embed_all": "重新处理所有分块，确保数据一致性" if lang == "中文" else "Reprocess all chunks to ensure data consistency",
            "advanced_options": "高级选项" if lang == "中文" else "Advanced Options",
            "force_reprocess_embed": "强制重新处理所有向量" if lang == "中文" else "Force reprocess all embeddings",
            "force_reprocess_embed_help": "忽略现有向量，重新生成所有向量" if lang == "中文" else "Ignore existing embeddings and regenerate all",
            "enable_deduplication": "启用去重" if lang == "中文" else "Enable Deduplication",
            "enable_deduplication_help": "防止重复内容生成多个向量" if lang == "中文" else "Prevent duplicate content from generating multiple embeddings",
            "pending_embed": "待嵌入:" if lang == "中文" else "Pending:",
            "complete_embed": "嵌入完成" if lang == "中文" else "Embedding Complete",
            "processing_session_files": "处理本次上传的文件:" if lang == "中文" else "Processing files from this session:",
            "auto_detect_chunks": "自动检测需要嵌入的分块" if lang == "中文" else "Auto-detecting chunks that need embedding",
            "processing_all_chunks": "处理所有分块" if lang == "中文" else "Processing all chunks",
            "start_embed": "生成向量" if lang == "中文" else "Generate Embeddings",
            "embed_success": "向量生成完成！" if lang == "中文" else "Embedding complete!",
            "duplicate_ids": "检测到重复ID，已跳过: {ids}" if lang == "中文" else "Duplicate IDs detected, skipped: {ids}",
            "partial_embed": "部分分块因ID重复未被生成向量，其余已完成。" if lang == "中文" else "Some chunks skipped due to duplicate IDs, others done.",
            "embed_fail": "向量生成失败: {err}" if lang == "中文" else "Embedding failed: {err}",

            "manifest_check_title": "#### 📊 Manifest 健康检查" if lang == "中文" else "#### 📊 Manifest Health Check",
            "missing_chunks": "未生成分块的文件: {files}" if lang == "中文" else "Files with no chunks: {files}",
            "all_chunked": "所有文件均已分块。" if lang == "中文" else "All files are chunked.",

            "status_title": "#### 当前分块 & 向量 状态" if lang == "中文" else "#### Current Chunk & Embedding Status",
            "embed_model": "向量模型: **{model}**" if lang == "中文" else "Embedding model: **{model}**",
            "chunk_count": "当前分块总数: **{n}**" if lang == "中文" else "Total Chunks: **{n}**",
            "embed_count": "当前向量数量: **{n}**" if lang == "中文" else "Total Embeddings: **{n}**",
            "progress_label": "向量进度（已入库/分块）" if lang == "中文" else "Embedding Progress (completed/chunks)",

            "manifest_title": "#### 📄 文件处理状态 (manifest)" if lang == "中文" else "#### 📄 File Processing Status (manifest)",
            "manifest_col_file": "文件" if lang == "中文" else "File",
            "manifest_col_nchunks": "分块数" if lang == "中文" else "Chunks",
            "manifest_col_chunkmethod": "分块方式" if lang == "中文" else "Chunk Method",
            "manifest_col_last": "最后处理" if lang == "中文" else "Last Processed",
            "no_manifest": "暂无 manifest.json，尚未预处理。" if lang == "中文" else "No manifest.json, not yet processed.",
        },
        "literature_tab": {
            "header": "文献综述与问答" if lang == "中文" else "Literature Review & QA",
            "step1_title": "### 步骤1：选择项目" if lang == "中文" else "### Step 1: Select Project",
            "step1_info": "请选择要进行文献综述和问答的项目，请确保已在RAG标签中上传并处理PDF。" if lang == "中文" else "Select a project to perform literature review and QA. Please make sure you have already uploaded and processed your PDFs in the RAG tab.",
            "select_project": "文献综述项目选择：" if lang == "中文" else "Select Project for Literature Review:",
            "no_project": "请先选择项目" if lang == "中文" else "Please select a project",
            "no_db_warning": "请先为该项目生成嵌入（见RAG标签）。" if lang == "中文" else "Please generate embeddings for this project first (see RAG tab).",

            "step2_title": "### 步骤2：输入检索问题" if lang == "中文" else "### Step 2: Enter Your Query",
            "step2_info": "描述你的研究问题或信息需求，系统将优化你的检索意图以获得更好结果。" if lang == "中文" else "Describe your research question or information need. The system will help you standardize and optimize your query for better retrieval.",
            "optimize_prompt": "进行检索意图优化（Prompt Optimization）" if lang == "中文" else "Prompt Optimization",
            "query_input": "请输入你的检索问题：" if lang == "中文" else "Enter Your Query:",
            "optimizing": "正在优化检索意图..." if lang == "中文" else "Prompt Optimization in progress...",
            "optimized_prompt": "优化后的检索意图: {prompt}" if lang == "中文" else "Optimized Prompt: {prompt}",

            "step3_title": "### 步骤3：编辑摘要模板" if lang == "中文" else "### Step 3: Customize Summarization Template",
            "step3_info": "你可以自定义摘要输出格式，模板支持分节及学术写作风格。" if lang == "中文" else "You can customize the output format for the summary. The template supports sections and academic writing style.",
            "default_structured": """请用以下结构进行总结：
1. 研究背景
2. 主要发现
3. 挑战
4. 未来方向
5. 结论
6. 关键数据或案例
7. 参考文献""" if lang == "中文" else """Please summarize using the following structure:
1. Research Background
2. Key Findings
3. Challenges
4. Future Directions
5. Conclusions
6. Key Data or Case Studies
7. References""",
            "default_direct": """直接、简明地回答上述问题，仅使用上下文中的信息。如果无法明确回答，则说明"上下文信息不足"。""" if lang == "中文" else """Provide a direct and concise answer to the question above, using only the information from the context. If unable to provide a clear answer, state "Insufficient context information".""",
            "structured_review": "**结构化文献综述**" if lang == "中文" else "**Structured Literature Review**",
            "structured_template": "结构化模板" if lang == "中文" else "Structured Template",
            "direct_answer": "**直接回答**" if lang == "中文" else "**Direct Answer**",
            "direct_template": "直接回答模板" if lang == "中文" else "Direct Answer Template",
            "choose_template": "选择摘要模板风格：" if lang == "中文" else "Choose summary template style:",
            "structured": "结构化" if lang == "中文" else "Structured",
            "direct": "直接回答" if lang == "中文" else "Direct Answer",

            "step4_title": "### 步骤4：检索参数设置与检索" if lang == "中文" else "### Step 4: Retrieval Settings & Run Retrieval",
            "step4_info": "调整检索参数。若无结果，可适当降低相似度阈值。" if lang == "中文" else "Adjust the retrieval parameters. If you get no results, try increasing the maximum distance threshold.",
            "relevance_threshold": "最小相似度阈值：" if lang == "中文" else "Set Minimum Similarity Score (Relevance Threshold):",
            "relevance_help": "值越高匹配越严格，若无结果可适当降低。" if lang == "中文" else "Higher values mean stricter match (more similar). If you get no results, try lowering this value.",
            "num_chunks": "检索块数：" if lang == "中文" else "Select Number of Chunks to Retrieve:",
            "run_retrieval": "执行检索" if lang == "中文" else "Run Retrieval",
            "retrieving": "正在检索相关分块..." if lang == "中文" else "Retrieving relevant chunks...",
            "chunks_found": "{n} 个分块已找到" if lang == "中文" else "{n} Chunks Found",

            "step5_title": "### 步骤5：生成摘要" if lang == "中文" else "### Step 5: Summarize Retrieved Chunks",
            "step5_info": "基于检索内容和你的模板生成结构化摘要。" if lang == "中文" else "Generate a structured summary based on the retrieved content and your template.",
            "select_model": "选择模型：" if lang == "中文" else "Select Model:",
            "model_options": ["gpt-4o", "gpt-4o-mini", "qwen-max", "qwen-plus", "qwen-turbo"],
            "temperature": "Temperature (创造性)：" if lang == "中文" else "Temperature (Creativity):",
            "temp_help": "值越高输出越有创造力，常用范围0.2~1.0" if lang == "中文" else "Higher values produce more creative output. Typical range: 0.2~1.0",
            "max_tokens": "最大输出 tokens：" if lang == "中文" else "Max Tokens:",
            "max_tokens_help": "摘要输出最大token数。" if lang == "中文" else "Maximum number of tokens in the summary output.",
            "log_metrics": "记录token消耗与处理时间" if lang == "中文" else "Log Token Consumption and Processing Time",
            "generate_summary": "生成摘要" if lang == "中文" else "Generate Summary",
            "summarizing": "正在生成摘要..." if lang == "中文" else "Summarizing Retrieved Chunks...",
            "show_time": "处理用时：{time} 秒" if lang == "中文" else "Processing Time: {time} seconds",
            "show_tokens": "总 tokens：{tokens}" if lang == "中文" else "Total Tokens: {tokens}",
            "summary_fail": "摘要生成失败，请检查输入或模板。" if lang == "中文" else "Summary generation failed, please check your input and template.",
            "no_chunks": "无分块可用，请先检索。" if lang == "中文" else "No chunks found for summarization. Please run retrieval first.",
            "basic_prompt": """你获得了以下论文片段：

{context}

这里是你要总结的问题，仅用上下文回答，引用文献请遵循学术风格 [Chicago] 并尽量包含DOI。
#####{query}#####
""" if lang == "中文" else """You are given the following excerpts from research papers:

{context}

And here is the query you want to summarize, use only the information in the context.
Generate reference according formal academic writing style [Chicago style], include DOI whenever available.
#####{query}#####
""",
        },
        "anki_tab": {
            "header": "生成 Anki 卡片" if lang == "中文" else "Generate Anki Cards",
            "no_projects": "未发现项目，请先在文献分析页创建项目。" if lang == "中文" else "No projects found. Please create a project in the Literature Analysis tab first.",
            "select_project": "选择卡片项目：" if lang == "中文" else "Select Project for Cards:",
            "select_project_help": "请选择包含要制作卡片的文档的项目" if lang == "中文" else "Choose the project containing the documents you want to create cards from",
            "please_select_project": "请先选择项目" if lang == "中文" else "Please select a project",
            "preprocess_warning": "请先为该项目预处理并生成嵌入（见RAG标签）。" if lang == "中文" else "Please preprocess and embed documents in this project first (see RAG tab).",
            "using_llm": "使用大语言模型生成高质量卡片" if lang == "中文" else "Using LLM for high-quality card generation",
            "card_type": "卡片类型：" if lang == "中文" else "Card Type:",
            "qa": "问答" if lang == "中文" else "Q&A",
            "cloze": "填空" if lang == "中文" else "Cloze",
            "card_type_help": "问答卡片为问答形式，填空卡片为完型填空" if lang == "中文" else "Q&A creates question-answer pairs, Cloze creates fill-in-the-blank style cards",
            "num_cards": "生成卡片数：" if lang == "中文" else "Number of Cards:",
            "num_cards_help": "要生成多少张卡片" if lang == "中文" else "How many cards to generate",
            "difficulty": "难度：" if lang == "中文" else "Difficulty:",
            "difficulty_options": ["简单", "中等", "困难"] if lang == "中文" else ["Easy", "Medium", "Hard"],
            "difficulty_default": "中等" if lang == "中文" else "Medium",
            "difficulty_help": "控制问题的复杂程度" if lang == "中文" else "Controls the complexity of the questions",
            "detail_level": "详细程度：" if lang == "中文" else "Detail Level:",
            "detail_level_options": ["简洁", "中等", "详细"] if lang == "中文" else ["Concise", "Medium", "Detailed"],
            "detail_level_default": "中等" if lang == "中文" else "Medium",
            "detail_level_help": "控制每张卡片的信息量" if lang == "中文" else "Controls how much information to include in each card",
            "query_input": "请输入主题或知识点：" if lang == "中文" else "Enter your query:",
            "query_help": "输入你想制作卡片的主题或概念，系统会自动检索相关内容" if lang == "中文" else "Enter the topic or concept you want to create cards for. The system will find relevant content from your documents.",
            "optimize_prompt": "优化查询" if lang == "中文" else "Optimize Query",
            "optimize_help": "使用AI优化您的查询以获得更好的检索效果" if lang == "中文" else "Use AI to optimize your query for better retrieval",
            "optimizing": "正在优化查询..." if lang == "中文" else "Optimizing query...",
            "optimized_query": "优化后的查询" if lang == "中文" else "Optimized Query",
            "current_query": "当前查询" if lang == "中文" else "Current Query",
            "standardized_query": "使用查询" if lang == "中文" else "Using query",
            "retrieval_complete": "检索完成！" if lang == "中文" else "Retrieval completed!",
            "question": "问题" if lang == "中文" else "Question",
            "answer": "答案" if lang == "中文" else "Answer", 
            "extra_info": "补充信息" if lang == "中文" else "Extra Info",
            "top_k": "检索Top-K分块：" if lang == "中文" else "Top-K Chunks to Retrieve:",
            "top_k_help": "每次检索多少分块用于卡片生成" if lang == "中文" else "How many relevant chunks to retrieve for card generation",
            "relevance_threshold": "最小相似度分数：" if lang == "中文" else "Minimum Similarity Score (Relevance Threshold):",
            "relevance_threshold_help": "值越高匹配越严格，若无结果可适当降低" if lang == "中文" else "Higher values mean stricter match (more similar). If you get no results, try lowering this value.",
            "retrieve_chunks": "检索相关分块" if lang == "中文" else "Retrieve Relevant Chunks",
            "retrieving": "正在检索相关分块..." if lang == "中文" else "Retrieving relevant chunks...",
            "preview_chunks": "检索到的分块预览：" if lang == "中文" else "Preview of retrieved chunks:",
            "please_enter_query": "请先输入检索主题" if lang == "中文" else "Please enter a query first",
            "chunks_retrieved": "检索到 {n} 个相关分块。" if lang == "中文" else "Retrieved {n} relevant chunks.",
            "chunk_id": "**分块 {idx}:** {src}" if lang == "中文" else "**Chunk {idx}:** {src}",
            "no_chunks_found": "未检索到相关分块，请尝试降低阈值或增大Top-K。" if lang == "中文" else "No relevant chunks found. Try lowering the threshold or increasing Top-K.",
            "generate_cards": "生成卡片" if lang == "中文" else "Generate Cards",
            "please_retrieve_chunks": "请先检索相关分块" if lang == "中文" else "Please retrieve relevant chunks first",
            "generating_cards": "正在生成卡片..." if lang == "中文" else "Generating cards...",
            "llm_output": "LLM输出（CSV格式）：" if lang == "中文" else "LLM Output (CSV format):",
            "no_content_preview": "无内容可预览。" if lang == "中文" else "No content to preview.",
            "error_generating": "生成卡片出错: {err}" if lang == "中文" else "Error generating cards: {err}",
            "export_csv": "导出为CSV" if lang == "中文" else "Export to CSV",
            "csv_saved": "CSV文件已保存至: {path}" if lang == "中文" else "CSV file saved to: {path}",
            "download_cards": "下载卡片" if lang == "中文" else "Download Cards",
        },
        "litmap_tab": {
            "header": "LitMap 知识图谱生成" if lang == "中文" else "LitMap Knowledge Graph Generation",
            "description": "从研究文献中自动提取实体和关系，构建交互式知识图谱，帮助理解研究领域的概念网络。" if lang == "中文" else "Automatically extract entities and relationships from research literature to build interactive knowledge graphs, helping understand concept networks in research fields.",
            
            # Step titles
            "step1_title": "第一步：项目选择" if lang == "中文" else "Step 1: Project Selection",
            "step1_info": "选择已预处理文档的项目，用于知识图谱生成。" if lang == "中文" else "Select a project with preprocessed documents for knowledge graph generation.",
            "step2_title": "第二步：配置设置" if lang == "中文" else "Step 2: Configuration Settings", 
            "step2_info": "调整知识图谱生成参数，包括处理数量和置信度阈值。" if lang == "中文" else "Adjust knowledge graph generation parameters including processing limits and confidence thresholds.",
            "step2_help_title": "配置参数说明" if lang == "中文" else "Configuration Parameters Help",
            "step2_help_content": """
**最大处理分块数：** 限制处理的文档分块数量。推荐从20-50开始测试，较多的分块会增加成本但提供更全面的知识图谱。

**置信度阈值：** 过滤AI提取结果的最低置信度。较高的阈值(0.7+)会产生更准确但可能更少的结果。

**启用实体去重：** 自动合并相似的实体(如"machine learning"和"ML")，减少冗余。

**启用物理模拟：** 在交互式网络图中启用物理引擎，使节点自动布局和动画效果。
            """ if lang == "中文" else """
**Maximum Chunks to Process:** Limits the number of document chunks to process. Recommend starting with 20-50 for testing. More chunks increase cost but provide more comprehensive knowledge graphs.

**Confidence Threshold:** Filters AI extraction results by minimum confidence. Higher thresholds (0.7+) produce more accurate but potentially fewer results.

**Enable Entity Deduplication:** Automatically merges similar entities (e.g., "machine learning" and "ML") to reduce redundancy.

**Enable Physics Simulation:** Enables physics engine in interactive network graphs for automatic layout and animation effects.
            """,
            "step3_title": "第三步：实体与关系类型选择" if lang == "中文" else "Step 3: Entity and Relation Type Selection",
            "step3_info": "选择要从文献中提取的实体和关系类型。" if lang == "中文" else "Choose which entity and relation types to extract from literature.",
            "step3_help_title": "实体和关系类型说明" if lang == "中文" else "Entity and Relation Types Help",
            "step3_help_content": """
**实体类型说明：**
- **研究主题(research_topic)：** 研究的核心领域或话题
- **方法论(methodology)：** 研究方法、技术或工具
- **研究人群(population)：** 研究对象、样本群体
- **结果(outcome)：** 研究发现、结论或测量指标
- **概念(concept)：** 理论概念或抽象概念
- **疾病(disease)：** 疾病、症状或健康状况
- **治疗(treatment)：** 治疗方法、药物或干预措施
- **发现(finding)：** 具体的研究发现或观察结果

**关系类型说明：**
- **使用方法(uses_method)：** 研究使用某种方法
- **研究人群(studies_population)：** 研究某个人群
- **调查主题(investigates_topic)：** 研究某个主题
- **报告结果(reports_outcome)：** 报告某个结果
- **相关性(relates_to)：** 一般性关联关系
- **因果关系(causes)：** 因果关系
- **治疗关系(treats)：** 治疗某种疾病
- **影响关系(affects)：** 影响某个对象
            """ if lang == "中文" else """
**Entity Types:**
- **Research Topic:** Core research fields or topics
- **Methodology:** Research methods, techniques, or tools
- **Population:** Study subjects or sample groups
- **Outcome:** Research findings, conclusions, or measured metrics
- **Concept:** Theoretical or abstract concepts
- **Disease:** Diseases, symptoms, or health conditions
- **Treatment:** Treatment methods, drugs, or interventions
- **Finding:** Specific research findings or observations

**Relation Types:**
- **Uses Method:** Research uses a certain method
- **Studies Population:** Studies a certain population
- **Investigates Topic:** Investigates a certain topic
- **Reports Outcome:** Reports a certain outcome
- **Relates To:** General associative relationship
- **Causes:** Causal relationship
- **Treats:** Treats a certain disease
- **Affects:** Affects a certain object
            """,
            "step4_title": "第四步：知识图谱生成" if lang == "中文" else "Step 4: Knowledge Graph Generation",
            "step4_info": "开始从文档中提取实体和关系，构建知识图谱。" if lang == "中文" else "Start extracting entities and relations from documents to build the knowledge graph.",
            "step4_help_title": "知识图谱生成说明" if lang == "中文" else "Knowledge Graph Generation Help",
            "step4_help_content": """
**生成过程：**
1. 将文档分块送入GPT模型进行实体识别
2. 对识别的实体进行关系抽取
3. 计算置信度并过滤低质量结果
4. 去重和标准化实体名称
5. 构建网络图结构

**注意事项：**
- 生成过程可能需要几分钟，取决于文档数量
- 会产生OpenAI API调用费用，建议先小规模测试
- 结果会自动保存，可重复使用避免重复计算
- 建议在网络稳定的环境下运行
            """ if lang == "中文" else """
**Generation Process:**
1. Send document chunks to GPT model for entity recognition
2. Extract relationships between identified entities
3. Calculate confidence scores and filter low-quality results
4. Deduplicate and standardize entity names
5. Build network graph structure

**Important Notes:**
- Generation may take several minutes depending on document quantity
- Will incur OpenAI API costs - recommend testing with small datasets first
- Results are automatically saved and can be reused to avoid recomputation
- Recommend running in stable network environment
            """,
            "step5_title": "第五步：提取结果" if lang == "中文" else "Step 5: Extraction Results",
            "step6_title": "第六步：知识图谱可视化" if lang == "中文" else "Step 6: Knowledge Graph Visualization",
            
            # Project Selection
            "project_selection": "项目选择" if lang == "中文" else "Project Selection",
            "no_project": "请先选择项目" if lang == "中文" else "Please select a project first",
            "no_projects": "未发现项目，请先在RAG标签页创建项目。" if lang == "中文" else "No projects found. Please create a project in the RAG tab first.",
            "select_project": "选择知识图谱项目：" if lang == "中文" else "Select Project for Knowledge Graph:",
            "please_select_project": "请先选择项目" if lang == "中文" else "Please select a project",
            "no_chunks_warning": "此项目尚未处理文档。请先在RAG标签页上传并预处理PDF文件。" if lang == "中文" else "No processed documents found in this project. Please upload and preprocess PDF files in the RAG tab first.",
            
            # Configuration
            "configuration": "知识图谱配置" if lang == "中文" else "Knowledge Graph Configuration",
            "max_chunks": "最大处理分块数：" if lang == "中文" else "Maximum Chunks to Process:",
            "max_chunks_help": "限制处理的文档分块数量以控制成本和时间" if lang == "中文" else "Limit the number of document chunks to process for cost and time control",
            "confidence_threshold": "置信度阈值：" if lang == "中文" else "Confidence Threshold:",
            "confidence_help": "过滤低置信度的实体和关系" if lang == "中文" else "Filter out low-confidence entities and relationships",
            "enable_deduplication": "启用实体去重" if lang == "中文" else "Enable Entity Deduplication",
            "deduplication_help": "合并相似的实体以简化图谱" if lang == "中文" else "Merge similar entities to simplify the graph",
            "physics_enabled": "启用物理模拟" if lang == "中文" else "Enable Physics Simulation",
            "physics_help": "在交互式可视化中启用物理引擎" if lang == "中文" else "Enable physics engine in interactive visualization",
            
            # Entity and Relation Configuration
            "entity_relation_config": "实体与关系类型配置" if lang == "中文" else "Entity and Relation Type Configuration",
            "entity_types": "选择实体类型：" if lang == "中文" else "Select Entity Types:",
            "entity_types_help": "选择要从文献中提取的实体类型" if lang == "中文" else "Choose which entity types to extract from literature",
            "relation_types": "选择关系类型：" if lang == "中文" else "Select Relation Types:",
            "relation_types_help": "选择要识别的关系类型" if lang == "中文" else "Choose which relation types to identify",
            
            # Knowledge Graph Generation
            "knowledge_graph_generation": "知识图谱生成" if lang == "中文" else "Knowledge Graph Generation",
            "existing_results_found": "发现已有的提取结果" if lang == "中文" else "Found existing extraction results",
            "load_existing": "加载已有结果" if lang == "中文" else "Load Existing Results",
            "load_existing_help": "使用之前保存的实体和关系数据" if lang == "中文" else "Use previously saved entity and relation data",
            "regenerate": "重新生成" if lang == "中文" else "Regenerate",
            "regenerate_help": "重新分析文档并提取实体关系" if lang == "中文" else "Re-analyze documents and extract entity relationships",
            "generate_knowledge_graph": "生成知识图谱" if lang == "中文" else "Generate Knowledge Graph",
            "generate_help": "开始从文档中提取实体和关系" if lang == "中文" else "Start extracting entities and relationships from documents",
            
            # Processing Status
            "initializing_extraction": "正在初始化提取过程..." if lang == "中文" else "Initializing extraction process...",
            "loading_chunks": "正在加载文档分块..." if lang == "中文" else "Loading document chunks...",
            "no_chunks_found": "未找到文档分块" if lang == "中文" else "No document chunks found",
            "processing_chunks": "正在处理 {n} 个分块" if lang == "中文" else "Processing {n} chunks",
            "extracting_entities_relations": "正在提取实体和关系..." if lang == "中文" else "Extracting entities and relationships...",
            "extraction_complete": "提取完成！发现 {entities} 个实体和 {relations} 个关系" if lang == "中文" else "Extraction complete! Found {entities} entities and {relations} relationships",
            "loaded_existing_results": "已加载已有结果" if lang == "中文" else "Loaded existing results",
            
            # Results Display
            "extraction_results": "提取结果" if lang == "中文" else "Extraction Results",
            "total_entities": "实体总数" if lang == "中文" else "Total Entities",
            "total_relations": "关系总数" if lang == "中文" else "Total Relations",
            "avg_entity_confidence": "平均实体置信度" if lang == "中文" else "Average Entity Confidence",
            "avg_relation_confidence": "平均关系置信度" if lang == "中文" else "Average Relation Confidence",
            "entity_summary": "实体类型统计" if lang == "中文" else "Entity Type Summary",
            "relation_summary": "关系类型统计" if lang == "中文" else "Relation Type Summary",
            "no_entities": "未发现实体" if lang == "中文" else "No entities found",
            "no_relations": "未发现关系" if lang == "中文" else "No relationships found",
            "most_connected": "连接度最高的实体" if lang == "中文" else "Most Connected Entities",
            
            # Visualization
            "knowledge_graph_visualization": "知识图谱可视化" if lang == "中文" else "Knowledge Graph Visualization",
            "building_graph": "正在构建图谱..." if lang == "中文" else "Building graph...",
            "graph_nodes": "图谱节点数" if lang == "中文" else "Graph Nodes",
            "graph_edges": "图谱边数" if lang == "中文" else "Graph Edges",
            "graph_density": "图谱密度" if lang == "中文" else "Graph Density",
            "visualization_type": "可视化类型：" if lang == "中文" else "Visualization Type:",
            "interactive_network": "交互式网络图" if lang == "中文" else "Interactive Network",
            "static_plotly": "静态网络图" if lang == "中文" else "Static Network Plot",
            "statistics_dashboard": "统计仪表板" if lang == "中文" else "Statistics Dashboard",
            "creating_visualization": "正在创建可视化..." if lang == "中文" else "Creating visualization...",
            "creating_dashboard": "正在创建仪表板..." if lang == "中文" else "Creating dashboard...",
            "insufficient_data": "数据不足，无法生成有意义的可视化" if lang == "中文" else "Insufficient data to generate meaningful visualization",
            
            # Export Options
            "export_options": "导出选项" if lang == "中文" else "Export Options",
            "export_graph_data": "导出图谱数据" if lang == "中文" else "Export Graph Data",
            "export_visualization": "导出可视化" if lang == "中文" else "Export Visualization",
            "graph_exported": "图谱数据已导出至：{path}" if lang == "中文" else "Graph data exported to: {path}",
            "visualization_exported": "可视化已导出至：{path}" if lang == "中文" else "Visualization exported to: {path}",
            "select_project_and_configure": "请选择项目并配置参数后开始生成知识图谱" if lang == "中文" else "Please select a project and configure parameters to start generating knowledge graph",
        }
    }
