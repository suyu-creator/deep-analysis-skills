<div align="center"><pre>
 ██████╗ ███████╗ ███████╗ ██████╗
██╔══██╗██╔════╝ ██╔════╝ ██╔══██╗
██║  ██║█████╗   █████╗   ██████╔╝
██║  ██║██╔══╝   ██╔══╝   ██╔═══╝
██████╔╝███████╗ ███████╗ ██║
╚═════╝ ╚══════╝ ╚══════╝ ╚═╝

 █████╗ ███╗   ██╗ █████╗ ██╗██╗   ██╗ ███████╗██╗███████╗
██╔══██╗████╗  ██║██╔══██╗██║╚██╗ ██╔╝██╔════╝██║██╔════╝
███████║██╔██╗ ██║███████║██║ ╚████╔╝ ███████╗██║███████╗
██╔══██║██║╚██╗██║██╔══██║██║  ╚═══╝  ╚════██║██║╚════██║
██║  ██║██║ ╚████║██║  ██║███████╗███████║██║███████║
╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚══════╝
  — 一条命令跑完需求理解 → 方向+模拟 → 报告 → PRD —
</pre></div>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License" /></a>
  <img src="https://img.shields.io/badge/Claude%20Code-native-purple?style=flat-square" alt="Claude Code Native" />
  <img src="https://img.shields.io/badge/deps-0-brightgreen?style=flat-square" alt="0 external dependencies" />
  <img src="https://img.shields.io/badge/version-1.0.0-orange?style=flat-square" alt="v1.0.0" />
</p>

<p align="center">
  <strong>复杂需求还在凭直觉直接写？做完才发现方向错了？</strong><br/>
  一条 <code>/deep-analysis &lt;需求&gt;</code> 命令，AI 先调研、再模拟、后对抗，最后给你一份能直接开工的 PRD。<br/>
  <br/>
  <em>不用装插件、不用配 MCP、不用外部服务 —— 纯 Claude Code 原生 skill 就能跑。</em>
</p>

---

## 一句话介绍

一个让 AI 对**复杂需求**做深度分析、产出可直接开工 PRD 的 Claude Code skill。

单条命令走完 **3 闸门**(需求理解 → 方向+模拟+可行性 → 报告) + **可选对抗 red-team** + **PRD 流水线**。内置 `researcher` / `simulator` / `reporter` 三个子代理,`pre-mortem` 死因自检 + `red-team` 对抗方法论。

**零外部依赖** —— 不依赖任何 MCP、不依赖任何外部 agent 注册,纯 Claude Code 原生 skill 即可运行。

---

## 痛点

你是不是也这样?

> "客户说要'做个商城',做完了才发现他要的是社区团购。"

> "复杂需求不敢让 AI 直接开工 —— 一开工就回不了头,返工成本太高。"

> "需求文档写出来和代码完全对不上,边写边改。"

**问题出在开工前的姿势不对。**

```
现在的流程:AI 听到需求 → 凭理解瞎做 → 方向错了 → 返工 → 还不对

应该有的流程:AI 先调研 → 先模拟 → 先确认方向 → 再动手 → 一次做对
```

**deep-analysis 把「深度需求分析」打包成一条命令。** 复杂需求,先想清楚再动手。

---

## 核心能力

### 🔥 3 闸门深度分析,方向不对坚决不写代码

```
闸门 1  需求理解      澄清范围,锁定 phase0 JSON(做什么 / 不做什么)
   ↓
闸门 2  方向+模拟+可行性  researcher ⟂ simulator 并行 → 整合可行性小结(含建议裁决)
   ↓
闸门 3  报告          reporter 汇总 6 部分报告,你验收
   ↓
PRD 阶段              整合 create-prd,跳过重复研究,产出 PRD
```

每道闸门都有明确的问题抛给你,你回答后才进下一道。**该问的必须问,不该等的绝不磨蹭。**

### 🔍 researcher 子代理:三层查询实时调研

写代码前先搞清楚**该怎么做**,不靠模型记忆瞎猜:

