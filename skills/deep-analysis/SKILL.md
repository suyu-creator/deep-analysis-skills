---
name: deep-analysis
description: 深度需求分析(全家桶)。单命令 /deep-analysis <需求> 走完 3 闸门(需求理解/方向+模拟+可行性小结/报告)+ 可选对抗 red-team + PRD 产出。内置 researcher/simulator/reporter 3 子代理 + pre-mortem/red-team 方法论 + create-prd 全套。零外部依赖,一处维护。触发:复杂/多模块/有架构决策/需调研的新功能或系统。简单需求(单页面/单接口/改文案)不触发,直接忽略。
argument-hint: <需求描述>
---

# Deep Analysis — 深度需求分析全家桶

单条命令跑完从「需求 → 方案 → 可行性 → 红队 → PRD」的完整流程。所有子代理、方法论、PRD 工具链都收进本技能目录,**不依赖任何外部 skill / 外部 agent 注册**,一处维护。

## 触发判断(第一步,不满足直接忽略)

**复杂需求才执行**,简单需求忽略。判断标准(满足任一即复杂):

- 多模块 / 多页面 / 需要架构决策
- 涉及外部集成(支付/登录/第三方 API/数据库迁移)
- 需要调研竞品 / 复用候选 / 技术选型
- 存在规模/并发/安全/合规风险
- 用户明确说"做个 XX 系统/平台",范围模糊需澄清

**简单需求**(单页、单接口、改逻辑、加字段)**:不执行本流程**,直接告诉用户这是简单需求,给出 1 句方案即可。避免为小需求跑完整流程浪费 token。

## 核心流程总览

```
/deep-analysis <需求>
  │
  ├─ Step 0  预检(MCP 双保险 + reflexion + git)
  ├─ 闸门 1  需求理解(澄清范围,锁定 phase0 JSON)── 用户确认
  ├─ 闸门 2  方向+模拟+可行性(researcher ⟂ simulator 并行 → 主 Agent 整合可行性小结)── 用户确认
  ├─ 可选    对抗 red-team(用户 decide;跑 → 攻击面清单 + GitHub 解决方案)
  ├─ 闸门 3  报告(reporter;未跑对抗 → 交叉降级为仅遗漏清单)── 用户验收
  └─ PRD 阶段(整合 create-prd,跳过重复研究,产出 PRD)
```

每道闸门都有一个明确的问题抛给用户,用户回答后才进下一道(可选对抗由用户 decide 是否跑)。**唯一原则:该问的必须问,不该等的绝不磨蹭。**

## Step 0: 预检(先跑通环境,再开始)

运行 `scripts/preflight.sh` 输出预检报告:

```bash
bash ~/.claude/skills/deep-analysis/scripts/preflight.sh
# ~ 展开失败(中文用户名坏字节)→ 用绝对路径
bash /c/Users/<用户名>/.claude/skills/deep-analysis/scripts/preflight.sh
```

预检检查(全部通过才继续,失败项按下表处置):

| 检查项 | 通过标志 | 失败处置 |
|---|---|---|
| GitHub 访问(内置工具) | preflight 脚本跑通 curl/gh 检查(curl 测 `api.github.com` / `gh --version`) | 都不可用 → 仅 WebSearch/WebFetch;匿名 curl 限 60 次/h,设 `GITHUB_TOKEN` 提到 5000 次/h |
| 内置工具 curl / gh CLI | `curl --version` / `gh --version` 可用 | curl 不可用 → 仅 WebFetch/WebSearch;gh 未装 → 用 curl 匿名 API |
| ⚠️ 网络通道(WebSearch/WebFetch/exa/tavily) | 编排 LLM 试 1 次 WebSearch(返回非空)+ WebFetch 抓 1 个 github 页面 + 查 `EXA_API_KEY`/`TAVILY_API_KEY` | ⚠️ 通道失效 → **强制禁用网页层**:researcher/simulator 一律走 GitHub 通道(`search_github` / `curl` / `gh`),不烧配额在空 WebSearch |
| reflexion 记忆 | `~/.claude/memory/reflexion/` 3 个 md 存在 | 首次使用,跳过该层(不阻塞) |
| git 仓库 | `.git` 存在 | 提示:PRD 阶段 run log 需 git,无 git 则跳过 run log |

