# Baynard Racing

Playweft's flagship game: an open-world kart racer with drift physics and barnyard animals. It's public,
featured and polished, so it sets the quality bar. The design is in [`DESIGN.md`](./DESIGN.md); keep it current
when a decision changes it.

- **This repo is public.** Stage by path, never `git add -A`. Nothing private (keys, tokens, personal data)
  goes in.
- **Game code lives here; the engine lives in `../playweft`.** A gap found here becomes a **general** Playweft
  feature (its own PR there, following its CLAUDE.md) or a card on the Playweft Overboard board tagged
  `baynard-racing`. Never a Baynard-only hack in the engine.
- **Art:** `art/` holds sources and approved pieces (`concepts/`, `racers/`, `karts/`, `world/`). Characters are
  sculpted in hifipushie; props and scenery come through oxidegen. Big working files go in `workspace/`
  (git-ignored).
- **Project files** (`playweft.json`, `scene.weave` …) are made by the Playweft editor
  (`pw-studio-desktop --new <folder>`), never hand-written.
- Plain words with Joe; recommend rather than list options.