- **第 1 层** 文件系统 reflexion 记忆(跨会话积累的坑 / 决策 / 原型)
- **第 2 层** GitHub 仓库源码(核心层,搜同类成熟项目,读关键实现)
- **第 3 层** WebSearch(辅助层,补竞品口碑 / 行业动态)

每条 Claim 标注来源 + 证据数(Per-claim 验证),硬性 **Sufficiency Gate** 判断信息够不够,不够就继续查,最多 depth 轮。

### 🧪 simulator 子代理:动手前先模拟一遍 + 主动遗漏扫描 ⭐

LLM 最强的是联想和跨界,不是死板填表。simulator 发挥这点:

- **自由模拟** 实现过程(数据库 → API → 前端 → 部署 → 监控),每层模拟 5 层深
- **⭐ 主动遗漏扫描** —— 你没想到的,它替你想:
  - 用户没提但可能需要的(并发 / 对账 / 合规 / 监控)
  - 用户可能想当然的假设(日单 1k 的峰值?秒杀?退款?)
  - 相邻领域的教训(同类项目踩过的坑)

**每条声明必须引用 GitHub 代码或标注「LLM 推测」**,不许空口说白话。

### ⚔️ 可选对抗 red-team:6 个对手替你把方案打一遍

方案出来后,你 decide 要不要跑对抗。跑的话 AI 扮演 6 个对手攻击方案:

> 聪明对手 / 愤怒的流失客户 / 怀疑的 CFO / 超负荷工程师 / 监管者 / 投资人

每条攻击具体到数字和机制,并给裁决:✅ 有答案 / 🟨 弱答案 / 🔴 无答案。**每个无答案攻击都会回查 GitHub 同类项目找应对方案。**

### 📄 PRD 流水线:研究 → 起草 → 审查 → 资深 PM → 多轮修订

研究已由 researcher 做完,PRD 阶段直接复用,**不重走调研**。每个模块标 **复用 / 改造 / 自研** 三选一,复用候选映射到具体章节。最多 3 轮修订。

### 🧠 reflexion 记忆:跨会话越用越准

每次分析后把「坑模式 / 技术决策 / 项目原型」写进 `~/.claude/memory/reflexion/`。下次分析同类需求,researcher 第 1 层直接读历史经验,**不用重新踩坑**。

---

## 装了 vs 没装

| | 没装 deep-analysis | 装了 deep-analysis |
|---|---|---|
| 复杂需求处理 | 凭直觉直接写 | 3 闸门先想清楚 |
| 竞品 / 技术选型调研 | 靠模型记忆瞎猜 | 三层查询实时调研,带来源 |
| 方向确认 | 写错了返工 | 先模拟 + 可行性小结再确认 |
| 遗漏点 | 写出来才发现 | simulator 主动扫描,开工前暴露 |
| 需求文档 | 没有,边写边改 | PRD 多轮修订,可直接开工 |
| 对抗审查 | 没有 | red-team 可选挑刺,6 个对手 |
| 历史经验 | 每次从零 | reflexion 记忆跨会话复用 |
| 外部依赖 | — | 零 MCP 零插件,原生 skill |

---

## 快速开始

### 安装(任选其一)

**方式 A:手动复制(推荐,最简单)**

```bash
# 1. 把 skills/deep-analysis 复制到你的 skill 目录
cp -r skills/deep-analysis ~/.claude/skills/deep-analysis

# 2. 初始化 reflexion 记忆(首次,跨会话复用)
mkdir -p ~/.claude/memory/reflexion
cp reflexion/*.md ~/.claude/memory/reflexion/
```

**方式 B:marketplace 安装**

```bash
# 在 Claude Code 中
/plugin marketplace add <本仓库 URL>
/plugin install deep-analysis@<marketplace 名>
```

> ⚠️ marketplace 安装后 skill 位于插件缓存目录(非 `~/.claude/skills/deep-analysis/`)。PIPELINE.md 内默认路径需替换为实际安装路径(见 PIPELINE.md 顶部「路径适配」说明)。**若嫌麻烦,推荐方式 A 手动复制。**

**方式 C:git clone**

