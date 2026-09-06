# 从零复刻说明

本文档说明如何从一个空目录开始，尽可能复刻本仓库中的七周实验。

需要先说明边界：当前仓库是实验归档仓库，保存了实验脚本、配置、结构化结果、图表和文档。若要完整重跑涉及记忆检索、投毒写入、LLM 调用和防御闭环的 live 实验，还需要原始 MemEvolve / Flash-Searcher 工程中的本地模块。

## 复刻层级

| 层级 | 目标 | 是否只需要本仓库 | 说明 |
|---|---|---|---|
| L0 | 阅读实验设计、结论和图表 | 是 | 查看 `README.md`、`doc/`、`experiments/week*/README.md` 和 `results/` |
| L1 | 核对已有实验结果 | 是 | 直接检查 JSON / CSV / PNG 等结果文件 |
| L2 | 重新生成汇总表和图表 | 基本是 | 依赖 `results/` 中已有数据和 Python 绘图依赖 |
| L3 | 重新运行离线检测和统计脚本 | 部分是 | 不调用原始记忆系统的脚本通常可以运行 |
| L4 | 重新运行 live 记忆投毒、防御和闭环实验 | 否 | 需要原始 MemEvolve / Flash-Searcher 工程、本地模块和 API |
| L5 | 从零完整复刻七周实验 | 否 | 还需要原始工程版本、初始记忆库、API、执行顺序和运行状态 |

## 推荐复刻方式

如果只是查看和核对结果，直接 clone 本仓库即可。

```powershell
git clone https://github.com/TreehaoL/MemEvolve-DPMF-Experiments.git
cd MemEvolve-DPMF-Experiments
```

如果需要完整重跑实验，建议准备原始 MemEvolve / Flash-Searcher 工程，然后把本仓库作为实验补丁目录使用。

建议目录结构如下：

```text
E:\AIProjects\
├── MemEvolve\
│   └── Flash-Searcher-main\          # 原始工程，可运行 EvolveLab / MemEvolve 模块
└── MemEvolve-DPMF-Experiments\        # 本仓库，保存实验归档
```

完整重跑时，需要把本仓库中的 `experiments/`、`data/`、`minimal_memory_demo.py` 等内容放入原始 `Flash-Searcher-main` 项目根目录，或保证 Python 能够同时找到原始工程模块和本仓库实验脚本。

## 环境准备

### 方式一：Conda

```powershell
conda env create -f environment.yml
conda activate memevolve-dpmf
```

### 方式二：已有 Python 环境

```powershell
python -m pip install -r requirements.txt
```

如果使用的是原始项目中已经配置好的环境，也可以直接激活原环境：

```powershell
conda activate memevolve
```

## API 配置

部分 live 实验依赖在线 LLM API。仓库只提供 `.env.example`，不提供真实 `.env`。

在本地新建 `.env`：

```text
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.deepseek.com
DEFAULT_MODEL=deepseek-v4-flash
```

注意：不要把 `.env` 提交到 GitHub。

## crawl4ai 说明

实验环境中使用过 `crawl4ai` 辅助网页抓取和 WebWalkerQA 输入整理。它不是 DPMF 主体模块。

如果需要运行涉及网页抓取或数据准备的脚本，可能需要额外安装浏览器运行环境：

```powershell
python -m pip install crawl4ai playwright
python -m playwright install chromium
```

如果只查看已有结果，不需要运行 `crawl4ai`。

## 运行前检查

在原始 `Flash-Searcher-main` 项目根目录中执行：

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONIOENCODING = "utf-8"
python -c "import EvolveLab, MemEvolve; print('local modules ok')"
```

如果这里报错，说明原始工程模块没有被 Python 找到，需要先检查当前目录和 `PYTHONPATH`。

## 可优先运行的脚本

以下脚本主要基于已有结果文件做汇总或绘图，适合作为复刻检查的第一步：

```powershell
python experiments\week6\scripts\build_week6_summary.py
python experiments\week7\scripts\summarize_week7.py
python experiments\week7\scripts\plot_week7_results.py
```

预期会重新生成或更新：

```text
experiments/week6/results/week6_summary.json
experiments/week7/results/week7_summary.json
experiments/week7/results/figures/
```

## live 实验复刻条件

如果要重新运行 Week 2 到 Week 7 的 live 实验，需要确认：

- 原始 MemEvolve / Flash-Searcher 工程可以正常运行。
- `EvolveLab`、`MemEvolve` 等本地模块可以 import。
- `.env` 中 API key、base URL 和模型名可用。
- 网络能够访问对应 LLM API。
- 初始记忆库、clean / poisoned 记忆快照或脚本生成逻辑完整。
- 运行顺序与每周 README 中记录的实验流程一致。

live 实验可能因为模型版本、API 响应、网络状态和随机性出现轻微差异，因此复刻时更应关注指标趋势和关键行为是否一致，而不是要求每一次文本输出完全相同。

## 若要让仓库真正独立复刻

如果希望别人只 clone 本仓库就能完整重跑，需要进一步补齐以下内容：

1. 上传必要的原始工程源码模块，例如 `EvolveLab/`、`MemEvolve/`、`FlashOAgents/` 等。
2. 删除缓存、虚拟环境、API key、本地日志和大体积运行产物。
3. 固定原始工程版本，记录来源仓库、分支和 commit。
4. 增加一键检查脚本，例如 `scripts/check_env.py`。
5. 增加一键复刻脚本，例如 `scripts/run_reproduce.ps1`。
6. 明确每周脚本的运行顺序和预期输出。
7. 准备最小初始数据和最小记忆快照，保证实验从同一状态开始。

在这些内容补齐之前，本仓库更适合描述为“实验归档与结果复核仓库”，而不是“完全自包含复刻仓库”。

## 建议提交到 GitHub 的文件

建议至少提交：

```text
README.md
environment.yml
requirements.txt
.env.example
doc/REPRODUCE.md
doc/*.docx
experiments/
data/
minimal_memory_demo.py
```

不建议提交：

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
