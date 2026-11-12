// A player driving: their controls become the kart's asks. The stick steers with x; pushed forward it
// is the throttle and pulled back the brake, then reverse, and a gamepad's triggers are those too.
//
// Runs in `act`, before the kart reads its asks.
const K = pw.component("kart");
const ask = Object.fromEntries(["steerAsk", "gasAsk", "brakeAsk", "driftAsk", "respawnAsk"].map((n) => [n, K.property(n)]));
const stick = pw.action("drive", "stick");
const gas = pw.action("drive", "gas");
const brake = pw.action("drive", "brake");
const drift = pw.action("drive", "drift");
const respawn = pw.action("drive", "respawn");

const human = K.property("human");

pw.registerSystem("driver", { includeComponents: ["kart", "controls"] }, ({ objects }) => {
  for (const kart of objects) {
    // The game drives a kart no player has (systems/rivals.ts).
    if (kart.get(human) === 0) continue;
    const [sx, sy] = kart.get(stick) ?? [0, 0];
    kart.set(ask.steerAsk, sx);
    kart.set(ask.gasAsk, Math.max(sy, kart.get(gas) ?? 0, 0));
    kart.set(ask.brakeAsk, Math.max(-sy, kart.get(brake) ?? 0, 0));
    kart.set(ask.driftAsk, kart.get(drift) === true ? 1 : 0);
    kart.set(ask.respawnAsk, kart.get(respawn) === true ? 1 : 0);
  }
});
