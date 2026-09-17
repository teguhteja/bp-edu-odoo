# All state lives in the view; no Python models

Messages, styling, schedule window, and behavior flags are stored as content and data attributes in the editable view (set via native builder options). No Python models, no backend settings screens. This keeps translation, multi-website copy-on-write, and cache-safety native for free. Consequences: schedule and dismissal are enforced client-side (the bar renders hidden and JS reveals it), so visitors without JavaScript never see the bar — accepted, since rotation already requires JS.
