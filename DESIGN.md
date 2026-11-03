# Baynard Racing — design

*Living document. Started 2026-11-03. Anything marked **(proposal)** hasn't been decided; change it freely.*

## The pitch

An open-world kart racer starring barnyard animals. Drive anywhere across one big, joined-up stretch of
countryside, drift through hairpins until your wheels throw sparks, and race friends online or on the couch.
Think Mario Kart World's open world and party feel, with drift handling that has real depth.

The name is a play on *barnyard*. (It's also a nod to Bayard, the legendary horse.)

Baynard Racing is **Playweft's flagship game**: public, featured, and polished. It's what we point people at
to show what the engine can do, so it sets the quality bar. (3 Dimenshift is the other game we build, but it's
for internal testing and finding gaps. This one ships.)

## Pillars

1. **Drifting feels great.** Easy to start, deep to master. A beginner holds drift and goes round the
   corner; an expert chains drifts, times mini-turbos and picks lines. If the drift isn't fun, nothing else
   matters.
2. **One world, no loading screens.** Tracks are routes through a single connected world. Between races
   you're still driving, through the same fields, orchards and fairgrounds.
3. **Characters with charm.** Every animal has a look, a voice, a personality and a way of celebrating.
   Losing to a goose should be funny.
4. **Play together anywhere.** Online in the browser from a link, with no install; split screen on one
   machine; mixed groups of the two.

## The world (proposal)

One county, **Baynard County**, made of regions that flow into each other:

| Region | Feel | Signature track ideas |
|---|---|---|
| Home Farm | the hub: barns, silos, a duck pond | **Barnyard Loop**, the first track and tutorial |
| Orchard Hills | rolling rows of trees, falling apples | switchbacks through the rows |
| Mill River | a river, a waterwheel, wooden bridges | jumps across the water, a race through the mill |
| County Fair | lights, a Ferris wheel, food stands, night | a race through the fair at night, under fireworks |
| Cornfield Maze | tall corn, crop circles | a maze with shortcuts you have to learn |
| High Pasture | a mountain pass, goats, fog, snow at the top | a downhill run with wide drifts |
| Salt Marsh & Coast | boardwalk, lighthouse, beach | beach sand that steals your grip |

- **Free roam** between races: collectibles (golden eggs?), small challenges, secrets.
- **Day and night, and weather**: rain makes roads slippery; mud slows you down.
- Tracks are built in Playweft's level editor from world shapes, not imported from other tools.

## The racers (proposal)

Starting roster, about eight, with more to unlock. Each is a sculpted, rigged character with facial
expressions.

| Animal | Personality | Weight class |
|---|---|---|
| **Hen** | anxious perfectionist, lays eggs when nervous | light |
| **Pig** | cheerful, loves mud | medium |
| **Goat** | chaotic, eats things | medium |
| **Cow** | calm and unstoppable | heavy |
| **Sheep** | fluffy, unbothered | light |
| **Goose** | menace | medium |
| **Horse** (Bayard) | proud champion, the rival | heavy |
| **Barn Cat** | smug, precise | light |

Later: Duck, Donkey, Sheepdog, Rooster, Rabbit, Turkey.

Weight class changes handling: lighter animals turn and accelerate faster, heavier ones have more top speed
and win collisions.

## Karts

- Farm-built, mismatched: a tractor seat on a cart frame, a wheelbarrow kart, a milk-churn engine.
- Parts can be swapped (body, wheels, glider-style extra) and they change the stats. Cosmetic paint
  on top.

## Driving

- **Drift:** hold the drift button with a direction to start one. It builds through spark tiers
  (blue → orange → purple); let go for a mini-turbo whose strength depends on the tier.
- **Hop** to start a drift and to cross small gaps.
- **Slipstream** behind another kart.
- **Tricks** off ramps and bumps for a small boost.
- **Fence grinding** (proposal): ride along fence rails like Mario Kart World's rail grinding.
- **Surfaces matter:** tarmac, dirt, grass, mud, ice, sand and boost pads each have their own grip and
  sound.
- Handling is built on real wheel physics (suspension, tyre grip), with the arcade layer on top
  written as game code. Drift should come out of the physics and the tuning, not be animated on.

## Items (proposal)

Farm-themed, readable at a glance:

| Item | What it does |
|---|---|
| Egg | dropped behind you; whoever hits it spins out |
| Egg carton | three eggs |
| Corn-cob rocket | fires straight ahead |
| Mud pie | splats screens and makes the road slippery |
| Hay bale | a shield you hold behind you |
| Honk | short shockwave that bumps nearby karts (louder when the Goose uses it) |
| Hornet nest | homes in on the leader |
| Carrot | a speed boost |

## Modes

- **Grand Prix**: four-race cups.
- **Open Road**: free roam across the whole county.
- **Time Trial**, with ghosts.
- **Online**: quick race and private rooms joined by link.
- **Couch**: split screen for 2–4 players; online and couch players can mix.
- **Battle** (later): arenas built into the world.

## Look and sound (proposal)

- **Look:** stylised, chunky, toy-like. Soft, clay-like shapes, bright saturated colours, warm light.
  Readable silhouettes at kart speed. Not realistic.
- **Characters** are sculpted in hifipushie (SDF clay sculpting), rigged to the standard humanoid skeleton
  where they can be, with ARKit-named face shapes for expressions.
- **Props and scenery** come from oxidegen (concept image → mesh) and are cleaned up before use.
- **Audio:** every engine is a live sound graph that follows revs and load; animal voices for hits,
  overtakes and wins; music that follows the race (a lap-three surge, the final-lap key change).

## What this shows off in Playweft

| Feature | Where it shows up |
|---|---|
| Vehicle physics | every kart |
| World geometry and level editor | every region and track |
| Streaming and 64-bit positions | one big county with no loading screens |
| Multiplayer with prediction and rollback | online races |
| Split screen | couch play |
| Animation (motion library, faces) | racers reacting, celebrating, getting hit |
| Audio engine | engine sounds, spatial mixing, music that follows the race |
| Particles and trails | drift sparks, skid marks, mud, dust, boosts |
| Probe lighting, sky, day and night | the county fair at night, weather |
| Web-first | play from a link in a browser |
| Agent-native authoring (MCP) | much of the game built with AI agents in the editor |

## Engine or game code

Following Playweft's rule: **the engine supplies general means, the game's rules are game code.**

- **Engine** (filed on Playweft's board, tagged `baynard-racing`): vehicle physics, surfaces, closest
  point on a curve, split screen, trails, racing-grade netcode, streaming, 64-bit positions, particles.
- **Game code** (this repo): drift and boost rules, kart stats, items, race logic (laps, positions,
  respawn), AI drivers, camera rig, menus and HUD.
- A gap found here becomes a **general** Playweft feature, never a Baynard-only hack in the engine.

## Milestones

1. **First playable:** one kart, one animal stand-in, the Barnyard Loop blocked out, laps counted, drift
   and boost. *(Waits on vehicle physics in the engine.)*
2. **Feel pass:** drift tuning until it's fun with a gamepad; camera; surfaces.
3. **First cup:** four tracks around Home Farm; items; AI drivers.
4. **Online and couch:** races over a link; split screen.
5. **Open world:** the regions joined up, free roam.
6. **Polish and launch.**

Art can run ahead of all of these: concept art, the first racers and the Home Farm look.

## Open questions

- Final roster and names.
- Item list and balance.
- Should drift be manual only, or have an assist option for younger players?
- Target player count online (8? 12? 24 like Mario Kart World?).
