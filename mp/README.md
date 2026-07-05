<div
     style="padding: 20px;
            color: white;
            font-size: 250%;
            text-align: center;
            display: fill;
            border-radius: 5px;
            background-color: #b8482f;
            overflow: hidden;
            font-weight: 700;
            border: 5px solid #d4ccc4;"
    Momentum Prodigy (mp)
</div>

> MomentumProdigy is an offline-first spaced-repetition learning command center for analytics mastery. It combines a locked course structure, Anki-style review scheduling, semantic search, an offline tutor, voice commands, and progress systems in one React/TypeScript app. This public repository is sanitized for GitHub. It ships with synthetic demo course content so the application, tests, and build can be reviewed without publishing private course packets, extracted textbook text, or model weights.

# **Architecture**

## 1. Course generation pipeline (build time)

```
Concepts to learn and include.xlsx
        │  extract.mjs        — parse rows, fix ~40 known typos
        ▼
  taxonomy.mjs                — 55 classes → 10 decks (foundational → advanced),
        │                       semantic clustering of unclassified tool rows
        │                       into 7 subdecks, lesson chunking (5–9 concepts)
        ▼
  synthesize.mjs              — per-concept mini-lesson:
        │                       glossary entry (longest-match wins) + class context
        │                       → explanation / how / why / workplace / worked example /
        │                         key terms / mistakes / related / 5 sources
        ▼
  cards.mjs                   — cloze cards from «marked» phrases (one blank per card),
        │                       term-recall, applied-scenario, pitfall variants;
        │                       difficulty-scaled budgets (d1≈5–8, d3 up to 22);
        │                       image-occlusion cards where diagrams genuinely match
        ▼
  diagrams.mjs + embed.mjs    — 24 original SVG diagrams with labeled mask regions;
        │                       192-dim hashed-feature embeddings per concept
        ▼
public/course/course.json     — ~13 MB, bundled into every installer
```

The knowledge base (`pipeline/knowledge/`) is the researched content layer:
- `contexts-a/b.mjs` — 62 class/cluster teaching contexts (overview, why,
  workplace, scenario, mistakes, 5-source pool each).
- `glossary/*.mjs` — ~600 curated entries covering **100% of the 1,370
  concepts** via normalized longest-substring matching. Guillemets «…» mark
  phrases that become cloze blanks, keeping card quality editorial rather
  than algorithmic.
- `sources.mjs` — 80+ credible references (textbooks, papers, official docs,
  university course notes) from which every card's 5-source evidence comes.

## 2. Runtime data model (local "database")

Persistence is namespaced JSON in `localStorage` behind a `StorageAdapter`
(in-memory adapter for tests). Schema (`src/core/store.ts`):

| Key | Contents |
|---|---|
| `cortex.profile` | username, PBKDF2 salt+hash, WebAuthn credential id |
| `cortex.settings` | sound / voice / speak-answers toggles |
| `cortex.cardStates` | per-card `CardState`: phase, due, interval, ease, steps, lapses, streak, accuracy |
| `cortex.reviewLog` | append-only review history (capped 20k) |
| `cortex.introducedByDay` | new-card pacing tally |
| `cortex.gamification` | xp, streak, badges, reviews, boss wins |
| `cortex.practiceCards` / `practiceStates` | AI Practice deck (editable) + its scheduling |

The locked course itself is **never** in mutable storage — it is the static
`course.json`, which is why it cannot be edited or reset.

## 3. Scheduler (`src/core/scheduler.ts`)

Original SM-2-family implementation mirroring Anki behavior:

- Phases: `new → learning (1m, 10m) → review`; lapses → `relearning (10m)`.
- Graduation 1d, easy-graduation 4d; ease starts 2.50, floor 1.30.
- Review answers: Again (lapse: ease −0.20, interval ×0.5), Hard (ease −0.15,
  interval ×1.2), Good (interval ×ease), Easy (ease +0.15, ×ease×1.3).
- Deterministic ±5% interval fuzz prevents due-date clumping.
- **Automatic new-card pacing** (no manual limit): daily allowance =
  `clamp(20 − dueReviews/8, 4, 20)`, introduced strictly in lesson order.

