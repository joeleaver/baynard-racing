// The results: every kart in the order it finished (the rest by how far round they got), a county
// fair's ribbons for the first three, who drove each, and its time. The host takes everyone back to
// the lobby for the next race.
import { box, label, button, image } from "@pw/ui";
import { RACERS, ordinal, clock } from "../data/racers";

const K = pw.component("kart");
const [racerOf, human, place, finished, phase] = ["racer", "human", "place", "finished", "phase"].map((n) => K.property(n));
const heads = RACERS.map((r) => pw.image(`${r.name} headshot`));
const RIBBONS = ["r1", "r2", "r3"];

pw.screen("results", { includeComponents: [K] }, ({ seat, objects }) => {
  if (objects.length === 0 || objects[0].get(phase) !== 2) return [];
  const order = [...objects].sort((a, b) => a.get(place) - b.get(place));
  const lines = order.map((kart, i) => {
    const who = kart.get(human);
    const mine = who === seat.player;
    const n = kart.get(racerOf);
    return box({ class: mine ? "line mine" : "line" }, [
      label({ class: `ribbon ${RIBBONS[i] ?? "rn"}` }, ordinal(i + 1)),
      image(heads[n - 1], { class: "face" }),
      label({ class: "lname" }, RACERS[n - 1].name),
      label({ class: "ldriver" }, mine ? "You" : who > 0 ? `Player ${who}` : "Bot"),
      label({ class: "ltime" }, kart.get(finished) > 0 ? clock(kart.get(finished)) : "Still racing"),
    ]);
  });
  return box({ class: "full dim center" }, [box({ class: "board results" }, [label({ class: "boardtitle" }, "Results"), ...lines])]);
});

// The host's button, from the seats (a kart does not know who the host is).
const S = pw.component("seat");
const hostOf = S.property("host");
const seatPhase = S.property("phase");
const player = pw.field("controls", "player");

pw.screen("results button", { includeComponents: [S] }, ({ seat, objects }) => {
  const me = objects.find((o) => o.get(player) === seat.player);
  if (me === undefined || me.get(seatPhase) !== 2) return [];
  const host = me.get(hostOf);
  return box({ class: "resultsgo" }, [
    host === seat.player ? button({ class: "go", onclick: pw.emit("again") }, "Back to the lobby") : label({ class: "bannerchip" }, `Waiting for Player ${host} to go back to the lobby`),
  ]);
});