**GitHub 代码接入(纯内置工具,零外部依赖,整个流程都要用,记牢)**:

不内置任何脚本,直接用编码工具(Claude Code / Codex / OpenCode)自带的内置工具。**curl 和 gh CLI 优先**,WebFetch / WebSearch 兜底:
  ```bash
  # 搜仓库(按 star 排序)
  curl -s "https://api.github.com/search/repositories?q=<查询>&sort=stars&per_page=10"
  gh search repos "<查询>" --sort stars --limit 10

  # 读文件(raw,无需 token 不限流,最优先)
  curl -s "https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>"

  # 列目录 / 读文件内容(API)
  curl -s "https://api.github.com/repos/<owner>/<repo>/contents/<path>"
  gh api "repos/<owner>/<repo>/contents/<path>"

  # 搜代码(API 需 GITHUB_TOKEN;gh 自动用已认证 token)
  curl -s -H "Authorization: Bearer $GITHUB_TOKEN" "https://api.github.com/search/code?q=<关键词>"
  gh search code "<关键词>"
  ```
  匿名 curl 限 60 次/h,设 `GITHUB_TOKEN` 提到 5000 次/h。`raw.githubusercontent.com` 读文件不受限流。可选增强:配 `github-code-rag` MCP 可加速「查已读代码」层并免限流,见项目 README「可选增强」。

**工具映射速查**(整个流程照此用):

| 动作 | 内置工具(默认) |
|---|---|
| 查已读代码历史 | 无本地索引 → 跳过该层,WebSearch 兜底(可选:配 github-code-rag MCP 才有 `search_code`/`search_history`) |
| 搜仓库 | `gh search repos` / `curl …/search/repositories` |
| 列目录 | `curl …/contents/<path>` / `gh api …/contents` |
| 读文件 | `curl raw.githubusercontent.com`(优先,不限流) |
| 搜代码 | `gh search code` / `curl …/search/code`(需 token) |
| 网页信息 | `WebSearch` / `WebFetch` |

不依赖任何 MCP,所有 GitHub 操作都走内置工具。

## 闸门 1: 需求理解

1. **澄清范围**(1-2 个最关键问题,不要一次问 5 个):平台(Web/小程序/App)?规模(日活/单量/并发)?已有代码还是全新?**明确不做哪些**(anti-goal,防需求蔓延)?
2. 生成 **phase0 JSON**(后续所有子代理的唯一输入):
   ```json
   {
     "requirement": "<需求原文>",
     "platform": "<平台>",
     "scale": "<规模/量级>",
     "tech_stack": "<已有栈或留空>",
     "existing_code": "<greenfield / 已有项目路径>",
     "anti_goal": "<明确不做哪些(范围边界,必填;说不清则留空并标注「待用户补充」)>",
     "experience_target": "<理想体验目标 0-10 星(可选,锦上添花)>",
     "scope_locked": true
   }
   ```
3. 展示给用户:**"范围锁定为:…。不做:…。对吗?"** 用户确认才进闸门 2。

**greenfield 判定**:无现有代码 → `existing_code: "greenfield"`。researcher 三层查询退化为「Reflexion + GitHub 同类项目 + WebSearch」,复用候选清单改为「可借鉴/可 fork 的项目」。有现有代码 → researcher 先读现有代码再调研。

## 闸门 2: 方向 + 模拟 + 可行性(researcher ⟂ simulator 并行)

基于 phase0 JSON,**并行 spawn 两个子代理**(用 prompt-file 方式,不依赖外部 agent 注册):

- **researcher** — 方向/调研。Spawn an Agent using the prompt from `agents/researcher.md`(相对本 skill 目录),把 phase0 JSON 作为传入需求。三层查询(Reflexion / GitHub 仓库搜索 / WebSearch)并发 + Sufficiency Gate + Claim 列表 + 复用候选清单。输出「Phase 1: 调研报告」markdown(不写文件)。
- **simulator** — 模拟+遗漏扫描(⭐核心创新)。Spawn an Agent using the prompt from `agents/simulator.md`(相对本 skill 目录),把 phase0 JSON 作为传入需求。基于真实 GitHub 代码灵活模拟实现过程 + 主动遗漏扫描 + 已知风险。1 条硬约束:每条声明必须引用 GitHub 代码(repo+file+line)或标注「LLM 推测」。输出「Phase 1.5: 模拟+遗漏扫描」markdown(不写文件)。

