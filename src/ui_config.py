# ui_config.py
"""
UI配置和多语言映射
负责UI显示文本到内核标识符的转换
"""

# 分块方法映射：UI显示文本 -> 内核标识符
CHUNKING_METHOD_MAPPING = {
    # 中文映射
    "按句子": "by_sentence",
    "按段落": "by_paragraph", 
    "按页": "by_page",
    "固定长度": "fixed_size",
    
    # 英文映射（直接传递）
    "by_sentence": "by_sentence",
    "by_paragraph": "by_paragraph",
    "by_page": "by_page", 
    "fixed_size": "fixed_size",
    
    # 其他可能的别名
    "sentence": "by_sentence",
    "paragraph": "by_paragraph",
    "page": "by_page",
    "size": "fixed_size",
}

# 清洗级别映射：UI显示文本 -> 内核标识符
CLEANING_LEVEL_MAPPING = {
    # 中文映射
    "基础清洗": "basic",
    "深度清洗": "deep",
    
    # 英文映射（直接传递）
    "basic": "basic",
    "deep": "deep",
    
    # 其他可能的别名
    "basic_clean": "basic",
    "deep_clean": "deep",
    "standard": "basic",
    "advanced": "deep",
}

# UI显示用的分块方法选项（用于界面下拉框）
CHUNKING_METHOD_OPTIONS = [
    "按句子",      # by_sentence
    "按段落",      # by_paragraph  
    "按页",        # by_page
    "固定长度"     # fixed_size
]

# UI显示用的清洗级别选项（用于界面单选框）
CLEANING_LEVEL_OPTIONS = [
    "基础清洗",    # basic
    "深度清洗"     # deep
]

def get_chunking_method(ui_value: str) -> str:
    """将UI显示值转换为内核标识符"""
    return CHUNKING_METHOD_MAPPING.get(ui_value, "fixed_size")  # 默认固定长度

def get_cleaning_level(ui_value: str) -> str:
    """将UI显示值转换为内核标识符"""
    return CLEANING_LEVEL_MAPPING.get(ui_value, "basic")  # 默认基础清洗

def is_deep_clean_enabled(ui_value: str) -> bool:
    """判断是否启用深度清洗"""
    return get_cleaning_level(ui_value) == "deep"
