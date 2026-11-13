# Releases: one version in `__init__.py`, GitHub only, and Bob says yes to every push and tag

When cutting, preparing or checking a release, bumping the version, or editing `CHANGELOG.md`, `docs/releasing.md` or `tools/release-check.sh`: the version lives only in `glra_midi/__init__.py`, and tagging, pushing and publishing need Bob's go-ahead each time.

## Triggers
- release
- version bump
- CHANGELOG
- release-check
- PROFILE_VERSION

## Context
As of 2026-11-13 (Bob's answers, `loom:public-release`): GitHub releases only, no PyPI;
first release 0.1.0; SemVer, where a 0.x minor bump may break the profile format or the CLI.
`pyproject.toml` takes the version from `glra_midi.__version__` (`dynamic`); the repo holds
the last released version (0.0.1 until `first-release` bumps it). `tools/release-check.sh
<version>` builds from `git archive HEAD` and checks version, changelog section, LICENSE and
THIRD_PARTY_NOTICES in both files, and a fresh install; it never tags or pushes. The profile
file's `version = 1` (`PROFILE_VERSION`) counts separately; `docs/releasing.md` holds the
worker's proposed rule for when it bumps (not yet confirmed by Bob). Steps: `docs/releasing.md`.

## Associations
- [[glra-studio-reuse]]
