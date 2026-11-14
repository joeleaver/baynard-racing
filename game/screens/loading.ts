// The loading screen: drawn while the game's files come in and it starts (`pw.loadingScreen`), in the
// county-show look of the title — the name, the eight racers waiting at the start, a bar filling with
// yolk, and a tip that changes every few seconds.
import { box, label, image } from "@pw/ui";
import { RACERS } from "../data/racers";

const heads = RACERS.map((r) => pw.image(`${r.name} headshot`));

const TIPS = [
  "Hold drift through a corner and let go on the way out for a boost.",
  "Hay bales are soft. Fences are not.",
  "Heavier karts hold the line; light ones turn on a sixpence.",
  "Mud slows everyone down. Tarmac is quickest.",
  "Bots fill every kart nobody is in, so there is always a race.",
  "Press Ready in the lobby: the race starts when everyone is.",
];

pw.loadingScreen(({ loading }) => {
  const tip = TIPS[Math.floor(loading.seconds / 5) % TIPS.length];
  const mb = (b) => (b / 1e6).toFixed(1);
  return box({ class: "full loadfield center" }, [
    label({ class: "hero" }, "Braynard Racing"),
    box({ class: "loadheads" }, heads.map((h, i) => image(h, { class: "loadhead", style: `animation-delay: ${i * 0.12}s` }))),
    box({ class: "loadbar" }, [box({ class: loading.starting ? "loadfill starting" : "loadfill", style: `width: ${Math.round(loading.done * 1000) / 10}%` }, [])]),
    label({ class: "loadcount" }, loading.starting ? "Lining up on the grid…" : loading.total > 0 ? `${mb(loading.bytes)} of ${mb(loading.total)} MB` : "Loading…"),
    label({ class: "loadtip" }, tip),
  ]);
});
