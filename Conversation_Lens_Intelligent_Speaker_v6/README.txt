CONVERSATION LENS v6 — ADAPTIVE LISTENING + CONVERSATIONAL SPEAKER MEMORY
======================================================================

STATUS: Usable experimental build. Browser UI and local backend regressions PASS.
PHYSICAL MICROPHONE + ACCURACY WITH TWO REAL SPEAKERS: NOT YET VERIFIED.

NEUTRAL DEFAULT (current repository revision)
- Context starts empty on every fresh page load; no scenario or participant history is loaded from browser form restoration.
- The default mode is Observe neutrally. Focused modes are explicit opt-ins.
- The example uses a routine meeting, not a private relationship dispute.
- The optional context field is passed to the AI only when the user enters it.
- Names are learned only from consenting, actual recorded introductions or separate voluntary enrollment; context never creates a voiceprint.

LATEST PRIVACY + USABILITY UPLIFT
- BIG MAC AI IS OPT-IN: availability checks do not send transcript text; actively enable the checkbox. Only text/context go through the private LAN tunnel, never audio or embeddings.
- The same enrollment recording is rejected as a repeated sample or under a different speaker name.
- Another open tab receives a capture conflict. Approve takeover explicitly or Stop the previous tab.
- Correct transcribed words using Correct words. Correcting text does not verify or relabel a voice.
- Review the literal passage behind each sourced local cue. Grounded AI quotations also link to matching passages.
- Processing backlog and skipped recording windows are visibly tracked; skipped audio cannot silently be recovered.
- On narrow screens setup/mic precede coaching/transcript, and DOM order matches.
- With Whisper down use manual text entry; external browser speech providers are disabled.

WHAT CHANGED FROM v5
- Silence-guided local audio segmentation: end a window around 0.9s after measured silence following speech, never sooner than ~2.8s, with an 8.9s hard cap. This is acoustic-energy heuristics, not a trained turn boundary detector. If the input meter is unavailable, fixed-length clipping remains available.
- Visible real-time mic input meter and no-signal warning. The meter tests microphone energy, not proof that words can be transcribed.
- Real server capture lease: Start opens a random session through the localhost server. Stop explicitly revokes it. The server rejects stale uploads and discards late Whisper results rather than assigning identities or displaying old text.
- Explicit "Erase all session data": stop capture, erase transcript text and optional context in the page, reset to neutral observation, and wipe all in-memory speaker profiles; race-safe against enrollment still finishing.
- Grounded Big Mac coaching: invented text quotations are rejected in favor of a no-match warning. The model can still make interpretive errors.
- All v5 spoken self-introduction behavior, enrollment, voice correction, Unknown/Mixed safeguards and manual transcript entry are preserved.

RUN ON THE MACBOOK AIR / BRAVE
1. From the cloned repository in ~/Conversation_Lens, launch with:
   cd "$HOME/Conversation_Lens" && /bin/zsh ./Conversation_Lens_Intelligent_Speaker_v6/Launch_Conversation_Lens.command
2. Leave Terminal running. Brave should open Conversation Lens over http://127.0.0.1 at a random port.
3. Verify LOCAL WHISPER READY and LOCAL VOICE MODEL READY.
4. Tell everyone present about transcription and voice recognition. Confirm transcription consent separately from the spoken-name learning opt-in.
5. Press Start listening, allow Brave microphone access, say a complete sentence, and confirm the transcript appears.
6. With consent to speaker learning enabled, have someone say something like: "Hi, this is Dale, and I want to explain something important to you."
   The label Dale ? means provisional, NOT confirmed identity. Additional consistent speaking windows may strengthen it. Manually correct errors.
7. Press Stop whenever needed. For additional privacy, press Erase all session data and confirm it; this also clears custom context and names. Close the Terminal server to permanently end that session.

DEPENDENCIES
- MacBook Air / macOS; Brave; Homebrew whisper-cli and FFmpeg; existing DexDictate ggml-base model used read-only.
- sherpa-onnx == 1.13.8 and NumPy in isolated ~/Library/Application Support/ConversationLensSpeakerID/venv; a 25 MiB speaker ONNX model under the same application support folder.
- The launcher executes Setup_Speakers.command, which installs missing speaker dependencies and checksum-verifies the exact model. It does NOT replace DexDictate or modify its model.
- Optional Big Mac tunnel: Ollama model gemma3:4b at localhost:11435; without it, local linguistic cues still work.
- No Docker, cloud account, hosted server, or API key is required for the normal local Whisper path.

PRIVACY
- Conversation audio is POSTed only to the MacBook localhost server in normal Whisper mode; ephemeral FFmpeg/Whisper files are removed after worker completion. No automatically saved transcript history. Speaker vectors and audio hashes stay in server RAM and are lost at server exit or erase.
- The coaching prompt sends transcript snippets and editable context, NOT raw mic audio or voice embeddings, to Big Mac via the existing local tunnel.
- STOP prevents further microphone capture immediately in the UI and sends a revoke request to the server; any already-running Whisper process may finish computation but its result is discarded after the server receives the revoke request. STOP does not erase preexisting voice profiles unless you choose Erase or Forget profiles.
- Browser speech-service fallback is deliberately disabled; when local Whisper is unavailable, manual text entry still works. This prevents unrequested external audio processing.
- This is NOT authentication, surveillance, or evidence of consent to record. Do not identify someone from their voice without their knowledge and consent.

KNOWN LIMITS
- Early name attribution is a linguistic and acoustic hypothesis, not proof. Whisper can mistranscribe names, especially short introductory phrases.
- A speaker saying "This is Dale" might be introducing someone else or quoting them. Do not take the name at face value in a conflict.
- Two people speaking inside one short clip cannot be reliably separated word by word; a label may be Unknown, Unassigned, Mixed, or wrong.
- Volume threshold, room noise, mic placement, pauses, accents, and similar-sounding speakers materially affect identification.
- Speaker cosine scores are uncalibrated heuristics, NOT identity probabilities or confidence percentages.
- Audio segmentation does not guarantee sentence boundaries. Long uninterrupted speaking can still be cut at 8.9 seconds.
- Brave UI tests simulate microphone input and acoustic vectors; full-stack synthetic-speech smoke exercised real FFmpeg, Whisper, the ONNX voice embedding worker and Big Mac AI on the MacBook. Human voice accuracy remains untested.
- Big Mac AI can take several seconds per suggestion; not an instantaneous interruption system.
- Second-tab takeover revokes the previous tab's capture session without modifying earlier text.

ROLLBACK
v5, v4, v3 and DexDictate were not modified. This ZIP installs as a separate folder. Stop v6 and launch your previous version to roll back.
