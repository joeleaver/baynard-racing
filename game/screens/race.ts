// The race read-out: the lap, the clock, the last and best laps, the speed, and the drift's sparks.
import { row, label, value } from "@pw/ui";

const K = pw.component("kart");
const p = (n) => K.property(n);
const [laps, progress, raceTime, lastLap, bestLap, finished, charge, driftDir, boost, speed, tierTimes] =
  ["laps", "progress", "raceTime", "lastLap", "bestLap", "finished", "charge", "driftDir", "boost", "speed", "tierTimes"].map(p);

const clock = (s) => (s <= 0 ? "-" : `${Math.floor(s / 60)}:${(s % 60).toFixed(2).padStart(5, "0")}`);
const SPARKS = ["", "blue sparks", "orange sparks", "purple sparks"];

pw.screen("race", { includeComponents: [K] }, ({ seat }) =>
  seat.objects.flatMap((kart) => {
    const total = kart.get(laps);
    const done = kart.get(finished) > 0;
    const lap = Math.min(total, Math.max(1, Math.floor(kart.get(progress)) + 1));
    const tier = kart.get(driftDir) === 0 ? 0 : Math.min(3, Math.floor(kart.get(charge) / kart.get(tierTimes)));
    const rows = [
      row([label(done ? "Finished" : "Lap"), value(done ? clock(kart.get(finished)) : `${lap} / ${total}`)]),
      row([label("Time"), value(clock(kart.get(raceTime)))]),
      row([label("Last lap"), value(clock(kart.get(lastLap)))]),
      row([label("Best lap"), value(clock(kart.get(bestLap)))]),
      row([label("Speed"), value(`${Math.round(Math.abs(kart.get(speed)) * 3.6)} km/h`)]),
    ];
    if (kart.get(boost) > 0) rows.push(row([label("Mini-turbo!"), value("")]));
    else if (kart.get(driftDir) !== 0) rows.push(row([label("Drift"), value(tier > 0 ? SPARKS[tier] : "...")]));
    return rows;
  }));
