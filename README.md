<div align="center"><pre>
 ██████╗ ███████╗ ███████╗ ██████╗
██╔══██╗██╔════╝ ██╔════╝ ██╔══██╗
██║  ██║█████╗   █████╗   ██████╔╝
██║  ██║██╔══╝   ██╔══╝   ██╔═══╝
██████╔╝███████╗ ███████╗ ██║
╚═════╝ ╚══════╝ ╚══════╝ ╚═╝

 █████╗ ███╗   ██╗ █████╗ ██╗  ██╗   ██╗ ███████╗██╗███████╗
██╔══██╗████╗  ██║██╔══██╗██║  ╚██╗ ██╔╝██╔════╝██║██╔════╝
███████║██╔██╗ ██║███████║██║   ╚████╔╝ ███████╗██║███████╗
██╔══██║██║╚██╗██║██╔══██║██║    ╚═══╝  ╚════██║██║╚════██║
██║  ██║██║ ╚████║██║  ██║███████╗    ███████║██║███████║
╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝    ╚══════╝╚═╝╚══════╝
 — One command: clarify → research → dual-simulate → build plan —
</pre></div>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License" /></a>
  <img src="https://img.shields.io/badge/Claude%20Code-native-purple?style=flat-square" alt="Claude Code Native" />
  <img src="https://img.shields.io/badge/files-3-lightgrey?style=flat-square" alt="3 files" />
  <img src="https://img.shields.io/badge/version-3.0.0-orange?style=flat-square" alt="v3.0.0" />
</p>

<p align="center">
  <strong>Research first, simulate for gaps, verify with a second simulation, then output a build-ready execution plan.</strong><br/>
  One <code>/deep-analysis &lt;requirement&gt;</code>, 3 files, ~8KB, ultra-lightweight.<br/>
  <br/>
  <em>Pure markdown. Zero built-in MCPs. Zero external dependencies.</em>
</p>

---

## v3.0 Changes

v3.0: **PRD → Closure Report**. No longer an analysis document — it's an executable build plan. **Dual simulation** ensures a closed loop.

| | v2.1 | v3.0 |
|---|---|---|
| Final output | PRD.md (analysis) | **CLOSURE.md (build plan)** |
| Simulation | 1 pass (gap scan) | **2 passes (pre-sim discover + post-sim verify)** |
| 7-class death check | Yes | **Removed** (not needed for build plans) |
| Reuse candidates | Suitability rating | **Build info** (file / method / changes needed) |
| Gap list | Describes gaps | **Gap + build action** |

**Closure Report 5 sections**: Project skeleton → Reuse build sheet → Implementation roadmap → Custom build sheet → Closure self-check (post-sim)

---

## v2.0 Changes

v1.0 had 30+ files, 250KB+ pipeline — way too heavy. v2.0 cut to **3 files, ~8KB**:

| | v1.0 | v2.0 |
|---|---|---|
| Files | 30+ | **3** |
| Total size | ~250KB | **~8KB** |
| Sub-agents / stages | 3 | **2** (sequential) |
| PRD output | 250KB pipeline | **LLM writes directly** |
| Red-team | Standalone method | **Inline optional** |
| GitHub search | curl/gh CLI | **gh/curl built-in**, optional github-code-rag MCP |
| External deps | Zero | **Zero** (MCP is optional enhancement) |

---

## Overview

Run `/deep-analysis <requirement>` — AI researches GitHub for similar projects → pre-sim discovers gaps → confirms direction → outputs a closure report (executable build plan with post-simulation self-check).

---

## Core Flow

```
/deep-analysis <requirement>
  ├─ Step 1  Clarify (1-2 questions → lock scope) ── You confirm
  ├─ Step 2  researcher → pre-sim (sequential)
  │          ┌──────────────┐  ┌──────────────┐
  │          │ researcher   │→ │  pre-sim      │
  │          │ GitHub search │  │ discover gaps │
  │          │ build material │  │ gap→action   │
  │          └──────────────┘  └──────────────┘
  ├─ Step 3  Feasibility (reuse + gaps) ── You confirm
  ├─ Optional red-team (6 roles attack the plan) ── You decide
  └─ Step 4  Output CLOSURE.md (with post-sim = self-check)
        ⤴ New requirement anytime → pause, follow hard rule 4
```

