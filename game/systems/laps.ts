// Laps, counted along the track's centre line: each tick the kart's place on the closed curve (0 to 1)
// is compared with the last, and the difference added to how far round it has gone, so driving the
// wrong way takes laps back off and a shortcut across the infield counts only what it covers. The race
// clock runs until the last lap is done. A kart that falls off the world, or whose driver asks, is put
// back on the centre line where it left it, facing the way round. Then every kart is given its place:
// the finished in the order they finished, then the rest by how far round they are.
//
// Runs in `react`, after physics, so it reads where the kart ended up this tick.
const K = pw.component("kart");
const R = Object.fromEntries(
  ["laps", "progress", "lastT", "raceTime", "lapStart", "lastLap", "bestLap", "finished", "boost", "driftDir", "charge", "clock", "startDelay", "place", "respawnAsk"].map((n) => [n, K.property(n)]),
);
const trackOf = pw.object("kart", "track");
const position = pw.vec3("transform", "position");
const rotation = pw.quat("transform", "rotation");

pw.registerSystem("laps", { phase: "react", includeComponents: ["kart", "rigid_body"] }, ({ objects }) => {
  const dt = objects.dt;
  const field = [];
  for (const kart of objects) {
    field.push(kart);
    const clock = kart.get(R.clock) + dt;
    kart.set(R.clock, clock);
    const track = kart.get(trackOf);
    if (track === null || !track.exists) continue;
    const at = kart.get(position);
    const near = track.curve.closest(at);

    let progress = kart.get(R.progress);
    const last = kart.get(R.lastT);
    // On the grid: just behind the line counts as a little short of no way round at all.
    if (last < 0) progress = near.t > 0.5 ? near.t - 1 : near.t;
    else {
      let d = near.t - last;
      if (d < -0.5) d += 1;
      if (d > 0.5) d -= 1;
      progress += d;
    }
    const laps = kart.get(R.laps);
    const time = kart.get(R.raceTime);
    const finished = kart.get(R.finished);
    // A lap is done when the kart has gone round once more than it had at the lap's start.
    const lapsDone = Math.max(0, Math.floor(progress));
    const before = Math.max(0, Math.floor(kart.get(R.progress)));
    if (finished === 0 && lapsDone > before) {
      const lap = time - kart.get(R.lapStart);
      kart.set(R.lastLap, lap);
      if (kart.get(R.bestLap) === 0 || lap < kart.get(R.bestLap)) kart.set(R.bestLap, lap);
      kart.set(R.lapStart, time);
      if (lapsDone >= laps) kart.set(R.finished, time);
    }
    kart.set(R.progress, progress);
    kart.set(R.lastT, near.t);
    if (finished === 0 && clock >= kart.get(R.startDelay)) kart.set(R.raceTime, time + dt);

    // Back on the road: below the world, or asked for.
    if (at[1] < -5 || kart.get(R.respawnAsk) > 0) {
      const [x, y, z] = track.curve.at(near.t);
      const [dx, , dz] = track.curve.directionAt(near.t);
      kart.rigidBody.teleport([x, y + 0.6, z]);
      kart.rigidBody.velocity = [0, 0, 0];
      kart.rigidBody.angularVelocity = [0, 0, 0];
      kart.set(rotation, pw.axisAngle([0, 1, 0], Math.atan2(-dx, -dz)));
      kart.set(R.boost, 0);
      kart.set(R.driftDir, 0);
      kart.set(R.charge, 0);
    }
  }

  // Places: finished karts by when they finished, then the rest by how far round they are.
  field.sort((a, b) => {
    const fa = a.get(R.finished);
    const fb = b.get(R.finished);
    if (fa > 0 || fb > 0) return fa > 0 && fb > 0 ? fa - fb : fa > 0 ? -1 : 1;
    return b.get(R.progress) - a.get(R.progress);
  });
  field.forEach((kart, i) => kart.set(R.place, i + 1));
});