**两个代理并行跑,不串行等**(互不依赖,都只依赖 phase0)。

### ⭐ 可行性+风险小结(主 Agent 整合,闸门 2 收尾)

两者都返回后,主 Agent 直接整合一份「可行性+风险小结」(不再单独跑 pre-mortem 闸门):

1. **7 类死因轻量自检**(方法见 `methods/pre-mortem.md` 压缩版):市场 / 执行技术 / 人组织 / 时机 / 钱单位经济 / 采用 / 外部监管,逐类问一句"这个死因对本项目成立吗",挑出成立的 HIGH。
2. ⚠️ **每个 HIGH 风险/死因 → 查 GitHub 同类项目给应对方案**(用 `search_github` / `read_github_file`,看同类成熟开源项目怎么解决,把 GitHub 实证并入缓解列;查不到才允许推断)。这是"检查到风险时重新查 GitHub 给出完善方案"——不要拿着第一版方案直接下裁决。⚠️ **查询预算与 HIGH 数量挂钩**:整个整合环节 ≤ min(HIGH 数, 12) 次,每个 HIGH 最多 1 次;⚠️ **同类风险合并查询**:同一领域/很可能同一仓库的风险(如 websocket 路由 + 坐席分配可能指向同一客服项目)一次读文件查证多个;读文件遵守读取纪律(>300 行用 curl+sed 分段,整文件 read_github_file ≤2 个);⚠️ **预算耗尽出口**:预算用完后的剩余 HIGH 不再新查询,用已有证据/推断补应对方案,统一标「未查码=推测」,并在闸门 3 报告列为已知局限(不得装作已查证)。
3. **建议裁决**: proceed / 改(proceed-with-changes) / 转向(pivot) / kill。

展示给用户(一次合并展示,不额外加确认闸门):
- 调研摘要(三层命中数 / Sufficiency Gate 状态 / 复用候选前 3 个)
- ⭐ 遗漏清单(simulator 主动发现,重点)
- 已知风险(基于 GitHub 代码)
- Claim 列表前 5 条
- ✅ 可行性+风险小结(死因自检命中 + GitHub 实证应对方案 + 建议裁决)

⚠️ **深入选项(第一轮结果展示后主动问,不默认跳过)**:展示完上面 5 项后,问用户:**"要不要深入再看看?可以——(a) 指定方向/候选仓库深挖(如'把 XX 仓库的 XX 模块再看细'),(b) 补查某个遗漏点,(c) 不加,直接确认。"**
- 选「深入」→ 对应子代理**续跑第二轮(非重跑)**:主 Agent 把**第一轮产物 + 用户深入方向**作为附加上下文传入,禁止重复已查内容,只补指定缺口。⚠️ **第二轮预算减半**:researcher 追加 ≤8 次(读文件 ≤3,大文件仍 curl+sed),simulator 追加 ≤5 次(读码 ≤2);第二轮只出**增量**,不重写整份报告。补完 → **重做可行性小结整合**(随新产物更新死因自检与裁决),再展示一次,用户再确认。
- 选「不加」→ 直接确认当前可行性小结。

问用户(⚠️ **方向确认 + 对抗决策合并为一次询问,防止被打断/快进跳过**):**"调研方向和遗漏清单对吗?可行性小结和裁决 OK 吗?另外要不要跑对抗(red-team)?可以跳过。"**
- 用户确认 + 「跳过对抗」→ 直接进闸门 3。
- 用户确认 + 「对抗」→ 进下方「对抗 red-team」环节。
- ⚠️ 即使用户答「直接下一步」/「确认」,也必须**追问对抗决策**,答完才进闸门 3。

- 裁决 **kill** → 流程终止,主 Agent 写 reflexion 记忆(见「记忆」节)。
- 裁决 **改/转向** → 把裁决和改动记录进 phase0 JSON 的 `decisions` 字段。