**Dual simulation**:
- **Pre-sim (Step 2)**: Discover what you don't know you don't know → gap list
- **Post-sim (Step 4)**: Simulate executing the plan. If it fails, fix it and re-simulate until it passes → coverage table + dependency check + source honesty

### researcher — GitHub Research

Search GitHub for similar projects, produce reuse candidates. **Defaults to `gh` CLI / `curl`** — zero external dependencies. If you have `github-code-rag` MCP installed, the agent automatically prefers MCP for better search experience.

### simulator — Pre-sim (Gap Scan)

Simulate the implementation process. Three scan categories:
- **User didn't mention but needs**: edge cases, ops, compliance, monitoring
- **User's implicit assumptions**: scale, platform, business, integration, data
- **Lessons from adjacent domains**: similar projects' pitfalls

Every gap comes with a build action. Every claim must cite GitHub code or mark "LLM speculation".

### Closure Report — Executable Build Plan

5 sections:
1. **Project skeleton** — directory structure + init commands, copy-paste to run
2. **Reuse build sheet** — where to copy from, what to copy, what to change, why
3. **Implementation roadmap** — phased, each phase has steps + deps + verification
4. **Custom build sheet** — what can't be reused, concrete implementation approach
5. **Closure self-check (post-sim)** — simulated walkthrough, fix on failure, re-check

---

## Quick Start

### Install

```bash
# Copy 3 files to skills directory
cp -r skills/deep-analysis ~/.claude/skills/deep-analysis
```

### Optional Enhancement: github-code-rag MCP

This skill **works with zero dependencies by default**. Researcher/simulator use Claude Code built-in tools (`gh` CLI, `curl`, WebSearch) for GitHub search.

