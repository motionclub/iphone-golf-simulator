const assets = "../../../GolfArcade/Unity/";
const artwork = {
  golf: {
    title: "Cliffside", titleArt: "golf-cliffside", scene: "scenes/golf.jpg",
    palette: {
      top: "#1a4f7a", bottom: "#103757", frame: "#efe3c8", "frame-deep": "#b8a57f",
      surface: "#1a5a88", line: "#d5ecf7", cream: "#fff4df", ink: "#123a5c",
      accent: "#33e0e4", "accent-deep": "#1ca3b4", "accent-ink": "#0f3352",
    },
    heading: "Round complete", scores: ["To par", "Strokes"], winner: "Nia", change: "Change Course",
    players: [
      { name: "Nia", scores: ["−3", "16"], xp: [["Round played", 80], ["Under par", 120], ["Birdies", 75]], level: 2, start: 82 },
      { name: "Adnan", scores: ["−1", "18"], xp: [["Round played", 80], ["Under par", 40], ["Birdies", 25], ["Coins", 60], ["Bounties", 20]], level: 1, start: 0 },
      { name: "Milo", scores: ["E", "19"], xp: [["Round played", 80], ["Level par", 30], ["Birdies", 25]], level: 2, start: 105 },
      { name: "Kai", scores: ["+2", "21"], xp: [["Round played", 80], ["Coins", 35]], level: 1, start: 48 },
    ],
  },
  tennis: {
    title: "Tropical Resort", titleArt: "tennis-resort", scene: "scenes/tennis.jpg",
    palette: {
      top: "#1e3c73", bottom: "#142a55", frame: "#d49553", "frame-deep": "#8a5426",
      surface: "#1f4fa8", line: "#f4e3c3", cream: "#fff1d8", ink: "#16264a",
      accent: "#35dccb", "accent-deep": "#1a9c93", "accent-ink": "#112a4c",
    },
    heading: "Match complete", scores: ["Games", "Result"], winner: "Adnan", change: "Change Court",
    players: [
      { name: "Adnan", scores: ["6", "Win"], xp: [["Match played", 60], ["Victory", 120], ["Aces", 36], ["Winners", 54], ["Points won", 25]], level: 1, start: 0 },
      { name: "Milo", scores: ["3", "Loss"], xp: [["Match played", 60], ["Good effort", 30], ["Winners", 30], ["Points won", 16]], level: 1, start: 16 },
    ],
  },
  bowling: {
    title: "Club Lanes", titleArt: "bowling-club", scene: assets + "MenuArt/map-bowling-club.jpg",
    palette: {
      top: "#1e2756", bottom: "#131a3e", frame: "#8a5a30", "frame-deep": "#4e2f16",
      surface: "#26306a", line: "#d9b25a", cream: "#fff1d8", ink: "#1b2148",
      accent: "#e9b949", "accent-deep": "#c9a464", "accent-ink": "#1b2148",
    },
    heading: "Game complete", scores: ["Score", "Strikes"], winner: "Kai", change: "Change Lanes",
    players: [
      { name: "Kai", scores: ["158", "5"], xp: [["Game bowled", 60], ["Over 150", 60], ["Strikes", 75], ["Spares", 16], ["Top of the sheet", 60]], level: 2, start: 24 },
      { name: "Nia", scores: ["142", "3"], xp: [["Game bowled", 60], ["Triple digits", 30], ["Strikes", 45], ["Spares", 32]], level: 2, start: 4 },
      { name: "Adnan", scores: ["123", "4"], xp: [["Game bowled", 60], ["Triple digits", 30], ["Strikes", 60]], level: 1, start: 90 },
      { name: "Milo", scores: ["80", "0"], xp: [["Game bowled", 60]], level: 1, start: 58 },
    ],
  },
};
const resultSteps = [["victory", "Victory"], ["results", "Results"], ["xp", "XP earned"], ["next", "Play again"]];
const sequenceBeats = [
  { step: "victory", at: 0 },
  { step: "results", at: 2050 },
  { step: "xp", at: 5150 },
  { step: "next", at: 8300 },
];
const sequenceEnd = 10200;
const motionNames = ["snap", "turn", "spotlight"];
const golfScores = [
  ["Par", 4, 4, 5, 3, 3, 19],
  ["Nia", 3, 3, 4, 3, 3, 16],
  ["Adnan", 3, 4, 5, 3, 3, 18],
  ["Milo", 3, 4, 6, 3, 3, 19],
  ["Kai", 4, 5, 5, 4, 3, 21],
];
const bowlingFrames = {
  Kai: ["4 /|– –|X|9 –|X|X|X|2 /|X|8 1", [10, 10, 29, 38, 68, 90, 110, 130, 149, 158]],
  Nia: ["X|9 /|8 –|4 /|9 /|– 5|X|2 /|X|6 –", [20, 38, 46, 65, 75, 80, 100, 120, 136, 142]],
  Adnan: ["X|8 1|8 1|X|8 1|8 1|X|8 1|8 1|X 1 1", [19, 28, 37, 56, 65, 74, 93, 102, 111, 123]],
  Milo: ["7 1|7 1|7 1|7 1|7 1|7 1|7 1|7 1|7 1|7 1", [8, 16, 24, 32, 40, 48, 56, 64, 72, 80]],
};
const tennisPoints = { Adnan: 25, Milo: 16 };
const tennisAces = { Adnan: 3, Milo: 0 };
const calibrationSteps = [["intro", "Intro"], ["scan", "TV scan"], ["latency", "TV latency"], ["countdown", "Get ready"], ["bounce", "Ball drop"], ["ready", "Ready"], ["aim", "Aim practice"]];
const screenTest = { warning: 1500, flashes: 4, interval: 1700, lit: 450, resultHold: 550, sampleLatency: 128 };
const swingTest = { countdown: 5000, interval: 1200, warmups: 2, scored: 7, finishHold: 700 };
const colors = { Nia: "#e9a75a", Adnan: "#35988f", Milo: "#7586bf", Kai: "#ad754c" };
const places = ["1st", "2nd", "3rd", "4th"];

