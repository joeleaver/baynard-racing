// How a racer's ratings (data/racers.ts, 1 to 5) become their kart's stats: 3 is the kart the game was
// tuned with, and each step either side moves it by the same amount.

/** The kart card's stats for `r`, a racer's ratings, and the rigid body's mass. */
export function statsOf(r) {
  const step = (rating, middle, per) => middle + (rating - 3) * per;
  return {
    topSpeed: step(r.speed, 21, 0.9),
    engineForce: step(r.accel, 520, 45),
    steerFast: step(r.handling, 0.2, 0.025),
    steerSlow: step(r.handling, 0.5, 0.03),
    driftTurn: step(r.drift, 1.1, 0.1),
    driftCarve: step(r.drift, 450, 45),
    mass: step(r.weight, 120, 14),
  };
}
