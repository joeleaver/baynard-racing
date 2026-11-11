// A tyre that lets go in a drift: on a Wheel of a kart, its sideways grip drops to `driftGrip` while
// the kart drifts, so the tail swings out on real tyre physics (systems/tyres.ts).
pw.defineComponent("tyre", {
  kart: pw.object({ doc: "The kart it belongs to." }),
  grip: pw.float(1.8, { doc: "Its best sideways grip, driving normally." }),
  slideGrip: pw.float(1.4, { doc: "Its sideways grip once it slides, driving normally." }),
  driftGrip: pw.float(1.5, { doc: "Its best sideways grip while the kart drifts." }),
  driftSlideGrip: pw.float(1.3, { doc: "Its sliding sideways grip while the kart drifts." }),
});
