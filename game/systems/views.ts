// What each player looks through: in a race, the chase camera behind their own kart; watching a race
// they are not in, the leader's, through to the results; in the lobby, the scene's own camera on the grid.
//
// Runs in `react`, after the cameras have followed their karts.
import { race, seats, LOBBY } from "./state";

const targetOf = pw.object("chaseCamera", "target");
const human = pw.field("kart", "human");
const place = pw.field("kart", "place");

pw.registerSystem("views", { phase: "react", includeComponents: ["chaseCamera"] }, ({ objects }) => {
  const mine = new Map();
  let leader = null;
  for (const cam of objects) {
    const kart = cam.get(targetOf);
    if (kart === null || !kart.exists) continue;
    if (kart.get(human) !== 0) mine.set(kart.get(human), cam);
    if (kart.get(place) === 1) leader = cam;
  }
  for (const [seat, s] of seats) {
    if (!s.here) continue;
    if (race.phase === LOBBY) pw.view.set(seat, null);
    else pw.view.set(seat, mine.get(seat) ?? leader);
  }
});