### ⚠️ 闸门 2.5: 对抗决策(合并进闸门 2 收尾确认,不单独设闸门)

> **上次运行暴露的问题**:对抗闸门被跳过,用户没有机会 decide 是否跑 red-team。修复:对抗决策**合并进闸门 2 收尾的确认询问**(见上),与方向确认一次问完,杜绝被「直接下一步」快进跳过。

用户回答「跳过」→ 直接进闸门 3;回答「对抗」→ 进下方「对抗 red-team」环节。

## 对抗 red-team(可选环节,非闸门)

可行性判断已并入闸门 2 的「可行性+风险小结」,不再单独跑 pre-mortem 闸门。对抗是**可选环节**,用户在闸门 2 确认后 decide 是否跑:

**跑(用户选「对抗」)** — 主 Agent 直接执行:
1. **red-team** — 用 `methods/red-team-the-plan.md` 的方法论,扮演 6 个对手攻击方案:聪明对手 / 愤怒的流失客户 / 怀疑的 CFO / 超负荷工程师 / 监管者 / 投资人。每个角色 3-6 条具体攻击(要具体到数字和机制,不要"成本可能偏高")。对每条攻击给裁决:✅ 有答案 / 🟨 弱答案 / 🔴 无答案。
2. ⚠️ **每条 🔴/🟨 攻击 → 查 GitHub 同类项目给解决方案**(用 `search_github` / `read_github_file`,看同类成熟开源项目怎么应对,把 GitHub 实证并入「响应」列);查不到才允许推断。
3. 输出「未答复攻击清单」按 可能被真正观众提出 × 杀伤力 排序,每条给响应(fix / pre-empt / rebut / accept)。
4. 把裁决和改动记录进 phase0 JSON 的 `decisions` 字段。
5. ⚠️ **工具上限**:整个对抗环节 GitHub 查询 ≤ min(🔴/🟨 数, 15) 次,每条 🔴/🟨 攻击最多 1 次;⚠️ **同类攻击合并查询**:多条攻击指向同一仓库/同一问题时一次读文件查证多个;⚠️ **预算耗尽出口**:超上限 → 剩余攻击用已有证据/推断补响应并统一标「未查码=推测」(不得装作已查证),并在闸门 3 报告列为已知局限。防止对抗环节 token 膨胀。

**不跑(用户选「跳过」)** — 直接进闸门 3;reporter 交叉环节自动降级为仅遗漏清单(不编造攻击面)。

## 闸门 3: 报告(reporter 汇总)

用户决定对抗后,spawn reporter 汇总(若选了「对抗」,主 Agent 先跑对抗产出攻击面清单,再 spawn reporter;若「跳过」,直接 spawn):

1. **reporter(spawn)** — Spawn an Agent using the prompt from `agents/reporter.md`(相对本 skill 目录),把闸门 1-3 全部产物(含 **可行性+风险小结** + **simulator 遗漏清单** + **可选的红队攻击面清单**)作为输入传入。产出 6 部分完整报告(模板见 reporter.md,含可行性结论 + 红队攻击面清单)。**reporter 必须做遗漏×攻击面交叉:同一问题被 simulator 预见且被 red-team 攻击 → 标 HIGH 提到最前**(这是编排层唯一的产物缝合逻辑,缺了遗漏清单和攻击面就是两条平行线)。
2. ⚠️ **验证 reflexion 写入** — reporter 汇报"已写 reflexion"不算数,主 Agent 必须抽查 3 个文件(Read `~/.claude/memory/reflexion/{pitfalls_patterns,tech_decisions_lessons,project_archetypes}.md` 末尾,确认有本次 `<YYYY-MM-DD> <项目>` 条目)。reporter 偷懒/失败未写 → **主 Agent 补写**,记忆不静默丢失。

⚠️ **交叉降级**:用户跳过对抗 → reporter 无攻击面输入,**第 5 节交叉环节自动降级为仅输出遗漏清单**(不做交叉、不编造攻击面)。

reporter 写最终报告,展示给用户验收。

问用户:**"报告完整吗?有要调整的吗?确认后进入 PRD 阶段。"**

