// Entry point for the visual-composer SPA.
// Slice SLICE-003-001-01 keeps this intentionally minimal — downstream
// slices (02+) wire up the parser-output preview and the canvas.
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

const rootEl = document.getElementById('root');
if (rootEl) {
  createRoot(rootEl).render(
    <StrictMode>
      <div>Visual Composer — scaffolding (SLICE-003-001-01)</div>
    </StrictMode>,
  );
}
