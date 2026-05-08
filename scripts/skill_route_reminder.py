"""UserPromptSubmit hook — inject a system-reminder when the user message
matches a skill trigger phrase, nudging Claude to invoke the skill via the
`Skill` tool instead of inline-reimplementing.

Why: Claude has a known failure mode of bypassing skills and writing inline
`python -c "..."` even when the user message literally matches a skill's
trigger phrase. CLAUDE.md text guidance alone hasn't been enough to break
the inline-tool inertia. This hook injects a high-salience, message-specific
warning at the moment the user submits — read BEFORE Claude reads the
message itself.

Design:
  - Advisory only (additionalContext) — never blocks.
  - Conservative regex: literal high-confidence phrases only.
    Date inserts (e.g. "生成5/10入院序列") allowed via `.{0,N}` slack.
  - Single-word generic terms (抽籤, 改期, 摘要 …) are NOT triggers —
    they appear too often in casual reference and would over-fire.
  - Source-of-truth: CLAUDE.md «Step → Skill mapping» table. Keep this
    list in sync when skills are added / renamed / triggers change.
  - Multiple matches are listed; Claude decides workflow order.

Output schema (PostToolUse-style):
  {"hookSpecificOutput": {
     "hookEventName": "UserPromptSubmit",
     "additionalContext": "<reminder text>"}}
Silent (exit 0, empty stdout) when no trigger matches.
"""
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Each skill → list of regex patterns. Patterns are OR'd within a skill.
# Use `.{0,N}` slack to tolerate date inserts ("5/10", "本週", etc).
TRIGGERS = {
    'admission-image-to-excel': [
        r'匯入入院名單',
        r'讀取圖片.{0,4}匯入',
        r'讀取圖片匯入Excel',
    ],
    'admission-lottery': [
        r'抽住院籤',
        r'排入院順序',
    ],
    'admission-emr-extraction': [
        r'提取.{0,5}EMR',
        r'EMR\s*extraction',
        r'做.{0,5}EMR.{0,5}摘要',
    ],
    'admission-emr-refresh': [
        r'重抓.{0,15}EMR',
        r'refresh\s*EMR',
        r'重跑.{0,15}EMR',
        r'更新.{0,15}EMR',
    ],
    'admission-ordering': [
        r'排.{0,15}住院序',
        r'排.{0,15}入院序(?!列)',
        r'設定.{0,15}入院順序',
        r'生成.{0,15}入院序列',
    ],
    'admission-cathlab-keyin': [
        r'排.{0,8}導管(?!床)',
        r'key[ \-]?in.{0,3}導管',
        r'導管排程',
        r'key.{0,3}導管',
    ],
    'admission-reschedule': [
        r'重啟改期功能',
        r'改.{0,5}\d+/\d+.{0,5}住院',
    ],
    'admission-sheet-rebuild': [
        r'重建.{0,5}sheet',
        r'重新建立.{0,5}\d{8}',
        r'從頭建.{0,5}sheet',
        r'sheet.{0,3}壞了',
    ],
    'admission-line-push': [
        r'推播.{0,5}入院名單',
        r'推.{0,5}入院序',
        r'測試推播',
        r'LINE.{0,5}推播',
    ],
    'reminder-management': [
        r'新增提醒',
        r'修改提醒',
        r'移除提醒',
        r'加一個提醒',
        r'改提醒內容',
    ],
    'workflow-docs': [
        r'/workflow-docs?',
        r'更新工作流程',
        r'同步說明文件',
        r'產生操作說明',
        r'交班',
    ],
    'check-previous-progress': [
        r'/check-previous-progress',
        r'/check[ \-]previous',
    ],
    'euroscore-workflow': [
        r'跑.{0,3}Euroscore',
        r'算.{0,3}Euroscore',
        r'Euroscore.{0,3}評估',
        r'新一批.{0,3}Euroscore',
    ],
    'pci-cert-cheatsheet': [
        r'PCI.{0,3}認證(?!.{0,3}第二)',
        r'PCI.{0,3}病歷小抄',
        r'認證.{0,3}病歷',
        r'認證.{0,3}小抄',
        r'PCI\s*cert(?!.{0,3}comp)',
    ],
    'pci-cert-cheatsheet-complication': [
        r'PCI.{0,3}認證.{0,5}第二組',
        r'complication.{0,3}認證',
        r'cover.{0,3}stent.{0,3}認證',
        r'併發症.{0,3}認證.{0,3}小抄',
    ],
    'journal-presentation': [
        r'journal\s*club',
        r'JC\s*報告',
    ],
    'cv-scheduler': [
        r'排班\s*\d{4}',
        r'值班\s*生成',
    ],
}


def find_matches(msg: str) -> list[tuple[str, str]]:
    out = []
    for skill, patterns in TRIGGERS.items():
        for p in patterns:
            if re.search(p, msg, re.IGNORECASE):
                out.append((skill, p))
                break  # one match per skill is enough
    return out


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    # Various harness implementations use different keys.
    msg = (
        payload.get('prompt')
        or payload.get('user_message')
        or payload.get('message')
        or (payload.get('tool_input') or {}).get('prompt')
        or ''
    )
    if not isinstance(msg, str) or not msg.strip():
        sys.exit(0)

    matches = find_matches(msg)
    if not matches:
        sys.exit(0)

    bullets = '\n'.join(
        f'  - `{skill}` (matched pattern `{p}`)' for skill, p in matches
    )
    reminder = (
        '⚠ Skill trigger phrase detected in user message.\n'
        f'Matched skills:\n{bullets}\n\n'
        'Per CLAUDE.md «Step → Skill mapping» (HARD RULE): '
        'invoke the matched skill via the `Skill` tool as your FIRST action — '
        'do NOT inline-reimplement (bypassing skill reproduces bugs the skill '
        'already solved, e.g. weighted lottery, sub-table H→R mapping, '
        'format gaps). If multiple skills match, run them in workflow order. '
        'See `memory/feedback_skill_trigger_match_must_invoke.md`.'
    )

    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'UserPromptSubmit',
            'additionalContext': reminder,
        }
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
