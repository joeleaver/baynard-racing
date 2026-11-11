// The chase camera: behind the kart and above it, looking a little ahead of it. It swings round after
// the kart's heading rather than snapping to it, so a drift shows the kart turned across the road.
//
// Runs in `react`, after physics, so it follows where the kart ended up this tick.
const C = pw.component("chaseCamera");
const R = Object.fromEntries(["distance", "height", "lookHeight", "lookAhead", "follow", "swing", "yaw", "placed"].map((n) => [n, C.property(n)]));
const targetOf = pw.object("chaseCamera", "target");
const position = pw.vec3("transform", "position");
const rotation = pw.quat("transform", "rotation");

const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const closing = (rate, dt) => 1 - Math.exp(-rate * dt);

pw.registerSystem("chase camera", { phase: "react", includeComponents: ["chaseCamera"] }, ({ objects }) => {
  const dt = objects.dt;
  for (const cam of objects) {
    const kart = cam.get(targetOf);
    if (kart === null || !kart.exists) continue;
    const g = (n) => cam.get(R[n]);
    const at = kart.get(position);
    const nose = pw.rotateVector([0, 0, -1], kart.get(rotation));
    const heading = Math.atan2(-nose[0], -nose[2]);
    const first = g("placed") === 0;
    const yaw = first ? heading : wrap(g("yaw") + wrap(heading - g("yaw")) * closing(g("swing"), dt));
    const back = [Math.sin(yaw) * g("distance"), 0, Math.cos(yaw) * g("distance")];
    const wanted = [at[0] + back[0], at[1] + g("height"), at[2] + back[2]];
    const was = cam.get(position);
    const k = first ? 1 : closing(g("follow"), dt);
    const eye = [was[0] + (wanted[0] - was[0]) * k, was[1] + (wanted[1] - was[1]) * k, was[2] + (wanted[2] - was[2]) * k];
    cam.set(position, eye);
    const v = kart.rigidBody.velocity;
    const ahead = g("lookAhead");
    cam.lookAt([at[0] + v[0] * ahead, at[1] + g("lookHeight"), at[2] + v[2] * ahead]);
    cam.set(R.yaw, yaw);
    cam.set(R.placed, 1);
  }
});