## PRD 阶段(整合 create-prd,跳过重复研究)

调用 `prd/PIPELINE.md` 的完整 PRD 流水线(研究→起草→审查→资深PM判断→多轮修订),但**跳过已经做完的部分**:

| create-prd 阶段 | 本技能处理 |
|---|---|
| Phase 0 范围澄清 | **跳过** — 闸门 1 已锁定范围,直接传 phase0 JSON |
| Phase 1 研究 | **跳过** — 闸门 2 的 researcher 已产出调研,传给 prd-researcher 复用 |
| Gate 1 研究审查 | **跳过** — 闸门 2 已确认方向 |
| Phase 2 PRD 起草 | 执行 — spawn `prd/agents/prd-writer.md`,传入:phase0 JSON + 调研结果 + 可行性小结裁决 + 复用候选清单 |
| Gate 2 草稿审查 | 执行 — prd-lint.py + 用户确认 |
| Phase 3 PRD 审查 | 执行 — spawn `prd/agents/prd-reviewer.md` |
| Phase 3.5 资深PM | 执行 — spawn `prd/agents/prd-senior-pm.md` |
| Gate 3 决策+教训 | 执行 — 展示决策表+教训+词表,用户批复 |
| 修订循环 | 执行 — 最多 3 轮 |

前置条件(缺失则按 PIPELINE.md 原规则处理):
- `.claude/project-context.md` 必须存在 — 不存在时让用户从 `project-context.template.md`(本 skill 目录内)复制填写(或从闸门 1-3 的产物直接生成一份)。
- run log 需要 git — 无 git 仓库则跳过 run log,其余照常。

**PRD 阶段的隐藏接缝**:闸门 1-3 的产物(phase0 JSON / 调研 / 可行性小结 / 复用候选 / 可选的红队攻击面)要作为附加上下文传给 prd-writer 和 prd-senior-pm,避免它重走研究。由主 Agent 在 spawn prd-writer / prd-senior-pm 时把 `contextHandoff`(含 `phase0Json` / `research` / `feasibilityVerdict` / `reuseCandidates` / `redTeamAttacks`(可选,跳过对抗则无))作为 **prompt 附加上下文直接传入**——researcher/simulator 产物只在对话里不落盘,不依赖 state 文件。

⚠️ **集成模式防重复研究**:spawn prd-writer 时**必须显式告知**"research 内容已在附加上下文中,跳过 prd-writer Step 2 的 `{initiative}-research.md` 文件检查与代码调研"——否则 prd-writer 在 `_artifacts/` 找不到 research 文件会判定 standalone 而**自己重新调研代码库**,正好造成 PRD 阶段要跳过的重复研究。prd-writer 的 Step 2 已加集成模式识别,但编排层这句话仍是兜底保险。

⚠️ **复用必写清楚**:PRD 每个模块必须标 **复用 / 改造 / 自研 三选一**,复用候选清单映射到具体 PRD 章节,禁止"尽量复用"这种模糊话(详见 prd-writer 的 Reuse Annotation 规则)。

## 硬规则(3+N)

**3 条总硬规则**(任何情况都不得违反):

1. **复杂需求才触发** — 简单需求直接忽略,不为小需求跑完整流程。
2. **复用优先** — researcher/simulator 必须先搜 GitHub 代码和 reflexion 记忆,有现成的就直接引用;禁止从零想方案。每条声明必须引用 GitHub 代码或标注「LLM 推测」。
3. **单命令完整流程** — 一条 `/deep-analysis <需求>` 走完全流程,不要求用户分步调用子技能,不中途抛给别的 skill。

**N 条阶段硬规则**(各阶段内强制执行):

