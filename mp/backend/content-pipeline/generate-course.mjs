// Course generation orchestrator: authored taxonomy + knowledge files →
// frontend/public/course/course.json
// Run: npm run generate
import { writeFileSync, mkdirSync } from 'node:fs';
import { buildStructure, chunkLessons, lessonTitle } from './taxonomy.mjs';
import { contextFor, buildLesson } from './synthesize.mjs';
import { generateCards } from './cards.mjs';
import { buildDiagrams } from './diagrams.mjs';
import { embed, packVector, EMBED_DIMS } from './embed.mjs';
import { slug } from './util.mjs';

/**
 * Assemble a full course from a deck/subdeck skeleton (as produced by
 * taxonomy.mjs's buildStructure(), or a fixture equivalent). Accepts
 * optional `contexts`/`entries` overrides so tests can build a small,
 * deterministic course without depending on the real authored content.
 */
export function assembleCourse(deckSkeleton, { contexts, entries } = {}) {
  const diagrams = buildDiagrams();

  const decks = [];
  const concepts = [];
  const cards = [];
  const lessons = [];
  let lessonUnlockIndex = 0;
  let curatedCount = 0;

  for (const deck of deckSkeleton) {
    const outDeck = { id: deck.id, title: deck.title, tagline: deck.tagline, order: deck.order, subdeckIds: [] };
    decks.push(outDeck);
    const subdecks = [];
    outDeck.subdecks = subdecks;

    for (const sd of deck.subdecks) {
      const ctx = contextFor(sd, contexts);
      const outSd = {
        id: sd.id, deckId: deck.id, title: sd.title, difficulty: sd.difficulty,
        sourceClass: null, domain: ctx.domain, lessonIds: [],
      };
      subdecks.push(outSd);
      outDeck.subdeckIds.push(sd.id);

      const seenInSd = new Set();
      const sdConcepts = sd.concepts
        .filter((term) => {
          const key = slug(term, 80);
          if (seenInSd.has(key)) return false; // duplicate terms
          seenInSd.add(key);
          return true;
        })
        .map((term, i) => ({
          id: `${sd.id}-${i}`,
          term,
          displayTerm: term,
          rawTerm: term,
          excelRow: null,
          difficulty: sd.difficulty,
          subdeckId: sd.id,
          deckId: deck.id,
        }));

      const lessonChunks = chunkLessons(sdConcepts);
      lessonChunks.forEach((chunk, li) => {
        const lessonId = `${sd.id}-L${li + 1}`;
        const lessonObj = {
          id: lessonId, subdeckId: sd.id, deckId: deck.id,
          title: lessonTitle(chunk.map((c) => c.displayTerm), li),
          order: li,
          unlockIndex: lessonUnlockIndex++,
          conceptIds: chunk.map((c) => c.id),
          cardIds: [],
        };
        lessons.push(lessonObj);
        outSd.lessonIds.push(lessonId);

        for (const concept of chunk) {
          const neighbors = chunk.filter((c) => c.id !== concept.id).map((c) => c.displayTerm);
          const mini = buildLesson(concept, ctx, neighbors, entries);
          if (mini.curated) curatedCount++;
          concept.lessonId = lessonId;

          const conceptCards = generateCards(concept, mini, ctx, diagrams);
          for (const card of conceptCards) {
            card.lessonId = lessonId;
            card.subdeckId = sd.id;
            card.deckId = deck.id;
            cards.push(card);
            lessonObj.cardIds.push(card.id);
          }

          const { entry, ...publicLesson } = mini; // entry is pipeline-internal
          concepts.push({
            ...concept,
            cardIds: conceptCards.map((c) => c.id),
            mini: publicLesson,
            vec: packVector(embed(`${concept.displayTerm}. ${publicLesson.explanation} ${publicLesson.workplace}`)),
          });
        }
      });
    }
  }

  return {
    meta: {
      name: 'MomentumProdigy — generated from real course material and textbooks',
      generatedAt: new Date().toISOString(),
      embedDims: EMBED_DIMS,
      counts: {
        decks: decks.length,
        subdecks: decks.reduce((a, d) => a + d.subdecks.length, 0),
        lessons: lessons.length,
        concepts: concepts.length,
        cards: cards.length,
        clozeCards: cards.filter((c) => c.type === 'cloze').length,
        occlusionCards: cards.filter((c) => c.type === 'occlusion').length,
        curatedConcepts: curatedCount,
      },
    },
    decks,
    lessons,
    concepts,
    cards,
    diagrams,
  };
}

/** Builds and writes the production course JSON file used by the frontend. */
export function generateCourse() {
  return assembleCourse(buildStructure());
}

const isMain = process.argv[1] && import.meta.url.endsWith(process.argv[1].replace(/\\/g, '/').split('/').pop());
if (isMain) {
  const course = generateCourse();
  mkdirSync(new URL('../../frontend/public/course/', import.meta.url), { recursive: true });
  const outPath = new URL('../../frontend/public/course/course.json', import.meta.url);
  writeFileSync(outPath, JSON.stringify(course));
  const c = course.meta.counts;
  console.log(`Course generated → frontend/public/course/course.json`);
  console.log(`  decks=${c.decks} subdecks=${c.subdecks} lessons=${c.lessons} concepts=${c.concepts}`);
  console.log(`  cards=${c.cards} (cloze=${c.clozeCards}, occlusion=${c.occlusionCards})`);
  if (c.concepts > 0) {
    console.log(`  curated mini-lessons: ${c.curatedConcepts}/${c.concepts} (${Math.round((100 * c.curatedConcepts) / c.concepts)}%)`);
  }
}