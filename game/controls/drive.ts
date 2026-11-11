// Driving a kart. The stick (WASD, the arrows or a gamepad's left stick) steers with x; pushed forward
// it is the throttle and pulled back the brake, then reverse. A gamepad's triggers are the throttle and
// the brake too. Hold drift with a direction to hop into a drift; let go for the mini-turbo.
pw.defineControls("drive", {
  stick: pw.stick(["wasd", "arrows", "pad:left-stick"]),
  gas: pw.axis(["pad:right-trigger"]),
  brake: pw.axis(["pad:left-trigger"]),
  drift: pw.button(["key:space", "key:shift", "pad:right-bumper", "pad:b"]),
  respawn: pw.button(["key:r", "pad:back"]),
});
