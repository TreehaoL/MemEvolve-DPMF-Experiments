# 复现实验指南

本文档面向希望复现本仓库实验的读者，说明如何从公开仓库开始准备环境、叠加实验文件，并复核或重跑 DPMF 记忆投毒、架构漂移感知与动态防御实验。

## 复现前提

本仓库保存的是基于 MemEvolve / Flash-Searcher 工程完成的实验归档，包括实验脚本、配置、结构化结果、图表和说明文档。由于原始工程源码来自上游论文仓库，本仓库不重复分发完整原始工程源码。

完整复现采用“两仓库复现方式”：

| 步骤 | 内容 |
|---|---|
| 1 | 获取上游 MemEvolve / Flash-Searcher 原始工程 |
| 2 | 获取本仓库的 DPMF 实验文件 |
| 3 | 将本仓库的实验目录叠加到上游工程的 `Flash-Searcher-main` 目录 |
| 4 | 配置 Python 环境、API key 和运行路径 |
| 5 | 先复核已有结果，再按周次重跑实验 |

## 仓库来源

| 类型 | 地址 | 用途 |
|---|---|---|
| 上游原始工程 | `https://github.com/bingreeky/MemEvolve.git` | 提供 MemEvolve、EvolveLab、Flash-Searcher 等基础代码 |
| 本实验仓库 | `https://github.com/TreehaoL/MemEvolve-DPMF-Experiments.git` | 提供七周 DPMF 实验脚本、配置、结果和文档 |

上游仓库可定位的公开版本：

```text
6035d5659d7a092dbfa6a87b1a32a3cee652ba54
```

本实验开发环境中记录的 `Flash-Searcher-main` 本地 HEAD：

```text
fec17231cb01e4e0854755f9b2c0ef347a7c23ca
```

该本地 HEAD 不一定对应上游公开仓库中的可 checkout commit。因此，公开复现时建议以上游仓库 `6035d565...` 为基础版本，再叠加本实验仓库中的文件。

## 目录准备

以下示例使用 Windows PowerShell。

```powershell
mkdir E:\AIProjects\MemEvolve-Reproduce
cd E:\AIProjects\MemEvolve-Reproduce
```

下载上游原始工程：

```powershell
git clone https://github.com/bingreeky/MemEvolve.git MemEvolve
cd MemEvolve
git checkout 6035d5659d7a092dbfa6a87b1a32a3cee652ba54
cd ..
```

下载本实验仓库：

```powershell
git clone https://github.com/TreehaoL/MemEvolve-DPMF-Experiments.git MemEvolve-DPMF-Experiments
```

准备后的目录结构：

```text
E:\AIProjects\MemEvolve-Reproduce\
├── MemEvolve\
│   └── Flash-Searcher-main\
└── MemEvolve-DPMF-Experiments\
    ├── data\
    ├── doc\
    ├── experiments\
    ├── minimal_memory_demo.py
    ├── environment.yml
    ├── requirements.txt
    └── .env.example
```

## 实验数据说明

`data/webwalkerqa/simple_python_task.json` 是本仓库提供的最小 WebWalkerQA 风格任务样例，用于说明网页任务输入格式。该样例包含：

| 字段 | 说明 |
|---|---|
| `question` | 实验中的事实探针问题 |
| `answer` | 判断回答是否正确的标准答案 |
| `root_url` | 任务来源网页 |
| `info` | 领域、难度、语言和来源类型等元信息 |
| `golden_path` | 多跳网页任务中的参考路径，本样例中为空 |

七周实验主要围绕该 Python 作者事实探针构造 clean / poisoned 记忆检索、架构漂移和防御对照。复现者可以先用该最小样例确认数据格式，再按各周 README 运行更完整的实验脚本。

## 叠加实验文件

将本实验仓库中的文件复制到上游工程的 `Flash-Searcher-main` 目录：

```powershell
$SRC = "E:\AIProjects\MemEvolve-Reproduce\MemEvolve-DPMF-Experiments"
$DST = "E:\AIProjects\MemEvolve-Reproduce\MemEvolve\Flash-Searcher-main"

Copy-Item "$SRC\experiments" "$DST\" -Recurse -Force
Copy-Item "$SRC\data" "$DST\" -Recurse -Force
Copy-Item "$SRC\minimal_memory_demo.py" "$DST\" -Force
Copy-Item "$SRC\environment.yml" "$DST\" -Force
Copy-Item "$SRC\requirements.txt" "$DST\" -Force
Copy-Item "$SRC\.env.example" "$DST\" -Force
```

后续命令均在上游工程的 `Flash-Searcher-main` 目录下执行：

```powershell
cd "E:\AIProjects\MemEvolve-Reproduce\MemEvolve\Flash-Searcher-main"
```

## 环境配置

使用 Conda 创建环境：

```powershell
conda env create -f environment.yml
conda activate memevolve-dpmf
```