const query = new URLSearchParams(location.search);
const requestedSport = query.get("sport");
let sport = Object.hasOwn(artwork, requestedSport) || requestedSport === "calibration" ? requestedSport : "golf";
const designButtons = Array.from(document.querySelectorAll(".designs [data-design]"));
const finalDesigns = new Set(designButtons.filter(button => button.hasAttribute("data-final-design")).map(button => button.dataset.design));
const hasFinalDesigns = () => sport === "tennis" || sport === "bowling";
const defaultDesign = () => hasFinalDesigns() ? "box-score" : "scorebook";
const requestedDesign = designButtons.find(button => button.dataset.design === query.get("design"))?.dataset.design;
let design = requestedDesign && (!finalDesigns.has(requestedDesign) || hasFinalDesigns()) ? requestedDesign : defaultDesign();
const isScorebook = () => design === "scorebook" || finalDesigns.has(design);
const motionQuery = query.get("motion");
let motion = motionNames.includes(motionQuery) ? motionQuery : "snap";
const victoryControls = document.getElementById("victory-controls");
const victoryButtons = Array.from(victoryControls.querySelectorAll("[data-victory]"));
let victoryDesign = victoryButtons.find(button => button.dataset.victory === query.get("victory"))?.dataset.victory ?? "venue-plaque";
const capture = query.has("capture");
if (capture) document.body.classList.add("capture");
let step = initialStep(query.get("step") ?? "victory");
let xpPlayer = "Adnan";
let calibrationAnimation = 0;
let nextAction = "";
let sequenceAnimation = 0;
let playbackBeat = null;

const review = document.querySelector(".review");
const tv = document.getElementById("tv");
const steps = document.getElementById("steps");
const switchButtons = document.querySelectorAll("[data-sport]");
const motionControls = document.getElementById("motion-controls");
const motionButtons = motionControls.querySelectorAll("[data-motion]");
const playButton = document.getElementById("play-sequence");
const simulateScan = document.getElementById("simulate-scan");
const designControls = document.querySelector(".designs");
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
const currentMap = () => artwork[sport === "calibration" ? "tennis" : sport];
const availableSteps = () => sport === "calibration" ? calibrationSteps : resultSteps;

function initialStep(requested) {
  const options = sport === "golf" ? [...resultSteps, ["scorecard", "Scorecard"]] : sport === "calibration" ? calibrationSteps : resultSteps;
  return options.some(([key]) => key === requested) ? requested : sport === "calibration" ? "intro" : "results";
}

