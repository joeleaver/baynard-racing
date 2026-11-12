// A kart: its stats (how it drives, drifts and boosts) and what it is doing. It rides on the engine's
// Vehicle and Wheels; everything arcade about it is here and in systems/kart.ts.
const stat = (value, unit, doc) => pw.float(value, { ...(unit ? { unit } : {}), group: "Stats", doc });
const doing = (value, doc) => pw.float(value, { group: "Doing", doc });

pw.defineComponent("kart", {
  track: pw.object({ group: "Links", doc: "The track's centre line (a closed Curve): laps are counted along it." }),
  laps: pw.int(3, { group: "Race", doc: "Laps in a race." }),
  startDelay: pw.float(3, { unit: "s", group: "Race", doc: "The countdown before the start: every kart waits on its brakes." }),

  engineForce: stat(520, "N", "The push at each driving tyre, flat out from a standstill."),
  topSpeed: stat(21, "m/s", "Where the engine runs out of push."),
  reverseForce: stat(260, "N", "The push backwards."),
  brakeForce: stat(700, "N", "How hard each tyre brakes."),
  steerSlow: stat(0.5, "rad", "How far the front wheels turn at a crawl."),
  steerFast: stat(0.2, "rad", "How far they turn flat out."),
  grassSpeed: stat(0.55, "", "The share of top speed left on grass."),
  padBoost: stat(0.8, "s", "How long a boost pad's boost lasts."),

  hop: stat(210, "N·s", "The kick up when a drift starts."),
  driftMinSpeed: stat(7, "m/s", "Slower than this, a drift ends."),
  driftSteer: stat(0.22, "rad", "How far the wheels turn into a drift held straight."),
  driftRange: stat(0.2, "rad", "How far the stick tightens or opens a drift."),
  driftTurn: stat(1.1, "rad/s", "How fast a drift held straight turns the kart."),
  driftTurnRange: stat(0.7, "rad/s", "How much the stick quickens or slows that turn."),
  driftAngle: stat(28, "°", "How far across its path a drift lets the kart swing, at most."),
  driftHold: stat(1000, "N·m·s", "How firmly the drift keeps to its turn."),
  driftCarve: stat(450, "N", "The pull toward the inside of a drift, so it turns tighter than grip alone."),
  tierTimes: stat(0.9, "s", "How long a drift takes to reach each spark tier (blue, orange, purple)."),
  boostForce: stat(1500, "N", "The push of a mini-turbo."),
  boostSpeed: stat(6, "m/s", "How much a mini-turbo raises top speed."),
  boostTimes: stat(0.5, "s", "How long a tier-one mini-turbo lasts; each tier adds as much again."),

  driftDir: doing(0, "-1 drifting left, 1 right, 0 not drifting."),
  charge: doing(0, "Seconds of drift built up."),
  boost: doing(0, "Seconds of boost left."),
  held: doing(0, "1 while drift is held."),
  airborne: doing(0, "Seconds since the kart last touched the ground."),
  progress: doing(0, "Laps driven, as a number: 1.5 is half way round the second."),
  lastT: doing(-1, "Where on the track it was last tick, 0 to 1; -1 before the start."),
  raceTime: doing(0, "Seconds since the start."),
  lapStart: doing(0, "When the lap being driven started."),
  lastLap: doing(0, "The last lap's time."),
  bestLap: doing(0, "The best lap's time."),
  finished: doing(0, "When the race was finished, 0 until then."),
  speed: doing(0, "How fast it is going along its nose."),
  clock: doing(0, "Seconds since Play, countdown included."),
  place: doing(0, "Where it is in the race: 1 leads; 0 before the first count."),

  // What its driver asks for this tick, written by systems/driver.ts or systems/rivals.ts.
  steerAsk: pw.float(0, { group: "Asks", doc: "Steering, -1 full left to 1 full right." }),
  gasAsk: pw.float(0, { group: "Asks", doc: "Throttle, 0 to 1." }),
  brakeAsk: pw.float(0, { group: "Asks", doc: "Brake, then reverse, 0 to 1." }),
  driftAsk: pw.float(0, { group: "Asks", doc: "1 while drift is held." }),
  respawnAsk: pw.float(0, { group: "Asks", doc: "1 to be put back on the road." }),
});