| 阶段 | 硬规则 |
|---|---|
| 闸门 1 | 一次只问 1-2 个最关键问题;scope 必须用户确认才锁 |
| 闸门 2 | researcher ≤15 次工具调用(⚠️ 读文件前先探测大小,>300 行禁用 read_github_file 整读、改用 curl+sed 分段,整文件读 ≤3 次,每仓库 ≤3 文件,报告 800-1200 字),simulator ≤10 次(读码 ≤4 次含 curl+sed,输出 500-800 字),超上限强制推进;不写文件,markdown 直接返回;⚠️ 每个 HIGH 风险必须查 GitHub 给应对方案(编排层整合 ≤ min(HIGH 数,12) 次,同类风险合并查询,预算耗尽标「未查码=推测」并列为报告局限);必须显式裁决;⚠️ **深入续跑第二轮预算减半**(researcher ≤8 / simulator ≤5,只出增量) |
| 闸门 2.5 | ⚠️ 对抗决策**合并进闸门 2 收尾确认**(与方向确认一次问完);即使用户说「直接下一步」/「确认」也必须追问对抗问题,答完才进闸门 3,不得省略 |
| 对抗(可选) | 红队攻击必须具体到数字/机制,不得泛泛;每条攻击必须有响应,且 🔴/🟨 必须查 GitHub 给方案(整个对抗 GitHub 查询 ≤ min(🔴/🟨 数,15) 次,同类攻击合并查询,预算耗尽标「未查码=推测」并列为报告局限,同样遵守读取纪律);跳过则无攻击面 |
| 闸门 3 | 报告含可行性结论;跳过对抗 → 交叉降级为仅遗漏清单 |
| PRD | 最多 3 轮修订;run log 需 git,无则跳过 |

## 记忆(Reflexion,跨会话积累)

⚠️ **路径说明**:reflexion 写 `~/.claude/memory/reflexion/`(本技能专属的跨会话记忆,researcher 第 1 层会读它做复用),与 Claude Code 的 auto memory(`~/.claude/projects/<项目>/memory/`)是**两套独立目录,互不干扰**。

流程关键节点写 reflexion 记忆,供下次复用。**分工唯一化,避免重复写**:

- 正常流程:reporter 在闸门 3 汇总时**统一 append 全部 3 个** reflexion 文件(pitfalls_patterns / tech_decisions_lessons / project_archetypes,见 reporter.md),主 Agent 不重复写。
- ⚠️ 正常流程 reporter 写完后,**主 Agent 必须验证写入成功**(闸门 3 第 2 步),reporter 未写则主 Agent 补写,记忆不静默丢失。
- 闸门 2 的可行性小结判定 **kill** 时:流程终止、reporter 不会跑 → 由**主 Agent** append `~/.claude/memory/reflexion/pitfalls_patterns.md`(这个需求为什么不该做)。

## 目录结构

```
~/.claude/skills/deep-analysis/
├── SKILL.md                 # 本文件:编排 + 3 闸门 + 可选对抗 + PRD 阶段
├── agents/                  # 3 子代理(prompt-file,不依赖全局注册)
│   ├── researcher.md        # 深度调研:三层查询 + Sufficiency Gate
│   ├── simulator.md         # ⭐ 模拟 + 遗漏扫描 + GitHub 锚定
│   └── reporter.md          # 6 部分报告:含可行性结论 + 红队攻击面清单
├── methods/                 # 方法论
│   ├── pre-mortem.md        # 轻量自检(7 类死因) → 可行性小结
│   └── red-team-the-plan.md # 6 对手红队
├── prd/                     # create-prd 全套(吸收)
│   ├── PIPELINE.md          # PRD 流水线(集成模式:跳过 Phase0/1/Gate1)
│   ├── agents/              # prd-writer / prd-reviewer / prd-senior-pm / …
│   ├── rules/               # 写作规则 6 条
│   ├── scripts/             # prd-lint / validate-handoff / run-log / check-docs
│   └── docs/                # PRD 模板 + 18 个分节
├── scripts/
│   └── preflight.sh         # Step 0 环境预检(检查 MCP + curl/gh 可用性)
└── project-context.template.md
```

## 常用 prompt 模板

- spawn 子代理固定句式:
  > Spawn an Agent using the prompt from `agents/<name>.md`(相对本 skill 目录,装到哪都能用)
- 传参:
  > 传入需求:phase0 JSON。附加上下文:闸门 1-3 产物摘要。
- GitHub 代码接入(纯内置工具):
  > 用 `curl raw.githubusercontent.com` 读文件 / `gh search repos` 搜仓库 / `WebSearch` 兜底(详见 Step 0 工具映射速查)。零外部依赖。
