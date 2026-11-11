# Baynard Racing — the Playweft project

Open it with the Playweft desktop editor (`pw-studio-desktop --open game`) and press **Play**.

**First playable:** Hettie in her crate kart on the blocked-out Barnyard Loop, three laps.

| Do | Keys | Gamepad |
|---|---|---|
| Steer, throttle, brake / reverse | WASD or the arrows | left stick, right and left triggers |
| Drift (hold with a direction; let go for a mini-turbo) | Space or Shift | right bumper or B |
| Back on the road | R | Back |

A drift builds blue, orange and then purple sparks; letting go gives a mini-turbo that lasts longer
the higher the tier. Grass slows the kart. Laps are counted along the track's centre line, so a
shortcut across the infield or driving the wrong way doesn't count.

- `systems/kart.ts`: driving, the drift and the mini-turbo, on the engine's Vehicle and Wheels.
- `systems/tyres.ts`: the rear tyres' sideways grip while drifting.
- `systems/laps.ts`: laps, the race clock and respawns.
- `systems/chase_camera.ts`: the camera.
- `components/`: the cards (a kart's stats, its tyres, the camera), with every number tunable in the Inspector.
- The kart's wheels are separate models made by `tools/split_kart.py` from `art/karts/hettie/kart.glb`.
  The loop's layout is `tools/barnyard_loop.py`.
