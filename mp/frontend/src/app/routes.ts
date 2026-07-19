/** Union of all navigable screens; TypeScript uses it to prevent invalid route objects. */
export type Route =
  | { name: 'dashboard' }
  | { name: 'tree' }
  | { name: 'library'; deckId?: string; lessonId?: string }
  | { name: 'review'; boss?: string }
  | { name: 'tutor' }
  | { name: 'search'; query?: string }
  | { name: 'practice' }
  | { name: 'settings' };