function showStage(next, animate = false, outgoing = false) {
  const previous = outgoing ? tv.querySelector(".stage:not(.leaving)") : null;
  cancelAnimationFrame(calibrationAnimation);
  calibrationAnimation = 0;
  nextAction = "";
  step = next;
  render();
  if (!animate) return;

  const entering = tv.querySelector(".stage");
  entering.classList.add("entering");
  if (previous) {
    previous.className = "stage leaving";
    previous.inert = true;
    previous.setAttribute("aria-hidden", "true");
    entering.before(previous);
  }
}

function stopSequence() {
  cancelAnimationFrame(sequenceAnimation);
  sequenceAnimation = 0;
  playbackBeat = null;
  tv.querySelector(".stage.leaving")?.remove();
  updateEarnedTotal(Infinity);
  playButton.textContent = "Play sequence";
}

function selectStep(next, animate = false) {
  stopSequence();
  showStage(next, animate);
}

function arrow() {
  return '<span class="arrow" aria-hidden="true">›</span>';
}

function action(label, target, quiet = false) {
  return `<button type="button" class="action ${quiet ? "quiet" : ""}" data-go="${target}">${label}${arrow()}</button>`;
}

function venue(map, name) {
  return `<div class="venue">
    <img src="${assets}MapSkins/skin-title-${map.titleArt}.png" alt="${map.title}">
    ${name && !isScorebook() ? `<div class="outcome">${name}</div>` : ""}
  </div>`;
}

function stageTitle(title, detail = "") {
  return `<header class="stage-title"><h2>${title}</h2>${detail && isScorebook() ? `<span>${detail}</span>` : ""}</header>`;
}

function scoresFor(map, scores) {
  return map.scores.map((label, index) => `<div><dt>${label}</dt><dd>${scores[index]}</dd></div>`).join("");
}

function winningScore(map) {
  const [score, secondary] = map.players[0].scores;
  if (sport === "tennis") return { score: `${score}–${map.players[1].scores[0]}`, detail: `vs. ${map.players[1].name}` };
  if (sport === "golf") return { score, detail: `${secondary} strokes` };
  return { score, detail: `${secondary} strikes` };
}

function victory(map) {
  const { score, detail } = winningScore(map);
  const isPlaque = victoryDesign === "venue-plaque";
  const scoreLine = `<div class="victory-score"><strong>${score}</strong><span>${detail}</span></div>`;
  const headline = `<h2>${map.winner} <span>wins</span></h2>`;
  const nameplate = `
    <img src="${assets}MapSkins/skin-plate-${map.titleArt}.png" alt="">
    <div class="victory-nameplate">${headline}${scoreLine}</div>`;
  return `<div class="victory-layout">
    ${venue(map)}
    <div class="victory-badge">
      ${isPlaque ? nameplate : headline + scoreLine}
    </div>
    ${action("Results", "results")}
  </div>`;
}

function broadcastStandings(map) {
  return `<ol class="finish-line" style="--places:${map.players.length}">${map.players.map(({ name, scores }, index) => `
    <li class="finisher ${index === 0 ? "finisher-winner" : ""}">
      <strong class="finish-place">${places[index]}</strong>
      <strong class="finish-name">${name}</strong>
      <dl class="finish-scores">${scoresFor(map, scores)}</dl>
    </li>`).join("")}</ol>`;
}

function podiumWinner(map) {
  const { name, scores } = map.players[0];
  return `<div class="winner-podium">
    <div class="podium-face">
      <strong class="podium-place">1<sup>st</sup></strong>
      <strong class="podium-name">${name}</strong>
      <dl class="finish-scores">${scoresFor(map, scores)}</dl>
    </div>
  </div>`;
}

function boxScore(map) {
  if (sport === "tennis") {
    return `<table class="results box-tennis">
      <thead><tr>${["Place", "Player", "Games", "Points won", "Aces", "Result"].map(label => `<th scope="col">${label}</th>`).join("")}</tr></thead>
      <tbody>${map.players.map(({ name, scores }, index) => `<tr class="${index === 0 ? "first" : ""}">
        <td class="place">${places[index]}</td><th scope="row">${name}</th>
        <td class="num">${scores[0]}</td><td>${tennisPoints[name]}</td><td>${tennisAces[name]}</td><td>${scores[1]}</td>
      </tr>`).join("")}</tbody>
    </table>`;
  }

  return `<table class="results frame-score">
    <thead><tr><th scope="col">Place</th><th scope="col">Player</th>
      ${Array.from({ length: 10 }, (_, i) => `<th scope="col" aria-label="Frame ${i + 1}">${i + 1}</th>`).join("")}
      <th scope="col">Total</th>
    </tr></thead>
    <tbody>${map.players.map(({ name, scores }, index) => {
      const [marks, runningTotals] = bowlingFrames[name];
      return `<tr class="${index === 0 ? "first" : ""}">
        <td class="place">${places[index]}</td><th scope="row">${name}</th>
        ${marks.split("|").map((mark, i) => `<td><span class="frame-marks">${mark}</span><strong class="frame-total">${runningTotals[i]}</strong></td>`).join("")}
        <td class="num">${scores[0]}</td>
      </tr>`;
    }).join("")}</tbody>
  </table>`;
}

