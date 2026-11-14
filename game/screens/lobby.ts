// The title and the lobby. The title's menu: Single player opens the lobby of the game on this
// machine, to race the bots. Quick match joins the open game Playweft runs for this game's link
// (`net.join`); Create private game starts one only friends with its code can join (`net.create`),
// and a code typed in joins theirs (`net.join` with `{ code }`). A page opened at a friend's invite
// link offers their game first (`net.invited`). If a game can't be joined the title says why and
// offers to host on this computer instead (`net.host`, Playweft on a desktop). In a shared game the
// lobby shows straight away, with a private game's code and invite link. In the lobby
// players pick one of the eight racers (one each: a racer another player has is theirs) and press
// Ready; the race starts a moment after everyone is ready. Bots race every kart nobody is in.
import { box, label, button, image, input, styles } from "@pw/ui";
import { RACERS, RATINGS } from "../data/racers";
import { style } from "../data/style";

styles(style());

const S = pw.component("seat");
const [here, entered, picked, ready, phase, countdown] = ["here", "entered", "picked", "ready", "phase", "countdown"].map((n) => S.property(n));
const name = S.text("name");
const player = pw.field("controls", "player");
const karts = RACERS.map((r) => pw.image(`${r.name} kart`));
const heads = RACERS.map((r) => pw.image(`${r.name} headshot`));
const LAPS = 3;

/** Five pips, the first `n` lit. */
const pips = (n) => [1, 2, 3, 4, 5].map((p) => box({ class: p <= n ? "pip on" : "pip" }, []));

function title(net, typed) {
  // While a game is being joined the menu says so, instead of buttons that seem to do nothing.
  const menu = net.joining
    ? [label({ class: "wait" }, "Joining the game…")]
    : [
        ...(net.invited !== ""
          ? [button({ class: "go", onclick: pw.emit("net.join", { code: net.invited }), focus: "first" }, "Join your friend's game")]
          : []),
        button({ class: net.invited !== "" ? "go second" : "go", onclick: pw.emit("enter"), ...(net.invited !== "" ? {} : { focus: "first" }) }, "Single player"),
        label({ class: "menuhead" }, "Multiplayer"),
        button({ class: "go second", onclick: pw.emit("net.join") }, "Quick match"),
        button({ class: "go second", onclick: pw.emit("net.create") }, "Create private game"),
        box({ class: "coderow" }, [
          input({ class: "code", name: "code", placeholder: "Friend's code" }),
          button({ class: "pick join", onclick: pw.emit("net.join", { code: typed.code ?? "" }) }, "Join"),
        ]),
      ];
  if (net.problem !== "" && !net.joining) {
    menu.push(label({ class: "problem" }, net.problem));
    menu.push(button({ class: "pick", onclick: pw.emit("net.host") }, "Host on this computer"));
  }
  return box({ class: "full deep center" }, [
    label({ class: "hero" }, "Baynard Racing"),
    label({ class: "tagline" }, "Race your friends round the Barnyard Loop. Bots fill the empty karts."),
    box({ class: "board titleboard" }, menu),
  ]);
}

pw.screen("lobby", { includeComponents: [S] }, ({ seat, objects, net, typed }) => {
  const me = objects.find((o) => o.get(player) === seat.player);
  if (me === undefined) return [];
  const shared = net.joined || net.hosting;
  if (me.get(entered) === 0 && !shared) return title(net, typed);
  if (me.get(phase) !== 0) return [];

  // On this machine the lobby is whoever came past the title; in a shared game, everyone here.
  const lobby = objects
    .filter((o) => o.get(here) === 1 && (shared || o.get(entered) === 1))
    .sort((a, b) => a.get(player) - b.get(player));
  const mine = me.get(picked);

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
      box({ class: "entrantname" }, [
        label({ class: "who" }, o.get(name) || (you ? "You" : `Player ${p}`)),
        label({ class: "whatracer" }, n > 0 ? RACERS[n - 1].name : "Choosing"),
      ]),
      ...(o.get(ready) === 1 ? [label({ class: "tag ready" }, "Ready")] : []),
    ]);
  });
  const bots = RACERS.length - lobby.length;
  // Everyone presses Ready; a moment after the last one does, the race starts.
  const meReady = me.get(ready) === 1;
  const unready = lobby.filter((o) => o.get(ready) !== 1).length;
  const left = Math.ceil(me.get(countdown));
  const status =
    left > 0
      ? label({ class: "wait soon" }, `Starting in ${left}…`)
      : meReady
        ? label({ class: "wait" }, `Waiting for ${unready} ${unready === 1 ? "player" : "players"} to get ready`)
        : null;
  const start = [
    ...(status === null ? [] : [status]),
    button({ class: meReady ? "go second" : "go", onclick: pw.emit("ready") }, meReady ? "Not ready" : "Ready"),
  ];
  const away = shared
    ? button({ class: "pick back", onclick: pw.emit("net.leave"), focus: "back" }, net.hosting ? "Stop hosting" : "Leave")
    : button({ class: "pick back", onclick: pw.emit("leave"), focus: "back" }, "Back");

  return box({ class: "full dim" }, [
    box({ class: "bar" }, [label({ class: "logo" }, "Baynard Racing"), label({ class: "track" }, `Barnyard Loop, ${LAPS} laps`)]),
    box({ class: "stage" }, [
      box({ class: "board" }, [label({ class: "boardtitle" }, "Pick your racer"), box({ class: "grid", focus: "group" }, pens)]),
      box({ class: "board side", focus: "group" }, [
        label({ class: "boardtitle" }, shared ? "In the lobby" : "Single player"),
        label({ class: "count" }, shared ? `${lobby.length} ${lobby.length === 1 ? "player" : "players"} here` : "You against the bots"),
        ...(net.hosting && net.address !== "" ? [label({ class: "count" }, `Others join at ${net.address}`)] : []),
        ...(net.code !== ""
          ? [label({ class: "gamecode" }, `Game code: ${net.code}`), label({ class: "count" }, `Invite link: ${net.address}`)]
          : []),
        ...entrants,
        // The name this player goes by: typed here, kept in their save for every game they join.
        box({ class: "coderow" }, [
          input({ class: "code", name: "playername", placeholder: me.get(name) || "Your name" }),
          button({ class: "pick join", onclick: pw.emit("rename", { to: typed.playername ?? "" }) }, "Save name"),
        ]),
        box({ class: "spacer" }, []),
        label({ class: "bots" }, bots === 0 ? "Every kart has a player." : `${bots} ${bots === 1 ? "bot fills" : "bots fill"} the rest of the grid.`),
        ...start,
        away,
      ]),
    ]),
  ]);
});
