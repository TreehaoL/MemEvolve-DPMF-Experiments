# MemEvolve-DPMF-Experiments

自进化 Agent 记忆架构漂移感知与投毒动态防御策略研究的七周实验归档。

本仓库整理了基于 MemEvolve / Flash-Searcher 的记忆投毒、架构漂移、DPMF 漂移感知、风险评估与动态防御闭环实验。仓库重点保存实验脚本、配置、结构化结果、图表和每周说明，便于查看七周工作的推进过程和主要结论。

## 复现指南

本仓库采用“实验归档仓库 + 上游原始工程”的复现方式。完整重跑 live 实验时，需要先准备上游 MemEvolve / Flash-Searcher 工程，再叠加本仓库中的实验脚本、配置和数据。

完整步骤见：[doc/REPRODUCE.md](doc/REPRODUCE.md)

复现方式概览：

| 目标 | 需要的内容 | 说明 |
|---|---|---|
| 查看实验设计与结果 | 本仓库 | 可直接阅读 README、每周说明、结果 JSON / CSV 和图表 |
| 重生成汇总表和图表 | 本仓库 + Python 依赖 | 使用已有 `results/` 文件运行汇总和绘图脚本 |
| 从零重跑 live 实验 | 上游 MemEvolve 工程 + 本仓库实验文件 + API 配置 | 按 `doc/REPRODUCE.md` 的“两仓库复现流程”执行 |

## 项目主线

| 阶段 | 周次 | 核心内容 | 输出 |
|---|---|---|---|
| 环境与投毒基线 | Week 2 | 构造无防护记忆投毒基线，验证投毒记忆进入 Top-K 并影响指导 | clean / poisoned 记忆库、重复实验、查询变体、自动写入结果 |
| 架构漂移 | Week 3 | 构造 Top-K 漂移与检索策略漂移，比较漂移前后行为 | 漂移配置、架构快照、D1/D2 对照结果 |
| 静态防御 | Week 4 | 比较 F1 检索前过滤与 F2 Retrieval Trust Gate | 防御矩阵、架构-防御映射知识库 |
| DPMF 感知 | Week 5 | 将漂移检测、风险评分、防御推荐标准化为 DPMF 事件 | drift event schema、风险评分、在线复验 |
| 检测评估 | Week 6 | 扩展 live case，评估 structural / behavioral detection | 检测指标、风险梯度、LLM 后验解释 |
| 动态闭环 | Week 7 | 封装 F0/F1/F2 防御算子，由 scheduler 自动执行防御 | 闭环调度结果、Week7 汇总图表 |

## 核心概念

- **记忆投毒**：向 Agent 长期记忆中写入伪造经验，使后续检索和指导受到污染。
- **架构漂移**：记忆系统的结构、参数或策略发生变化，例如 Top-K 从 3 增加到 5，或检索策略从语义相关性优先变为历史成功率优先。
- **DPMF**：Drift Perception Middleware Framework，漂移感知中间件框架，用于记录架构状态、检测漂移、计算风险并推荐防御。
- **F1**：检索前静态历史统计过滤。
- **F2**：检索后、进入 synthesis 前的 Retrieval Trust Gate。
- **scheduler**：读取 DPMF 标准化事件，根据风险和防御建议自动选择 F0/F1/F2。

## 仓库结构

```text
.
├── data/
│   └── webwalkerqa/
│       └── simple_python_task.json
├── doc/
│   └── REPRODUCE.md
├── experiments/
│   ├── week2/
│   ├── week3/
│   ├── week4/
│   ├── week5/
│   ├── week6/
│   └── week7/
├── minimal_memory_demo.py
├── environment.yml
├── requirements.txt
├── .env.example
└── README.md
```

每周目录通常包含：

| 目录 | 作用 |
|---|---|
| `configs/` | 实验配置，例如 Top-K、retrieval policy、模型和场景设置 |
| `scripts/` | 实验脚本、统计脚本和绘图脚本 |
| `results/` | JSON / CSV 形式的实验结果和汇总指标 |
| `results/figures/` | 实验图表 |
| `snapshots/` | 漂移前后的架构快照 |
| `schemas/` | DPMF 标准化事件 Schema |
| `knowledge_base/` | 架构-防御映射知识库 |
| `cases/` | live case 与评估样本定义 |

## 数据说明

`data/webwalkerqa/simple_python_task.json` 是一个最小 WebWalkerQA 风格任务样例，用于说明实验中的网页任务输入格式。该文件包含问题、标准答案、来源网页和任务元信息：

