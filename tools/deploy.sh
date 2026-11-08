#!/usr/bin/env bash
# 一键部署三个 Actor 到 Apify。
#
# 用法：
#   export APIFY_TOKEN=apify_api_xxx
#   ./tools/deploy.sh              # 全部
#   ./tools/deploy.sh funding-arb  # 单个
#
# 说明：
#   * APIFY_TOKEN 必须是有「创建/修改 Actor」权限的 token（未限定权限的 personal token）。
#     Apify 的 scoped token 不允许创建/修改 Actor，这是平台限制。
#   * token 只通过环境变量传入，不落盘、不进 shell history（建议用 read -s 输入）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACTORS_DIR="$ROOT/apify-actors"
TARGET="${1:-}"

if [[ -z "${APIFY_TOKEN:-}" ]]; then
  echo "缺少 APIFY_TOKEN。先执行：" >&2
  echo "  read -rs APIFY_TOKEN && export APIFY_TOKEN" >&2
  exit 1
fi

if ! command -v apify >/dev/null 2>&1; then
  echo "→ 安装 apify-cli ..."
  npm install -g apify-cli >/dev/null 2>&1 || {
    echo "安装失败，请手动执行 npm i -g apify-cli" >&2; exit 1; }
fi

if [[ -n "$TARGET" ]]; then
  DIRS=("$ACTORS_DIR/$TARGET")
else
  DIRS=()
  while IFS= read -r d; do DIRS+=("$d"); done < <(find "$ACTORS_DIR" -maxdepth 1 -mindepth 1 -type d ! -name '.*' | sort)
fi

echo "→ 待部署: ${#DIRS[@]} 个"
FAILED=0
for dir in "${DIRS[@]}"; do
  name="$(basename "$dir")"
  if [[ ! -f "$dir/.actor/actor.json" ]]; then
    echo "  ⚠ $name: 缺 .actor/actor.json，跳过"; FAILED=$((FAILED+1)); continue
  fi
  echo "→ [$name] 推送 ..."
  if ( cd "$dir" && APIFY_TOKEN="$APIFY_TOKEN" apify push --yes --quiet ); then
    echo "  ✓ $name 推送成功"
    ( cd "$dir" && APIFY_TOKEN="$APIFY_TOKEN" apify actors info "$(python3 -c "import json;print(json.load(open('.actor/actor.json'))['name'])")" 2>/dev/null | head -12 || true )
  else
    echo "  ❌ $name 推送失败（看上面的日志）"; FAILED=$((FAILED+1))
  fi
done

echo
if [[ "$FAILED" -gt 0 ]]; then
  echo "完成，但有 $FAILED 个失败。"; exit 1
fi
echo "全部完成。下一步在 Console 里为每个 Actor 设置 Store 信息与定价（见各 README 的 How much does it cost 段）。"
