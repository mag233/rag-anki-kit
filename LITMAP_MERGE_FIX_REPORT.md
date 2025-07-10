# LitMap 合并数据问题修复报告

## 问题描述
用户反映在执行 "merge new data" 操作后，历史数据出现问题，可视化也不见了。

## 问题分析

通过代码审查，发现了以下关键问题：

### 1. 重复的去重操作 ❌
**位置**: `litmap_tab.py` 第 677-679 行
```python
# 去重 (使用业务逻辑模块的函数)
all_entities = dedup_items(all_entities, 'entity')
all_relations = dedup_items(all_relations, 'relation')
all_relations = dedup_items(all_relations, 'relation')  # 重复了！
```

**问题**: `all_relations` 被重复去重，可能导致数据处理异常。

### 2. 关系去重字段不匹配 ❌
**位置**: `litmap.py` `dedup_items` 函数
```python
# 原代码使用错误的字段名
key = (
    item.get('source', '').lower(),     # 应该是 'subject'
    item.get('target', '').lower(),     # 应该是 'object'  
    item.get('type', '').lower()        # 应该是 'relation_type'
)
```

**问题**: 实际关系数据使用 `subject`、`object`、`relation_type` 字段，但去重逻辑使用 `source`、`target`、`type` 字段，导致去重完全失效。

## 修复方案

### ✅ 修复1: 移除重复的去重操作
```python
# 修复后
all_entities = dedup_items(all_entities, 'entity')
all_relations = dedup_items(all_relations, 'relation')
# 移除了重复的去重行
```

### ✅ 修复2: 修正关系去重字段映射
```python
# 修复后 - 兼容两种字段格式
subject = item.get('subject') or item.get('source', '')
obj = item.get('object') or item.get('target', '')
rel_type = item.get('relation_type') or item.get('type', '')
key = (subject.lower(), obj.lower(), rel_type.lower())
```

### ✅ 修复3: 增加调试信息
为了更好地追踪问题，在关键位置添加了调试输出：

- 合并数据时显示数据量统计
- 数据选择时显示当前模式和数据量
- 可视化时显示数据检查结果
- 数据不足时提供详细的错误信息

## 验证结果

### 功能测试 ✅
- 实体去重: 3 -> 2 (正确识别大小写重复)
- 关系去重: 3 -> 2 (正确识别重复关系)

### 模块测试 ✅
- 所有模块导入正常
- 关键函数工作正常
- 无语法错误或运行时错误

## 根本原因分析

1. **数据模型不一致**: 代码中存在两套字段命名约定，导致去重逻辑失效
2. **代码重复**: 手动复制粘贴导致的重复操作
3. **缺乏调试信息**: 难以快速定位数据流问题

## 预防措施

1. **统一数据模型**: 确保整个应用使用一致的字段命名
2. **增加单元测试**: 为关键的数据处理函数添加测试
3. **改进调试工具**: 在关键数据流节点添加日志输出
4. **代码审查**: 避免手动重复的数据处理逻辑

## 用户操作建议

修复完成后，用户可以：

1. **重新合并数据**: 现在合并操作应该正常工作
2. **检查数据量**: 通过调试信息确认数据合并正确
3. **验证可视化**: 确保历史数据和可视化正常显示

如果问题仍然存在，请查看终端输出的调试信息，这将帮助进一步定位问题。