| 字段 | 说明 |
|---|---|
| `question` | 实验中的事实探针问题，例如 Python 作者是谁 |
| `answer` | 用于判断回答是否正确的标准答案 |
| `root_url` | 任务来源网页 |
| `info` | 领域、难度、语言和来源类型等元信息 |
| `golden_path` | 多跳网页任务中的参考访问路径，本最小样例中为空 |

本实验主要围绕该 Python 作者事实探针构造 clean / poisoned 记忆检索、架构漂移和防御对照。`crawl4ai` 仅作为网页内容抓取与输入材料整理的辅助工具，不是 DPMF 主体模块。

## 快速阅读路线

如果只想快速理解项目，可以按这个顺序阅读：

1. `doc/REPRODUCE.md`：从零复刻条件、复刻层级和运行边界。
2. `experiments/week2/README.md`：无防护投毒基线。
3. `experiments/week3/README.md`：Top-K 与检索策略漂移。
4. `experiments/week4/README.md`：F1 / F2 静态防御对照。
5. `experiments/week5/README.md`：DPMF 漂移检测与风险评分。
6. `experiments/week6/README.md`：检测准确率与端到端信号输出。
7. `experiments/week7/README.md`：动态防御 scheduler 闭环。

## 关键结果

### Week 2：无防护投毒基线

- 干净基线：7 条 strategic 记忆 + 4 条 operational 记忆。
- 投毒后：8 条 strategic 记忆 + 5 条 operational 记忆。
- Poison Hit@3：1.0。
- Attack Success Rate：1.0。
- 查询变体迁移测试中，投毒命中率和攻击成功率均为 1.0。

### Week 3：架构漂移

- D1 Top-K 3 -> 5：clean correctness 从 1.0 降至 0.6，投毒 ASR 保持 1.0。
- D2 semantic-first -> history-first：clean correctness 从 1.0 降至 0.0，投毒 ASR 保持 1.0。

### Week 4：静态防御

| 漂移场景 | 防御 | Clean Correct Rate | Attack Success Rate | Defense Block Rate |
|---|---|---:|---:|---:|
| D1 | F0 无防御 | 0.6 | 1.0 | 0.0 |
| D1 | F1 检索前过滤 | 0.4 | 0.0 | 1.0 |
| D1 | F2 Trust Gate | 1.0 | 0.0 | 1.0 |
| D2 | F0 无防御 | 0.0 | 1.0 | 0.0 |
| D2 | F1 检索前过滤 | 0.0 | 0.0 | 1.0 |
| D2 | F2 Trust Gate | 0.8 | 0.0 | 1.0 |

### Week 5：DPMF 感知

- D1 离线风险分数：0.6167，HIGH。
- D2 离线风险分数：0.9120，HIGH。
- 在线复验风险排序保持为：D2 > D1 > CONTROL。
- DPMF 对无漂移对照输出 `drift_detected = false`。

### Week 6：检测评估

- Structural Detection：Accuracy / Precision / Recall / F1 均为 1.0000。
- Behavioral Detection：Accuracy 0.8800，Recall 0.9750，F1 0.9286。
- D4 combined 风险最高，Risk Score = 0.6225，HIGH。

### Week 7：动态防御闭环

| 场景 | Risk | Defense | Clean Correct | Week7 ASR |
|---|---:|---|---:|---:|
| S0 | 0.1500 | F0 | 1.0 | 0.0 |
| D1 | 0.3542 | F2 | 1.0 | 0.0 |
| D3 | 0.5400 | F2 | 1.0 | 0.0 |
| D4 | 0.6225 | F1 -> F2 | 1.0 | 0.0 |

## 环境说明

本仓库不上传 `.venv`、Conda 环境目录或 Anaconda 安装目录。原因是这些目录体积很大，并且包含大量本机路径、缓存和平台相关文件，不适合放进 GitHub。

仓库中建议上传的是可重建环境的描述文件：

| 文件 | 作用 |
|---|---|
| `environment.yml` | Conda 环境定义，适合重新创建实验环境 |
| `requirements.txt` | pip 依赖列表，适合在已有 Python 环境中补装依赖 |
| `.env.example` | API 配置模板，不包含真实 key |

实验环境中还使用过 `crawl4ai` 作为辅助网页抓取与内容清洗工具，主要用于获取或整理 WebWalkerQA 相关输入材料。它不是 DPMF 漂移感知与防御闭环的核心模块，只是数据准备阶段的辅助依赖。

需要注意：本公开仓库主要是七周实验归档，不是完整 MemEvolve / Flash-Searcher 原始工程的镜像。部分脚本依赖原始工程中的本地模块，例如 `EvolveLab`、`MemEvolve` 或相关 provider。如果要重新运行这些脚本，需要在原始 MemEvolve / Flash-Searcher 项目环境中执行，或先把这些本地模块补齐到 Python 路径中。

