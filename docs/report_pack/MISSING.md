# What is missing from the report pack, and why

Nothing below has been estimated or filled in. Each item needs a real run first.

| # | Missing | Why | How to get it |
|---|---|---|---|
| 1 | **The rest of the Part B instructions after `screenshots/`** | The request text ended right after `screenshots/`, so any further items for the pack were never received | Send the rest of the list and it will be added |
| 2 | Screenshots of the **Android app on a real phone** (camera, GPS prompt, result screen) | No phone was connected; `BioMantra.apk` is built but not installed | Install the APK (docs/DEMO.md §B), take phone screenshots, put them in `screenshots/phone_device_*.png` |
| 3 | Fraud test cases **3, 6, 7** | They need real phone photos (a screen showing a plant; littered → clean; still littered) | `docs/HANDOFF.md` section E: run `scripts/fraud_tests.py` with the photos and paste the table into `raw/test_results.md` |
| 4 | Verification figures from **real campus photos** | Only a COCO stand-in plant photo and a generated wall texture were available | After step 3, run `report_figures.py` again with the real photos copied into `raw/samples/` (and update the two file names in `main()`) |
| 5 | Live accuracy of the **deployed v2 forecast** | Test scores use the actual next-24 h weather; live forecasts use the Open-Meteo weather forecast, which is less accurate, and no live log has been collected | Save `/forecast` once a day for a few weeks and compare it with the observed 24-h mean |
| 6 | Proof of **deployment** (Render/Vercel/ngrok) and a **mobile-data** test | Needs accounts and logins | `docs/HANDOFF.md` section F |
| 7 | The original **synopsis** comparison | The synopsis document isn't in the repository | Add its items to `raw/changes_from_synopsis.md` |
| 8 | **The rest of the second instruction list** (the `limitations.md` bullets after "modelled data, not CPCB station data", and anything after it) | The second request also ended mid-list | `docs/limitations.md` covers the received bullet plus the limitations already documented in the project; send the rest to add them |
| 9 | Rendered **PNG diagrams** | `mmdc` (mermaid-cli) isn't installed; the instructions said to include only the `.mmd` files in that case | `npx -p @mermaid-js/mermaid-cli mmdc -i <file>.mmd -o <file>.png -s 3 -b white`, or mermaid.live |
| 10 | **Phone model** in `docs/tech_stack.md` | No phone has been connected | Fill it in after installing the APK |
| 11 | **Why the project moved out of OneDrive** | Not recorded in progress.md | Add the reason to `docs/implementation_story.md` §3 |
| 12 | A **real `/hotspots` sample** with data | No dumping report was approved in the recorded API runs (the screenshot hotspots were inserted directly as demo data) | Approve a dumping report in `/admin`, then save the `GET /hotspots` output |
