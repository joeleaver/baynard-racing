// Baynard Racing's systems, in the order they run each tick.
//
// Before physics: the kart turns its driver's stick into the Vehicle's asks and its drift and boost,
// and the tyres take the grip the drift gives them. After physics: laps are counted along the track,
// and the chase camera follows.
import "./systems/kart";
import "./systems/tyres";
import "./systems/laps";
import "./systems/chase_camera";
import "./systems/telemetry";
