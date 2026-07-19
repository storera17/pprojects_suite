import type { Route } from './routes';

/** Describes the NavItem data shape so future readers know what fields travel through the app. */
export interface NavItem {
  route: Route['name'];
  label: string;
  ic: string;
}

/** Single source of truth for the left-rail navigation labels, icons, and route names. */
export const NAV_ITEMS: NavItem[] = [
  { route: 'dashboard', label: 'Dash', ic: '◉' },
  { route: 'tree', label: 'Tree', ic: '⟁' },
  { route: 'library', label: 'Decks', ic: '⬡' },
  { route: 'review', label: 'Review', ic: '◈' },
  { route: 'tutor', label: 'Tutor', ic: '⌬' },
  { route: 'search', label: 'Search', ic: '✦' },
  { route: 'practice', label: 'Practice', ic: '⟐' },
  { route: 'settings', label: 'System', ic: '◬' },
];

