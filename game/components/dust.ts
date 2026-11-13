// A trail a kart throws up behind it: dust off dirt, spray off mud, sparks off a boost, smoke from
// its exhaust. Each kart
// carries one emitter of each kind (its Particles card says how it looks); systems/dust.ts starts the
// one that matches the ground under the kart and stops the rest.
pw.defineComponent("dust", {
  kart: pw.object({ doc: "The kart it trails behind." }),
  kind: pw.int(1, { doc: "What it is for: 1 dirt, 2 sand, 3 mud, 4 grass, 5 ice, 6 tyre smoke (drifting on tarmac), 7 boost sparks, 8 exhaust under throttle (dark and thick), 9 exhaust cruising (light)." }),
});
