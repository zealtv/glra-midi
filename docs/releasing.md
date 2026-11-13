# Releasing glra-midi

How a version gets numbered and a release gets cut. Written by the `release-process` worker on
2026-11-13 from Bob's answers of the same day (`.loom/threads/public-release/instructions.md`):
GitHub releases only for now, no PyPI; the first release is 0.1.0; SemVer.

## Who decides

**Tagging, pushing, creating a GitHub release and changing the repo's visibility each need
Bob's go-ahead at the time** (Bob, 2026-11-13: every push, tag and visibility change on his
word). A go-ahead for one release does not carry to the next, nor from one step to another.
Agents prepare and check; `tools/release-check.sh` builds and never tags or pushes.

## Versioning

Semantic Versioning, `MAJOR.MINOR.PATCH`, starting at 0.1.0 (Bob, 2026-11-13: "SemVer 0.x").

- **During 0.x**, a minor bump (0.1.x to 0.2.0) may break the profile format or the command
  line. A patch bump (0.1.0 to 0.1.1) fixes bugs and adds nothing that breaks.
- **From 1.0.0 on**, the usual rules: breaking changes to the profile format, the command
  line or the documented behaviour need a major bump. Bob decides when 1.0.0 happens.
- **One place:** `__version__` in `glra_midi/__init__.py`. `pyproject.toml` reads it
  (`dynamic = ["version"]`), and `glra-midi --version` prints it. Don't write the version
  anywhere else. The repo holds the last released version between releases (0.0.1 until the
  first release; the 0.1.0 bump belongs to the `first-release` stitch).
- **Changelog:** `CHANGELOG.md`, Keep a Changelog form. Add a line under `## [Unreleased]`
  with the change that earns it (Added, Changed, Deprecated, Removed, Fixed, Security), in the
  same commit. A release turns `Unreleased` into `## [X.Y.Z] - YYYY-MM-DD`.
- **Tags:** `vX.Y.Z`, annotated or not, on the version-bump commit on `main`.

### The profile format's own version

A profile starts with `version = 1` (`PROFILE_VERSION` in `glra_midi/profile.py`), and
`glra-midi` reads exactly that number and refuses any other. It counts separately from the
release number. This was the worker's proposal on 2026-11-13, for Bob to correct:

- **Bump it** when a change makes a profile that loaded before fail to load or mean something
  else: a key renamed or removed, a value's meaning or range changed, a new required key.
- **Don't bump it** for a new optional key with a default, or a looser check. Note that
  `glra-midi` rejects keys it doesn't know, so an older release will refuse a file that uses
  the new key; say so in the changelog entry.
- A bump goes in a minor release during 0.x (a major one from 1.0.0), with a `Changed` or
  `Removed` entry that says what an old file needs. Whether an old file gets a converter or a
  hard break stays Bob's call each time (on 2026-11-13 he chose a hard break for the
  pre-profile mapping files: "we can hard break").
- The default profile, `docs/config-app.md` §2 and `README.md` change in the same commit.

## Cutting a release

For release `X.Y.Z`, from a clean `main` that has everything the release needs.

1. **Tell Bob** what the release holds and ask for the go-ahead to cut it.
2. **Changelog:** rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD` and put a fresh empty
   `## [Unreleased]` above it. Bob reads the entries.
3. **Version:** set `__version__ = "X.Y.Z"` in `glra_midi/__init__.py`. Commit steps 2 and 3
   together, e.g. `release: X.Y.Z`. (Docs that name the version or status, such as the README's
   "Status" line, change in this commit too.)
4. **Check:** `tools/release-check.sh X.Y.Z`. It needs a clean tree on `main` and a network
   (pip), and it checks:
   - the tag `vX.Y.Z` doesn't exist yet;
   - `./test.sh` passes;
   - `__version__` and a `## [X.Y.Z] - date` changelog section match;
   - `python -m build` makes a wheel and an sdist from `git archive HEAD` in a temporary
     virtualenv;
   - both contain `LICENSE` and `THIRD_PARTY_NOTICES.md` (the wheel also the default profile,
     the layout and the QML files);
   - a fresh virtualenv installs the wheel, and `glra-midi --version` prints `glra-midi X.Y.Z`.

   It leaves the two files in `dist/` (git-ignored). Fix whatever it reports and run it
   again; the check only reads and builds, so a rerun does no harm. Before step 3 you can
   rehearse on any branch with `--allow-any-branch` (it still wants a version and changelog
   section to match, so a rehearsal needs a throwaway commit or clone).
5. **Ask Bob** for the go-ahead to push and tag. Then, on his word:
   `git push origin main`, `git tag vX.Y.Z`, `git push origin vX.Y.Z`.
6. **GitHub release**, on his word: create release `vX.Y.Z` from that tag, with the
   changelog section as the notes, and attach the two files from `dist/`
   (`glra_midi-X.Y.Z-py3-none-any.whl`, `glra_midi-X.Y.Z.tar.gz`), e.g.
   `gh release create vX.Y.Z dist/glra_midi-X.Y.Z-py3-none-any.whl dist/glra_midi-X.Y.Z.tar.gz --title X.Y.Z --notes-file <notes>`.
   No PyPI upload (Bob, 2026-11-13: GitHub only for now).
7. **After:** note the release in the loom (the stitch that cut it) and, if the release taught
   something lasting, in glean.

If `release-check.sh` fails after the tag exists, don't move the tag: fix forward and cut the
next patch version, unless Bob says otherwise.

## Installing a release

The attached wheel installs with `pip install glra_midi-X.Y.Z-py3-none-any.whl` (add the
`gui` extra for the configuration app: `pip install 'glra_midi-X.Y.Z-py3-none-any.whl[gui]'`).
macOS and Python 3.13 or later, as the README says.
