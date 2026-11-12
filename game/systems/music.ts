// The music: the title song on the title screen and in the lobby, the race song from the start of a
// race through its results, and back to the title song when the host takes everyone to the lobby.
// Both loop, flat (from nowhere in the world), on the mix's Music bus; changing song fades the old
// one out by its sound's stop fade. Game code runs on every machine in step, so everyone hears the
// same song; in a browser it starts at the page's first click or key, as far in as it should be.
//
// Runs in `react`, after the race rules have moved the race on this tick.
import { RACING, RESULTS } from "./state";

const R = pw.component("race");
const phase = R.property("phase");
const TITLE = pw.sound("Title music");
const RACE = pw.sound("Race music");
let song = null;
let playing = null;

pw.registerSystem("music", { phase: "react", includeComponents: ["race"] }, ({ objects }) => {
  for (const r of objects) {
    const p = r.get(phase);
    const want = p === RACING || p === RESULTS ? RACE : TITLE;
    if (want === song) continue;
    playing?.stop();
    song = want;
    playing = pw.play(want);
  }
});
