// Baynard Racing's look: the county show. Pasture-green painted boards with hedge-dark edges, the karts
// on straw, egg-yolk for what you press, and show rosettes for who is who (red you, blue other players)
// and for the podium (blue, red and white ribbons, as at a county fair). Lilita One for names and
// headings, Lato for everything else.
//
// A function, not a string: the fonts' families come from the game's library (`pw.font`), which a
// screen asks for once it runs.
export function style() {
  const display = pw.font("Lilita One");
  const text = pw.font("Lato Bold");
  const strong = pw.font("Lato Black");
  return `
.full { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; display: flex; flex-direction: column; font-family: ${text}; }
.dim { background: linear-gradient(180deg, #10261699 0%, #10261633 35%, #102616cc 100%); }
.deep { background: linear-gradient(180deg, #102616cc 0%, #10261688 50%, #102616ee 100%); }
.center { align-items: center; justify-content: center; }
.spacer { flex-grow: 1; }

.bar { display: flex; flex-direction: row; align-items: baseline; padding: 22px 40px 0 40px; }
.logo { font-family: ${display}; font-size: 34px; color: #FFC531; text-shadow: 0 3px 0 #1D4426; }
.track { font-size: 17px; color: #FFFBF2; margin-left: 18px; }

.board { background: #2F6B3A; border: 4px solid #1D4426; border-radius: 18px; box-shadow: inset 0 3px 0 #4E8C55, 0 6px 0 #1D4426; padding: 16px 18px 18px 18px; display: flex; flex-direction: column; }
.boardtitle { font-family: ${display}; font-size: 30px; color: #FFFBF2; margin: 0 0 12px 4px; }
.go { font-family: ${display}; font-size: 30px; color: #1D4426; background: #FFC531; border: 0; border-radius: 14px; padding: 14px 0; box-shadow: 0 5px 0 #B07F12; text-align: center; }
.wait { font-size: 16px; color: #FFFBF2; text-align: center; padding: 16px 10px; border: 2px dashed #4E8C55; border-radius: 14px; }

.hero { font-family: ${display}; font-size: 120px; color: #FFC531; text-shadow: 0 8px 0 #1D4426, 0 14px 36px #0009; }
.tagline { font-size: 22px; color: #FFFBF2; margin: 4px 0 34px 0; text-shadow: 0 2px 6px #000c; }
.titleboard { width: 360px; align-items: stretch; }
.go.second { margin-top: 14px; background: #FFFBF2; box-shadow: 0 5px 0 #B9D6B4; }
.menuhead { font-family: ${display}; font-size: 22px; color: #FFFBF2; text-align: center; margin: 22px 0 0 0; }
.coderow { display: flex; flex-direction: row; gap: 10px; margin-top: 14px; }
.code { flex: 1; font-size: 20px; color: #1D4426; background: #FFFBF2; border: 0; border-radius: 10px; padding: 8px 12px; }
.pick.join { margin-top: 0; padding: 8px 18px; font-size: 18px; }
.gamecode { font-family: ${display}; font-size: 26px; color: #FFC531; margin: 0 0 4px 4px; }
.problem { font-size: 15px; color: #FFFBF2; text-align: center; margin: 16px 0 10px 0; }
.pick.back { margin-top: 12px; background: #24552E; color: #FFFBF2; box-shadow: 0 3px 0 #1D4426; }
.here { font-size: 15px; color: #B9D6B4; margin-top: 12px; text-align: center; }

.stage { display: flex; flex-direction: row; gap: 20px; padding: 16px 40px 0 40px; align-items: flex-start; }
.grid { display: flex; flex-direction: row; flex-wrap: wrap; gap: 12px; width: 780px; }
.pen { position: relative; width: 180px; background: #24552E; border-radius: 12px; border: 3px solid #1D4426; display: flex; flex-direction: column; }
.pen.mine { border-color: #D63B2F; box-shadow: 0 0 0 3px #D63B2F; }
.pen.theirs { border-color: #2F6FD6; }
.floor { position: relative; height: 92px; border-radius: 9px 9px 0 0; background: linear-gradient(180deg, #9CCFEA 0%, #C9E6F4 55%, #E3BE63 56%, #D2A048 100%); }
.kart { position: absolute; left: 18px; top: 2px; width: 144px; height: 96px; }
.head { position: absolute; left: 8px; top: 70px; width: 40px; height: 40px; border-radius: 20px; border: 3px solid #FFFBF2; }
.name { font-family: ${display}; font-size: 20px; color: #FFFBF2; padding: 3px 0 0 56px; height: 28px; }
.stats { padding: 0 10px 8px 12px; display: flex; flex-direction: column; }
.stat { display: flex; flex-direction: row; align-items: center; height: 13px; }
.statname { width: 66px; font-size: 11px; color: #B9D6B4; }
.pip { width: 16px; height: 7px; border-radius: 4px; background: #1D4426; margin-right: 3px; }
.pip.on { background: #FFC531; }
.pick { margin-top: 5px; font-family: ${strong}; font-size: 14px; color: #1D4426; background: #FFC531; border-radius: 10px; padding: 4px 0; text-align: center; border: 0; box-shadow: 0 3px 0 #B07F12; }
/* The button a controller has focused (the engine marks it pw-focused). */
.go.pw-focused, .pick.pw-focused { box-shadow: 0 0 0 4px #FFFBF2, 0 0 18px 5px rgba(255,197,49,0.85); transform: scale(1.05); }
.pickgap { margin-top: 5px; height: 27px; }
.rosette { position: absolute; right: 8px; top: 8px; width: 46px; height: 46px; border-radius: 23px; display: flex; align-items: center; justify-content: center; font-family: ${display}; font-size: 15px; color: #FFFBF2; }
.rosette.red { background: #D63B2F; box-shadow: 0 0 0 4px #FFFBF2, 0 0 0 7px #D63B2F; }
.rosette.blue { background: #2F6FD6; box-shadow: 0 0 0 4px #FFFBF2, 0 0 0 7px #2F6FD6; }

.side { width: 300px; height: 520px; }
.count { font-size: 15px; color: #B9D6B4; margin: -6px 0 12px 4px; }
.entrant { display: flex; flex-direction: row; align-items: center; padding: 8px 6px; border-radius: 10px; margin-bottom: 6px; background: #24552E; }
.face { width: 36px; height: 36px; border-radius: 18px; border: 2px solid #FFFBF2; margin-right: 10px; }
.blank { width: 36px; height: 36px; border-radius: 18px; border: 2px dashed #B9D6B4; margin-right: 10px; }
.entrantname { display: flex; flex-direction: column; }
.who { font-size: 17px; color: #FFFBF2; }
.whatracer { font-size: 13px; color: #B9D6B4; }
.tag { margin-left: auto; font-family: ${strong}; font-size: 12px; color: #1D4426; background: #FFC531; border-radius: 8px; padding: 3px 8px; }
.tag.ready { background: #7BC86C; }
.wait.soon { font-family: ${display}; font-size: 24px; color: #FFC531; border-color: #FFC531; margin-bottom: 10px; }
.bots { font-size: 15px; color: #B9D6B4; margin: 4px 4px 12px 4px; }

.order { position: fixed; left: 18px; top: 120px; display: flex; flex-direction: column; }
.slot { display: flex; flex-direction: row; align-items: center; height: 46px; }
.slotpos { width: 26px; font-family: ${display}; font-size: 18px; color: #FFFBF2; text-shadow: 0 2px 0 #1D4426; }
.slothead { width: 34px; height: 34px; border-radius: 17px; border: 3px solid #1D4426; }
.slot.mine .slothead { border-color: #FFC531; width: 40px; height: 40px; border-radius: 20px; }
.slot.player .slothead { border-color: #2F6FD6; }
.place { position: fixed; left: 24px; top: 14px; display: flex; flex-direction: row; align-items: baseline; }
.placebig { font-family: ${display}; font-size: 76px; color: #FFC531; text-shadow: 0 5px 0 #1D4426, 0 8px 18px #0007; }
.placeof { font-family: ${display}; font-size: 26px; color: #FFFBF2; margin-left: 6px; text-shadow: 0 3px 0 #1D4426; }
.lapbox { position: fixed; right: 24px; top: 20px; display: flex; flex-direction: column; align-items: flex-end; font-family: ${text}; }
.lap { font-family: ${display}; font-size: 40px; color: #FFFBF2; text-shadow: 0 4px 0 #1D4426; }
.time { font-size: 22px; color: #FFFBF2; text-shadow: 0 2px 4px #000c; }
.best { font-size: 15px; color: #E5F1E2; text-shadow: 0 2px 4px #000c; }
.speedo { position: fixed; right: 28px; bottom: 22px; display: flex; flex-direction: row; align-items: baseline; font-family: ${text}; }
.speed { font-family: ${display}; font-size: 64px; color: #FFFBF2; text-shadow: 0 4px 0 #1D4426; width: 112px; text-align: right; }
.unit { font-size: 18px; color: #FFFBF2; margin-left: 6px; text-shadow: 0 2px 4px #000c; }
.spark { position: fixed; left: 0; width: 100vw; bottom: 34px; display: flex; flex-direction: row; justify-content: center; }
.chip { font-family: ${display}; font-size: 24px; color: #1D4426; border-radius: 14px; padding: 6px 18px; }
.chip.blue { background: #7CC4FF; box-shadow: 0 4px 0 #2F6FD6; }
.chip.orange { background: #FF9F2E; box-shadow: 0 4px 0 #A85A10; }
.chip.purple { background: #C79BFF; box-shadow: 0 4px 0 #6B3FC0; }
.chip.turbo { background: #FFC531; box-shadow: 0 4px 0 #B07F12; }
.countdown { position: fixed; top: 20%; left: 0; width: 100vw; text-align: center; font-family: ${display}; font-size: 190px; color: #FFC531; text-shadow: 0 10px 0 #1D4426, 0 16px 40px #0008; }
.banner { position: fixed; bottom: 110px; left: 0; width: 100vw; display: flex; flex-direction: row; justify-content: center; }
.bannerchip { font-size: 20px; color: #FFFBF2; background: #1D4426cc; border-radius: 14px; padding: 10px 22px; font-family: ${text}; }

.results { width: 640px; margin-bottom: 70px; }
.resultsgo { position: fixed; bottom: 28px; left: 0; width: 100vw; display: flex; flex-direction: row; justify-content: center; }
.resultsgo .go { padding: 12px 40px; }
.line { display: flex; flex-direction: row; align-items: center; height: 50px; border-radius: 10px; padding: 0 10px; margin-bottom: 4px; background: #24552E; }
.line.mine { box-shadow: 0 0 0 3px #FFC531; }
.ribbon { width: 40px; height: 40px; border-radius: 20px; margin-right: 12px; display: flex; align-items: center; justify-content: center; font-family: ${display}; font-size: 15px; }
.r1 { background: #2F6FD6; color: #FFFBF2; box-shadow: 0 0 0 3px #FFFBF2, 0 0 0 5px #2F6FD6; }
.r2 { background: #D63B2F; color: #FFFBF2; box-shadow: 0 0 0 3px #FFFBF2, 0 0 0 5px #D63B2F; }
.r3 { background: #FFFBF2; color: #1D4426; box-shadow: 0 0 0 3px #B9D6B4, 0 0 0 5px #FFFBF2; }
.rn { color: #B9D6B4; }
.lname { font-family: ${display}; font-size: 21px; color: #FFFBF2; width: 190px; }
.ldriver { font-size: 15px; color: #B9D6B4; width: 150px; }
.ltime { font-size: 18px; color: #FFFBF2; margin-left: auto; }
.after { margin-top: 14px; display: flex; flex-direction: column; }
`;
}
