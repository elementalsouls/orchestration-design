#!/usr/bin/env bash
# Package the skill and install it for this machine.
#   ./build.sh          package + install
#   ./build.sh --pack   package only
set -euo pipefail

cd "$(dirname "$0")"

SRC="skill/orchestration-design"
OUT="orchestration-design.skill"
DEST="$HOME/.claude/skills/orchestration-design"

# macOS litters these; they must never reach the bundle
find "$SRC" -name '.DS_Store' -delete

# zip from inside skill/ so archive paths start at orchestration-design/
rm -f "$OUT"
(cd skill && zip -rq "../$OUT" orchestration-design -x '*.DS_Store')

echo "packed $OUT"

# zip -r already recurses into modules/, so this is a guard, not a fix. The bundle
# is what ships: a module missing from it would leave the skill telling a reader to
# open a file that is not there.
for m in "$SRC"/modules/*/SKILL.md; do
  [ -e "$m" ] || continue                    # no modules yet — nothing to assert
  rel="${m#skill/}"
  if ! unzip -Z1 "$OUT" | grep -qxF "$rel"; then
    echo "  BUNDLE ERROR: $rel is on disk but missing from $OUT" >&2
    exit 1
  fi
done

unzip -Z1 "$OUT" | sed 's/^/  /'

if [[ "${1:-}" == "--pack" ]]; then
  exit 0
fi

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -R "$SRC" "$DEST"
echo "installed to $DEST"
