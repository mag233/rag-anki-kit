# format_template.py
# 统一的模板管理中心

# ===== Anki 卡片生成模板 =====
CARD_FORMAT_PROMPT = """
你是一个专业的Anki学习卡片生成助手。请根据下述要求和内容，生成{num_cards}张{card_type}类型的学习卡片，难度为{difficulty}，细节程度为{detail_level}。

用户查询: {query}

相关内容:
{context}

请严格按照以下CSV表格格式输出（不需要表头）：

- 若为"Q&A"类型，每行格式为：问题,答案,补充信息

CSV格式要求：
- 如果文本内容包含逗号，必须用双引号包围整个文本
- 正确示例："什么是机器学习, 它的应用有哪些?","机器学习是一种AI技术，包括监督学习、无监督学习等方法。","广泛应用于图像识别、自然语言处理等领域。"
- 错误示例：什么是机器学习, 它的应用有哪些?,机器学习是一种AI技术，包括监督学习、无监督学习等方法。,广泛应用于图像识别、自然语言处理等领域。

卡片质量要求：
- 问题要具体、深入，避免泛泛而谈
- 答案要详细、准确，包含具体的定义、机制、数据或例子
- 补充信息要提供实用的背景知识、应用场景或相关概念
- 确保每张卡片都有独特的学习价值
- 根据难度调整问题复杂度：简单=基础概念，中等=应用理解，困难=深度分析
- 根据细节程度调整内容：简洁=核心要点，中等=适度展开，详细=全面深入

注意事项：
- 不要输出除CSV内容以外的任何文字
- 严格使用标准CSV格式，包含逗号的文本必须用双引号包围
- 严格基于提供的上下文内容，不得编造信息
- 每张卡片都要有实际学习价值，避免重复或过于简单的内容
- 不需要标题行或```csv标记
"""

CARD_FORMAT_PROMPT_EN = """
You are a professional Anki flashcard generation assistant. Based on the following requirements and content, generate {num_cards} {card_type} flashcards, with difficulty: {difficulty}, and detail level: {detail_level}.

User query: {query}

Relevant content:
{context}

Strictly output in the following CSV format (no header):

- For "Q&A" type: each line as Question,Answer,Extra Info

CSV Format Requirements:
- If text contains commas, enclose the entire text in double quotes
- Correct example: "What is machine learning, and how does it work?","Machine learning is a type of AI that enables systems to learn from data, improve performance over time without explicit programming.","It is widely used in image recognition, natural language processing, and other fields."
- Incorrect example: What is machine learning, and how does it work?,Machine learning is a type of AI that enables systems to learn from data, improve performance over time without explicit programming.,It is widely used in image recognition, natural language processing, and other fields.

Quality Requirements:
- Questions should be specific and in-depth, avoid generic inquiries
- Answers should be detailed and accurate, including specific definitions, mechanisms, data, or examples
- Extra info should provide useful background knowledge, application scenarios, or related concepts
- Ensure each card has unique learning value
- Adjust complexity based on difficulty: Easy=basic concepts, Medium=applied understanding, Hard=deep analysis
- Adjust content based on detail level: Concise=core points, Medium=moderate expansion, Detailed=comprehensive depth

Notes:
- Do NOT output anything except the CSV content
- Use standard CSV format with proper quoting for text containing commas
- Strictly base content on provided context; do not fabricate information
- Each card must have real learning value; avoid repetitive or overly simple content
- No title rows or ```csv markers needed
"""

# ===== 文献综述模板 =====
def get_literature_templates(lang):
    """获取文献综述相关模板"""
    if lang == "中文":
        return {
            "structured": """请用以下结构进行总结：
1. 研究背景
2. 主要发现
3. 挑战
4. 未来方向
5. 结论
6. 关键数据或案例
7. 参考文献""",
            "direct": """直接、简明地回答上述问题，仅使用上下文中的信息。如果无法明确回答，则说明"上下文信息不足"。""",
            "basic_prompt": """你获得了以下论文片段：

{context}

这里是你要总结的问题，仅用上下文回答，引用文献请遵循学术风格 [Chicago] 并尽量包含DOI。
#####{query}#####
"""
        }
    else:
        return {
            "structured": """Please summarize using the following structure:
1. Research Background
2. Key Findings
3. Challenges
4. Future Directions
5. Conclusions
6. Key Data or Case Studies
7. References""",
            "direct": """Provide a direct, concise answer to the above question using only the information from the context. If you cannot provide a clear answer, state "Insufficient context information".""",
            "basic_prompt": """You are given the following excerpts from research papers:

{context}

And here is the query you want to summarize, use only the information in the context.
Generate reference according formal academic writing style [Chicago style], include DOI whenever available.
#####{query}#####
"""
        }

# ===== 查询优化模板 =====
SUMMARIZE_PROMPT = """
You are an academic assistant. 
Given the following user input, rewrite it as a clear, structured, and specific question or query for academic research literature retrieval. 
Keep the user's original intent and important details. Add keywords and phrases to enhance clarity and focus for retrieval.
Output only the improved query, nothing else.

User input:
{user_query}

Improved query:
"""

ANKI_PROMPT = """
You are an academic learning assistant. Convert the following user input into a focused, concise query optimized for semantic document retrieval.

Instructions:
- Extract key concepts and technical terms
- Focus on core learning objectives  
- Make it concise and keyword-rich
- Avoid lengthy explanations or structured lists
- Output ONLY the final optimized query

Examples:

Input: "I want to learn about machine learning algorithms"
Output: machine learning algorithms supervised unsupervised neural networks classification regression

Input: "How does natural language processing work in AI systems"
Output: natural language processing NLP AI systems text analysis language models tokenization

Input: "Explain the basics of artificial intelligence and its applications"
Output: artificial intelligence AI basics applications machine learning neural networks automation

User input:
{user_query}

Optimized retrieval query:
"""
