// The rivals' driving: each tick a rival looks along the track's centre line from where it is, aims at
// a point ahead (further at speed), a lane to its side, and steers for it. It reads the corners coming
// up and takes the speed it can carry through the tightest of them, braking in time; a long corner it
// drifts and lets go as the road straightens, for the mini-turbo. Its asks go to the kart like a
// player's, so a rival drives the same kart by the same rules.
//
// It is not a perfect driver. Its hands wander off the aim a little (a slow random drift, not a
// jitter), and now and then it makes a mistake: it brakes late for a corner, or lets a drift go before
// the sparks were worth it. Its style is its own: how far it cuts into a corner, how keen it is to
// drift, and whether it swerves into a kart alongside. `Math.random` is the run's own seeded stream,
// so every machine in a shared game sees the same mistakes.
//
// Runs in `act`, before the kart reads its asks.
const K = pw.component("kart");
const V = pw.component("rival");
const k = Object.fromEntries(
  ["steerAsk", "gasAsk", "brakeAsk", "driftAsk", "respawnAsk", "laps", "topSpeed", "driftMinSpeed", "driftDir", "speed", "clock", "startDelay"].map((n) => [n, K.property(n)]),
);
const r = Object.fromEntries(
  ["lane", "pace", "cornerGrip", "braking", "aim", "aimPerSpeed", "steering", "driftTurn", "stuckAfter", "stuck", "wanted",
    "cutCorners", "barge", "wobble", "mistakes", "shake", "lapse"].map((n) => [n, V.property(n)]),
);
const trackOf = pw.object("kart", "track");
const position = pw.vec3("transform", "position");
const rotation = pw.quat("transform", "rotation");

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const wrap = (t) => t - Math.floor(t);
/** The signed turn from heading `a` to heading `b`, both [x, z] on the ground: positive turns right. */
const turnOf = (a, b) => Math.atan2(a[0] * b[1] - a[1] * b[0], a[0] * b[0] + a[1] * b[1]);
const flat = (d) => {
  const n = Math.hypot(d[0], d[2]) || 1;
  return [d[0] / n, d[2] / n];
};

/** How far a corner turns, signed, over `metres` of the curve from `t`, and the tightest speed in it. */
function lookAlong(curve, t, metres, step, grip) {
  let heading = flat(curve.directionAt(t));
  let turned = 0;
  let tightest = Infinity;
  let at = 0;
  for (let s = step; s <= metres; s += step) {
    const next = flat(curve.directionAt(wrap(t + s / curve.length)));
    const bend = turnOf(heading, next);
    turned += bend;
    // A bend of `bend` radians over `step` metres is a circle of radius step / |bend|.
    const radius = step / Math.max(Math.abs(bend), 1e-4);
    const carry = Math.sqrt(grip * radius);
    if (carry < tightest) {
      tightest = carry;
      at = s;
    }
    heading = next;
  }
  return { turned, tightest, at };
}

/** A random number from -1 to 1. */
const noise = () => Math.random() * 2 - 1;

const nearby = pw.sphere(3.5);

