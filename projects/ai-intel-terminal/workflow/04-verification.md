# Verification

## 目标

- 验证数据质量、结构化准确率、评分稳定性和输出可用性

## 输入

- implementation 阶段产出的最小闭环

## 输出

- 数据质量检查结果
- 去重与聚类验证结果
- 预测与评分回溯结果

## 责任角色

- 主责任 Agent：Reviewer
- 可协作 Agent：ETL Agent、Intel Analyst Agent

## 执行动作

1. 抽样验证事件抽取是否准确
2. 验证 rumor 与 confirmed 事件是否分层
3. 验证 cluster 是否合并正确
4. 验证预测能否回溯到支持证据

## 验收标准

1. 关键字段无系统性缺失
2. 事实层与推断层不混写
3. 输出中的高优先级信号均可回溯

## 失败回退

- 若 ETL 误差过大，回退到 implementation 修正抽取与对齐逻辑

## 下一跳

- `05-delivery.md`