```bash
git clone <本仓库 URL> ~/.claude/skills/deep-analysis-skills
# 然后把 skills/deep-analysis 链接或复制到 ~/.claude/skills/
```

### 使用

```bash
/deep-analysis 做一个日单 1k 的电商小程序
```

流程自动跑:**Step 0 预检 → 闸门 1 需求理解(问你 1-2 个关键问题)→ 闸门 2 researcher+simulator 并行 + 可行性小结 → 可选对抗 red-team → 闸门 3 报告 → PRD 产出**。你只在每道闸门答一个问题,不要求分步调用。

### 试试这个

装好后跟你的 AI 说:

> "做个多商户的 SaaS 订单系统,要支持支付、库存、对账,先去调研一下再出方案"

看看它是不是**先调研 → 先模拟 → 先确认方向**,而不是直接开写。

---

## 触发判断(先用对,再用好)

**复杂需求才触发**(满足任一):多模块 / 多页面、外部集成(支付/登录/第三方 API/数据库迁移)、需调研竞品/技术选型、存在规模/并发/安全/合规风险、范围模糊。

**简单需求不触发**(单页、单接口、改逻辑、加字段):skill 会**直接忽略**,给 1 句方案即可 —— 不为小需求浪费 token 跑完整流程。

---

## 分层定位

| 工具 | 定位 | 适用 |
|---|---|---|
| **deep-analysis (本 skill)** | 复杂任务 | 多模块 / 需架构决策 / 需调研竞品与技术选型 / 存在规模·并发·安全·合规风险 / 范围模糊的新功能或系统 |
| **github-code-rag MCP**(可选增强) | 中 / 简单任务 | 快速查已读代码、免限流的 GitHub 检索 |

两者互补:复杂需求走本 skill 的 3 闸门 + 对抗 + PRD;中/简单需求直接让 LLM 用内置工具或 github-code-rag 快速解决,不必跑完整流程。

---

## 工作原理

```
/deep-analysis <需求>
  │
  ├─ Step 0  预检(preflight.sh:GitHub 访问 + curl/gh 内置工具)
  ├─ 闸门 1  需求理解(澄清范围,锁定 phase0 JSON)─────────── 你确认
  ├─ 闸门 2  方向+模拟+可行性
  │          ┌─────────────┐   ┌──────────────┐
  │          │ researcher  │ ⟂ │  simulator   │   并行,互不依赖
  │          │ 三层查询     │   │ 模拟+遗漏扫描  │
  │          └─────────────┘   └──────────────┘
  │                  └→ 主 Agent 整合「可行性+风险小结」
  ├─ 可选    对抗 red-team(6 对手攻击方案,🔴/🟨 回查 GitHub)─── 你 decide
  ├─ 闸门 3  报告(reporter 6 部分 + self-refine)─────────── 你验收
  └─ PRD    整合 create-prd,跳过重复研究,多轮修订 ──────── 你批复
```

### 为什么这么重,不是直接让 AI 写?

| | 直接写 | deep-analysis |
|---|---|---|
| 方向验证 | 写错了才知道 | 闸门 2 先模拟 + 可行性 |
| 竞品调研 | 模型记忆 | 实时 GitHub 源码 |
| 遗漏发现 | 用户自己发现 | simulator 主动扫描 |
| 需求文档 | 无 | PRD 流水线产出 |
| 返工成本 | 高 | 开工前确认 |

**核心哲学:复杂需求最贵的是返工,不是分析。** 花 10 分钟确认方向,省下 10 天的返工。

---

## 目录结构

```
deep-analysis-skills/
├── .claude-plugin/
│   ├── plugin.json          # Claude Code 插件清单
│   └── marketplace.json     # marketplace 聚合(支持 /plugin marketplace add)
├── skills/
│   └── deep-analysis/       # 核心 skill(可独立复制使用)
│       ├── SKILL.md         # 编排:3 闸门 + 可选对抗 + PRD 阶段
│       ├── agents/          # researcher / simulator / reporter 子代理
│       ├── methods/         # pre-mortem(7 类死因) / red-team(6 对手)
│       ├── scripts/         # preflight.sh 环境预检
│       ├── prd/             # PRD 流水线(研究→起草→审查→资深PM→多轮修订)
│       └── project-context.template.md
├── reflexion/               # 首次使用的空骨架记忆(复制到 ~/.claude/memory/reflexion/)
├── README.md
├── LICENSE                  # MIT
└── .gitignore
```