## 复现范围说明

仅凭本仓库可以复核实验设计、配置、结果文件和图表，但不能保证从零完整复刻所有 live 实验。不同层级的复现条件如下：

如果需要从零重跑 live 实验，推荐采用“两仓库复刻法”：先准备上游原始工程 `https://github.com/bingreeky/MemEvolve.git`，再将本仓库中的 `experiments/`、`data/` 和相关脚本叠加到上游工程的 `Flash-Searcher-main` 目录中。完整步骤见 `doc/REPRODUCE.md`。

| 复现目标 | 仅凭本仓库是否足够 | 说明 |
|---|---|---|
| 阅读每周实验设计与结论 | 可以 | 每周 README、配置、结果 JSON / CSV 和图表已保留 |
| 核对关键指标 | 可以 | 可直接查看 `experiments/week*/results/` 中的结构化结果 |
| 重新生成部分汇总表和图表 | 基本可以 | 依赖已有 `results/` 文件和 Python 绘图/统计依赖 |
| 重新运行离线分析脚本 | 部分可以 | 若脚本只读取本仓库结果文件，一般可以运行 |
| 重新运行记忆检索、投毒和防御 live 实验 | 不完全足够 | 需要原始 MemEvolve / Flash-Searcher 工程、本地模块、API 配置和对应运行环境 |
| 从零完整复刻七周实验 | 不足够 | 还需要原始工程代码、可用 LLM API、初始记忆库/运行状态和相同的实验执行流程 |

因此，本仓库更准确的定位是“七周实验归档与结果复核仓库”。如果需要完整复刻，应先准备原始 MemEvolve / Flash-Searcher 环境，再将本仓库中的 `experiments/`、`data/` 和相关脚本放入对应项目结构中运行。

完整复刻还需要额外确认：

- 原始 MemEvolve / Flash-Searcher 工程版本和本地模块路径。
- `.env` 中的 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 和 `DEFAULT_MODEL`。
- Python / Conda 依赖是否与 `environment.yml`、`requirements.txt` 一致。
- live 实验依赖在线模型，结果可能受模型版本、接口响应和网络状态影响。
- 本仓库没有上传虚拟环境、缓存、完整日志和本地长期记忆存储目录。

## 环境重建方式

方式一：使用 Conda 创建环境。

```powershell
conda env create -f environment.yml
conda activate memevolve-dpmf
```

方式二：在已有 Python 3.10 环境中安装 pip 依赖。

```powershell
python -m pip install -r requirements.txt
```

如果运行涉及网页抓取或 WebWalkerQA 数据准备的脚本，可能还需要安装并初始化 `crawl4ai` / Playwright 浏览器环境：

```powershell
python -m pip install crawl4ai playwright
python -m playwright install chromium
```

如果只查看本仓库中的实验配置、结构化结果和图表，不需要运行 `crawl4ai`。

如果要运行依赖在线 LLM API 的实验，需要参考 `.env.example` 在本地创建 `.env`：

```text
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.deepseek.com
DEFAULT_MODEL=deepseek-v4-flash
```

安全原因：真实 `.env`、API key、虚拟环境、缓存、完整运行日志和本地存储目录不放入仓库。

## 运行方式

以下命令适用于已经配置好原始 MemEvolve / Flash-Searcher 环境的本地项目。

```powershell
cd <Flash-Searcher-main 项目根目录>
$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONIOENCODING = "utf-8"
```

Week 7 汇总：

```powershell
python experiments\week7\scripts\summarize_week7.py
```

Week 7 绘图：

```powershell
python experiments\week7\scripts\plot_week7_results.py
```

Week 6 汇总：

```powershell
python experiments\week6\scripts\build_week6_summary.py
```

## 当前限制

- 当前攻击样例主要围绕 Python 作者事实探针，后续需要扩展到更多任务和更多投毒模式。
- `architecture_defense_mapping_v0.csv` 仍是初版知识库，覆盖 D1/D2 较充分，对组合漂移、索引漂移和存储策略漂移覆盖不足。
- F2 当前是静态规则 Trust Gate，后续可进一步加入自适应阈值、多信号融合和跨任务泛化验证。
- 部分 live 实验依赖外部 API，结果可能存在轻微运行波动。

## 项目状态

当前仓库保存的是七周实验归档版本，重点用于展示实验设计、核心脚本、结构化结果和阶段性结论。

七周主线已经完成：

```text
记忆投毒基线 -> 架构漂移模拟 -> 静态防御对照 -> DPMF 漂移感知 -> 检测评估 -> 动态防御闭环
```
