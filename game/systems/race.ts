// The race's rules: the lobby until the host starts it, then the race, then the results once every kart
// has finished or the rest have had long enough after the winner, then the lobby again when the host
// says so. A race nobody is in any more goes back to the lobby.
//
// Runs in `act` after the seats are counted (systems/race_phase.ts read the phase at the top of the
// tick), and changes the phase.
import { race, players, host, LOBBY, RACING, RESULTS } from "./state";

const R = pw.component("race");
const p = Object.fromEntries(["phase", "host", "firstFinish", "allDone", "clock", "wait"].map((n) => [n, R.property(n)]));

pw.registerSystem("race rules", { includeComponents: ["race"], events: ["start", "again"] }, ({ objects, events }) => {
  const dt = objects.dt;
  const boss = host();
  for (const r of objects) {
    r.set(p.host, boss);
    const said = (name) => events.some((e) => e.name === name && e.seat === boss);
    let phase = r.get(p.phase);
    if (phase === LOBBY && boss !== 0 && said("start")) {
      phase = RACING;
      race.started = true;
      r.set(p.clock, 0);
      r.set(p.firstFinish, 0);
      r.set(p.allDone, 0);
    } else if (phase === RACING) {
      const clock = r.get(p.clock) + dt;
      r.set(p.clock, clock);
      const first = r.get(p.firstFinish);
      if (r.get(p.allDone) === 1 || (first > 0 && clock - first > r.get(p.wait))) phase = RESULTS;
    } else if (phase === RESULTS && said("again")) {
      phase = LOBBY;
      race.backToLobby = true;
    }
    // Everybody left: back to an empty lobby.
    if (phase !== LOBBY && players().length === 0) {
      phase = LOBBY;
      race.backToLobby = true;
    }
    r.set(p.phase, phase);
    race.phase = phase;
  }
});

// After the laps are counted: when the first kart finished, and whether they all have.
const K = pw.component("kart");
const finished = K.property("finished");
let firstFinish = 0;
let allDone = 0;
pw.registerSystem("finishes", { phase: "react", includeComponents: ["kart"] }, ({ objects }) => {
  firstFinish = 0;
  allDone = 1;
  for (const kart of objects) {
    const f = kart.get(finished);
    if (f > 0 && (firstFinish === 0 || f < firstFinish)) firstFinish = f;
    if (f === 0) allDone = 0;
  }
});
pw.registerSystem("race finishes", { phase: "react", includeComponents: ["race"] }, ({ objects }) => {
  for (const r of objects) {
    if (r.get(p.phase) !== RACING) continue;
    // On the race clock, so the wait for the rest counts from the moment the winner crossed the line.
    if (firstFinish > 0 && r.get(p.firstFinish) === 0) r.set(p.firstFinish, r.get(p.clock));
    r.set(p.allDone, allDone);
  }
});
