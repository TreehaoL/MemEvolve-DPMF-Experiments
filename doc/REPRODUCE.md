# 从零复刻指南

本文档说明如何从空目录开始复刻本仓库中的 DPMF 记忆投毒、架构漂移感知与动态防御实验。

本仓库不直接复制 MemEvolve / Flash-Searcher 原始工程源码。原始工程来自公开论文仓库，本仓库保存的是在该工程基础上新增的实验脚本、配置、结果、图表和文档。因此，完整复刻采用“两仓库复刻法”：

1. 先 clone 原始 MemEvolve 工程。
2. 再 clone 本实验仓库。
3. 将本仓库中的实验文件叠加到原始工程的 `Flash-Searcher-main` 目录中运行。

## 仓库来源

| 类型 | 仓库 | 说明 |
|---|---|---|
| 上游原始工程 | `https://github.com/bingreeky/MemEvolve.git` | MemEvolve / EvolveLab / Flash-Searcher 原始代码来源 |
| 本实验归档 | `https://github.com/TreehaoL/MemEvolve-DPMF-Experiments.git` | 七周 DPMF 实验脚本、配置、结果和文档 |

建议复刻时优先使用上游公开 `main` 分支当前可定位的 commit：

```text
6035d5659d7a092dbfa6a87b1a32a3cee652ba54
```

本实验开发机中记录的 `Flash-Searcher-main` 本地 HEAD 为：

```text
fec17231cb01e4e0854755f9b2c0ef347a7c23ca
```

该 SHA 不一定存在于上游公开仓库，因此不能要求复刻者直接 `git checkout fec17231...`。公开复刻建议以上游仓库 `6035d565...` 为基底，再叠加本实验仓库文件。

## 目录准备

建议在一个新的工作目录中复刻，避免污染已有项目。

```powershell
mkdir E:\AIProjects\MemEvolve-Reproduce
cd E:\AIProjects\MemEvolve-Reproduce
```

clone 上游原始工程：

```powershell
git clone https://github.com/bingreeky/MemEvolve.git MemEvolve
cd MemEvolve
git checkout 6035d5659d7a092dbfa6a87b1a32a3cee652ba54
cd ..
```

clone 本实验仓库：

```powershell
git clone https://github.com/TreehaoL/MemEvolve-DPMF-Experiments.git MemEvolve-DPMF-Experiments
```

此时目录结构应类似：

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

## 叠加实验文件

将本实验仓库中的实验文件复制到上游工程的 `Flash-Searcher-main` 目录。

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

复制后，实验运行目录应为：

```powershell
cd "E:\AIProjects\MemEvolve-Reproduce\MemEvolve\Flash-Searcher-main"
```

## 创建运行环境

如果使用 Conda：

```powershell
conda env create -f environment.yml
conda activate memevolve-dpmf
```

如果已经有可用的 Python 3.10 环境：

```powershell
python -m pip install -r requirements.txt
```

如果复刻者已经有原始 MemEvolve 环境，也可以直接使用原环境：

```powershell
conda activate memevolve
python -m pip install -r requirements.txt
```

## API 配置

live 实验依赖在线 LLM API。本仓库只提供 `.env.example`，不会上传真实 `.env`。

在 `Flash-Searcher-main` 根目录创建 `.env`：

```text
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.deepseek.com
DEFAULT_MODEL=deepseek-v4-flash
```

注意：`.env` 不能提交到 GitHub。

## crawl4ai 依赖

实验环境中使用过 `crawl4ai` 辅助网页抓取和 WebWalkerQA 输入整理。它不是 DPMF 主体模块。

如需运行相关数据准备脚本，可额外执行：

```powershell
python -m pip install crawl4ai playwright
python -m playwright install chromium
```

如果只复核已有结果或运行汇总脚本，可以暂时不处理 `crawl4ai`。

## 运行前检查

在 `Flash-Searcher-main` 根目录执行：

```powershell
cd "E:\AIProjects\MemEvolve-Reproduce\MemEvolve\Flash-Searcher-main"
$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONIOENCODING = "utf-8"
python -c "import EvolveLab, MemEvolve; print('local modules ok')"
```

如果这里报错，优先检查：

- 当前目录是否为 `Flash-Searcher-main`。
- `PYTHONPATH` 是否设置为当前目录。
- 上游工程是否完整 clone。
- 当前 Python 环境是否安装依赖。

## 先复核已有结果

建议先运行不依赖 live API 的汇总与绘图脚本，确认环境和路径正常。

```powershell
python experiments\week6\scripts\build_week6_summary.py
python experiments\week7\scripts\summarize_week7.py
python experiments\week7\scripts\plot_week7_results.py
```

预期输出包括：

```text
experiments\week6\results\week6_summary.json
experiments\week7\results\week7_summary.json
experiments\week7\results\figures\
```

## 每周实验复刻路线

建议按周次递进复刻，而不是直接运行 Week 7。

| 周次 | 复刻目标 | 重点目录 |
|---|---|---|
| Week 2 | 无防护记忆投毒基线 | `experiments/week2/` |
| Week 3 | Top-K 漂移与 history-first 检索策略漂移 | `experiments/week3/` |
| Week 4 | F1 / F2 静态防御对照 | `experiments/week4/` |
| Week 5 | DPMF 事件、漂移检测与风险评分 | `experiments/week5/` |
| Week 6 | 检测指标、风险梯度和 LLM 后验解释 | `experiments/week6/` |
| Week 7 | 防御算子、scheduler 和动态闭环 | `experiments/week7/` |

每周目录下的 `README.md` 记录了该周的实验目标、关键脚本、输入输出和主要结果。完整复刻时建议先阅读对应周次 README，再运行脚本。

## live 实验注意事项

live 实验结果可能不会逐字一致。原因包括：

- 在线模型版本可能更新。
- API 响应存在一定随机性。
- 网络状态会影响调用稳定性。
- 初始记忆库和运行状态需要保持一致。

复刻时更应关注以下指标是否一致：

- Poison Hit@K 是否能复现投毒记忆进入检索上下文。
- Attack Success Rate 是否能体现无防护场景下的攻击成功。
- 架构漂移后 clean correctness 是否下降。
- DPMF risk score 是否保持 D2 / D4 高于普通对照。
- F1 / F2 / scheduler 是否能把最终 ASR 降低到 0。

## 复刻失败时的排查顺序

1. 确认当前目录是 `Flash-Searcher-main`。
2. 确认 `python -c "import EvolveLab, MemEvolve"` 能通过。
3. 确认 `.env` 存在且 API key 可用。
4. 确认 `requirements.txt` 依赖已安装。
5. 确认 `experiments/week*/results/` 中的输入结果文件存在。
6. 如果只想看结果，优先运行汇总/绘图脚本，不先跑 live API。

## 不能上传的内容

为了安全和仓库体积控制，不应上传：

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

## 本仓库的复刻定位

本仓库本身不是原始 MemEvolve 工程的完整镜像。准确定位是：

```text
上游 MemEvolve / Flash-Searcher 工程
        +
本仓库 experiments / data / scripts / docs
        =
可复刻 DPMF 七周实验环境
```

也就是说，别人只看本仓库可以理解和复核结果；如果要从零重跑，则需要按照本文档先准备上游工程，再叠加本实验仓库。
