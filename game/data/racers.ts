// The eight racers, in the order a kart's `racer` number counts them (1 is Hettie): their names and how
// their karts handle, 1 to 5. The lobby shows the ratings; systems/grid.ts turns them into each kart's
// stats when a race starts (data/handling.ts), so what a card says is how the kart drives. How a
// racer drives when a bot has it is on its kart's Rival card.
export const RACERS = [
  { name: "Hettie", speed: 3, accel: 4, handling: 4, drift: 3, weight: 2 },
  { name: "Max", speed: 5, accel: 2, handling: 3, drift: 3, weight: 4 },
  { name: "Puddles", speed: 4, accel: 3, handling: 3, drift: 3, weight: 3 },
  { name: "The Major", speed: 3, accel: 3, handling: 2, drift: 5, weight: 3 },
  { name: "Mabel", speed: 4, accel: 2, handling: 3, drift: 2, weight: 5 },
  { name: "Scraps", speed: 2, accel: 4, handling: 2, drift: 5, weight: 3 },
  { name: "Marmalade", speed: 3, accel: 3, handling: 5, drift: 3, weight: 1 },
  { name: "Duvet", speed: 2, accel: 5, handling: 4, drift: 3, weight: 1 },
];

/** The ratings a card shows, in order, with their names. */
export const RATINGS = [
  ["speed", "Speed"],
  ["accel", "Accel"],
  ["handling", "Handling"],
  ["drift", "Drift"],
  ["weight", "Weight"],
];

/** Racer `n` (1 to 8). */
export const racer = (n) => RACERS[n - 1];

/** A finishing place as a word: 1st, 2nd, 3rd, 4th. */
export const ordinal = (n) => `${n}${n % 10 === 1 && n % 100 !== 11 ? "st" : n % 10 === 2 && n % 100 !== 12 ? "nd" : n % 10 === 3 && n % 100 !== 13 ? "rd" : "th"}`;

/** A race time as minutes, seconds and hundredths, or a dash before there is one. */
export const clock = (s) => (s <= 0 ? "-" : `${Math.floor(s / 60)}:${(s % 60).toFixed(2).padStart(5, "0")}`);
