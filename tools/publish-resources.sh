#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
for arg in "$@"; do
	case "$arg" in
		--dry-run) DRY_RUN=1 ;;
		*) echo "Unknown args: $arg" >&2; exit 2 ;;
	esac
done

cd "$(dirname "$0")/.."

DIRS=
for game in maimai chunithm; do
	for type in covers plates avatars; do
		[ -d "data/$game/$type" ] || continue
		DIRS="$DIRS $game/$type"
	done
done
[ -n "$DIRS" ] || { echo "Resources not found" >&2; exit 1; }

REPO=xszqxszq/KarenBot-Resources
TAG=rhythm-game-assets-$(date +%Y%m%d)
STAGE=$(mktemp -d)
if [ "$DRY_RUN" -eq 0 ]; then
	trap 'rm -rf "$STAGE"' EXIT
fi

(cd data && zip -0 -q -r "$STAGE/$TAG.zip" $DIRS -x '*_s.jpg' -x '*.DS_Store' -x '__MACOSX/*')

echo "Packed:"
packed=0
for dir in $DIRS; do
	count=$(find "data/$dir" -type f -not -name '*_s.jpg' -not -name '.DS_Store' | wc -l | tr -d ' ')
	bytes=$(find "data/$dir" -type f -not -name '*_s.jpg' -not -name '.DS_Store' -print0 | xargs -0 wc -c | awk 'END{print $1+0}')
	packed=$((packed + bytes))
	printf '  %-18s %5s files  %6.1f MB\n' "$dir" "$count" "$(echo "$bytes" | awk '{print $1/1048576}')"
done
printf '  %-18s %5s          %6.1f MB\n' "Total" "" "$(echo "$packed" | awk '{print $1/1048576}')"

zip_size=$(wc -c < "$STAGE/$TAG.zip" | tr -d ' ')
if [ "$zip_size" -lt "$packed" ]; then
	echo "Error: archive smaller than packed data" >&2
	exit 1
fi
ls -lh "$STAGE/$TAG.zip"

if [ "$DRY_RUN" -eq 1 ]; then
	rm -rf "$STAGE"
	exit 0
fi

if ! gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
	gh release create "$TAG" --repo "$REPO" --title "$TAG" --notes-file /dev/null
fi
gh release upload "$TAG" --repo "$REPO" --clobber "$STAGE/$TAG.zip"
