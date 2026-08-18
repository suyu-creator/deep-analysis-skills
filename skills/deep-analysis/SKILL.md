---
name: deep-analysis
description: 深度需求分析。单命令 /deep-analysis <需求> 走完 需求澄清→GitHub调研+模拟→可行性整合→可选对抗→PRD 输出。内置 researcher/simulator 2 子代理并行。触发:复杂/多模块/需调研的功能。简单需求(单页面/单接口/改文案)不触发。
argument-hint: <需求描述>
---

# Deep Analysis

单命令走完「需求 → 调研 → 可行性 → PRD」。

## 触发判断

复杂需求才执行，满足任一即复杂：
- 多模块 / 需要架构决策
- 涉及外部集成(支付/登录/第三方 API)
- 需要调研竞品 / 复用候选 / 技术选型
- 存在规模/并发/安全风险
- 用户说"做个 XX 系统/平台"，范围模糊

**简单需求不执行**，直接给 1 句方案。

## 流程总览

```
/deep-analysis <需求>
  ├─ Step 1  需求澄清(1-2 问 → 锁定范围)── 用户确认
  ├─ Step 2  researcher ⟂ simulator 并行调研
  ├─ Step 3  可行性整合(主 Agent 直接输出)── 用户确认
  ├─ 可选    对抗 red-team(用户 decide)
  └─ Step 4  输出 PRD.md(标注每个模块复用来源)
```

## Step 1: 需求澄清

问 1-2 个关键问题（平台？规模？已有代码还是全新？），锁定范围后用户确认。

输出 `phase0`：
```json
{
  "requirement": "<需求原文>",
  "platform": "<平台>",
  "scale": "<规模>",
  "existing_code": "<greenfield / 已有项目路径>",
  "anti_goal": "<明确不做哪些>"
}
```

## Step 2: 调研 + 模拟（并行 spawn）

基于 phase0，**并行 spawn 两个子代理**：

- **researcher** — 用 `github-code-rag` MCP 搜 GitHub 同类项目，产出复用候选清单。Spawn an Agent using the prompt from `agents/researcher.md`，传入 phase0。
- **simulator** — 模拟实现过程，主动发现遗漏。Spawn an Agent using the prompt from `agents/simulator.md`，传入 phase0。

两者都只依赖 phase0，互不依赖，并行跑。

## Step 3: 可行性整合

两者返回后，主 Agent 直接整合输出：

```
## 可行性整合

### 复用候选 Top 3
| repo | 用途 | 适用性 |

### 遗漏 Top 5（从 simulator）
| 遗漏 | 严重度 | 解决方案 | 来源 |

### 7 类死因自检
| 死因 | 成立? | 应对 |
|------|------|------|
| 市场 | 是/否 | <方案> |
| 技术 | 是/否 | <方案> |
| 人 | 是/否 | <方案> |
| 时机 | 是/否 | <方案> |
| 钱 | 是/否 | <方案> |
| 采用 | 是/否 | <方案> |
| 监管 | 是/否 | <方案> |

### 裁决
proceed / 改 / 转向 / kill
```

HIGH 风险给应对方案，查 GitHub 找实证。

展示后问用户：**"方向对吗？可行性 OK 吗？要不要跑对抗 red-team？"**

## 可选: 对抗 red-team

用户选「对抗」时执行。扮演 6 个角色攻击方案：竞争者 / 愤怒客户 / CFO / 超负荷工程师 / 监管者 / 投资人。每个角色 3-6 条具体攻击。每条 🔴/🟨 攻击给解决方案，查 GitHub 找实证。输出未答复攻击清单按杀伤力排序。

用户选「跳过」→ 直接进 Step 4。

## Step 4: 输出 PRD

写 `PRD.md` 文件，模板：

```markdown
# PRD: <项目名>

## 1. 需求概述
## 2. 范围（做什么 / 不做什么）

## 3. 模块分解
| 模块 | 方案 | 复用来源 |
|------|------|---------|
| <模块A> | 复用 | github.com/xxx/yyy — <文件路径> |
| <模块B> | 改造 | github.com/aaa/bbb — <参考了什么，改了什么> |
| <模块C> | 自研 | 无现成方案 — <理由> |

## 4. 技术栈
## 5. 风险与缓解
## 6. 任务分解（含依赖）
```

每个模块必须标 **复用 / 改造 / 自研**，复用/改造必须标注来源 repo + 文件路径。

## 硬规则

1. **复杂需求才触发** — 简单需求直接忽略
2. **复用优先** — 先搜 GitHub，有现成直接引用，不从零想方案
3. **每条声明标注来源** — GitHub 代码(repo@文件:行号) 或 「LLM 推测」

## 目录结构

```
~/.claude/skills/deep-analysis/
├── SKILL.md              # 本文件: 编排 + 4 Step + 可选对抗
├── agents/
│   ├── researcher.md      # 调研: GitHub 搜索 + 复用候选
│   └── simulator.md       # 模拟: 遗漏扫描 + 风险
```