## 4. Mastery & unlocking (`src/core/mastery.ts`)

- Card mastery ∈ [0,1] grows with graduation, correct streak, interval
  maturity, and lifetime accuracy.
- Lesson mastery = mean card mastery; readiness = share of cards in `review`.
- Lesson *i+1* unlocks when lesson *i* has **mastery ≥ 0.9 AND readiness ≥ 0.8**.
- Weak topics: concepts with accuracy < 75% or ≥2 lapses — feed the dashboard
  and the AI-practice generator.

## 5. Search (`src/core/search.ts`, `src/core/embedding.ts`)

Hybrid offline search: keyword scoring (title-weighted, stopword-filtered)
blended 65/35 with cosine similarity over **hashed word+trigram embeddings**.
The identical embedding function runs in the pipeline (course vectors,
int8-quantized base64) and in the app (query vectors); a parity test pins the
two implementations together. Type weighting keeps concepts above raw cards;
results deduplicate by title.

## 6. Tutor (`src/core/tutor.ts`)

Two tiers behind one interface — see `docs/OFFLINE_AI.md`. The always-on tier
retrieves top concepts (embedding + keyword), then composes answers from
curated lesson fields with intent routing (what/why/how/example/mistake/
comparison). Card explanation re-grounds the revealed answer in the concept's
lesson. Practice generation clozes lesson sentences *not used* by locked
cards, so the AI Practice deck supplements rather than duplicates.

## 7. UI (`src/ui/`)

React 18, no router library (typed route state), screens:
Login · Dashboard · SkillTree · Library (decks→subdecks→lessons→mini-lessons)
· Review (cloze + occlusion, voice, tutor explain) · TutorChat · Search ·
Practice · Settings. WebAudio-synthesized UI sounds (zero assets, mutable).
Card visual identity (hue/glyph/pattern) is derived from the card id hash at
generation time and is not user-editable.

# **Momentum Prodigy — User Guide**

## First launch

1. Install (Windows MSI, macOS DMG, or iPhone app) and open CORTEX.
2. Create your **local operator profile** — a name and password. There is no
   cloud account; everything stays on your device.
3. (Recommended) In **System**, enroll **Face ID / Touch ID / Windows Hello**.
   If you ever forget your password, biometric unlock still gets you in while
   it remains enrolled.
4. The full course is already inside the app — nothing to import.

## How studying works

- Press **◈ Start Review** on the dashboard. CORTEX shows due cards first,
  then introduces new cards from your current lesson at an automatic pace
  (lighter on heavy review days — you never set a limit).
- Read the card, recall the blanked answer (or the masked diagram element),
  press **Show answer** (space), then grade yourself:
  - **Again** — didn't know it (card returns in ~1–10 minutes)
  - **Hard** — barely (shorter next interval, slightly harder ease)
  - **Good** — knew it (normal growth)
  - **Easy** — trivial (bigger jump)
  The intervals shown under each button are exactly when you'll see the card
  next. Keyboard: 1–4.
- After revealing, **⌬ Tutor: explain this answer** gives a grounded
  explanation; the **Extra / Evidence** drawer lists the five sources behind
  the card.

## Lessons & the skill tree

Open **⟁ Tree**. Each column is a deck; each node a lesson. A lesson unlocks
the next when it reaches **90% mastery** and most of its cards have graduated
into review. You can read any *unlocked* lesson's mini-lessons in **⬡ Decks**
at any time — reading is never blocked, only the pacing of new cards.

## The AI tutor

**⌬ Tutor** answers questions about the course and broader analytics, data,
and coding topics — fully offline. Use the microphone for voice questions;
enable **Speak tutor answers** in System to hear responses. Conversations are
not saved after the session ends.

## Voice commands

Say: "start review", "show answer", "again/hard/good/easy", "open dashboard",
"ask tutor", "open skill tree", "search ⟨topic⟩", "mute".

## AI Practice deck

