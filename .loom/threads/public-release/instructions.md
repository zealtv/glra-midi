# public-release — rename to glra-midi, set a versioning and release process, publish a first release

Bob, 2026-11-13, during the config-app orchestrator run: "after the
config-app-tour we'll rename the repo to glra-midi and create a public
release, along with a versioning and release process/strategy".

Not yet shaped. Off the queue: the config-app run doesn't start it (bounded
queue, see qtable's `work-the-queue-as-a-bounded-release`). Bob queues it after
the tour. It needs `config-app-tour`.

What Bob named, to split into stitches when shaped with him:

- **Rename** the repo, package and CLI from glra-osc to glra-midi (repo
  directory, `pyproject.toml` name and entry point, Python package, docs,
  glean/lore references, peer-repo paths that name `glra-osc`).
- **Versioning and release process/strategy**: scheme, changelog, how a
  release gets cut and checked.
- **Public release**: the first published version. Publishing, pushing and
  tagging need Bob's go-ahead at the time.

Questions for the shaping session (not answered as of 2026-11-13): where it
gets published (GitHub only, PyPI too?); the version number for the first
release; what the GPL-3.0-only vendored code in `glra_osc/device/` needs for a
public release (notices, attribution to glra-studio).
