// Driving a kart: the stick turns into the Vehicle's engine force, brake and steer, and the arcade
// layer goes on top — a drift (hop in, the wheels turned into the corner, the tail swung out, sparks
// building through three tiers) and the mini-turbo when it is let go. The grip itself is the tyres'
// (systems/tyres.ts lowers the rear tyres' sideways grip while drifting), so the slide is physics.
//
// Runs in `act`, before physics, reading the world the last step left.

const K = pw.component("kart");
const R = Object.fromEntries(
  ["laps", "engineForce", "topSpeed", "reverseForce", "brakeForce", "steerSlow", "steerFast", "grassSpeed", "hop",
    "driftMinSpeed", "driftSteer", "driftRange", "driftTurn", "driftTurnRange", "driftAngle", "driftHold", "driftCarve", "tierTimes", "boostForce", "boostSpeed", "boostTimes",
    "driftDir", "charge", "boost", "held", "airborne", "speed"].map((n) => [n, K.property(n)]),
);
const position = pw.vec3("transform", "position");
const rotation = pw.quat("transform", "rotation");
const stick = pw.action("drive", "stick");
const gas = pw.action("drive", "gas");
const brake = pw.action("drive", "brake");
const drift = pw.action("drive", "drift");

/** Which spark tier a drift of `charge` seconds has reached: 0 none, 1 blue, 2 orange, 3 purple. */
export function tierOf(charge, step) {
  return Math.min(3, Math.floor(charge / step));
}

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

pw.registerSystem("kart", { includeComponents: ["kart", "vehicle", "rigid_body", "controls"] }, ({ objects, physics }) => {
  const dt = objects.dt;
  for (const kart of objects) {
    const g = (n) => kart.get(R[n]);
    const [sx, sy] = kart.get(stick) ?? [0, 0];
    const throttle = Math.max(sy, kart.get(gas) ?? 0, 0);
    const braking = Math.max(-sy, kart.get(brake) ?? 0, 0);
    const holding = kart.get(drift) === true;

    const rot = kart.get(rotation);
    const forward = pw.rotateVector([0, 0, -1], rot);
    const up = pw.rotateVector([0, 1, 0], rot);
    const right = pw.rotateVector([1, 0, 0], rot);
    const body = kart.rigidBody;
    const v = body.velocity;
    const speed = dot(v, forward);

    // What it stands on, straight down from its middle.
    const at = kart.get(position);
    const ground = physics.ray([at[0], at[1] + 0.5, at[2]], [-up[0], -up[1], -up[2]], 1.2, { exclude: kart });
    const onGround = ground !== null;
    const airborne = onGround ? 0 : g("airborne") + dt;
    const grass = ground !== null && ground.surface === "grass";

    // The engine runs out of push toward top speed (lower on grass, higher in a boost).
    let boost = Math.max(0, g("boost") - dt);
    const top = g("topSpeed") * (grass ? g("grassSpeed") : 1) + (boost > 0 ? g("boostSpeed") : 0);
    let engine = 0;
    let brakeForce = 0;
    if (throttle > 0) engine = g("engineForce") * throttle * clamp(1 - speed / top, -1, 1);
    if (braking > 0) {
      if (speed > 0.5) brakeForce = g("brakeForce") * braking;
      else engine = -g("reverseForce") * braking * clamp(1 + speed / 6, 0, 1);
    }

    // Steering: less of it the faster it goes, as a real kart needs.
    const fast = clamp(Math.abs(speed) / g("topSpeed"), 0, 1);
    let steer = -sx * (g("steerSlow") + (g("steerFast") - g("steerSlow")) * fast);

    // The drift: held with a direction at speed, it hops in. Held, the wheels stay turned into the
    // corner (the stick only tightens or opens it), the tail is swung out, and sparks build. Let go,
    // and the tier reached is a mini-turbo.
    let dir = g("driftDir");
    let charge = g("charge");
    const pressed = holding && g("held") === 0;
    if (dir === 0 && pressed && onGround && speed > g("driftMinSpeed") && Math.abs(sx) > 0.3) {
      dir = sx > 0 ? 1 : -1;
      charge = 0;
      body.applyImpulse([up[0] * g("hop"), up[1] * g("hop"), up[2] * g("hop")]);
    }
    if (dir !== 0) {
      const stillDrifting = holding && speed > g("driftMinSpeed") && airborne < 0.6;
      if (stillDrifting) {
        const tighten = clamp(sx * dir, -1, 1);
        // How far the nose is swung across the kart's path, into the drift (radians).
        const swung = Math.atan2(-dot(v, right), Math.max(Math.abs(speed), 0.1)) * dir;
        const target = ((g("driftAngle") * Math.PI) / 180) * (0.7 + 0.3 * tighten);
        // The front wheels counter-steer for the driver: they follow the kart's path, turned into the
        // corner by the drift's steer, so the slide holds instead of spinning.
        steer = clamp(dir * swung - dir * (g("driftSteer") + g("driftRange") * tighten), -0.7, 0.7);
        if (onGround) {
          charge += dt * (1 + 0.5 * Math.max(0, tighten));
          // Turn at the drift's rate, and swing the tail out to the drift's angle and no further.
          const rate = -dir * (g("driftTurn") + g("driftTurnRange") * tighten);
          const wanted = rate - dir * 6 * (target - swung);
          const yaw = g("driftHold") * (wanted - dot(body.angularVelocity, up));
          body.applyTorque([up[0] * yaw, up[1] * yaw, up[2] * yaw]);
          // And carve: a pull toward the inside of the turn, across the kart's path.
          const flat = Math.hypot(v[0], v[2]);
          if (flat > 1) {
            const pull = g("driftCarve") * (0.6 + 0.4 * tighten) * clamp(speed / g("topSpeed"), 0, 1);
            // The inside of a right drift is to the right of the path: (−vz, vx) turned the drift's way.
            const ix = (dir * -v[2]) / flat;
            const iz = (dir * v[0]) / flat;
            body.applyForce([ix * pull, 0, iz * pull]);
          }
        }
      } else {
        const tier = tierOf(charge, g("tierTimes"));
        if (tier > 0 && holding === false) boost = Math.max(boost, g("boostTimes") * tier);
        dir = 0;
        charge = 0;
      }
    }
    if (boost > 0 && onGround) {
      // Along the way the kart is going, not where its nose points: a drift ends with the nose turned
      // into the corner, and a push that way would fire the kart into the inside wall.
      const f = g("boostForce");
      const going = Math.hypot(v[0], v[1], v[2]);
      const along = going > 2 ? [v[0] / going, v[1] / going, v[2] / going] : forward;
      body.applyForce([along[0] * f, along[1] * f, along[2] * f]);
    }

    kart.vehicle.engineForce = engine;
    kart.vehicle.brake = brakeForce;
    kart.vehicle.steer = steer;
    kart.set(R.driftDir, dir);
    kart.set(R.charge, charge);
    kart.set(R.boost, boost);
    kart.set(R.held, holding ? 1 : 0);
    kart.set(R.airborne, airborne);
    kart.set(R.speed, speed);
  }
});