---

## 可选增强:github-code-rag MCP

本 skill **默认不依赖任何 MCP** 即可运行(GitHub 检索全走内置工具 curl / gh CLI / WebSearch)。若你愿意,可配置 [github-code-rag MCP](https://github.com/suyu-creator/github-code-rag-mcp) 获得:

- **免限流**:GitHub API 匿名限 60 次/h,配 MCP 后走本地 SQLite 索引,不耗配额
- **已读代码复用**:`search_code` / `search_history` 本地 FTS5 全量搜历史读过的代码,跨会话复用
- **加速中/简单任务**:小需求直接问它快速检索,不必跑完整 deep-analysis 流程

配置方式(在 `~/.claude.json` 的 `mcpServers` 或 Claude Desktop 配置中):

```json
{
  "mcpServers": {
    "github-code-rag": {
      "command": "<启动命令>",
      "args": ["<参数>"]
    }
  }
}
```

> ⚠️ MCP 是**可选加分项**。未配置时 skill 的 GitHub 访问自动降级为内置工具(见 SKILL.md Step 0「工具映射速查」),功能完整不受影响。配置后建议重启 Claude Code 生效。

---

## reflexion 记忆(跨会话积累)

skill 在流程关键节点写 `~/.claude/memory/reflexion/` 下 3 个文件(pitfalls_patterns / tech_decisions_lessons / project_archetypes),供下次分析复用(坑模式、技术决策、项目原型)。**首次使用需初始化**(见「安装 方式 A」步骤 2),把 `reflexion/` 下的空骨架复制过去。这是与 Claude Code auto memory 独立的一套记忆,互不干扰。

---

## 硬规则速览

1. **复杂需求才触发** — 简单需求直接忽略,不为小需求跑完整流程
2. **复用优先** — 先搜 GitHub 代码和 reflexion 记忆,有现成直接引用;每条声明必须引用 GitHub 代码或标「LLM 推测」
3. **单命令完整流程** — 一条 `/deep-analysis <需求>` 走完全流程,不要求分步调用子技能

---

## FAQ

**简单需求会触发吗?**

不会。单页、单接口、改逻辑、加字段 —— skill 直接忽略,给 1 句方案,不为小需求浪费 token。

**依赖任何 MCP 或外部服务吗?**

零依赖。所有 GitHub 检索走 Claude Code 内置工具(curl / gh CLI / WebSearch),不配任何 MCP 就能跑完整流程。

**和 github-code-rag MCP 什么关系?**

可选的加速器,不是依赖。配了可以免限流 + 已读代码复用;不配功能完整不受影响。

**为什么 researcher / simulator 要引用 GitHub 代码?**

防止 AI 凭训练记忆瞎编。每条声明要么有真实代码锚点(repo+file+line),要么显式标注「LLM 推测,未验证」,两者一目了然。

**分析结果存在哪?**

报告直接对话展示,不落盘。PRD 走 create-prd 流水线落盘。reflexion 记忆 append 到 `~/.claude/memory/reflexion/`,供下次复用。

**能跳过某道闸门吗?**

可以。对抗 red-team 是可选环节,你在闸门 2 确认时 decide 跑不跑。闸门 1/2/3 是核心流程,建议走完 —— 每道闸门只花你 1 个问题的时间。

**这个项目被 GitHub 限流了怎么办?**

匿名 curl 限 60 次/h。配 `GITHUB_TOKEN` 提到 5000 次/h;`raw.githubusercontent.com` 读文件不受限流;再不行降级 WebSearch。多路兜底。

---

## 参与贡献

- 发现 Bug → 提 Issue
- 有新想法 → 先开 Issue 讨论
- 代码贡献 → Fork + PR
- 觉得好用 → 点个 star,让更多人看到

---

## License

[MIT](LICENSE)
