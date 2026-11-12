// Baynard Racing's systems, in the order they run each tick.
//
// Before physics: the drivers ask (a player through their controls, a rival by reading the track),
// the kart turns those asks into the Vehicle's engine, brake and steer and its drift and boost, and
// the tyres take the grip the drift gives them. After physics: laps and places are counted along the
// track, and the chase camera follows.
import "./systems/driver";
import "./systems/rivals";
import "./systems/kart";
import "./systems/tyres";
import "./systems/laps";
import "./systems/chase_camera";
import "./systems/telemetry";
