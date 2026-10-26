#!/usr/bin/env bash
# 阻塞等待 Reviewer 的验收报告出现。Coder 在提审后调用。
#
# 用法：scripts/wait-for-verdict.sh <验收报告路径> [最长等待秒数，默认 540]
# 退出码：0 = 报告已出现；2 = 超时，报告尚未出现（再调用一次继续等）；64 = 用法错误
#
# 为什么需要它：/goal 在每轮结束后检查目标是否达成，未达成就让 agent 继续。
# 如果 Coder 用"结束回合"来等待，会被立即叫醒、反复空转。在一次工具调用内阻塞，
# 等待就不会触发续跑。
#
# Reviewer 先写 <报告>.tmp 再 mv 成正式文件名，所以文件一出现就是完整的。
# 默认 540 秒，留在 Claude Code Bash 工具 600 秒的上限之内；
# 调用时请把命令超时设为 600 秒。若运行环境的命令超时更短，传入更小的秒数。

set -eu

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  echo "用法: $0 <验收报告路径> [最长等待秒数]" >&2
  exit 64
fi

report="$1"
limit="${2:-540}"
interval=15
waited=0

case "$limit" in
  ''|*[!0-9]*) echo "最长等待秒数必须是非负整数: $limit" >&2; exit 64 ;;
esac

while [ ! -s "$report" ]; do
  if [ "$waited" -ge "$limit" ]; then
    echo "TIMEOUT: 等待 ${waited}s 后 $report 仍未出现。再次调用本脚本继续等待。"
    exit 2
  fi
  sleep "$interval"
  waited=$((waited + interval))
done

echo "VERDICT_READY: $report"
grep -m1 -E '\*\*裁决\*\*' "$report" || true
