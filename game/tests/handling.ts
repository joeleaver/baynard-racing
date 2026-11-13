// How the karts feel to drive: a player on the keys and one on a gamepad, three laps each in Hettie's
// kart, counting how often the kart spins round. Run with balance.ts for every racer.
import { startRace, drive, report } from "./driver";

test("Hettie on the keys", (game) => {
  startRace(game, 1);
  const r = drive(game, 1, "keys");
  console.log(report(r));
  expect(r.finished).toBeGreaterThan(0);
});

test("Hettie on a gamepad", (game) => {
  startRace(game, 1);
  const r = drive(game, 1, "smooth");
  console.log(report(r));
  expect(r.finished).toBeGreaterThan(0);
});
