// The grid: who drives which kart, and where the race starts. Eight karts, one for each racer; the
// players in the lobby drive the ones they picked (a player who picked none is given a free one), and
// the game drives the rest, each as its Rival card says. A player who leaves mid-race hands their kart
// to the game. When a race starts, the karts are shuffled onto the grid and every race number on them
// goes back to the start, and each kart takes its racer's handling (data/handling.ts); when the lobby
// comes back, they line up again.
//
// Runs in `act`, after the race rules, before anyone drives.
import { race, seats, players, pickOf, LOBBY } from "./state";
import { racer } from "../data/racers";
import { statsOf } from "../data/handling";

const K = pw.component("kart");
const driver = K.text("driver");
const k = Object.fromEntries(
  ["racer", "human", "progress", "lastT", "raceTime", "lapStart", "lastLap", "bestLap", "finished", "boost", "driftDir", "charge", "held", "airborne", "clock", "place", "steerAsk", "gasAsk", "brakeAsk", "driftAsk", "respawnAsk", "phase"].map((n) => [n, K.property(n)]),
);
const player = pw.field("controls", "player");
const mass = pw.field("rigid_body", "mass");
const STATS = ["topSpeed", "engineForce", "steerFast", "steerSlow", "driftTurn", "driftCarve"].map((n) => [n, K.property(n)]);

/** A kart takes its racer's handling: what the lobby's card shows is how it drives. */
function tune(kart) {
  const r = racer(kart.get(k.racer));
  if (r === undefined) return;
  const stats = statsOf(r);
  for (const [n, field] of STATS) kart.set(field, stats[n]);
  kart.set(mass, stats.mass);
}
const trackOf = pw.object("kart", "track");
const rotation = pw.quat("transform", "rotation");

/** The grid's eight places, front row first: two by two up the plateau, behind the kicker. */
const SLOTS = [
  [-1.8, 21],
  [1.8, 21],
  [-1.8, 24.5],
  [1.8, 24.5],
  [-1.8, 28],
  [1.8, 28],
  [-1.8, 31.5],
  [1.8, 31.5],
];

/** Who drives racer `n` this race: the seat that picked it, else 0 (the game). */
function driverOf(n, assigned) {
  for (const [seat, racer] of assigned) if (racer === n) return seat;
  return 0;
}

/** Each player in the lobby and the racer they drive: their pick, or the first one nobody has. */
function assign() {
  const assigned = new Map();
  for (const seat of players()) if (pickOf(seat) > 0) assigned.set(seat, pickOf(seat));
  const free = [1, 2, 3, 4, 5, 6, 7, 8].filter((n) => ![...assigned.values()].includes(n));
  for (const seat of players()) if (!assigned.has(seat)) assigned.set(seat, free.shift());
  return assigned;
}

function reset(kart) {
  for (const n of ["progress", "raceTime", "lapStart", "lastLap", "bestLap", "finished", "boost", "driftDir", "charge", "held", "airborne", "clock", "place", "steerAsk", "gasAsk", "brakeAsk", "driftAsk", "respawnAsk"]) kart.set(k[n], 0);
  kart.set(k.lastT, -1);
}

function park(kart, slot) {
  const track = kart.get(trackOf);
  const [x, z] = SLOTS[slot];
  // On the road's surface there: the centre line's height at the nearest point, a little above it.
  const y = track !== null && track.exists ? track.curve.closest([x, 2, z]).point[1] + 0.25 : 1.75;
  kart.rigidBody.teleport([x, y, z]);
  kart.rigidBody.velocity = [0, 0, 0];
  kart.rigidBody.angularVelocity = [0, 0, 0];
  kart.set(rotation, [0, 0, 0, 1]);
}

pw.registerSystem("grid", { includeComponents: ["kart", "controls", "rigid_body"] }, ({ objects }) => {
  const karts = [...objects];
  if (race.started) {
    const assigned = assign();
    // The grid order: shuffled, from the run's own seeded stream, so every machine agrees.
    const order = [...Array(karts.length).keys()];
    for (let i = order.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [order[i], order[j]] = [order[j], order[i]];
    }
    let i = 0;
    for (const kart of karts) {
      const seat = driverOf(kart.get(k.racer), assigned);
      kart.set(k.human, seat);
      kart.set(player, seat);
      reset(kart);
      tune(kart);
      park(kart, order[i] % SLOTS.length);
      kart.set(k.phase, race.phase);
      i += 1;
    }
    return;
  }
  if (race.backToLobby) {
    let i = 0;
    for (const kart of objects) {
      kart.set(k.human, 0);
      kart.set(player, 0);
      reset(kart);
      park(kart, i % SLOTS.length);
      kart.set(k.phase, race.phase);
      i += 1;
    }
    return;
  }
  // A player who has gone hands their kart to the game.
  for (const kart of objects) {
    const seat = kart.get(k.human);
    if (seat !== 0 && !(seats.get(seat)?.here ?? false)) {
      kart.set(k.human, 0);
      kart.set(player, 0);
    }
  }
  // Each kart shows the name of whoever drives it; a bot shows none.
  for (const kart of objects) {
    const called = kart.get(k.human) === 0 ? "" : (seats.get(kart.get(k.human))?.name ?? "");
    if (kart.get(driver) !== called) kart.set(driver, called);
  }
  if (race.phase === LOBBY) for (const kart of objects) kart.set(k.place, 0);
  for (const kart of objects) kart.set(k.phase, race.phase);
});
