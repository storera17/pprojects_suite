import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './ui/App';
import './styles/tokens.css';
import './styles/layout.css';
import './styles/components.css';
import './styles/screens.css';
import './styles/theme-light.css';

/**
 * Application bootstrap.
 *
 * The HTML page supplies one empty #root element; this file attaches React to
 * that element and loads the global stylesheet layers in a predictable order:
 * tokens → layout → reusable components → screen modules → theme override.
 */
createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
