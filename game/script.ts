// Baynard Racing's systems, in the order they run each tick.
//
// Before physics: the race's phase is read, the seats counted (who is here, what they picked), the
// race moves on (the host starts it; it ends when every kart is in), the grid hands each kart to a
// player or the game, the drivers ask (a player through their controls, a rival by reading the
// track), the kart turns those asks into the Vehicle's engine, brake and steer and its drift and
// boost, and the tyres take the grip the drift gives them. After physics: laps and places are counted
// along the track, the chase cameras follow, and each player is shown their own.
import "./systems/race_phase";
import "./systems/seats";
import "./systems/race";
import "./systems/grid";
import "./systems/driver";
import "./systems/rivals";
import "./systems/kart";
import "./systems/tyres";
import "./systems/laps";
import "./systems/chase_camera";
import "./systems/views";
import "./systems/telemetry";
