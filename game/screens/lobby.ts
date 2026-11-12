// The title and the lobby. A player arriving sees the title until they press Play. In the lobby they
// pick one of the eight racers (one each: a racer another player has is theirs), see who else is
// here, and the host (the first player in) starts the race. Bots race every kart nobody picked.
import { box, label, button, image, styles } from "@pw/ui";
import { RACERS, RATINGS } from "../data/racers";
import { style } from "../data/style";

styles(style());

const S = pw.component("seat");
const [here, entered, picked, phase, hostOf] = ["here", "entered", "picked", "phase", "host"].map((n) => S.property(n));
const player = pw.field("controls", "player");
const karts = RACERS.map((r) => pw.image(`${r.name} kart`));
const heads = RACERS.map((r) => pw.image(`${r.name} headshot`));
const LAPS = 3;

/** Five pips, the first `n` lit. */
const pips = (n) => [1, 2, 3, 4, 5].map((p) => box({ class: p <= n ? "pip on" : "pip" }, []));

function title(players) {
  const others = players - 1;
  return box({ class: "full deep center" }, [
    label({ class: "hero" }, "Baynard Racing"),
    label({ class: "tagline" }, "Race your friends round the Barnyard Loop. Bots fill the empty karts."),
    box({ class: "board titleboard" }, [
      button({ class: "go", onclick: pw.emit("enter") }, "Play"),
      label({ class: "here" }, others > 0 ? `${others} ${others === 1 ? "player is" : "players are"} already here` : "You're the first one here"),
    ]),
  ]);
}

pw.screen("lobby", { includeComponents: [S] }, ({ seat, objects }) => {
  const me = objects.find((o) => o.get(player) === seat.player);
  if (me === undefined) return [];
  if (me.get(entered) === 0) return title(objects.filter((o) => o.get(here) === 1).length);
  if (me.get(phase) !== 0) return [];

  const lobby = objects.filter((o) => o.get(here) === 1 && o.get(entered) === 1).sort((a, b) => a.get(player) - b.get(player));
  const mine = me.get(picked);
  const host = me.get(hostOf);

  const pens = RACERS.map((r, i) => {
    const n = i + 1;
    const holder = lobby.find((o) => o.get(picked) === n && o.get(player) !== seat.player);
    const isMine = mine === n;
    const parts = [
      box({ class: "floor" }, [image(karts[i], { class: "kart" })]),
      image(heads[i], { class: "head" }),
      label({ class: "name" }, r.name),
      box({ class: "stats" }, RATINGS.map(([key, word]) => box({ class: "stat" }, [label({ class: "statname" }, word), ...pips(r[key])]))),
    ];
    if (isMine) parts.push(box({ class: "rosette red" }, [label("You")]));
    else if (holder !== undefined) parts.push(box({ class: "rosette blue" }, [label(`P${holder.get(player)}`)]));
    parts.push(isMine || holder !== undefined ? box({ class: "pickgap" }, []) : button({ class: "pick", onclick: pw.emit("pick", { racer: n }) }, "Pick"));
    return box({ class: isMine ? "pen mine" : holder !== undefined ? "pen theirs" : "pen" }, parts);
  });

  const entrants = lobby.map((o) => {
    const p = o.get(player);
    const n = o.get(picked);
    const you = p === seat.player;
    return box({ class: "entrant" }, [
      n > 0 ? image(heads[n - 1], { class: "face" }) : box({ class: "blank" }, []),
      box({ class: "entrantname" }, [label({ class: "who" }, you ? "You" : `Player ${p}`), label({ class: "whatracer" }, n > 0 ? RACERS[n - 1].name : "Choosing")]),
      ...(p === host ? [label({ class: "tag" }, "Host")] : []),
    ]);
  });
  const bots = RACERS.length - lobby.length;

  return box({ class: "full dim" }, [
    box({ class: "bar" }, [label({ class: "logo" }, "Baynard Racing"), label({ class: "track" }, `Barnyard Loop, ${LAPS} laps`)]),
    box({ class: "stage" }, [
      box({ class: "board" }, [label({ class: "boardtitle" }, "Pick your racer"), box({ class: "grid" }, pens)]),
      box({ class: "board side" }, [
        label({ class: "boardtitle" }, "In the lobby"),
        label({ class: "count" }, `${lobby.length} of ${RACERS.length} karts taken`),
        ...entrants,
        box({ class: "spacer" }, []),
        label({ class: "bots" }, bots === 0 ? "Every kart has a player." : `${bots} ${bots === 1 ? "bot fills" : "bots fill"} the rest of the grid.`),
        host === seat.player ? button({ class: "go", onclick: pw.emit("start") }, "Start race") : label({ class: "wait" }, `Waiting for Player ${host} to start the race`),
      ]),
    ]),
  ]);
});
