// Laps, counted along the track's centre line: each tick the kart's place on the closed curve (0 to 1)
// is compared with the last, and the difference added to how far round it has gone, so driving the
// wrong way takes laps back off and a shortcut across the infield counts only what it covers. The race
// clock runs until the last lap is done. A kart that falls off the world, or whose driver asks, is put
// back on the centre line where it left it, facing the way round.
//
// Runs in `react`, after physics, so it reads where the kart ended up this tick.
const K = pw.component("kart");
const R = Object.fromEntries(
  ["laps", "progress", "lastT", "raceTime", "lapStart", "lastLap", "bestLap", "finished", "boost", "driftDir", "charge"].map((n) => [n, K.property(n)]),
);
const trackOf = pw.object("kart", "track");
const position = pw.vec3("transform", "position");
const rotation = pw.quat("transform", "rotation");
const respawn = pw.action("drive", "respawn");

pw.registerSystem("laps", { phase: "react", includeComponents: ["kart", "rigid_body", "controls"] }, ({ objects }) => {
  const dt = objects.dt;
  for (const kart of objects) {
    const track = kart.get(trackOf);
    if (track === null || !track.exists) continue;
    const at = kart.get(position);
    const near = track.curve.closest(at);

    let progress = kart.get(R.progress);
    const last = kart.get(R.lastT);
    if (last >= 0) {
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
    if (finished === 0) kart.set(R.raceTime, time + dt);

    // Back on the road: below the world, or asked for.
    if (at[1] < -5 || kart.get(respawn) === true) {
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
});
