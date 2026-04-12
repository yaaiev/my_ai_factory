# Projects Python Environment

这个目录下的所有项目共用一个 Python 虚拟环境：

- 环境路径：`/Users/dev/yana_prj/my_ai_factory/projects/.venv`

## 激活

```bash
cd /Users/dev/yana_prj/my_ai_factory/projects
source .venv/bin/activate
```

## 安装依赖

建议始终在激活共享环境后安装依赖：

```bash
python -m pip install --upgrade pip
python -m pip install playwright
python -m playwright install chromium
```

## 运行项目脚本

示例：

```bash
cd /Users/dev/yana_prj/my_ai_factory/projects
source .venv/bin/activate
python /Users/dev/yana_prj/my_ai_factory/projects/ai-intel-terminal/pipelines/twitter_observer_demo.py
```
