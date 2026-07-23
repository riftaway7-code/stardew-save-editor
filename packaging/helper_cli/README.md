Stardew Save Editor — iPad helper (scaffold)

Purpose
- Small helper CLI to PULL a Stardew save from a connected iPad and PUSH an edited save back.
- Designed to be bundled later with PyInstaller so casual users don't need Python or pip.

Current status
- This folder contains a lightweight Python wrapper that either (A) calls the local pymobiledevice3 CLI if available, or (B) prints copy-paste commands and instructions for users.

Security & trust
- ALWAYS publish the source alongside any binaries.
- After building a binary, upload it to VirusTotal and link the report in the repo/README.
- Avoid telling users to "ignore antivirus"; instead provide the source + VirusTotal scan + build instructions.

How to use (developer)
- Install dependencies for development: python3 -m pip install pymobiledevice3
- Run the helper script (dry-run): python3 pull_push.py --help

Packaging notes
- Use PyInstaller to bundle: pyinstaller --onefile --name "svse-helper" pull_push.py
- After building, test on target OS, then upload the binary and source. Submit false-positive reports to vendors if needed.

User-facing steps (what the helper will do when implemented)
- Pull: copy the Stardew save file from the app container to ~/Downloads
- Show a friendly message: "Drag the pulled save (Downloads/<farm_name>) into the web editor."
- Push: after user downloads edited save, helper copies it back into the app container and notifies success.

Notes
- This is a scaffold. The real device logic is non-trivial (pairing, house_arrest). Use pymobiledevice3 or your existing device/ code to implement the heavy lifting.