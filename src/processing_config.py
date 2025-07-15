# processing_config.py
"""
文档处理配置和多语言映射
统一管理所有处理相关的常量和语言映射
"""

# ============================================================================
# 内部标准化常量（全英文）
# ============================================================================

# 分块方法标准标识符
CHUNKING_METHODS = {
    "by_page": "by_page",
    "by_sentence": "by_sentence", 
    "by_paragraph": "by_paragraph",
    "fixed_size": "fixed_size"
}

# 清洗级别标准标识符
CLEANING_LEVELS = {
    "basic": "basic",
    "deep": "deep"
}

# 深度清洗选项标准键名
DEEP_CLEAN_OPTIONS = {
    "remove_references": "remove_references",
    "remove_authors": "remove_authors", 
    "remove_footnotes": "remove_footnotes",
    "remove_page_numbers": "remove_page_numbers",
    "normalize_whitespace": "normalize_whitespace",
    "remove_citations": "remove_citations"
}

# ============================================================================
# 多语言映射配置
# ============================================================================

# UI显示文本到内部标识符的映射
CHUNKING_METHOD_MAPPING = {
    # 中文映射
    "按页": "by_page",
    "按句子": "by_sentence",
    "按段落": "by_paragraph", 
    "固定长度": "fixed_size",
    
    # 英文映射（保持一致性）
    "By Page": "by_page",
    "By Sentence": "by_sentence",
    "By Paragraph": "by_paragraph",
    "Fixed Size": "fixed_size",
    
    # 直接映射（向后兼容）
    "by_page": "by_page",
    "by_sentence": "by_sentence", 
    "by_paragraph": "by_paragraph",
    "fixed_size": "fixed_size"
}

CLEANING_LEVEL_MAPPING = {
    # 中文映射
    "基础清洗": "basic",
    "深度清洗": "deep",
    
    # 英文映射
    "Basic Cleaning": "basic", 
    "Deep Cleaning": "deep",
    
    # 直接映射
    "basic": "basic",
    "deep": "deep"
}

# ============================================================================
# 多语言显示文本配置
# ============================================================================

DISPLAY_TEXTS = {
    "zh": {
        "chunking_methods": {
            "by_page": "按页",
            "by_sentence": "按句子",
            "by_paragraph": "按段落", 
            "fixed_size": "固定长度"
        },
        "cleaning_levels": {
            "basic": "基础清洗",
            "deep": "深度清洗"
        },
        "deep_clean_options": {
            "remove_references": "去除参考文献",
            "remove_authors": "去除作者信息",
            "remove_footnotes": "去除脚注", 
            "remove_page_numbers": "去除页码",
            "normalize_whitespace": "规范化空白字符",
            "remove_citations": "去除引用标记"
        }
    },
    "en": {
        "chunking_methods": {
            "by_page": "By Page",
            "by_sentence": "By Sentence", 
            "by_paragraph": "By Paragraph",
            "fixed_size": "Fixed Size"
        },
        "cleaning_levels": {
            "basic": "Basic Cleaning",
            "deep": "Deep Cleaning"
        },
        "deep_clean_options": {
            "remove_references": "Remove References",
            "remove_authors": "Remove Authors",
            "remove_footnotes": "Remove Footnotes",
            "remove_page_numbers": "Remove Page Numbers", 
            "normalize_whitespace": "Normalize Whitespace",
            "remove_citations": "Remove Citations"
        }
    }
}

# ============================================================================
# 辅助函数
# ============================================================================

def normalize_chunking_method(method: str) -> str:
    """将任何语言的分块方法名称标准化为英文标识符"""
    return CHUNKING_METHOD_MAPPING.get(method, "fixed_size")

def normalize_cleaning_level(level: str) -> str:
    """将任何语言的清洗级别标准化为英文标识符"""
    return CLEANING_LEVEL_MAPPING.get(level, "basic")

def get_display_text(category: str, key: str, lang: str = "zh") -> str:
    """获取指定语言的显示文本"""
    return DISPLAY_TEXTS.get(lang, {}).get(category, {}).get(key, key)

def get_chunking_methods_for_ui(lang: str = "zh") -> list:
    """获取用于UI显示的分块方法列表"""
    methods = DISPLAY_TEXTS.get(lang, {}).get("chunking_methods", {})
    return list(methods.values())

def get_cleaning_levels_for_ui(lang: str = "zh") -> list:
    """获取用于UI显示的清洗级别列表"""
    levels = DISPLAY_TEXTS.get(lang, {}).get("cleaning_levels", {})
    return list(levels.values())

# ============================================================================
# 默认配置
# ============================================================================

DEFAULT_DEEP_CLEAN_CONFIG = {
    "min_ref_lines": 2,
    "max_nonmatch_lines": 7,
    "remove_authors": True,
    "remove_references": True,
    "remove_citations": True,
    "remove_page_numbers": True,
    "normalize_whitespace": True,
}
