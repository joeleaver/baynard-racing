// A rival: a kart the game drives. It follows the track's centre line, a lane to one side of it, slows
// for the corners it sees coming, and drifts the long ones for the mini-turbo. Every number is a dial:
// how good a driver it is (pace, grip, braking), its style (how it takes corners, whether it drifts,
// whether it barges), and how human (unsteady hands, the odd mistake).
const dial = (value, unit, doc) => pw.float(value, { ...(unit ? { unit } : {}), group: "Driving", doc });

pw.defineComponent("rival", {
  lane: dial(0, "m", "How far right of the centre line it drives (left if negative)."),
  pace: dial(0.95, "", "The share of the kart's top speed it drives at on a straight."),
  cornerGrip: dial(9, "m/s²", "How hard it lets a corner pull it sideways before it slows down for it."),
  braking: dial(6, "m/s²", "How hard it expects to brake into a corner, so how late it brakes."),
  aim: dial(5, "m", "How far ahead it aims, at a crawl."),
  aimPerSpeed: dial(0.3, "s", "How much further ahead it aims for every metre per second."),
  steering: dial(2.2, "", "How sharply it steers toward where it aims."),
  driftTurn: dial(0.9, "rad", "A corner turning at least this much in the next 20 m, it drifts."),
  stuckAfter: dial(2.5, "s", "Stopped or far off the road this long, it asks to be put back."),

  cutCorners: dial(0, "m", "How far toward a corner's inside it moves its line as the corner comes."),
  barge: dial(0, "", "How hard it swerves into a kart alongside, 0 never to 1 always."),
  wobble: dial(0.3, "", "How unsteady its hands are: 0 a perfect line, 1 all over the road."),
  mistakes: dial(1, "/min", "How often it fluffs something: brakes late, or lets a drift go early."),

  stuck: pw.float(0, { group: "Doing", doc: "Seconds it has been stopped or lost." }),
  wanted: pw.float(0, { group: "Doing", doc: "The speed it is aiming for this tick." }),
  shake: pw.float(0, { group: "Doing", doc: "How far off its aim its hands are this tick (radians)." }),
  lapse: pw.float(0, { group: "Doing", doc: "Seconds left of a mistake: braking late, it ignores the corners ahead." }),
});
