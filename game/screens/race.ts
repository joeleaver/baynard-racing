// The race read-out: the countdown; your place; the field in race order down the left, as faces (yours
// ringed in yellow, other players' in blue); the lap and the clock; the speed; and the drift's sparks
// and the mini-turbo. A player watching a race they are not in is told they'll race in the next one.
import { box, label, image } from "@pw/ui";
import { RACERS, ordinal, clock } from "../data/racers";

const K = pw.component("kart");
const p = (n) => K.property(n);
const [laps, progress, raceTime, bestLap, finished, charge, driftDir, boost, speed, tierTimes, place, clockOf, startDelay, phase, racerOf, human] =
  ["laps", "progress", "raceTime", "bestLap", "finished", "charge", "driftDir", "boost", "speed", "tierTimes", "place", "clock", "startDelay", "phase", "racer", "human"].map(p);
const heads = RACERS.map((r) => pw.image(`${r.name} headshot`));
const SPARKS = [null, ["blue", "Blue sparks"], ["orange", "Orange sparks"], ["purple", "Purple sparks"]];

pw.screen("race", { includeComponents: [K] }, ({ seat, objects }) => {
  if (objects.length === 0 || objects[0].get(phase) !== 1) return [];
  const order = [...objects].filter((k) => k.get(place) > 0).sort((a, b) => a.get(place) - b.get(place));
  const strip = box({ class: "order" }, order.map((k) => {
    const who = k.get(human);
    const cls = who === seat.player ? "slot mine" : who > 0 ? "slot player" : "slot";
    return box({ class: cls }, [label({ class: "slotpos" }, `${k.get(place)}`), image(heads[k.get(racerOf) - 1], { class: "slothead" })]);
  }));

  const kart = seat.objects[0];
  if (kart === undefined) return [strip, box({ class: "banner" }, [label({ class: "bannerchip" }, "Race in progress. You'll race in the next one.")])];

  const out = [strip];
  const toGo = kart.get(startDelay) - kart.get(clockOf);
  if (toGo > -1) out.push(label({ class: "countdown" }, toGo > 0 ? `${Math.ceil(toGo)}` : "Go!"));
  out.push(box({ class: "place" }, [label({ class: "placebig" }, kart.get(place) > 0 ? ordinal(kart.get(place)) : "-"), label({ class: "placeof" }, `of ${objects.length}`)]));

  const total = kart.get(laps);
  const done = kart.get(finished) > 0;
  const lap = Math.min(total, Math.max(1, Math.floor(kart.get(progress)) + 1));
  out.push(box({ class: "lapbox" }, [
    label({ class: "lap" }, done ? "Finished" : `Lap ${lap}/${total}`),
    label({ class: "time" }, clock(done ? kart.get(finished) : kart.get(raceTime))),
    label({ class: "best" }, `Best lap ${clock(kart.get(bestLap))}`),
  ]));
  out.push(box({ class: "speedo" }, [label({ class: "speed" }, `${Math.round(Math.abs(kart.get(speed)) * 3.6)}`), label({ class: "unit" }, "km/h")]));

  const tier = kart.get(driftDir) === 0 ? 0 : Math.min(3, Math.floor(kart.get(charge) / kart.get(tierTimes)));
  if (kart.get(boost) > 0) out.push(box({ class: "spark" }, [label({ class: "chip turbo" }, "Mini-turbo!")]));
  else if (tier > 0) out.push(box({ class: "spark" }, [label({ class: `chip ${SPARKS[tier][0]}` }, SPARKS[tier][1])]));
  if (done) out.push(box({ class: "banner" }, [label({ class: "bannerchip" }, "Finished! Waiting for the others.")]));
  return out;
});
