#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
#
# Check that the committed tree can be released as <version>. It builds; it never tags,
# pushes or publishes (those need Bob's go-ahead, docs/releasing.md).
#
#   tools/release-check.sh 0.1.0
#   tools/release-check.sh --allow-any-branch 0.1.0   # rehearsal: skips the "on main" check
#
# Checks, in order, stopping at the first failure:
#   1. the working tree is clean and HEAD is on main (the branch check is the only thing
#      --allow-any-branch skips), and the tag vX.Y.Z does not exist yet;
#   2. ./test.sh passes;
#   3. glra_midi/__init__.py says __version__ = "X.Y.Z" and CHANGELOG.md has a
#      "## [X.Y.Z] - YYYY-MM-DD" section;
#   4. `python -m build` makes a wheel and an sdist from `git archive HEAD` in a temp venv
#      (so it builds what is committed, not stray files);
#   5. both files contain LICENSE and THIRD_PARTY_NOTICES.md, and the wheel the package data
#      (default profile, layout, QML);
#   6. a fresh venv installs the wheel and `glra-midi --version` prints "glra-midi X.Y.Z".
#
# The wheel and sdist end up in dist/ (git-ignored) for the GitHub release.
# Needs network (pip fetches `build` and the dependencies). PYTHON picks the interpreter
# for the temp venvs (default: this repo's .venv/bin/python, Python 3.13 or later).

set -eu

allow_any_branch=0
if [ "${1:-}" = "--allow-any-branch" ]; then
    allow_any_branch=1
    shift
fi
if [ $# -ne 1 ]; then
    echo "usage: tools/release-check.sh [--allow-any-branch] <version>" >&2
    exit 2
fi
version=$1
case $version in
    [0-9]*.[0-9]*.[0-9]*) ;;
    *) echo "release-check: '$version' is not X.Y.Z" >&2; exit 2 ;;
esac
if ! printf '%s\n' "$version" | grep -Eq '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'; then
    echo "release-check: '$version' is not a plain SemVer X.Y.Z" >&2
    exit 2
fi

cd "$(dirname "$0")/.."
root=$(pwd)
PYTHON=${PYTHON:-$root/.venv/bin/python}

step() { printf '\n== %s\n' "$*"; }
fail() { printf 'release-check FAILED: %s\n' "$*" >&2; exit 1; }

step "1. clean tree on main, tag free"
[ -z "$(git status --porcelain)" ] || fail "working tree is not clean (git status)"
branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$allow_any_branch" -eq 1 ]; then
    echo "REHEARSAL: on '$branch', not checking for main (a real release runs without the flag)"
elif [ "$branch" != "main" ]; then
    fail "on '$branch', not main"
fi
if git rev-parse -q --verify "refs/tags/v$version" >/dev/null; then
    fail "tag v$version already exists"
fi

step "2. ./test.sh"
./test.sh > /dev/null 2>&1 || { ./test.sh 2>&1 | tail -30; fail "./test.sh failed"; }
echo "tests pass"

step "3. version and changelog"
declared=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' glra_midi/__init__.py)
[ "$declared" = "$version" ] || fail "glra_midi/__init__.py has '$declared', expected '$version'"
grep -Eq "^## \[$version\] - [0-9]{4}-[0-9]{2}-[0-9]{2}\$" CHANGELOG.md \
    || fail "CHANGELOG.md has no '## [$version] - YYYY-MM-DD' section"
echo "version $version, changelog section found"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

step "4. build wheel and sdist from HEAD"
mkdir "$tmp/src"
git archive HEAD | tar -x -C "$tmp/src"
"$PYTHON" -m venv "$tmp/buildenv"
"$tmp/buildenv/bin/pip" install --quiet --disable-pip-version-check build
(cd "$tmp/src" && "$tmp/buildenv/bin/python" -m build --outdir "$tmp/dist" > "$tmp/build.log" 2>&1) \
    || { tail -30 "$tmp/build.log"; fail "python -m build failed"; }
wheel="$tmp/dist/glra_midi-$version-py3-none-any.whl"
sdist="$tmp/dist/glra_midi-$version.tar.gz"
[ -f "$wheel" ] || fail "no $(basename "$wheel") built (found: $(ls "$tmp/dist"))"
[ -f "$sdist" ] || fail "no $(basename "$sdist") built (found: $(ls "$tmp/dist"))"
echo "built $(basename "$wheel") and $(basename "$sdist")"

step "5. contents"
"$PYTHON" -I - "$wheel" "$sdist" "$version" <<'PY' || fail "a built file is missing something (above)"
import sys, tarfile, zipfile

wheel, sdist, version = sys.argv[1:4]
wnames = zipfile.ZipFile(wheel).namelist()
snames = tarfile.open(sdist).getnames()
prefix = f"glra_midi-{version}/"
missing = []
for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
    if not any(n.endswith(f".dist-info/licenses/{name}") for n in wnames):
        missing.append(f"wheel: {name}")
    if prefix + name not in snames:
        missing.append(f"sdist: {name}")
for name in ("glra_midi/default_profile.toml", "glra_midi/device/layout.json",
             "glra_midi/app/qml/Main.qml"):
    if name not in wnames:
        missing.append(f"wheel: {name}")
for m in missing:
    print("missing", m)
sys.exit(1 if missing else 0)
PY
echo "LICENSE, THIRD_PARTY_NOTICES.md and package data present"

step "6. fresh install"
"$PYTHON" -m venv "$tmp/fresh"
"$tmp/fresh/bin/pip" install --quiet --disable-pip-version-check "$wheel"
got=$("$tmp/fresh/bin/glra-midi" --version)
[ "$got" = "glra-midi $version" ] || fail "glra-midi --version printed '$got'"
echo "$got"

mkdir -p dist
cp "$wheel" "$sdist" dist/
step "OK: $version can be released"
echo "files for the GitHub release (git-ignored):"
ls -1 "dist/$(basename "$wheel")" "dist/$(basename "$sdist")"
if [ "$allow_any_branch" -eq 1 ]; then
    echo "This was a rehearsal; the real check runs on main without --allow-any-branch."
fi
echo "Nothing was tagged or pushed."