function finalScore(map) {
  const { score, detail } = winningScore(map);
  return `<aside class="score-leaf" aria-label="Final score">
    <strong>${map.winner} wins</strong>
    <span class="leaf-amount">${score}</span>
    <span class="leaf-detail">${detail}</span>
  </aside>`;
}

function standingsTable(map, firstRow) {
  return `<table class="results">
    <thead><tr><th scope="col">Place</th><th scope="col">Player</th>${map.scores.map(header => `<th scope="col">${header}</th>`).join("")}</tr></thead>
    <tbody>
      ${map.players.slice(firstRow).map(({ name, scores }, index) => `<tr ${index + firstRow === 0 ? 'class="first"' : ""}>
        <td class="place">${places[index + firstRow]}</td>
        <td><span class="badge" aria-hidden="true" style="--bib:${colors[name]}"></span>${name}</td>
        <td class="num">${scores[0]}</td><td class="${sport === "tennis" ? "label" : "num"}">${scores[1]}</td>
      </tr>`).join("")}
    </tbody>
  </table>`;
}

function standings(map) {
  const winner = `${map.winner} wins`;
  const firstRow = design === "podium" ? 1 : 0;
  const showWinnerStrip = design === "box-score" || (sport === "golf" && design === "scorebook");
  const { score, detail } = winningScore(map);
  const table = design === "broadcast" ? broadcastStandings(map)
    : design === "box-score" ? boxScore(map)
    : standingsTable(map, firstRow);
  return `<div class="layout">
    ${venue(map, design === "podium" ? "" : winner)}
    ${design === "podium" ? podiumWinner(map) : ""}
    <div class="stack">
      <article class="card">
        ${stageTitle(map.heading, design === "open-book" || showWinnerStrip ? "" : winner)}
        ${showWinnerStrip ? `<div class="winner-strip"><span class="winner-rank">1st</span><strong>${winner}</strong><span class="winner-score"><strong>${score}</strong> ${detail}</span></div>` : ""}
        ${design === "open-book" ? `<div class="open-spread">${finalScore(map)}${table}</div>` : table}
      </article>
      <div class="result-actions">
        ${sport === "golf" ? action("Scorecard", "scorecard", true) : ""}
        ${action("Continue", "xp")}
      </div>
    </div>
  </div>`;
}

function scorecard(map) {
  return `<div class="layout">
    ${venue(map, `${map.winner} wins`)}
    <div class="stack">
      <article class="card">
        ${stageTitle("Scorecard", `${map.winner} wins`)}
        <table class="results golf-card">
          <thead><tr><th scope="col">Hole</th>${[1, 2, 3, 4, 5, "Total"].map(value => `<th scope="col">${value}</th>`).join("")}</tr></thead>
          <tbody>
            ${golfScores.map(([name, ...strokes], index) => `<tr class="${index === 1 ? "first" : ""}">
              <td>${name}</td>${strokes.map(value => `<td>${value}</td>`).join("")}
            </tr>`).join("")}
          </tbody>
        </table>
      </article>
      <div class="result-actions">${action("Back", "results", true)}${action("Continue", "xp")}</div>
    </div>
  </div>`;
}

function requiredXP(level) {
  const index = level - 1;
  return 200 + 60 * index + 6 * index * index;
}

function progress(player) {
  const total = player.xp.reduce((sum, [, award]) => sum + award, 0);
  let level = player.level;
  let current = player.start + total;
  while (level < 99 && current >= requiredXP(level)) {
    current -= requiredXP(level);
    level += 1;
  }
  return { total, level, current, required: requiredXP(level), leveled: level > player.level };
}