pw.registerSystem("rivals", { includeComponents: ["kart", "rival", "rigid_body"] }, ({ objects, physics }) => {
  const dt = objects.dt;
  for (const kart of objects) {
    const track = kart.get(trackOf);
    if (track === null || !track.exists) continue;
    const curve = track.curve;
    const at = kart.get(position);
    const rot = kart.get(rotation);
    const forward = pw.rotateVector([0, 0, -1], rot);
    const right = pw.rotateVector([1, 0, 0], rot);
    const speed = kart.get(k.speed);
    const near = curve.closest(at);

    const grip = kart.get(r.cornerGrip);
    const corner = lookAlong(curve, near.t, 20, 2, grip);

    // Where to aim: a point ahead along the centre line, its lane to the right, moved toward the inside
    // of the corner coming up by as much as it likes to cut corners.
    const ahead = kart.get(r.aim) + Math.max(0, speed) * kart.get(r.aimPerSpeed);
    const tAim = wrap(near.t + ahead / curve.length);
    const p = curve.at(tAim);
    const [hx, hz] = flat(curve.directionAt(tAim));
    const lane = clamp(kart.get(r.lane) + kart.get(r.cutCorners) * clamp(corner.turned / 1.2, -1, 1), -4.5, 4.5);
    const aimAt = [p[0] - hz * lane, p[1], p[2] + hx * lane];
    const to = [aimAt[0] - at[0], aimAt[1] - at[1], aimAt[2] - at[2]];
    const across = to[0] * right[0] + to[1] * right[1] + to[2] * right[2];
    const along = to[0] * forward[0] + to[1] * forward[1] + to[2] * forward[2];
    // Unsteady hands: an error that wanders slowly, pulled back toward none.
    let shake = kart.get(r.shake);
    shake += -shake * 1.2 * dt + kart.get(r.wobble) * 0.25 * Math.sqrt(dt) * noise();
    let angle = Math.atan2(across, along) + shake;

    // A barger leans into a kart close alongside, the nearer the harder.
    const barge = kart.get(r.barge);
    if (barge > 0) {
      for (const touch of physics.overlap(nearby, at, { exclude: kart })) {
        // Every kart races some laps; nothing else on the track does.
        const other = touch.object;
        if (other === null || other.get(k.laps) <= 0) continue;
        const there = other.get(position);
        const d = [there[0] - at[0], there[1] - at[1], there[2] - at[2]];
        const side = d[0] * right[0] + d[1] * right[1] + d[2] * right[2];
        const front = d[0] * forward[0] + d[1] * forward[1] + d[2] * forward[2];
        if (Math.abs(side) < 3.5 && Math.abs(front) < 2.5) angle += barge * 0.5 * Math.sign(side) * (1 - Math.abs(side) / 3.5);
      }
    }
    let steer = clamp(angle * kart.get(r.steering), -1, 1);

    // A mistake now and then, once the race is on: for a moment it stops reading the corners ahead
    // (and brakes late), or, in a drift, lets it go early.
    const racing = kart.get(k.clock) >= kart.get(k.startDelay);
    let lapse = Math.max(0, kart.get(r.lapse) - dt);
    let fluffDrift = false;
    if (racing && lapse === 0 && Math.random() < (kart.get(r.mistakes) / 60) * dt) {
      if (kart.get(k.driftDir) !== 0) fluffDrift = true;
      else lapse = 0.6 + Math.random() * 0.8;
    }

    // How fast to go: the slowest of what it can carry through the corners ahead, allowing for the
    // braking it takes to get down to each, and its pace on the straight.
    const brakeRate = kart.get(r.braking);
    let target = kart.get(k.topSpeed) * kart.get(r.pace);
    const reach = 8 + Math.max(0, speed) * 1.6;
    const step = 2;
    let heading = flat(curve.directionAt(near.t));
    for (let s = step; lapse === 0 && s <= reach; s += step) {
      const next = flat(curve.directionAt(wrap(near.t + s / curve.length)));
      const radius = step / Math.max(Math.abs(turnOf(heading, next)), 1e-4);
      target = Math.min(target, Math.sqrt(grip * radius + 2 * brakeRate * Math.max(0, s - step)));
      heading = next;
    }
    target = Math.max(target, kart.get(k.driftMinSpeed) + 1);

    // The drift: into a long corner at speed, held while the road keeps turning the same way. Only
    // with the kart already steering into that corner and lined up with the road, so a drift never
    // starts while it is still catching the last one; and only where the road runs on fairly straight
    // after it, so the mini-turbo it ends with has room instead of firing the kart into the next bend.
    const drifting = kart.get(k.driftDir);
    const [nx, nz] = flat(curve.directionAt(near.t));
    const lined = Math.abs(turnOf(flat(forward), [nx, nz])) < 0.3;
    const after = lookAlong(curve, wrap(near.t + 20 / curve.length), 25, 2.5, grip);
    let drift = 0;
    if (drifting !== 0) {
      const still = lookAlong(curve, near.t, 10, 2, grip).turned * drifting;
      drift = still > 0.25 && !fluffDrift ? 1 : 0;
      // In a drift the stick tightens or opens it: tighten when the aim point is further inside.
      if (drift) steer = clamp(drifting * angle * kart.get(r.steering), -1, 1) * drifting;
      // A drift carves tighter than grip alone, so it can carry a little more speed.
      if (drift) target *= 1.15;
    } else if (
      Math.abs(corner.turned) > kart.get(r.driftTurn) &&
      lined &&
      Math.abs(after.turned) < 0.6 &&
      Math.sign(steer) === Math.sign(corner.turned) &&
      Math.abs(steer) > 0.35 &&
      speed > kart.get(k.driftMinSpeed) + 3
    ) {
      drift = 1;
      steer = Math.sign(corner.turned);
    }

    // Throttle up to the speed it wants, brake down to it; never both, and off the throttle in a boost
    // that is already too fast.
    const gas = speed < target ? clamp((target - speed) * 0.6, 0, 1) : 0;
    const brake = speed > target + 1 ? clamp((speed - target) * 0.4, 0, 1) : 0;

    // Lost: stopped, or a long way off the road, for too long once the race is on.
    let stuck = kart.get(r.stuck);
    stuck = racing && (Math.abs(speed) < 1 || Math.abs(near.offset) > 9) ? stuck + dt : 0;
    const respawn = stuck > kart.get(r.stuckAfter) ? 1 : 0;
    if (respawn) stuck = 0;

    kart.set(k.steerAsk, steer);
    kart.set(k.gasAsk, gas);
    kart.set(k.brakeAsk, brake);
    kart.set(k.driftAsk, drift);
    kart.set(k.respawnAsk, respawn);
    kart.set(r.stuck, stuck);
    kart.set(r.wanted, target);
    kart.set(r.shake, shake);
    kart.set(r.lapse, lapse);
  }
});