或在已有 Python 3.10 环境中安装依赖：

```powershell
python -m pip install -r requirements.txt
```

如果本地已经有可运行的 MemEvolve 环境，也可以直接使用该环境，并补装本仓库依赖：

```powershell
conda activate memevolve
python -m pip install -r requirements.txt
```

## API 配置

部分 live 实验依赖在线 LLM API。仓库提供 `.env.example` 作为模板，不包含真实 API key。

在 `Flash-Searcher-main` 根目录创建 `.env`：

```text
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.deepseek.com
DEFAULT_MODEL=deepseek-v4-flash
```

`.env`、API key、虚拟环境、缓存和完整本地运行日志不属于公开复现材料。

## crawl4ai 依赖

实验环境中使用过 `crawl4ai` 辅助网页抓取和 WebWalkerQA 输入整理。该工具不是 DPMF 漂移感知或防御闭环的核心模块。

如需运行涉及网页抓取或数据准备的脚本，可额外初始化浏览器依赖：

```powershell
python -m pip install crawl4ai playwright
python -m playwright install chromium
```

如果只复核已有结果、查看图表或运行汇总脚本，可以暂时跳过该步骤。

## 运行前检查

在 `Flash-Searcher-main` 根目录执行：

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONIOENCODING = "utf-8"
python -c "import EvolveLab, MemEvolve; print('local modules ok')"
```

若输出 `local modules ok`，说明上游工程模块可以被当前 Python 环境识别。

## 复核已有结果

建议先运行不依赖在线 API 的汇总和绘图脚本，确认目录、依赖和结果文件可用。

```powershell
python experiments\week6\scripts\build_week6_summary.py
python experiments\week7\scripts\summarize_week7.py
python experiments\week7\scripts\plot_week7_results.py
```

典型输出包括：

```text
experiments\week6\results\week6_summary.json
experiments\week7\results\week7_summary.json
experiments\week7\results\figures\
```

## 按周复现实验

完整复现建议按周次递进进行。每周目录下的 `README.md` 记录了实验目标、关键脚本、输入输出和主要结果。

| 周次 | 复现目标 | 重点目录 |
|---|---|---|
| Week 2 | 无防护记忆投毒基线 | `experiments/week2/` |
| Week 3 | Top-K 漂移与 history-first 检索策略漂移 | `experiments/week3/` |
| Week 4 | F1 / F2 静态防御对照 | `experiments/week4/` |
| Week 5 | DPMF 事件、漂移检测与风险评分 | `experiments/week5/` |
| Week 6 | 检测指标、风险梯度和 LLM 后验解释 | `experiments/week6/` |
| Week 7 | 防御算子、scheduler 和动态闭环 | `experiments/week7/` |

## 结果一致性说明

live 实验调用在线模型，复现结果可能不会逐字一致。影响因素包括模型版本、API 响应、网络状态和初始记忆状态。

复现时建议重点核对以下行为和指标：

| 指标 | 期望现象 |
|---|---|
| Poison Hit@K | 投毒记忆在无防护或漂移场景下进入检索上下文 |
| Attack Success Rate | 无防护场景下攻击更容易成功 |
| Clean Correct Rate | 架构漂移后干净样本正确率下降 |
| DPMF Risk Score | D2 / D4 等漂移场景风险高于普通对照 |
| Defense Block Rate | F1 / F2 能阻断投毒记忆进入最终回答 |
| Week 7 ASR | scheduler 闭环后最终攻击成功率降至 0 |

## 常见问题

| 问题 | 检查方式 |
|---|---|
| `ModuleNotFoundError: EvolveLab` 或 `MemEvolve` | 确认当前目录为 `Flash-Searcher-main`，并设置 `$env:PYTHONPATH = (Get-Location).Path` |
| API 调用失败 | 检查 `.env` 中的 key、base URL、模型名和网络连接 |
| 图表脚本找不到输入文件 | 确认 `experiments/week*/results/` 已从本实验仓库复制到上游工程 |
| `crawl4ai` 报浏览器相关错误 | 执行 `python -m playwright install chromium` |
| live 输出与文档不完全一致 | 优先比较指标趋势和结构化结果，而不是逐字比较模型回答 |

## 公开仓库边界

本仓库不包含以下本地运行材料：

```text
.env
.venv/
__pycache__/
*.pyc
logs/
storage/
memevolve_work/
完整 API 运行日志
本地长期记忆存储目录
```

这些内容涉及安全、体积或本机状态，不适合作为公开仓库内容。复现时应通过环境文件、配置模板和脚本重新生成。

## 复现定位

本仓库的复现方式可以概括为：

```text
上游 MemEvolve / Flash-Searcher 工程
        +
本仓库 experiments / data / docs / environment files
        =
DPMF 七周实验复现环境
```

读者可以仅通过本仓库复核实验设计、结果和图表；若要重跑 live 实验，则应按本文档准备上游工程并叠加实验文件。
