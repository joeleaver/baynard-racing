// A camera that chases a kart from behind and above, swinging round after it.
const feel = (value, unit, doc) => pw.float(value, { ...(unit ? { unit } : {}), group: "Feel", doc });
pw.defineComponent("chaseCamera", {
  target: pw.object({ group: "Links", doc: "The kart it follows." }),
  distance: feel(5.2, "m", "How far behind."),
  height: feel(2.0, "m", "How far above."),
  lookHeight: feel(0.8, "m", "Where it looks, above the kart."),
  lookAhead: feel(0.25, "s", "How far ahead it looks, in seconds of the kart's speed."),
  follow: feel(6, "/s", "How quickly it catches up."),
  swing: feel(3.5, "/s", "How quickly it swings round behind."),
  yaw: pw.float(0, { group: "Doing", doc: "Which way it faces." }),
  placed: pw.float(0, { group: "Doing", doc: "1 once placed." }),
});
