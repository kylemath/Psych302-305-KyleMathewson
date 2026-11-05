# Week 9 · Make a game

**Name:**
**Date of class:** 4 November 2026
**Lab page:** https://kylemath.github.io/Psych302-305-KyleMathewson/game.html

This folder starts with `game.html`, a small working game. Tonight you make
it your own. By the end, this folder should have your changed `game.html`,
a saved data file (`game-week09.csv`), and this README. Work on your own.

To play it: open `game.html` in your browser (double-click it, or use
Live Server in VS Code). After every change, save and reload.

---

## 1. My game (3 points)
What is your game called, and how do you play it? Two or three sentences,
so someone who has never seen it could play.

Jungle Harmony: Monkey's Canopy. To play, allow microphone permissions, adjust your voice threshold bar, and click Start. When a banana appears hidden in the canopy, shout "BANANA!" loud enough to cross the threshold. Stay completely quiet for coconuts, between rounds, or once the banana has gone, or you'll lose a life! Watch the animated companion monkey in the corner react to your voice and your success.

## 2. What I changed (3 points)
List at least three changes you made to the starter game. For each one,
say what you changed in the code (for example: "raised `occlusion` in
SETTINGS so the fruit sits further under the leaves"). At least one change should be more than a
setting: a new rule, a new sound, a new thing that happens, a new column
in the data.

1. **Dynamic Jungle Wind Physics (Real-time Bio-Feedback):** I modified the drawing functions (`drawTree`, `drawVine`, `drawFerns`, etc.) to multiply their sway values by a newly added `windIntensity` factor. This factor is bound to the microphone's smoothed sound volume (`smoothLevel`). Shouting or speaking now physically sways and rustles the entire canopy in real-time, giving immediate sensory feedback.
2. **Expressive Procedural Monkey Companion & Floating Text:** I added a fully cartoonish helper monkey drawn dynamically using HTML Canvas geometric paths, sitting on a leafy branch in the bottom right corner. The monkey breathes, wags its tail, waves when excited (banana on screen), covers its eyes when scared (coconut), dizzily rolls its eyes on mistakes, eats a mini-banana when you win, and falls asleep (Zzz) when the game ends. I also implemented a floating text popup system (`spawnFloaty`) displaying `+10`, `+5 SAFE`, `MISS!`, `COCONUT!`, and `-1 LIFE` that drifts and fades up.
3. **Atmospheric Environment Themes & Audio Synthesis:** I replaced the single standard beep sound with clean retro synthesized chords and ditty soundscapes generated on-the-fly via the Web Audio API (a rising success arpeggio, safe chime, slide buzzer for errors, level-up trumpet fanfare, and game-over melody). I also added a continuous procedural forest wind ambient noise modulated by mic volume, background bird chirping, and beautiful atmosphere coloring (Dawn, High Noon, Sunset, Bioluminescent Midnight with glowing fireflies) that cycle based on the current level.

## 3. My guess, then my data (2 points)
Before you play your final round, write one guess about how you will do.
For example: "I will miss more bananas when they are deep and heavily covered."
Then play, save the CSV in this folder, and say what happened.

- **My guess (written before playing):** I guess that I will miss more bananas when they are deep in the trees (depth 3) or highly occluded by leaves, as the extra visual complexity, fog, and dimness will make it harder to react within the fast-decreasing level time limits.
- **What happened:** (use numbers from your CSV: how many turns, how many
  mistakes, at what level)

## 4. One reason not to trust it (1 point)
One reason your result might not mean much (only one person, only one
game, you got better with practice, ...).

## 5. Use of AI (1 point)
- Did you use an AI tool (like Copilot or ChatGPT)? yes / no
- If yes: what did you ask, what did you keep, and what did you change?

## Could this be part of your project? (optional, no points)
One sentence.
