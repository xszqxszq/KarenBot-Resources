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

(cd data && zip -0 -q -r "$STAGE/$TAG.zip" $DIRS -x '*_s.jpg')

if [ "$DRY_RUN" -eq 1 ]; then
	ls -lh "$STAGE"
	echo "dry-run: Saved at $STAGE"
	exit 0
fi

if ! gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
	gh release create "$TAG" --repo "$REPO" --title "$TAG" --notes-file /dev/null
fi
gh release upload "$TAG" --repo "$REPO" --clobber "$STAGE/$TAG.zip"