If you install [github-code-rag MCP](https://github.com/suyu-creator/github-code-rag-mcp) (separate project), the agent automatically prefers MCP for better search. Works fine without it.

### Usage

```bash
/deep-analysis Build an e-commerce mini-program handling 1k orders/day
```

---

## Trigger

**Complex requirements only** (any of): multi-module / architecture decisions, external integrations, competitor research / tech selection needed, scale/concurrency/security risks, vague scope like "build an XX system".

**Simple requirements skip** (single page, single endpoint, logic change, add field): give one-line solution directly.

---

## Directory Structure

```
deep-analysis-skills/
├── skills/
│   └── deep-analysis/
│       ├── SKILL.md              # Orchestration: 4 Steps + optional red-team + dual sim
│       └── stages/
│           ├── researcher.md      # Research: GitHub search + build material
│           └── simulator.md       # Pre-sim: gap scan + build actions
├── README.md
├── LICENSE
└── .gitignore
```

3 files, no pipelines, no scripts, no templates.

---

## Hard Rules

1. **Complex only** — skip simple requests
2. **Reuse first** — search GitHub first, cite existing solutions, don't invent from scratch
3. **Every claim sourced** — GitHub code (repo@file:line) or "LLM speculation"
4. **Requirement change = stop** — new requirement anytime (in-flow or post-report): pause → record → assess impact → roll back to affected step (scope change→Step1, approach change→Step2, append-only→report backlog) → user confirms → continue. Never silently proceed with old requirements

---

## FAQ

**Q: Will simple requirements trigger this?**
No. Single page, single endpoint, logic change — skill ignores and gives a one-line solution.

**Q: Dependencies?**
Zero. This repo is 3 markdown files only. No built-in MCPs or binaries. GitHub search uses Claude Code's built-in `gh` CLI / `curl`. `github-code-rag` MCP is a separate optional project.

**Q: Why must every claim cite a source?**
Prevents AI from fabricating based on training memory. Every claim has either a real code anchor or is explicitly marked "LLM speculation".

**Q: What is dual simulation?**
Pre-sim (Step 2) discovers what you don't know you don't know. Post-sim / closure self-check (Step 4) simulates executing the plan — if it fails, fix it and re-simulate until it passes.

**Q: Can I skip red-team?**
Yes. Red-team is optional. You decide after Step 3. If you run it, results must be confirmed before writing the closure report.

**Q: What if I want to change requirements mid-way or after the report?**
Just say so. Hard rule 4 "requirement change = stop": AI pauses → records new requirement → assesses impact → rolls back to the affected step → waits for your confirmation. Never silently proceeds with old requirements.

**Q: Where are results saved?**
Reports are displayed in conversation. The closure report is written to `CLOSURE.md`.

---

## License

[MIT](LICENSE)

---

---

# 中文

---

## v3.0 变化

v3.0 核心变化：**PRD → 闭环报告**。不再是分析文档，而是可执行的施工图纸。加入**双模拟机制**确保闭环。

| | v2.1 | v3.0 |
|---|---|---|
| 最终产出 | PRD.md（分析） | **CLOSURE.md（施工图纸）** |
| 模拟 | 1 次（遗漏扫描） | **2 次（前模拟发现未知 + 闭环自检验证覆盖）** |
| 7 类死因自检 | 有 | **砍掉**（施工计划不需要） |
| 复用候选 | 适用性评估 | **施工信息**（文件/复用方式/需改动） |
| 遗漏清单 | 描述遗漏 | **遗漏 + 施工动作** |

**闭环报告 5 块**：项目骨架 → 复用施工单 → 实施路线图 → 自研施工单 → 闭环自检（后模拟）

---

## v2.0 变化

v1.0 有 30+ 文件、250KB+ 流水线，太重了。v2.0 砍到 **3 个文件、~8KB**：

| | v1.0 | v2.0 |
|---|---|---|
| 文件数 | 30+ | **3** |
| 总大小 | ~250KB | **~8KB** |
| 子代理/阶段 | 3 | **2**（顺序执行） |
| PRD 产出 | 250KB 流水线 | **LLM 直接写文件** |
| 对抗 | 独立 red-team 方法 | **内联可选** |
| GitHub 搜索 | curl/gh CLI | **gh/curl 内置工具**，可选配 github-code-rag MCP 增强 |
| 外部依赖 | 零依赖 | **零依赖**（MCP 是可选增强，非必须） |

---

## 一句话介绍

复杂需求走 `/deep-analysis <需求>`，AI 先调研 GitHub 同类项目 → 前模拟发现遗漏 → 确认方向 → 输出闭环报告（可执行的施工图纸，含后模拟闭环自检）。

---

## 核心流程

```
/deep-analysis <需求>
  ├─ Step 1  需求澄清（1-2 问 → 锁定范围）── 你确认
  ├─ Step 2  researcher → 前模拟 顺序执行
  │          ┌──────────────┐  ┌──────────────┐
  │          │ researcher   │→ │  前模拟       │
  │          │ GitHub 调研   │  │ 发现未知遗漏   │
  │          │ 产出施工素材   │  │ 遗漏→施工动作  │
  │          └──────────────┘  └──────────────┘
  ├─ Step 3  可行性整合（复用候选 + 遗漏清单）── 你确认
  ├─ 可选    对抗 red-team（6 角色攻击方案）── 你 decide
  └─ Step 4  输出 CLOSURE.md（含后模拟=闭环自检）
        ⤴ 任意时刻冒出新需求 → 暂停，按硬规则 4 处理
```

**双模拟分工**：
- **前模拟（Step 2）**：发现你不知道自己不知道的事 → 遗漏清单
- **后模拟（闭环自检，Step 4）**：模拟执行计划，走不通就修，修完再走，直到通为止 → 覆盖表 + 依赖检查 + 来源诚实

### researcher — GitHub 调研

搜 GitHub 同类项目，产出复用候选清单。**默认走 `gh` CLI / `curl` 内置工具**，无需任何外部依赖。如果你装了 `github-code-rag` MCP，主 Agent 会自动优先走 MCP 获得更好的搜索体验。

### simulator — 前模拟（遗漏扫描）

模拟实现过程，三类扫描：
- **用户没提但需要的**：边缘场景、运营需求、合规、监控
- **用户想当然的假设**：规模、平台、业务、集成假设
- **相邻领域教训**：同类项目踩过的坑

每条遗漏配施工动作，每条声明必须引用 GitHub 代码或标注「LLM 推测」。

### 闭环报告 — 可执行的施工图纸

5 块内容：
1. **项目骨架** — 目录结构 + 初始化命令，复制粘贴就跑
2. **复用施工单** — 从哪抄、抄什么、改什么、为什么
3. **实施路线图** — 分 Phase，每个 Phase 有步骤 + 依赖 + 验证
4. **自研施工单** — 没得复用的部分，具体实现思路
5. **闭环自检（后模拟）** — 模拟走查，走不通就修，修完再走

---

## 快速开始

### 安装

```bash
# 复制 3 个文件到 skill 目录
cp -r skills/deep-analysis ~/.claude/skills/deep-analysis
```

### 可选增强：github-code-rag MCP

本 skill **默认不依赖任何外部服务**。researcher/simulator 阶段用 Claude Code 内置工具（`gh` CLI、`curl`、WebSearch）完成 GitHub 搜索。

如果你装了 [github-code-rag MCP](https://github.com/suyu-creator/github-code-rag-mcp)（独立项目，需单独安装），主 Agent 会自动优先走 MCP 通道，获得更好的搜索体验。没装也完全能用。

### 使用

```bash
/deep-analysis 做一个日单 1k 的电商小程序
```

---

## 触发判断

**复杂需求才触发**（满足任一）：多模块/需架构决策、外部集成、需调研竞品/技术选型、存在规模/并发/安全风险、范围模糊。

**简单需求不触发**（单页、单接口、改逻辑、加字段）：直接给 1 句方案。

---

## 目录结构

```
deep-analysis-skills/
├── skills/
│   └── deep-analysis/
│       ├── SKILL.md              # 编排：4 Step + 可选对抗 + 双模拟
│       └── stages/
│           ├── researcher.md      # 调研：GitHub 搜索 + 施工素材
│           └── simulator.md       # 前模拟：遗漏扫描 + 施工动作
├── README.md
├── LICENSE
└── .gitignore
```

3 个文件，没有流水线，没有脚本，没有模板。

---

## 硬规则

1. **复杂需求才触发** — 简单需求直接忽略
2. **复用优先** — 先搜 GitHub，有现成直接引用，不从零想方案
3. **每条声明标注来源** — GitHub 代码（repo@文件:行号）或「LLM 推测」
4. **需求变更即停** — 任意时刻冒出新需求（流程中/闭环报告后）：暂停 → 记录 → 评估影响 → 回退对应 Step（动范围→Step1、动方案→Step2、仅追加→闭环报告需求池）→ 用户确认后继续。绝不默默按旧需求做到底

---

## FAQ

**简单需求会触发吗？**
不会。单页、单接口、改逻辑 — skill 直接忽略，给 1 句方案。

**依赖什么？**
零外部依赖。本仓库只有 3 个 markdown 文件，不内置任何 MCP 或二进制。GitHub 搜索走 Claude Code 内置的 `gh` CLI / `curl`。`github-code-rag` MCP 是独立项目，可选安装，装了体验更好，不装也能正常用。

**为什么声明要标注来源？**
防止 AI 凭训练记忆瞎编。每条声明要么有真实代码锚点，要么显式标注「LLM 推测」。

**双模拟是什么？**
前模拟（Step 2）发现你不知道自己不知道的事；后模拟/闭环自检（Step 4）模拟执行计划，走不通就修，修完再走，直到通过。

**能跳过对抗吗？**
可以。对抗是可选的，Step 3 确认后你决定跑不跑。跑了的话，结果必须你确认后才写闭环报告。

**分析中途或出完报告后又想改需求？**
直接说。硬规则 4「需求变更即停」：AI 会暂停 → 记录新需求 → 评估影响 → 回退对应 Step → 你确认后再继续，绝不默默按旧需求做到底。

**分析结果存在哪？**
报告直接对话展示，闭环报告写 `CLOSURE.md` 文件落盘。

---

## License

[MIT](LICENSE)