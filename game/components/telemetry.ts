// A testing aid: on a kart or one of its wheels, systems/telemetry.ts logs what it is doing every tick
// (to the Console, and to an agent's advancePlay). Take it off for an ordinary run.
pw.defineComponent("telemetry", {
  label: pw.float(0, { doc: "A number to tell this object's lines apart." }),
});
