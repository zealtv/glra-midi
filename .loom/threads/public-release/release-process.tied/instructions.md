# release-process — versioning and how a release gets cut

Bob, 2026-11-13: GitHub releases only for now (no PyPI); first release 0.1.0;
SemVer, where during 0.x a minor bump may break the profile format or CLI.

- Version single-sourced (`glra_midi/__init__.py` or pyproject, one place);
  bump `0.0.1` → `0.1.0` in `first-release`, not here.
- `CHANGELOG.md` in Keep a Changelog form, with an `Unreleased` section filled
  from the loom's tied stitches for 0.1.0 (midi-mvp, config-app).
- `docs/releasing.md`: the checklist (tests, changelog, version bump commit,
  tag `vX.Y.Z`, build wheel and sdist, GitHub release with notes and the two
  files attached) and the rule that tagging, pushing and publishing need Bob's
  go-ahead each time.
- `tools/release-check.sh <version>`: clean tree on main, `./test.sh`, version
  and changelog entry match, `python -m build` in a temp venv, the wheel and
  sdist contain LICENSE and THIRD_PARTY_NOTICES, a fresh install runs
  `glra-midi --version`. It builds; it never tags or pushes.
- Note the profile format's own `version = 1` and when it must change.
