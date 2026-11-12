// The race's phase, read off the race card at the top of every tick into systems/state.ts, for the
// tick's other systems. Runs first.
import { race } from "./state";

const phase = pw.field("race", "phase");

pw.registerSystem("race phase", { includeComponents: ["race"] }, ({ objects }) => {
  for (const r of objects) race.phase = r.get(phase);
  race.started = false;
  race.backToLobby = false;
});
