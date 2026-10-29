# What is still missing, and why

Each item below needs either the **phone** or the **team**. Nothing here has been estimated or filled in.

## Needs the phone
| # | Missing | How to get it |
|---|---|---|
| 1 | Screenshots of the **Android app on a real phone** (camera, GPS prompt, result screen) | Install `BioMantra.apk` (`docs/user_manual.md` §5), take phone screenshots, add them as `screenshots/phone_device_*.png` |
| 2 | **Phone model** in `docs/tech_stack.md` | Fill it in after installing the APK |
| 3 | Fraud test cases **3, 6, 7** (photo of a screen; littered → clean; still littered) | Take the photos on campus, then `cd backend; python scripts/fraud_tests.py --plant … --wall … --screen … --before … --after-clean … --after-dirty …`, and paste the table into `raw/test_results.md` and `docs/testing.md` |
| 4 | Verification figures from **real campus photos** (now COCO stand-ins and a generated wall) | Copy the photos to `raw/samples/`, change the two file names in `report_figures.py` `main()`, and run it again |

## Needs the team
| # | Missing | How to get it |
|---|---|---|
| 5 | **Live accuracy** of the v2 forecast (test scores use actual next-day weather, so they're an upper bound) | Save the `/forecast` output once a day for a few weeks and compare it with the observed 24-h mean |
| 6 | **Deployment** beyond the laptop and a **mobile-data** test (optional; the demo runs on local Wi-Fi) | `docs/HANDOFF.md` section F |
| 7 | Comparison with the original **synopsis** | Add the synopsis items to `docs/changes_from_synopsis.md` |
| 8 | **Why the project moved out of OneDrive** (not recorded) | Add the reason to `docs/implementation_story.md` §3 |
