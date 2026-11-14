// Who is in the game and what they chose. Each seat object carries a Controls card for its seat, and
// a player is on it while those controls read something (an empty seat reads null). A player leaving
// lets go of their racer. On their own machine a player enters the lobby from the title ("Single
// player") and goes back with "Back"; in a shared game the screens show the lobby straight away, and
// picking a racer, or the host starting the race (systems/race.ts), is what enters it. A racer is picked in the lobby only, and only if nobody else in
// the lobby has it.
//
// A pick is heard by everyone in the game: the racer says one of its lines (the library's
// "<Name> pick" sound picks which). Game code runs on every machine in step, so each plays it.
//
// Runs first in `act`, after systems/race.ts has read the race's phase.
import { race, seats, host, LOBBY } from "./state";
import { RACERS } from "../data/racers";

const S = pw.component("seat");
const here = S.property("here");
const entered = S.property("entered");
const picked = S.property("picked");
const ready = S.property("ready");
const countdown = S.property("countdown");
/** How long everyone must stay ready before the race starts, in seconds. */
const READY_WAIT = 3;
const player = pw.field("controls", "player");
const stick = pw.action("drive", "stick");
const callouts = RACERS.map((r) => pw.sound(`${r.name} pick`));
// The line each seat's last pick is saying, so picking again stops it rather than talking over it.
const saying = new Map();

pw.registerSystem("seats", { includeComponents: ["seat", "controls"], events: ["enter", "leave", "pick", "ready"] }, ({ objects, events }) => {
  seats.clear();
  for (const seat of objects) {
    const present = seat.get(stick) !== null;
    if (!present) {
      seat.set(entered, 0);
      seat.set(picked, 0);
      seat.set(ready, 0);
    }
    seat.set(here, present ? 1 : 0);
    seats.set(seat.get(player), { here: present, entered: seat.get(entered) === 1, picked: seat.get(picked), ready: seat.get(ready) === 1, object: seat });
  }
  for (const e of events) {
    const s = seats.get(e.seat);
    if (s === undefined || !s.here) continue;
    if (e.name === "enter") {
      s.entered = true;
      s.object.set(entered, 1);
    } else if (e.name === "ready" && race.phase === LOBBY) {
      // Ready is a toggle: pressing it again takes it back. Being ready is being in the lobby.
      s.ready = !s.ready;
      s.object.set(ready, s.ready ? 1 : 0);
      s.entered = true;
      s.object.set(entered, 1);
    } else if (e.name === "leave" && race.phase === LOBBY) {
      s.entered = false;
      s.picked = 0;
      s.ready = false;
      s.object.set(entered, 0);
      s.object.set(picked, 0);
      s.object.set(ready, 0);
      saying.get(e.seat)?.stop();
    } else if (e.name === "pick" && race.phase === LOBBY && e.racer >= 1 && e.racer <= 8) {
      const taken = [...seats.entries()].some(([n, o]) => n !== e.seat && o.here && o.entered && o.picked === e.racer);
      if (!taken) {
        s.entered = true;
        s.object.set(entered, 1);
        s.picked = e.racer;
        s.object.set(picked, e.racer);
        saying.get(e.seat)?.stop();
        saying.set(e.seat, pw.play(callouts[e.racer - 1]));
      }
    }
  }
  // Everyone in the lobby — whoever is on a seat — ready: a short countdown, on every seat for the
  // screens, and when it runs out the race starts (systems/race.ts). Everyone races, picked or not (a
  // player with no pick is given a free racer), and is not ready for the next one until they say so.
  race.startNow = false;
  const lobby = [...seats.values()].filter((s) => s.here);
  const allReady = race.phase === LOBBY && lobby.length > 0 && lobby.every((s) => s.ready);
  const was = lobby.reduce((most, s) => Math.max(most, s.object.get(countdown) ?? 0), 0);
  const left = !allReady ? 0 : was > 0 ? was - objects.dt : READY_WAIT;
  if (allReady && left <= 0) {
    race.startNow = true;
    for (const s of lobby) {
      s.entered = true;
      s.ready = false;
      s.object.set(entered, 1);
      s.object.set(ready, 0);
    }
  }
  for (const seat of objects) seat.set(countdown, allReady && left > 0 ? left : 0);
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
