#!/usr/bin/env bash
# deep-analysis Step 0 环境预检
# 输出预检报告,逐项显示 PASS/FAIL。FAIL 项给出处置建议,不阻塞(流程可降级继续)。
# 用法: bash ~/.claude/skills/deep-analysis/scripts/preflight.sh
#       ~ 展开失败(中文用户名坏字节)时改用绝对路径:
#       bash /c/Users/<用户名>/.claude/skills/deep-analysis/scripts/preflight.sh

# 技能根目录从脚本自身位置推导,不依赖 $HOME(中文用户名在部分 shell 下展开为坏字节)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# 主目录定位:优先 $HOME;坏字节/为空时从 Windows USERPROFILE 推导(经 cygpath 转 MSYS 路径)
if [ -n "$HOME" ] && [ -d "$HOME" ] && [ -r "$HOME" ]; then
  USER_HOME="$HOME"
elif command -v cygpath >/dev/null 2>&1 && [ -n "$USERPROFILE" ]; then
  USER_HOME="$(cygpath -u "$USERPROFILE" 2>/dev/null || printf '%s' "$USERPROFILE")"
else
  USER_HOME="${HOME:-}"
fi
REFLEXION_DIR="$USER_HOME/.claude/memory/reflexion"

PASS=0
FAIL=0
WARN=0

report() { # $1=status  $2=label  $3=message
  case "$1" in
    PASS) PASS=$((PASS+1)) ;;
    FAIL) FAIL=$((FAIL+1)) ;;
    WARN) WARN=$((WARN+1)) ;;
  esac
  printf '%-4s %-28s %s\n' "$1" "$2" "$3"
}

echo "=== deep-analysis 预检 ==="
echo "技能目录: $SKILL_DIR"
echo ""

# 1. 技能目录结构
[ -f "$SKILL_DIR/SKILL.md" ] && report PASS "SKILL.md" "存在" || report FAIL "SKILL.md" "缺失!"
[ -d "$SKILL_DIR/agents" ] && [ -d "$SKILL_DIR/methods" ] && [ -d "$SKILL_DIR/prd" ] \
  && report PASS "目录 agents/methods/prd" "齐全" \
  || report FAIL "目录 agents/methods/prd" "缺失,检查全家桶搬运是否完整"

# 2. 内置工具 curl(MCP 离线时的首选,读 raw 文件不限流)
if command -v curl >/dev/null 2>&1; then
  report PASS "curl" "可用 → raw.githubusercontent.com 读文件 / GitHub REST API"
else
  report WARN "curl" "不可用 → 仅能 WebFetch/WebSearch 兜底"
fi

# 3. 内置工具 gh CLI(MCP 离线时搜仓库/搜代码)
if command -v gh >/dev/null 2>&1; then
  AUTH=$(gh auth status >/dev/null 2>&1 && echo "已认证" || echo "未认证")
  report PASS "gh CLI" "$AUTH"
else
  report WARN "gh CLI" "未安装 → 用 curl 匿名 API(限 60 次/h,设 GITHUB_TOKEN 提到 5000)"
fi

# 4. GITHUB_TOKEN(提升 API 配额,可选)
if [ -n "$GITHUB_TOKEN" ]; then
  report PASS "GITHUB_TOKEN" "已设置 → 配额 5000 次/h"
else
  report WARN "GITHUB_TOKEN" "未设置 → 匿名 curl 限 60 次/h"
fi

# 5. reflexion 记忆
if [ -d "$REFLEXION_DIR" ]; then
  N=$(ls "$REFLEXION_DIR"/*.md 2>/dev/null | wc -l)
  report PASS "reflexion 记忆" "$N 个 md 文件"
  for f in pitfalls_patterns tech_decisions_lessons project_archetypes; do
    [ -f "$REFLEXION_DIR/$f.md" ] || echo "       提示: 缺 $f.md(首次使用会缺失,不阻塞)"
  done
else
  report WARN "reflexion 记忆" "目录不存在 → 首次使用,researcher 跳过该层"
fi

# 6. git 仓库(PRD 阶段 run log 需要)
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  report PASS "git 仓库" "是 → PRD run log 可用"
else
  report WARN "git 仓库" "否 → PRD 阶段跳过 run log,其余照常"
fi

# 7. 当前工作目录
echo ""
echo "当前工作目录: $(pwd)"
if [ -d ".claude" ]; then
  [ -f ".claude/project-context.md" ] \
    && report PASS "project-context.md" "存在" \
    || report WARN "project-context.md" "缺失 → PRD 阶段需生成或复制模板"
else
  report WARN ".claude/" "不存在 → PRD 阶段需初始化 project-context"
fi

# 8. GitHub 访问检查(内置工具,零外部依赖)
echo ""
echo "=== GitHub 访问检查 ==="
if command -v curl >/dev/null 2>&1 && curl -s -o /dev/null -w "%{http_code}" "https://api.github.com" 2>/dev/null | grep -q "200"; then
  report PASS "GitHub API (匿名 curl)" "可达 api.github.com"
else
  report WARN "GitHub API" "curl 不可达 → 仅 WebSearch/WebFetch"
fi
if command -v gh >/dev/null 2>&1; then
  report PASS "gh CLI" "已安装"
else
  report WARN "gh CLI" "未安装 → 用 curl 匿名 API(限 60 次/h,设 GITHUB_TOKEN 提到 5000 次/h)"
fi
echo ""

echo "=== 汇总: PASS=$PASS  FAIL=$FAIL  WARN=$WARN ==="
[ "$FAIL" -gt 0 ] && echo "FAIL 项必须先处置才能开始;WARN 项可降级继续。"
exit $FAIL
