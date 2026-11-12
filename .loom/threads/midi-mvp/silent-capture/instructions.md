# silent-capture — apply the chosen suppression route at runtime

Suggested model: Sonnet, or whichever model fits the chosen route's complexity.

Implement the route chosen in `suppression-route` in the runtime used by
`monitor` and `run`:
- Apply it when the pad connects (and again on replug); undo it on exit,
  including Ctrl-C and SIGTERM, and on disconnect where that matters.
- If it can't be applied or verified, refuse to run (or run only with an
  explicit `--allow-typing` flag) and print why. Never fall back silently.
- Check by hand with Bob: pad silent in TextEdit, Finder, a DAW, with
  modifiers held; built-in and other keyboards unaffected; state restored
  after exit, after a crash (kill -9) and after a replug.
