// The race. One object in the scene carries it; systems/race.ts runs it and every screen reads it.
pw.defineComponent("race", {
  phase: pw.int(0, { doc: "0 the lobby, 1 racing (the countdown included), 2 the results." }),
  host: pw.int(0, { doc: "The seat that starts races: the lowest one in the lobby." }),
  firstFinish: pw.float(0, { unit: "s", doc: "The race clock when the first kart finished, 0 until then." }),
  allDone: pw.int(0, { doc: "1 once every kart has finished." }),
  clock: pw.float(0, { unit: "s", doc: "Seconds since this race started, the countdown included." }),
  wait: pw.float(15, { unit: "s", doc: "How long after the winner the race waits for the rest before the results." }),
});
