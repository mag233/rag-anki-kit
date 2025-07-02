# format_template.py

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

SUMMARIZE_PROMPT = """
You are an academic research assistant. 
Given the following user input, rewrite it as a clear, structured, and specific research question or query for academic literature retrieval. 
Keep the user's original intent and important details. Add relevant academic keywords and phrases to enhance clarity and focus for literature search.
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
