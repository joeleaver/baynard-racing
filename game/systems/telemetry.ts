// Logs a kart's motion and each wheel's contact every tick, for any object carrying a Telemetry card:
//   K <tick> <label> <height> <up speed> <speed> <pitch°> <roll°> <drift> <progress>
//   W <tick> <label> <on ground> <compression> <load>
// Runs in `react`, after physics. Nothing carries a Telemetry card in the scene as shipped; put one on
// the kart and its wheels to measure a run.
const label = pw.field("telemetry", "label");
const position = pw.vec3("transform", "position");
const rotation = pw.quat("transform", "rotation");
const speed = pw.field("kart", "speed");
const driftDir = pw.field("kart", "driftDir");
const progress = pw.field("kart", "progress");
let tick = 0;
const deg = (r) => ((r * 180) / Math.PI).toFixed(1);

pw.registerSystem("telemetry karts", { phase: "react", includeComponents: ["telemetry", "kart", "rigid_body"] }, ({ objects }) => {
  tick += 1;
  for (const k of objects) {
    const rot = k.get(rotation);
    const fwd = pw.rotateVector([0, 0, -1], rot);
    const right = pw.rotateVector([1, 0, 0], rot);
    const at = k.get(position);
    const v = k.rigidBody.velocity;
    console.log(`K ${tick} ${k.get(label)} ${at[1].toFixed(3)} ${v[1].toFixed(2)} ${k.get(speed).toFixed(2)} ${deg(Math.asin(fwd[1]))} ${deg(Math.asin(right[1]))} ${k.get(driftDir)} ${k.get(progress).toFixed(4)}`);
  }
});

pw.registerSystem("telemetry wheels", { phase: "react", includeComponents: ["telemetry", "wheel"] }, ({ objects }) => {
  for (const w of objects) {
    console.log(`W ${tick} ${w.get(label)} ${w.wheel.onGround ? 1 : 0} ${w.wheel.compression.toFixed(3)} ${w.wheel.load.toFixed(0)}`);
  }
});
