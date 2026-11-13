// Each kart's trail (components/dust.ts): what the ground under it throws up as it goes, so a kart
// leaves a cloud on dirt, clods on mud, glints on ice, smoke when it drifts on tarmac and sparks in a
// boost, and its exhaust smokes dark and thick under throttle and lightly as it cruises. Visual only:
// it starts and stops emitters, and rewinds with the game.
//
// A third of the emitters are looked at each tick, and an emitter is only started or stopped when it
// changes: a trail a twentieth of a second late is not seen, and the system stays cheap.
const kartOf = pw.object("dust", "kart");
const kind = pw.field("dust", "kind");
const speedOf = pw.field("kart", "speed");
const driftOf = pw.field("kart", "driftDir");
const boostOf = pw.field("kart", "boost");
const gasOf = pw.field("kart", "gasAsk");
const topOf = pw.field("kart", "topSpeed");
const position = pw.vec3("transform", "position");

const BY_SURFACE = { dirt: 1, sand: 2, mud: 3, grass: 4, ice: 5 };
const SMOKE = 6;
const SPARKS = 7;
const EXHAUST_HARD = 8;
const EXHAUST_SOFT = 9;
const SHARES = 3;

// Whether each emitter is on, by its place among the dust objects.
const lit = [];
let turn = 0;

pw.registerSystem("dust", { includeComponents: ["dust", "particles"] }, ({ objects, physics }) => {
  turn = (turn + 1) % SHARES;
  const under = new Map();
  let i = -1;
  for (const trail of objects) {
    i += 1;
    if (i % SHARES !== turn) continue;
    const kart = trail.get(kartOf);
    let on = false;
    if (kart !== null && kart.exists) {
      const speed = Math.abs(kart.get(speedOf));
      const k = trail.get(kind);
      // Pulling hard: the throttle open, the kart moving and still well short of its top speed.
      const pulling = kart.get(gasOf) > 0.3 && speed > 0.5 && speed < kart.get(topOf) * 0.85;
      let ground = "";
      if (k < EXHAUST_HARD) {
        ground = under.get(kart.index);
        if (ground === undefined) {
          const at = kart.get(position);
          const hit = physics.ray([at[0], at[1] + 0.5, at[2]], [0, -1, 0], 1.6, { exclude: kart });
          ground = hit === null ? "" : hit.surface;
          under.set(kart.index, ground);
        }
      }
      if (k === EXHAUST_HARD) on = pulling;
      else if (k === EXHAUST_SOFT) on = !pulling;
      else if (k === SMOKE) on = ground === "tarmac" && kart.get(driftOf) !== 0 && speed > 6;
      else if (k === SPARKS) on = kart.get(boostOf) > 0 && speed > 5;
      else on = BY_SURFACE[ground] === k && speed > (k === 5 ? 6 : 3);
    }
    if (lit[i] === on) continue;
    lit[i] = on;
    if (on) trail.particles.start();
    else trail.particles.stop();
  }
});
