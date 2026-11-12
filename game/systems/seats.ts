// Who is in the game and what they chose. Each seat object carries a Controls card for its seat, and
// a player is on it while those controls read something (an empty seat reads null). A player leaving
// lets go of their racer; one coming past the title screen enters the lobby; a racer is picked in the
// lobby only, and only if nobody else in the lobby has it.
//
// Runs first in `act`, after systems/race.ts has read the race's phase.
import { race, seats, host, LOBBY } from "./state";

const S = pw.component("seat");
const here = S.property("here");
const entered = S.property("entered");
const picked = S.property("picked");
const player = pw.field("controls", "player");
const stick = pw.action("drive", "stick");

pw.registerSystem("seats", { includeComponents: ["seat", "controls"], events: ["enter", "pick"] }, ({ objects, events }) => {
  seats.clear();
  for (const seat of objects) {
    const present = seat.get(stick) !== null;
    if (!present) {
      seat.set(entered, 0);
      seat.set(picked, 0);
    }
    seat.set(here, present ? 1 : 0);
    seats.set(seat.get(player), { here: present, entered: seat.get(entered) === 1, picked: seat.get(picked), object: seat });
  }
  for (const e of events) {
    const s = seats.get(e.seat);
    if (s === undefined || !s.here) continue;
    if (e.name === "enter") {
      s.entered = true;
      s.object.set(entered, 1);
    } else if (e.name === "pick" && race.phase === LOBBY && s.entered && e.racer >= 1 && e.racer <= 8) {
      const taken = [...seats.entries()].some(([n, o]) => n !== e.seat && o.here && o.entered && o.picked === e.racer);
      if (!taken) {
        s.picked = e.racer;
        s.object.set(picked, e.racer);
      }
    }
  }
});

// After the race rules: the phase and the host, copied onto each seat for the screens.
const phase = S.property("phase");
const hostOf = S.property("host");
pw.registerSystem("seats show", { phase: "react", includeComponents: ["seat"] }, ({ objects }) => {
  const boss = host();
  for (const seat of objects) {
    seat.set(phase, race.phase);
    seat.set(hostOf, boss);
  }
});
