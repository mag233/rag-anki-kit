# format_template.py
# 统一的模板管理中心

# ===== Anki 卡片生成模板 =====
CARD_FORMAT_PROMPT = """
你是一个专业的Anki学习卡片生成助手。请根据下述要求和内容，生成{num_cards}张{card_type}类型的学习卡片，难度为{difficulty}，细节程度为{detail_level}。

用户查询: {query}

相关内容:
{context}

请严格按照以下CSV表格格式输出（不需要表头）：

- 若为"Q&A"类型，每行格式为：1 详细描述的问题,2 详细的答案，计算题要有过程和anki友好的公式模型, 3 补充的相关背景信息
- 若为"Cloze"类型，每行格式为：填空句子（使用{{c1::...}}格式标记需要隐藏的内容）

注意事项：
- 不要输出除CSV内容以外的任何文字。
- 问题和答案或填空句子之间用英文逗号分隔。
- 根据提供的上下文内容，生成相关的学习卡片。不得使用上下文内容以外的内容。
- 生成的卡片要具有规定的的难度和细节程度，适合不同水平的学习者。
- 不需要标题行。
"""

CARD_FORMAT_PROMPT_EN = """
You are a professional Anki flashcard generation assistant. Based on the following requirements and content, generate {num_cards} {card_type} flashcards, with difficulty: {difficulty}, and detail level: {detail_level}.

User query: {query}

Relevant content:
{context}

Strictly output in the following CSV format (no header):

- For "Q&A" type: each line as Question,Answer,Extra Info
- For "Cloze" type: each line as a cloze sentence (use {{c1::...}} to mark hidden content)

Notes:
- Do NOT output anything except the CSV content.
- Use a comma to separate question and answer or cloze sentences.
- Only use the provided context content; do not invent additional information.
- The cards should be sufficiently detailed and challenging for learners at specified levels.
- No title rows needed.

Q&A Example:
who am I?, I am a cat.,This explains my behavior.
Cloze Example:
I am a {{c1::cat}}.,This explains my behavior.

Do not include any additional text or symbols such as ```csv.
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
Given the following user input, rewrite it as a clear, structured, and specific question or query for calculate the distance in the database. 
Keep the user's original intent and important details. Add keywords and phrases to enhance clarity and focus for retrieval.
Output only the improved query, nothing else.

User input:
{user_query}

Improved query:
"""

ANKI_PROMPT = """
Given the following user input, analyze the learning direction, focus, and main topic. Rewrite it as a clear, structured prompt suitable for generating learning material. 
Emphasize the core concepts, insights and key points that should be learned. 
Output only the improved prompt for embedding retrieval, nothing else.

User input:
{user_query}

"""
