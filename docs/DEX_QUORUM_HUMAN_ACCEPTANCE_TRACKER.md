# DEX//QUORUM human acceptance tracker

**Status:** PENDING — no human conversation has been performed or accepted.
**Target:** Installed `Dex Quorum.app`, build from `codex/conversation-lens-integration` at `252fd5ffd2fb255e7d05dd3b7c10da7cf938d579`.
**Participants:** A: ____________________  B: ____________________  **Both consent before capture:** Yes / No
**Date / room / noise / Mac input:** ______________________________________________
**Observer:** ____________________  **Start / end time:** ____________________

Use participant labels A and B in this tracker. Do not save a recording or personal conversation notes. Enter only observed app behavior and participant ratings. Do not count generated speech or synthetic tests as human acceptance.

**Separate native smoke check (October 19, 2026):** One owner-initiated controlled mic run produced two displayed mic passages and a local early-conversation observation; Stop, idle health, and Erase succeeded. Input-meter response was not independently verified, and whether the captured phrase was naturally spoken or speaker-played generated speech was not established. This does not change the two-person acceptance status above.

## Ten-minute procedure

1. **0:00–1:00 — consent and setup.** Both people agree to the test. Open the installed native app, verify `NOT LISTENING`, select the in-app consent checkbox, and press Start. Confirm the app reports the Mac's physical input and the meter responds to room sound and speech.
2. **1:00–3:00 — natural conversation.** A and B discuss an ordinary topic they choose. Each speaks in their own words. Do not read a script. Note which visible transcript passages belong to A, B, Unknown, or Mixed and any obvious attribution errors.
3. **3:00–5:00 — overlap and uncertainty.** Continue naturally. If convenient, briefly interrupt or overlap as people normally might. Record whether overlap is marked Mixed/uncertain rather than confidently assigned to one person. Record any unsupported speaker attribution.
4. **5:00–6:00 — Stop and retry.** Press Stop. Review any pending audio window and explicitly Keep or Drop it according to what the participants heard. Restart only after the app reports idle and both participants still consent.
5. **6:00–8:00 — corrections and observations.** Correct one transcript phrase only if it is actually wrong. Inspect the latest observation and its source passage. Each participant independently rates whether the observation is grounded and useful; mark unsupported or intrusive claims.
6. **8:00–10:00 — finish and privacy.** Stop, resolve pending Keep/Drop, and wait for `NOT LISTENING`. Use Erase session. Confirm transcript and session state are empty; verify health reports `captureActive=false`, queue idle, and no stale capture. Record any failure before closing the app.

If any step cannot be completed safely or with consent, stop and mark it BLOCKED. Do not fabricate an observation or force speaker recognition. The test is about observed behavior, not a requirement to make the app guess.

## Results tracker

| Check | Result (PASS / FAIL / BLOCKED / NOT OBSERVED) | Observed evidence / short note |
|---|---|---|
| Native microphone permission requested only after consent and Start | | |
| Physical input identified; meter responds to actual speech | | |
| Speech transcribed and displayed | | |
| A/B attribution matches participants; errors noted | | |
| Unknown abstention when evidence is insufficient | | |
| Overlap is marked Mixed/uncertain when appropriate | | |
| Stop, pending Keep/Drop, and retry behave as expected | | |
| Corrections change only the selected transcript text | | |
| Observation is tied to a source passage and judged accurate | | |
| Coaching usefulness ratings — A: ___ / 5; B: ___ / 5 | | |
| Mic released; no ghost session, active lease, or queue remains | | |
| Session erased and both participants confirm privacy cleanup | | |

**A's acceptance / concerns:** ____________________________________________________

**B's acceptance / concerns:** ____________________________________________________

**Final outcome (ACCEPT / ACCEPT WITH ISSUES / BLOCKED):** ________________________

**Unresolved defects / follow-up evidence:** ______________________________________