function rewards(map) {
  const player = map.players.find(({ name }) => name === xpPlayer);
  const { total, level, current, required, leveled } = progress(player);
  const levelBar = `<div class="level">
    <div class="level-labels"><strong>Level ${level}</strong><span>${current} / ${required} XP</span></div>
    <div class="level-track" role="progressbar" aria-label="Level progress" aria-valuenow="${current}" aria-valuemax="${required}">
      <span style="width:${100 * current / required}%"></span>
    </div>
  </div>`;
  return `<div class="layout">
    ${venue(map, player.name)}
    <div class="stack">
      <article class="card xp-card">
        ${stageTitle("XP earned", player.name)}
        <div class="xp-people" role="group" aria-label="Player XP">
          ${map.players.map(({ name }) => `<button type="button" data-player="${name}" aria-pressed="${name === xpPlayer}">${name}</button>`).join("")}
        </div>
        <div class="earnings">
          <div class="award-total">
            <div class="earned"><span data-earned="${total}">+${total}</span> <small>XP</small></div>
            <div class="earned-copy">${leveled ? "Level up" : "Club progress"}</div>
            ${design === "open-book" ? levelBar : ""}
          </div>
          <dl class="receipt">
            ${player.xp.map(([reason, points]) => `<div><dt>${reason}</dt><dd>+${points}</dd></div>`).join("")}
          </dl>
        </div>
        ${design === "open-book" ? "" : levelBar}
      </article>
      ${action("Continue", "next")}
    </div>
  </div>`;
}

function nextMenu(map) {
  const firstAction = sport === "tennis" ? "Rematch" : "Play Again";
  return `<div class="layout">
    ${venue(map)}
    <div class="stack">
      <article class="card next-card">
        ${stageTitle("Play again?")}
        ${action(firstAction, "action:replay")}
        ${action(map.change, "action:change", true)}
        ${action("Main Menu", "action:menu", true)}
        ${nextAction ? `<p class="small" role="status">Selected: ${nextAction}</p>` : ""}
      </article>
    </div>
  </div>`;
}

function calibrationCard(content, variant = "") {
  return `<div class="calibration-layout"><article class="card setup-card ${variant}">${content}</article></div>`;
}

function timingPanel(countdown) {
  return calibrationCard(`
    <h2>Swing when the ball hits the line</h2>
    <div class="timing-board" aria-hidden="true">
      <div class="ready-number" id="ready-count">${countdown ? swingTest.countdown / 1000 : ""}</div>
      <div class="baseline"></div><div class="contact"></div>
      <div class="ball" id="timing-ball" style="--lift:${countdown ? 8.5 : 1.4}cqw"></div>
    </div>
    <div class="swing-progress">
      <p id="swing-phase" class="swing-phase">${countdown ? "Get ready" : "Warm-up"}</p>
      <div class="pips" id="swing-pips" role="progressbar" aria-label="Recorded swings"
           aria-valuemin="0" aria-valuemax="${swingTest.scored}" aria-valuenow="0">
        ${Array.from({ length: swingTest.scored }, () => '<span class="pip" aria-hidden="true"></span>').join("")}
      </div>
    </div>`, "timing-card");
}

function calibration() {
  switch (step) {
    case "intro":
      return calibrationCard(`
        <h2>Tennis calibration</h2>
        <p>Scan your TV, then swing with the bouncing ball to sync your timing.</p>
        <p class="flash-notice">The TV will flash during the test.</p>
        ${action("Start", "scan")}`);
    case "scan":
      return `<div class="scan-layout">
        <h2>Point your phone at the TV</h2>
        <div class="scan-guide" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
      </div>`;
    case "warning":
      return calibrationCard(`
        <h2>Get ready for flashes</h2>
        <p>Keep your phone pointed at the TV.</p>`, "warning-card");
    case "flash":
      return '<div class="calibration-flash" aria-hidden="true"></div>';
    case "latency":
      return calibrationCard(`
        <h2>TV latency</h2>
        <p class="latency-reading">${screenTest.sampleLatency} <span>ms</span></p>
        ${action("Start calibration", "start-calibration")}`, "latency-card");
    case "aim":
      return `<div class="aim-layout"><article class="card">
        <h2>Forehand · Straight</h2><p class="instruction">Swing toward the ring.</p><p class="instruction">1 of 12</p>
      </article></div>`;
    case "ready":
      return calibrationCard(`<h2>Ready to play</h2><p>Tap Ready on your phone.</p>`);
    default:
      return timingPanel(step === "countdown");
  }
}

