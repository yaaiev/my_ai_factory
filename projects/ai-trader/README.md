## AI Trader

最小可运行的“基于情绪的交易回测系统”。

当前流程：

1. 读取 `data/raw/twitter/` 下的 OpenCLI Twitter JSON
2. 结构化为情绪与提及数据
3. 构建 3 天滚动特征
4. 生成简单买入信号
5. 使用 `data/raw/prices/` 中的价格数据做下一日开盘买入、收盘卖出回测
6. 输出回测结果与评估指标

共享环境：

```bash
cd /Users/dev/yana_prj/my_ai_factory/projects
source .venv/bin/activate
python /Users/dev/yana_prj/my_ai_factory/projects/ai-trader/main.py
```
