// A test driver: drives one racer's kart round the Barnyard Loop the way a player would, through the
// "drive" controls, and keeps count of how it went. Used by tests/handling.ts and tests/balance.ts.
//
// It reads the road's centre line from the Road's curve, aims at a point ahead of the kart (further
// the faster it goes), and takes the speed it can carry through the tightest corner coming up, braking
// in time. `style` is how it uses the stick: "smooth" steers in proportion, as a gamepad does;
// "keys" steers full left, full right or not at all, as arrow keys do.

export const KARTS = ["Hettie's Kart", "Max's Racer", "Puddles' Bathtub", "The Major's Boat", "Mabel's Churn", "Scraps' Can Kart", "Marmalade's Scoop", "Duvet's Wheelbarrow"];
export const NAMES = ["Hettie", "Max", "Puddles", "The Major", "Mabel", "Scraps", "Marmalade", "Duvet"];

const TICKS = 60;

function bezier(a, b, c, d, u) {
  const v = 1 - u;
  const k = [v * v * v, 3 * v * v * u, 3 * v * u * u, u * u * u];
  return [0, 1, 2].map((i) => k[0] * a[i] + k[1] * b[i] + k[2] * c[i] + k[3] * d[i]);
}

/** The road's centre line as points a metre or so apart, and the turn per metre at each. */
export function line(game) {
  const points = game.object("Road").get("curve", "points");
  const out = [];
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    const q = points[(i + 1) % points.length];
    const a = p.position;
    const b = a.map((v, j) => v + p.handle_out[j]);
    const d = q.position;
    const c = d.map((v, j) => v + q.handle_in[j]);
    for (let s = 0; s < 40; s++) out.push(bezier(a, b, c, d, s / 40));
  }
  const n = out.length;
  const heading = out.map((p, i) => {
    const q = out[(i + 1) % n];
    return Math.atan2(q[0] - p[0], -(q[2] - p[2]));
  });
  const step = out.map((p, i) => Math.hypot(out[(i + 1) % n][0] - p[0], out[(i + 1) % n][2] - p[2]));
  return { points: out, heading, step, n };
}

const wrapAngle = (a) => Math.atan2(Math.sin(a), Math.cos(a));

/** The kart's nose on the ground, as a heading (0 = -Z, positive turning right). */
function headingOf(q) {
  const [x, y, z, w] = q;
  // The kart's forward (0, 0, -1) turned by its rotation.
  const fx = -(2 * (x * z + w * y));
  const fz = -(1 - 2 * (x * x + y * y));
  return Math.atan2(fx, -fz);
}

/** Start a single-player race in racer `n`'s kart (1 to 8) and wait out the countdown. */
export function startRace(game, n) {
  game.say(1, "enter", {});
  game.run(3);
  game.say(1, "pick", { racer: n });
  game.run(3);
  game.say(1, "start", {});
  game.run(3.2 * TICKS);
}

/**
 * Drive racer `n`'s kart until it finishes (or `limit` seconds pass). Answers its lap times, its total,
 * how many times it spun round, how long it spent going backwards, and how often it was put back on
 * the road.
 */
export function drive(game, n, style, limit = 240) {
  const name = KARTS[n - 1];
  const road = line(game);
  let at = 0;
  let last = null;
  let spins = 0;
  let backwards = 0;
  let wasBackwards = false;
  let resets = 0;
  let stuck = 0;
  const every = 2;
  for (let tick = 0; tick < limit * TICKS; tick += every) {
    const kart = game.object(name);
    if (kart.get("kart", "finished") > 0) break;
    const p = kart.position;
    // Nearest point on the line, searched near the last one.
    let best = Infinity;
    let bi = at;
    for (let k = -30; k <= 60; k++) {
      const i = (at + k + road.n) % road.n;
      const q = road.points[i];
      const d = (q[0] - p[0]) ** 2 + (q[2] - p[2]) ** 2;
      if (d < best) { best = d; bi = i; }
    }
    at = bi;
    const nose = headingOf(kart.rotation);
    // How fast, and which way it is actually going.
    let speed = 0;
    let travel = nose;
    if (last !== null) {
      const dx = p[0] - last[0];
      const dz = p[2] - last[2];
      speed = Math.hypot(dx, dz) / (every / TICKS);
      if (speed > 1) travel = Math.atan2(dx, -dz);
    }
    last = p;
    // Spun: the nose more than a right angle from where the road goes.
    const off = Math.abs(wrapAngle(nose - road.heading[at]));
    const isBackwards = off > Math.PI / 2 && speed > 1;
    if (isBackwards) backwards += every / TICKS;
    if (isBackwards && !wasBackwards) spins++;
    wasBackwards = isBackwards;

    // Aim at a point ahead along the line.
    let ahead = 4 + 0.55 * speed;
    let j = at;
    while (ahead > 0) { ahead -= road.step[j]; j = (j + 1) % road.n; }
    const t = road.points[j];
    const want = Math.atan2(t[0] - p[0], -(t[2] - p[2]));
    const err = wrapAngle(want - nose);
    let steer = Math.max(-1, Math.min(1, err * 2.2));
    if (style === "keys") steer = err > 0.06 ? 1 : err < -0.06 ? -1 : 0;

    // The speed it can carry: the tightest corner in the next 45 m, braked for in time.
    let target = 40;
    let dist = 0;
    let k = at;
    while (dist < 45) {
      let span = 0;
      let m = k;
      while (span < 6) { span += road.step[m]; m = (m + 1) % road.n; }
      const turn = Math.abs(wrapAngle(road.heading[m] - road.heading[k]));
      const radius = span / Math.max(turn, 1e-3);
      const corner = Math.sqrt(9.0 * radius);
      target = Math.min(target, Math.sqrt(corner * corner + 2 * 7 * dist));
      dist += road.step[k];
      k = (k + 1) % road.n;
    }
    const brake = speed > target + 0.5 ? 1 : 0;
    game.hold(1, "drive", "stick", [steer, 0]);
    game.hold(1, "drive", "gas", brake ? 0 : 1);
    game.hold(1, "drive", "brake", brake);

    // Off the road and getting nowhere: back on the road, as a player would press R.
    stuck = speed < 1.5 ? stuck + every / TICKS : 0;
    if (stuck > 4 || best > 20 * 20) {
      game.press(1, "drive", "respawn");
      resets++;
      stuck = 0;
    }
    game.run(every);
  }
  const kart = game.object(name);
  return {
    name: NAMES[n - 1],
    finished: kart.get("kart", "finished"),
    best: kart.get("kart", "bestLap"),
    laps: kart.get("kart", "progress"),
    spins,
    backwards,
    resets,
  };
}

export const report = (r) =>
  `${r.name.padEnd(10)} ${r.finished > 0 ? r.finished.toFixed(2).padStart(7) + " s" : "  DNF   "}  best lap ${r.best.toFixed(2)}  spins ${r.spins}  backwards ${r.backwards.toFixed(1)} s  resets ${r.resets}`;