function runCalibrationPhase(update) {
  const started = performance.now();
  function tick(now) {
    calibrationAnimation = 0;
    if (update(now - started)) calibrationAnimation = requestAnimationFrame(tick);
  }
  tick(started);
}

function screenTestFrame(elapsed) {
  const time = elapsed - screenTest.warning;
  if (time < 0) return true;

  const lastPulseEnds = (screenTest.flashes - 1) * screenTest.interval + screenTest.lit;
  if (time >= lastPulseEnds + screenTest.resultHold) {
    if (step !== "latency") {
      showStage("latency");
      tv.querySelector("[data-go]")?.focus();
    }
    return false;
  }

  if (step !== "flash") showStage("flash");
  tv.querySelector(".calibration-flash").classList.toggle("lit", time % screenTest.interval < screenTest.lit);
  return true;
}

function swingTestFrame(elapsed) {
  const time = elapsed - swingTest.countdown;
  const { interval, warmups, scored, finishHold } = swingTest;
  const lastBounce = (warmups + scored) * interval;
  if (time >= lastBounce + finishHold) {
    showStage("ready");
    return false;
  }

  const next = time < 0 ? "countdown" : "bounce";
  if (step !== next) showStage(next);

  const landed = Math.floor(time / interval);
  const total = Math.max(0, Math.min(scored, landed - warmups));
  const phase = (time % interval) / interval;
  let height = 0;
  if (time < 0) height = 1;
  else if (landed === 0) height = 1 - phase ** 2;
  else if (time < lastBounce) height = 4 * phase * (1 - phase);

  const counter = tv.querySelector("#ready-count");
  const seconds = time < 0 ? String(Math.ceil(-time / 1000)) : "";
  if (counter.textContent !== seconds) counter.textContent = seconds;
  tv.querySelector("#timing-ball").style.setProperty("--lift", `${height * 8.5}cqw`);
  const phaseLabel = tv.querySelector("#swing-phase");
  const label = time < 0 ? "Get ready" : landed < warmups ? "Warm-up" : "Recorded swings";
  if (phaseLabel.textContent !== label) phaseLabel.textContent = label;
  const progress = tv.querySelector("#swing-pips");
  if (Number(progress.getAttribute("aria-valuenow")) !== total) {
    progress.setAttribute("aria-valuenow", total);
    progress.querySelectorAll(".pip").forEach((pip, index) => pip.classList.toggle("on", index < total));
  }
  return true;
}

function updateEarnedTotal(elapsed) {
  const total = tv.querySelector(".stage:not(.leaving) [data-earned]");
  if (!total) return;
  const delay = motion === "turn" ? 360 : motion === "spotlight" ? 300 : 230;
  const fraction = reducedMotion.matches ? 1 : Math.max(0, Math.min(1, (elapsed - delay) / 840));
  const value = Math.round(Number(total.dataset.earned) * (1 - (1 - fraction) ** 3));
  const label = `+${value}`;
  if (total.textContent !== label) total.textContent = label;
}

function sequenceAt(elapsed, scrub = false) {
  const beat = sequenceBeats.findLast(item => item.at <= elapsed) ?? sequenceBeats[0];
  if (beat !== playbackBeat) {
    showStage(beat.step, true, playbackBeat !== null);
    playbackBeat = beat;
  }
  const beatTime = Math.max(0, elapsed - beat.at);
  if (beatTime >= 720) tv.querySelector(".stage.leaving")?.remove();
  if (scrub) {
    tv.getAnimations({ subtree: true }).forEach(animation => {
      animation.pause();
      animation.currentTime = beatTime;
    });
  }
  if (beat.step === "xp") updateEarnedTotal(beatTime);
}

function playSequence() {
  stopSequence();
  const started = performance.now();
  playButton.textContent = "Stop sequence";
  sequenceAt(0);

  function tick(now) {
    const elapsed = now - started;
    if (elapsed >= sequenceEnd) {
      stopSequence();
      playButton.textContent = "Replay sequence";
      return;
    }
    sequenceAt(elapsed);
    sequenceAnimation = requestAnimationFrame(tick);
  }
  sequenceAnimation = requestAnimationFrame(tick);
}

