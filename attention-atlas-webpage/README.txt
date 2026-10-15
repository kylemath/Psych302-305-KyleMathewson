Attention Atlas — portable website export

This is a complete static website. No build step, API keys, or backend are required.

HOST ONLINE
1. Extract this ZIP.
2. Upload the extracted files to a static web host, keeping index.html at the root.
3. Open the resulting HTTPS URL. HTTPS enables service workers and app installation.

PREVIEW ON YOUR COMPUTER
From the extracted folder, run:
    python3 -m http.server 8000
Then open http://localhost:8000 in Chrome.
Opening index.html by double-clicking may prevent the reading data from loading,
because the app fetches papers.json. Use an HTTP server instead.

CONTENTS
index.html: app page
style.css: responsive styling
app.js: reader, progress, and seven mechanism demos
papers.json: seven-paper reading sequence
library.html: complete 30-paper annotated catalogue
manifest.webmanifest, sw.js, icon files: installable app and offline cache

The app caches its own files after a successful online load. Original papers
remain external links and are not included as PDFs. Progress is stored in the
browser and does not sync between devices. Morning reminders are separate
ChatGPT tasks; exporting the website does not export those reminders.

The original hosted copy is private to its owner. Hosting these files elsewhere
uses that host's access settings; Sites sign-in restrictions are not part of
this portable static export.

All demos are teaching illustrations, not reproductions of published experiments.