When CORTEX detects weak topics (lapses, low accuracy), generate extra
practice from the dashboard, the Tutor screen, or **⟐ Practice**. Practice
cards use the same scheduling, ride along in your review queue, and — unlike
the locked course — can be edited, deleted, exported, or reset.

## Boss reviews

Inside any deck (⬡ Decks → deck → "Boss review"), face the deck's hardest
cards in one gauntlet. Clear it with ≤20% misses for bonus XP and the Boss
Protocol badge.

## Tips

- Daily consistency beats volume: clear your due queue every day to protect
  your streak — the scheduler does the rest.
- Trust **Again**. Failing a card is the scheduler working, not you failing.
- Use Search (✦) like an index: keyword or plain-language ("making models not
  overfit") both work, offline.

# **Compatibility**

CORTEX implements compatible *concepts* with original code:

- **Cloze syntax** — cards use exact `{{c1::answer}}` /
  `{{c1::answer::hint}}` syntax (`src/core/cloze.ts`), so card text moves
  between the systems verbatim.
- **Scheduling** — SM-2-family with parameters (learning steps
  1m/10m, graduation 1d, easy 4d, ease 2.5 start / 1.3 floor, lapse behavior,
  interval fuzz), and the same four grades.
- **Image occlusion** — mask/reveal behavior mirrors image-occlusion
  cards over original generated diagrams.

## Export

- **AI Practice deck → JSON** from the Practice screen (`⇪ Export JSON`).
  Each card's `text` field is ready cloze text: paste into an Anki note
  of type *Cloze* directly, or convert the JSON to TSV
  (`text` column) and use Anki's File → Import.
- The locked course is intentionally not exportable from the UI (it is a
  locked product), but `public/course/course.json` is open data — a script can
  map `cards[].text` to cloze notes if you want it in.

## Import

- Practice-deck JSON exported from another CORTEX install imports via
  `Store.importPractice` (exposed for tooling; UI import intentionally
  minimal in v1).
- **`.apkg` import/export is not implemented in v1.** `.apkg` is a zip
  containing an SQLite database (`collection.anki2`); supporting it offline
  in-app requires bundling an SQLite reader. This is the documented gap —
  the JSON/TSV path above covers the practical interchange today. See
  `docs/LIMITATIONS.md`.

## Anki-Compatibility

- `.apkg` files are anki-platform files and are compatible with this platform.

# **Building, Running, Testing, Packaging**

## Prerequisites

- Node.js 18+ (tested on 24)
- For Windows/Mac packaging: Rust toolchain (`rustup`) — Tauri 2
- For iPhone: macOS with Xcode 15+, CocoaPods

## Develop & test

```bash
npm install
npm run generate      # regenerate public/course/course.json from the Excel file
npm test              # vitest — 71 tests (parsing, clustering, scheduling, search, tutor, auth, persistence…)
npm run dev           # Vite dev server at http://localhost:5173
npm run build         # generate + typecheck + production bundle in dist/
npm run preview       # serve the production bundle
```

The generated `public/course/course.json` is committed, so `npm run dev`
works even without the Excel file present.

## Windows packaging (MSI / NSIS)

```bash
# one-time
rustup default stable
npm i -D @tauri-apps/cli
# icons: place icon.ico / 128x128.png under src-tauri/icons (generate from public/icon.svg, e.g. `npx @tauri-apps/cli icon public/icon.svg`)

npm run desktop:build         # = tauri build → src-tauri/target/release/bundle/msi|nsis
```

Dev loop with the native shell: `npm run desktop:dev`.

## macOS packaging (DMG / .app)

Same commands on a Mac:

```bash
npm i -D @tauri-apps/cli
npm run desktop:build         # → src-tauri/target/release/bundle/dmg|macos
```

Sign/notarize with your Developer ID for distribution outside your machine
(`APPLE_SIGNING_IDENTITY` env vars per Tauri docs).

## iPhone packaging (native iOS app)

```bash
npm i -D @capacitor/cli @capacitor/core @capacitor/ios
npm run build
npm run ios:add               # creates ios/ Xcode project (once)
npm run ios:sync              # copies dist/ into the iOS app
npm run ios:open              # opens Xcode → set signing team → Run on device
```

Notes:
- Face ID: WebAuthn platform authenticator works in WKWebView on iOS 16+; for
  the richest experience add `@aparajita/capacitor-biometric-auth` and call it
  from `src/core/auth.ts` (the interface is isolated there).
- Voice: iOS provides on-device dictation and TTS through the same Web Speech
  APIs the app already uses.
- App Store: the bundle is fully offline; no privacy-impacting SDKs.

## Optional: local LLM for the tutor's generative tier

```bash
node scripts/fetch-models.mjs desktop   # Qwen2.5-3B-Instruct Q4_K_M (~2.0 GB)
node scripts/fetch-models.mjs ios       # Qwen2.5-1.5B-Instruct Q4_K_M (~1.0 GB)
```

Then wire the bridge per `docs/OFFLINE_AI.md`. The app is fully functional
without this step — the knowledge tutor ships inside the bundle.

## Test matrix

`npm test` covers: Excel parsing · deck/subdeck clustering · lesson ordering ·
card generation format · cloze rendering · image-occlusion rendering ·
spaced-repetition scheduling · review-button behavior · lesson unlocking ·
mastery calculation · weak-topic detection · keyword + semantic search ·
embedding parity (app ↔ pipeline) · offline tutor fallback · local login ·
AI-practice creation/reset · data persistence · voice-command grammar.

# **Limitations**

1. **Card volume vs. the 20–30 spec for advanced concepts.** Card counts scale
   by difficulty (simple ≈ 4–8, advanced up to ~22 where curated content
   supports it), averaging ~6.5 cards across 1,370 concepts (~8,900 total).
   Forcing 20–30 on *every* advanced concept would require padding with
   redundant clozes, which harms learning quality; we chose editorial blanks
   («marked» phrases) over volume. The budget knobs are in
   `pipeline/cards.mjs` (`clozeBudget`) if you want more.

2. **Semantic search is hashed-feature, not neural.** Offline semantic search
   uses word+trigram hashed embeddings — excellent for paraphrase with shared
   morphology, weaker for pure synonymy ("automobile" ≈ "car"). Keyword
   search compensates. Upgrade path: swap `src/core/embedding.ts` for an
   ONNX MiniLM via transformers.js (+~25 MB) without touching the index API.

3. **Tier-2 LLM weights are fetched, not committed.** The generative tutor
   model (~1–2 GB GGUF) can be bundled into installers
   (`src-tauri/tauri.conf.json` resources) but is not committed to the repo;
   `scripts/fetch-models.mjs` downloads it. Tier 1 (knowledge tutor) is fully
   bundled and the app meets "offline after installation" without Tier 2.

4. **Voice depends on platform speech engines.** Web Speech STT/TTS runs
   on-device on current iOS/macOS/Windows, but some older configurations
   route STT through OS cloud services. The `VoiceBridge` interface allows a
   whisper.cpp/piper sidecar for guaranteed-offline voice (documented in
   OFFLINE_AI.md, not wired by default).

5. **`.apkg` import/export not implemented** — see ANKI_COMPAT.md for the
   JSON/TSV interchange that is implemented, and why.

6. **Biometric login uses WebAuthn platform authenticators.** Works in
   browsers and WebView2 today; inside iOS WKWebView, the most reliable
   Face ID route is the Capacitor biometric plugin noted in BUILDING.md.
   Password login works everywhere. Local data is not encrypted at rest
   (explicitly out of scope for v1 per spec).

7. **Some glossary entries are concise.** All 1,370 concepts hit curated
   entries (100% coverage), but a minority share an entry with sibling terms
   (e.g., several LSTM-gate rows map to one gates entry plus their specific
   one). The matcher always prefers the most specific entry available.

8. **Packaging is configured but artifacts aren't pre-built.** Tauri/Capacitor
   configs are committed and verified to build the web bundle; producing
   signed MSI/DMG/IPA requires the platform toolchains (Rust/Xcode) per
   BUILDING.md — it cannot be done from inside this repo alone.
