# 🔄 Reprocess Select Chunks 操作流程说明 (From-Scratch Mode)

## 🚨 重要更新：从头开始测试模式

**新行为（2024-12-19）：**"Reprocess Select Chunks" 现在采用**从头开始**的测试模式，专为小规模测试设计。

### ⚠️ 关键变化
- **清空数据库**：先删除所有现有实体和关系数据
- **重置状态**：将所有chunk状态重置为"pending"
- **从头处理**：只处理选定数量的chunks，结果直接保存到主数据库
- **无需合并**：结果直接生效，无需额外确认步骤

## 📋 新的操作流程

### Step 1: 选择性重处理（从头开始）
```
[点击 "Reprocess Select Chunks"] 
→ 状态：Initializing selective reprocessing (from scratch)...
→ 清空：删除所有现有数据文件和临时文件
→ 重置：所有chunk状态变为"pending"
→ 处理：Processing N selected chunks from scratch...
→ 完成：✅ Selective reprocessing complete! Processed X entities and Y relations from N chunks.
```

**此时数据状态：**
- ✅ 新提取的数据直接保存到主数据库文件
- ✅ 数据立即生效，在UI中可见
- ✅ 只包含选定chunks的处理结果
- ❌ **原有数据已被清空**
- ❌ **这是不可逆操作**

### Step 2: 立即查看结果
```
→ 自动显示处理结果
→ UI和可视化立即更新
→ 显示新处理的 X 个实体和 Y 个关系
```
→ 保存到主数据库文件
→ 清理临时文件
→ 显示：新数据已合并到主数据库并保存！共Z个实体，W条关系。
```

**合并过程：**
1. 从磁盘读取历史数据文件
2. 从临时文件读取新处理数据
3. 合并两部分数据
4. 去重处理（相同name+type的实体，相同subject+object+relation_type的关系）
5. 写入主数据库文件（`project_name_entities.json`, `project_name_relations.json`）
6. 清理临时文件

## 🔒 使用场景

### ✅ 适合的使用场景
- **小规模测试**：用少量chunks测试提取参数和质量
- **配置调试**：验证不同的实体类型、关系类型设置
- **算法验证**：测试不同的优化策略和提取prompt
- **从头开始**：清空之前的错误数据，重新处理

### ⚠️ 不适合的使用场景
- **保留现有数据**：如果需要保留之前的处理结果
- **大规模处理**：如果需要处理大量chunks（建议使用"Continue from Last"）
- **数据追加**：如果需要在现有数据基础上添加新内容

## 🚨 安全提醒

### 数据丢失风险
- ⚠️ **操作不可逆**：一旦点击，现有数据将被永久删除
- ⚠️ **无法恢复**：没有自动备份机制
- ⚠️ **影响全局**：所有chunk状态都会被重置

### 推荐做法
1. **先备份**：如果有重要数据，手动备份entity和relation文件
2. **小量测试**：建议从5-10个chunks开始
3. **参数确认**：确认实体类型、关系类型、优化设置正确
4. **渐进式**：满意后再增加chunk数量

## 📊 新的数据流程图

```
选择性重处理 → 清空数据库 → 重置状态 → 处理chunks → 直接保存
     ↓             ↓          ↓         ↓         ↓
  [清空旧数据]   [删除文件]  [全部pending] [处理N个]  [立即生效]
     ↓             ↓          ↓         ↓         ↓
   无法恢复      不可逆      从头开始    新结果     即时更新
```

## 🔧 技术实现细节

### 清空操作
```python
# 删除主数据文件
os.remove(entities_file)
os.remove(relations_file)

# 删除临时文件
os.remove(temp_entities_file)
os.remove(temp_relations_file)
```

### 状态重置
```python
# 重置所有chunk状态为pending
fresh_chunk_status = {}
for chunk in all_chunks:
    fresh_chunk_status[chunk["chunk_id"]] = {
        "status": "pending",
        "last_processed_at": None,
        "confidence_score": None
    }
```

### 直接保存
```python
# 结果直接保存到主数据库
with open(entities_file, "w") as f:
    json.dump(entities, f)
    
# 立即更新session state
st.session_state['litmap_entities'] = entities
st.session_state['litmap_view_mode'] = 'history'
```

## ⚠️ 重要注意事项

### 什么时候数据会改变？
1. **不会改变**：
   - 点击 "Reprocess Select Chunks" 后
   - 点击 "Preview New Data" 后
   - 点击 "Load All History" 后

2. **会改变**：
   - 只有点击 "Merge New Data to Main DB" 后
   - 主数据库文件才会被更新

### 如何安全使用？
1. **测试阶段**：多次使用 "Reprocess Select Chunks" + "Preview New Data"
2. **满意后**：点击 "Merge New Data to Main DB" 一次性合并
3. **不满意**：直接调整参数重新处理，无需担心数据丢失

### 典型使用场景
```
# 参数调优
1. max_chunks=3, 启用improved extraction → Reprocess Select → Preview → 不满意
2. 调整similarity threshold → Reprocess Select → Preview → 还是不满意  
3. 禁用semantic similarity → Reprocess Select → Preview → 满意了
4. Merge New Data to Main DB → 永久保存

# 整个过程中，原有数据始终安全
```

## 🎯 总结

- ✅ **完全安全**：原有数据不会被意外覆盖
- ✅ **完全可控**：需要手动确认才会合并
- ✅ **完全透明**：每一步都有明确提示
- ✅ **状态已修复**：现在会正确显示完成状态并更新UI

**您现在可以放心使用 "Reprocess Select Chunks" 进行小规模测试，只有在满意结果后手动合并，才会更新主数据库！**
