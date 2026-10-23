# Brag Plan: Cryptonite

## 9-Question Rubric

1. **What is the app?**
   Cryptonite is a production-grade steganography toolkit that combines military-grade AES-256 encryption with ChaCha20 scattered embedding to hide secret payloads inside PNG, JPEG, and MP3 files without perceptible distortion.
2. **What is the funniest or most impressive claim?**
   "What you see is never all there is." (Also: hiding data directly in raw JPEG DCT coefficients with zero re-encoding artifacts, while passing real-time Chi-squared steganalysis evasion).
3. **What is the visual hook?**
   The cyber-forensic "Obsidian Protocol" UI — deep obsidian backgrounds (`#0d1117`), Neon Emerald (`#10b981`) for SAFE verdicts, and Rose Red (`#ef4444`) for threats. Typography is Inter and JetBrains Mono for a highly technical terminal feel.
4. **What should be shown from the actual UI?**
   The bit-plane diff viewer, the terminal CLI embedding a secret PDF into an image, and the Steganalysis Module verifying a "SAFE" verdict (< 0.5% detection rate).
5. **What is the shortest satisfying video?**
   ~20 seconds. It needs to establish the premise, show the terminal/UI action, and reveal the hidden data.
6. **What tone fits best?**
   Preset: `cinematic`. 
   Creative direction: "A dramatic, trailer-scale security reveal. Big motion, technical precision, dark cyber-forensics."
7. **What should the audio feel like?**
   Cinematic bed with a low, tense swell. Restrained motion-matched accents for terminal keystrokes, and subtle audio-reactive glow when the payload encrypts and scatters. Narration enabled (Kokoro via Hyperframes).
8. **What should the share caption say?**
   "What you see is never all there is. We just shipped Cryptonite: a production-grade steganography toolkit bypassing statistical analysis. Hide encrypted payloads directly in JPEG DCT coefficients. Open source."
9. **What's the user flow worth showing?**
   Terminal: `cryptonite embed` (cover.png + secret.pdf) -> Steganalysis UI audit flashing "SAFE" -> Terminal: `cryptonite extract` recovering the payload.

---

## Storyboard (Cinematic, Landscape, Voice)

**Duration:** ~22s

**Scene 1: The Hook (0-4s)**
- **Visual:** Pitch black. A single clean image (e.g., a serene landscape) fades in slowly. 
- **Action:** A scanning line sweeps across the image, revealing the chaotic encrypted bit-planes underneath for a split second, then hiding them again.
- **Text:** `What you see is never all there is.` (JetBrains Mono, glowing Emerald).
- **Audio:** A deep cinematic bass drop.
- **Voiceover:** "You think you're looking at a standard image. You're not."

**Scene 2: The Action (4-11s)**
- **Visual:** Smash cut to the dark Obsidian terminal interface. 
- **Action:** Fast typing: `cryptonite embed -c cover.png -p secret.pdf`. The screen flashes as AES-256-CBC and ChaCha20 scattering progress bars hit 100%.
- **Text:** `Military-grade steganography.`
- **Audio:** High-speed mechanical keyboard clacks, resolving into a heavy UI lock-in sound.
- **Voiceover:** "Cryptonite embeds AES-256 encrypted payloads directly into PNG, JPEG, and MP3 files..."

**Scene 3: The Proof (11-17s)**
- **Visual:** The Steganalysis Web UI.
- **Action:** The system runs a real-time Chi-squared and SSIM check against the generated file. The result locks in: `VERDICT: SAFE (< 0.5% DETECTABILITY)` in bright Neon Emerald.
- **Text:** `Zero re-encoding artifacts. Statistically invisible.`
- **Audio:** Tension building, digital confirmation chime.
- **Voiceover:** "...and it completely bypasses real-time statistical steganalysis. Zero re-encoding artifacts. Statistically invisible."

**Scene 4: The Reveal / Outro (17-22s)**
- **Visual:** Terminal extracts the payload: `cryptonite extract -> recovered.pdf`. The project title "CRYPTONITE" slams onto the screen.
- **Text:** 
  `CRYPTONITE`
  `Production-grade steganography.`
  `Open source.`
- **Audio:** Final heavy cinematic boom. 
- **Voiceover:** "Hide in plain sight. Cryptonite is open source and ready for production."

---

## Music Cue Guidance
- **Track Style:** Dark cinematic trailer pulse.
- **Cues:** 
  - `0.0s`: Deep bass drop.
  - `4.0s`: Hard beat transition (Terminal typing starts).
  - `11.0s`: Swell leading into UI reveal.
  - `17.0s`: Final heavy hit on title slam.
