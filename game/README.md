# Baynard Racing — the Playweft project

Open it with the Playweft desktop editor (`pw-studio-desktop --open game`) and press **Play**.

**First playable:** Hettie in her crate kart on the blocked-out Barnyard Loop, three laps. The loop starts on a low
plateau with a kicker that throws the kart onto the road falling away below it, climbs a right-hander onto the barn
hill, goes light over the crest, drops through an S and rounds a hairpin banked 15°.

| Do | Keys | Gamepad |
|---|---|---|
| Steer, throttle, brake / reverse | WASD or the arrows | left stick, right and left triggers |
| Drift (hold with a direction; let go for a mini-turbo) | Space or Shift | right bumper or B |
| Back on the road | R | Back |

The road has surfaces of its own: dirt on the inside of the first right-hander (so the
kart grips differently on each side), mud on the outside of the climb, ice through the S, sand on the run back
up to the start, and a boost pad before the kicker. Each is a material saying how a tyre grips it and how hard
it is to roll on, so the physics does the slipping and the dragging; only the boost pad is a game rule.

A drift builds blue, orange and then purple sparks; letting go gives a mini-turbo that lasts longer
the higher the tier. Grass slows the kart too. Laps are counted along the track's centre line, so a
shortcut across the infield or driving the wrong way doesn't count.

- `systems/kart.ts`: driving, the drift and the mini-turbo, on the engine's Vehicle and Wheels.
- `systems/tyres.ts`: the rear tyres' sideways grip while drifting.
- `systems/laps.ts`: laps, the race clock and respawns.
- `systems/chase_camera.ts`: the camera.
- `systems/telemetry.ts`: a testing aid that logs a kart's motion and its wheels' contact every tick, for objects
  given a Telemetry card.
- `components/`: the cards (a kart's stats, its tyres, the camera), with every number tunable in the Inspector.
- The kart's wheels are separate models made by `tools/split_kart.py` from `art/karts/hettie/kart.glb`.
  The loop's layout is `tools/barnyard_loop.py`: its road and hay walls are Sweeps with square rings (mitred
  ones of this length can take the editor minutes and gigabytes to build).
