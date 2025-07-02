# format_template.py

CARD_FORMAT_PROMPT = """
你是一个专业的Anki学习卡片生成助手。请根据下述要求和内容，生成{num_cards}张{card_type}类型的学习卡片，难度为{difficulty}，细节程度为{detail_level}。

用户查询: {query}

相关内容:
{context}

请严格按照以下CSV表格格式输出（不需要表头）：

- 若为"Q&A"类型，每行格式为：问题|答案|补充信息
  * 问题：清晰具体的问题，避免过于宽泛
  * 答案：详细完整的答案，包含关键要点、解释和步骤。对于概念题，需要包含定义、特点、应用等；对于计算题，需要包含完整计算过程和公式
  * 补充信息：相关概念、实例、数据、背景知识、应用场景或延伸阅读，帮助深入理解

- 若为"Cloze"类型，每行格式为：填空句子（使用{{c1::...}}格式标记需要隐藏的内容）

重要格式要求：
- 使用竖线"|"作为字段分隔符，不要使用逗号
- 如果内容中包含竖线，请用"丨"（中文竖线）替代
- 不要输出除CSV内容以外的任何文字，包括```csv等标记
- 根据提供的上下文内容生成卡片，不得添加上下文以外的内容
- 答案长度应为150-300字，补充信息应为100-200字
- 不需要标题行

示例格式：
什么是知识管理？|知识管理是指组织系统地收集、组织、共享和应用知识的过程，旨在提高组织的学习能力和创新能力。它包括显性知识和隐性知识的管理，通过建立知识库、专家网络等方式实现知识的有效利用。|知识管理在企业中的应用包括最佳实践分享、专家经验传承、创新管理等。著名的知识管理模型包括SECI模型（社会化、外化、组合、内化）和知识螺旋理论。
"""

CARD_FORMAT_PROMPT_EN = """
You are a professional Anki flashcard generation assistant. Based on the following requirements and content, generate {num_cards} {card_type} flashcards, with difficulty: {difficulty}, and detail level: {detail_level}.

User query: {query}

Relevant content:
{context}

Strictly output in the following format (no header):

- For "Q&A" type: Question|Answer|Extra Info
  * Question: Clear and specific question, avoid being too broad
  * Answer: Detailed and comprehensive answer including key points, explanations, and steps. For concepts, include definitions, characteristics, and applications; for calculations, include complete process and formulas
  * Extra Info: Related concepts, examples, data, background knowledge, application scenarios, or further reading to enhance understanding

- For "Cloze" type: Cloze sentence (use {{c1::...}} to mark hidden content)

Important formatting requirements:
- Use vertical bar "|" as field separator, NOT commas
- If content contains vertical bars, replace with "丨" (Chinese vertical bar)
- Do NOT output anything except the content, including ```csv markers
- Only use the provided context content; do not add external information
- Answer length should be 150-300 characters, Extra Info should be 100-200 characters
- No title rows needed

Example format:
What is knowledge management?|Knowledge management refers to the systematic process of collecting, organizing, sharing, and applying knowledge within an organization to enhance learning and innovation capabilities. It encompasses both explicit and tacit knowledge management through knowledge bases, expert networks, and other mechanisms.|Applications include best practice sharing, expert knowledge transfer, and innovation management. Famous models include the SECI model (Socialization, Externalization, Combination, Internalization) and knowledge spiral theory.
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
