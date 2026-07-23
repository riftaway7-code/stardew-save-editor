Stardew Save Editor — Deploy notes

Quick test
- Open web/index.html in your browser (double-click) and drop a known Stardew save file to test locally.

Deploy options (pick one)
1) Netlify (fast)
   - Go to https://app.netlify.com/drop and drop the entire `web/` folder. No account required for a trial deploy.
2) Cloudflare Pages
   - Create a new Pages project, connect repo, set build as "None (Static site)" and point to the `web/` folder.
3) GitHub Pages
   - Commit the `web/` folder to a branch (e.g., `gh-pages`) and enable Pages from that branch (root).

Important notes
- This is a static, client-side tool. No server required.
- Ad slots: replace the two adslot divs with your ad network snippet when ready (top banner + in-content).
- items.js contains the in-browser item database; keep it alongside index.html.
- iOS helper: the web editor supports iPad users via upload/pull/push workflow; a one-click bridge helper is a separate binary (coming later).

Recommended next steps
- Test with several save files (PC & iPad pull) and confirm byte-parity on re-download.
- Add a small privacy notice if you plan to publish widely: "No files are uploaded; everything runs locally in your browser."