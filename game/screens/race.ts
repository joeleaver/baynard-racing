// The race read-out: the countdown, the place, the lap, the clock, the last and best laps, the speed,
// and the drift's sparks.
import { row, box, label, value, styles } from "@pw/ui";

styles(`
.countdown { position: fixed; top: 22%; left: 0; width: 100vw; text-align: center; font-size: 120px; font-weight: 800; color: #fff6d8; text-shadow: 0 6px 0 #7a3b12, 0 0 24px #0008; }
.place { font-size: 44px; font-weight: 800; }
`);

const K = pw.component("kart");
const p = (n) => K.property(n);
const [laps, progress, raceTime, lastLap, bestLap, finished, charge, driftDir, boost, speed, tierTimes, place, clockOf, startDelay] =
  ["laps", "progress", "raceTime", "lastLap", "bestLap", "finished", "charge", "driftDir", "boost", "speed", "tierTimes", "place", "clock", "startDelay"].map(p);

const clock = (s) => (s <= 0 ? "-" : `${Math.floor(s / 60)}:${(s % 60).toFixed(2).padStart(5, "0")}`);
const SPARKS = ["", "blue sparks", "orange sparks", "purple sparks"];
const ordinal = (n) => `${n}${n % 10 === 1 && n % 100 !== 11 ? "st" : n % 10 === 2 && n % 100 !== 12 ? "nd" : n % 10 === 3 && n % 100 !== 13 ? "rd" : "th"}`;

pw.screen("race", { includeComponents: [K] }, ({ seat, objects }) =>
  seat.objects.flatMap((kart) => {
    const total = kart.get(laps);
    const done = kart.get(finished) > 0;
    const lap = Math.min(total, Math.max(1, Math.floor(kart.get(progress)) + 1));
    const tier = kart.get(driftDir) === 0 ? 0 : Math.min(3, Math.floor(kart.get(charge) / kart.get(tierTimes)));
    const rows = [];
    // Three, two, one, and "Go!" for a second after the start.
    const toGo = kart.get(startDelay) - kart.get(clockOf);
    if (toGo > -1) rows.push(box({ class: "countdown" }, [label(toGo > 0 ? `${Math.ceil(toGo)}` : "Go!")]));
    if (kart.get(place) > 0) rows.push(row([label({ class: "place" }, ordinal(kart.get(place))), value(`/ ${objects.length}`)]));
    rows.push(
      row([label(done ? "Finished" : "Lap"), value(done ? clock(kart.get(finished)) : `${lap} / ${total}`)]),
      row([label("Time"), value(clock(kart.get(raceTime)))]),
      row([label("Last lap"), value(clock(kart.get(lastLap)))]),
      row([label("Best lap"), value(clock(kart.get(bestLap)))]),
      row([label("Speed"), value(`${Math.round(Math.abs(kart.get(speed)) * 3.6)} km/h`)]),
    );
    if (kart.get(boost) > 0) rows.push(row([label("Mini-turbo!"), value("")]));
    else if (kart.get(driftDir) !== 0) rows.push(row([label("Drift"), value(tier > 0 ? SPARKS[tier] : "...")]));
    return rows;
  }));
