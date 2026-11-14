// A seat in the game: one object for each of the eight, carrying a Controls card for that seat's
// player, so the game can tell who is here (their controls read something) and what they chose.
pw.defineComponent("seat", {
  here: pw.int(0, { doc: "1 while a player is on this seat." }),
  entered: pw.int(0, { doc: "1 once they are past the title screen." }),
  picked: pw.int(0, { doc: "The racer they picked, 1 to 8 as on a kart's card; 0 for none yet." }),
  ready: pw.int(0, { doc: "1 while they are ready to race." }),
  name: pw.text("", { doc: "The name they go by, kept in their save; empty until they choose one." }),
  countdown: pw.float(0, { unit: "s", doc: "Seconds until the race starts once everyone is ready, 0 while not everyone is; copied here for the screens." }),
  phase: pw.int(0, { doc: "The race's phase (0 the lobby, 1 racing, 2 the results), copied here for the screens." }),
  host: pw.int(0, { doc: "The seat that takes everyone back to the lobby after a race, copied here for the screens." }),
});
