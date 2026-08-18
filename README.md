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
  — 一条命令跑完 需求澄清 → GitHub 调研 → 可行性 → PRD —
</pre></div>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License" /></a>
  <img src="https://img.shields.io/badge/Claude%20Code-native-purple?style=flat-square" alt="Claude Code Native" />
  <img src="https://img.shields.io/badge/files-3-lightgrey?style=flat-square" alt="3 files" />
  <img src="https://img.shields.io/badge/version-2.0.0-orange?style=flat-square" alt="v2.0.0" />
</p>

<p align="center">
  <strong>复杂需求先调研、再模拟、后确认方向，最后输出能直接开工的 PRD。</strong><br/>
  一条 <code>/deep-analysis &lt;需求&gt;</code>，3 个文件，~8KB，极简轻量。<br/>
  <br/>
  <em>纯 markdown 文件，3 个文件 ~8KB。不内置任何 MCP，不依赖外部服务。</em>
</p>

---

## v2.0 变化

v1.0 有 30+ 文件、250KB+ 流水线，太重了。v2.0 砍到 **3 个文件、~8KB**：

| | v1.0 | v2.0 |
|---|---|---|
| 文件数 | 30+ | **3** |
| 总大小 | ~250KB | **~8KB** |
| 子代理 | 3 (researcher/simulator/reporter) | **2** (researcher/simulator) |
| PRD 产出 | 250KB 流水线 | **LLM 直接写文件** |
| 对抗 | 独立 red-team 方法 | **内联可选** |
| GitHub 搜索 | curl/gh CLI | **gh/curl 内置工具**，可选配 github-code-rag MCP 增强 |
| 外部依赖 | 零依赖 | **零依赖**（github-code-rag MCP 是可选增强，非必须） |

---

## 一句话介绍

复杂需求走 `/deep-analysis <需求>`，AI 先调研 GitHub 同类项目 → 并行模拟发现遗漏 → 确认方向 → 输出 PRD.md（每个模块标注复用/改造/自研 + 来源）。

---

## 核心流程

```
/deep-analysis <需求>
  ├─ Step 1  需求澄清(1-2 问 → 锁定范围)── 你确认
  ├─ Step 2  researcher ⟂ simulator 并行
  │          ┌──────────────┐  ┌──────────────┐
  │          │ researcher   │  │  simulator   │
  │          │ GitHub 调研   │  │ 遗漏扫描+风险 │
  │          └──────────────┘  └──────────────┘
  ├─ Step 3  可行性整合(复用候选 + 遗漏 + 死因自检)── 你确认
  ├─ 可选    对抗 red-team(6 角色攻击方案)── 你 decide
  └─ Step 4  输出 PRD.md(模块→复用/改造/自研 + 来源)
```

### researcher — GitHub 调研

搜 GitHub 同类项目，产出复用候选清单。**默认走 `gh` CLI / `curl` 内置工具**，无需任何外部依赖。如果你装了 `github-code-rag` MCP，子代理会自动走 MCP 获得更好的搜索体验。

### simulator — 遗漏扫描

模拟实现过程，三类扫描：
- **用户没提但需要的**：边缘场景、运营需求、合规、监控
- **用户想当然的假设**：规模、平台、业务、集成假设
- **相邻领域教训**：同类项目踩过的坑

每条声明必须引用 GitHub 代码或标注「LLM 推测」。

### PRD 输出

每个模块标 **复用 / 改造 / 自研**，复用/改造必须标注来源 repo + 文件路径。

---

## 快速开始

### 安装

```bash
# 复制 3 个文件到 skill 目录
cp -r skills/deep-analysis ~/.claude/skills/deep-analysis
```

### 可选增强：github-code-rag MCP

本 skill **默认不依赖任何外部服务**。researcher/simulator 子代理用 Claude Code 内置工具（`gh` CLI、`curl`、WebSearch）完成 GitHub 搜索。

如果你装了 [github-code-rag MCP](https://github.com/suyu-creator/github-code-rag-mcp)（独立项目，需单独安装），子代理会自动优先走 MCP 通道，获得本地索引、免限流、已读代码复用等增强能力。没装也完全能用。

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
│       ├── SKILL.md              # 编排: 4 Step + 可选对抗
│       └── agents/
│           ├── researcher.md      # GitHub 调研 + 复用候选
│           └── simulator.md       # 遗漏扫描 + 风险
├── README.md
├── LICENSE
└── .gitignore
```

3 个文件，没有流水线，没有脚本，没有模板。

---

## 硬规则

1. **复杂需求才触发** — 简单需求直接忽略
2. **复用优先** — 先搜 GitHub，有现成直接引用
3. **每条声明标注来源** — GitHub 代码(repo@文件:行号) 或 「LLM 推测」

---

## FAQ

**简单需求会触发吗？** 不会。单页、单接口、改逻辑 — skill 直接忽略，给 1 句方案。

**依赖什么？** 零外部依赖。本仓库只有 3 个 markdown 文件，不内置任何 MCP 或二进制。GitHub 搜索走 Claude Code 内置的 `gh` CLI / `curl`。`github-code-rag` MCP 是独立项目，可选安装，装了体验更好，不装也能正常用。

**为什么声明要标注来源？** 防止 AI 凭训练记忆瞎编。每条声明要么有真实代码锚点，要么显式标注「LLM 推测」。

**能跳过对抗吗？** 可以。对抗是可选的，Step 3 确认后你 decide 跑不跑。

**分析结果存在哪？** 报告直接对话展示，PRD 写 `PRD.md` 文件落盘。

---

## License

[MIT](LICENSE)