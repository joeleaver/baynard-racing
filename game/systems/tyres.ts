// A drifting kart's tyres let go: a tyre on a kart that is drifting takes its drift grip sideways, and
// its own grip again once the drift ends. The slide that follows is the engine's tyre physics.
const T = pw.component("tyre");
const kartOf = pw.object("tyre", "kart");
const grip = T.property("grip");
const slideGrip = T.property("slideGrip");
const driftGrip = T.property("driftGrip");
const driftSlideGrip = T.property("driftSlideGrip");
const peak = pw.field("wheel", "sideways_peak_grip");
const slide = pw.field("wheel", "sideways_slide_grip");
const driftDir = pw.field("kart", "driftDir");

pw.registerSystem("tyres", { includeComponents: ["tyre", "wheel"] }, ({ objects }) => {
  for (const tyre of objects) {
    const kart = tyre.get(kartOf);
    const drifting = kart !== null && kart.exists && kart.get(driftDir) !== 0;
    tyre.set(peak, tyre.get(drifting ? driftGrip : grip));
    tyre.set(slide, tyre.get(drifting ? driftSlideGrip : slideGrip));
  }
});