function render() {
  const map = currentMap();
  Object.entries(map.palette).forEach(([key, value]) => review.style.setProperty(`--${key}`, value));
  tv.dataset.design = sport === "calibration" ? "scorebook" : design;
  tv.dataset.family = sport === "calibration" || isScorebook() ? "scorebook" : design;
  tv.dataset.motion = motion;
  tv.dataset.victory = victoryDesign;
  tv.dataset.sport = sport;
  tv.dataset.step = step;
  tv.dataset.venue = map.titleArt;
  const scene = sport === "calibration" ? (step === "aim" ? "scenes/aim.jpg" : "scenes/timing.jpg") : map.scene;
  const content = sport === "calibration" ? calibration()
    : step === "victory" ? victory(map)
    : step === "results" ? standings(map)
    : step === "scorecard" ? scorecard(map)
    : step === "xp" ? rewards(map)
    : nextMenu(map);
  tv.innerHTML = `<img class="scene" src="${scene}" alt=""><div class="shade" aria-hidden="true"></div><div class="stage">${content}</div>`;
  steps.innerHTML = availableSteps().map(([key, label]) => `<button type="button" data-step-tab="${key}" aria-pressed="${step === key}">${label}</button>`).join("");
  switchButtons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.sport === sport)));
  motionControls.hidden = sport === "calibration";
  victoryControls.hidden = sport === "calibration";
  designControls.hidden = sport === "calibration";
  simulateScan.hidden = sport !== "calibration" || step !== "scan";
  victoryButtons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.victory === victoryDesign)));
  motionButtons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.motion === motion)));
  designButtons.forEach(button => {
    const active = button.dataset.design === design;
    button.hidden = !active && (hasFinalDesigns() ? button.hasAttribute("data-earlier-design") : button.hasAttribute("data-final-design"));
    button.setAttribute("aria-pressed", String(active));
  });
}

designButtons.forEach(button => button.addEventListener("click", () => {
  design = button.dataset.design;
  selectStep(step);
}));

switchButtons.forEach(button => button.addEventListener("click", () => {
  const useDefault = design === defaultDesign();
  const showingVictory = step === "victory";
  sport = button.dataset.sport;
  if (useDefault || (!hasFinalDesigns() && finalDesigns.has(design))) design = defaultDesign();
  xpPlayer = "Adnan";
  selectStep(initialStep(showingVictory ? "victory" : undefined));
}));

steps.addEventListener("click", event => {
  const button = event.target.closest("[data-step-tab]");
  if (!button) return;
  const target = button.dataset.stepTab;
  selectStep(target, sport !== "calibration");
  if (sport === "calibration" && target === "countdown") runCalibrationPhase(swingTestFrame);
  if (sport === "calibration" && target === "bounce") swingTestFrame(swingTest.countdown + swingTest.interval / 2);
});

simulateScan.addEventListener("click", () => {
  if (sport !== "calibration" || step !== "scan") return;
  selectStep("warning");
  runCalibrationPhase(screenTestFrame);
});

motionButtons.forEach(button => button.addEventListener("click", () => {
  motion = button.dataset.motion;
  if (sequenceAnimation) playSequence();
  else showStage(step);
}));

victoryButtons.forEach(button => button.addEventListener("click", () => {
  victoryDesign = button.dataset.victory;
  motion = "snap";
  selectStep("victory", true);
}));

playButton.addEventListener("click", () => {
  if (sequenceAnimation) stopSequence();
  else playSequence();
});

tv.addEventListener("click", event => {
  const player = event.target.closest("[data-player]");
  if (player) {
    stopSequence();
    xpPlayer = player.dataset.player;
    render();
    Array.from(tv.querySelectorAll("[data-player]")).find(button => button.dataset.player === xpPlayer)?.focus();
    return;
  }

  const button = event.target.closest("[data-go]");
  if (!button) return;
  const target = button.dataset.go;
  if (target === "start-calibration") {
    selectStep("countdown");
    runCalibrationPhase(swingTestFrame);
  } else if (target.startsWith("action:")) {
    stopSequence();
    nextAction = button.firstChild.textContent;
    render();
  } else {
    selectStep(target, sport !== "calibration");
    if (sport === "calibration" && target === "scan") simulateScan.focus();
    else tv.querySelector("[data-go]")?.focus();
  }
});

document.getElementById("fullscreen").addEventListener("click", () => {
  if (document.fullscreenElement) document.exitFullscreen();
  else tv.requestFullscreen();
});
render();
if (query.has("play") && sport !== "calibration") playSequence();
