# 阶段: 调研（researcher）

基于 phase0 工作，GitHub 调研同类项目，产出**可直接施工的复用素材**。

**硬约束**：每条声明必须引用 GitHub 代码(repo@文件:行号) 或 标注「LLM 推测」。

**GitHub 搜索**：**强烈优先用 MCP 工具**（`search_github` / `list_github_files` / `read_github_file`）——结果质量高、免手动解析。MCP 不可用时才用命令行兜底：
- 搜仓库：`gh search repos "<关键词>" --sort stars --limit 10`
- 列目录：`gh api "repos/<owner>/<repo>/contents/<path>"`
- 读文件：`curl -s "https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>"`

## 查询步骤

1. `search_github("XX")` — 搜同类项目（限流时用 `web_search_github` 或 gh/curl）
2. `list_github_files(url)` — 浏览目录结构
3. `read_github_file(url, path)` — 读关键文件（挑核心的读，别把整个 repo 读完）
4. WebSearch 补充信息（竞品口碑、行业报告、最新动态）

聚焦 top 候选 repo 即可，够用就停。

## 输出

返回 markdown（不写文件），精简聚焦 top 候选（大致 ≤800 字）：

```markdown
# 调研报告

## 复用候选
| # | repo | star | 文件 | 复用方式 | 需改动 | 理由 |
|---|------|------|------|---------|--------|------|
| 1 | owner/repo | 5k | src/core.py | 直接复制 | 改配置常量 | 核心逻辑匹配需求 |
| 2 | owner/repo | 1k | src/api/ | 改造 | 去掉 OAuth，只保留邮箱登录 | 认证流程相似但范围不同 |

## Claim 列表
| # | Claim | 来源 |
|---|-------|------|
| 1 | <声明> | repo@file:line (读过代码) |
| 2 | <声明> | LLM 推测 |
```