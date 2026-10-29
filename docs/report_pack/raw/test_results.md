# Fraud test results (SPEC §12)

## Run 1: automated, stand-in images (2026-10-29, local backend, fresh database, real YOLOv8n)

Command: `python scripts/fraud_tests.py --plant coco_139_plant.jpg --wall synthetic_wall.jpg`

Images are **not** real campus photos: `coco_139_plant.jpg` is COCO val2017 image 139 (a living room with a potted plant) and `synthetic_wall.jpg` is a generated plain wall texture. Locations and times for cases 4 and 5 were set in the test request, as SPEC §12 allows.

| # | Case | Expected | Actual status | Confidence | Reasons |
|---|---|---|---|---|---|
| 1 | Potted plant photo (COCO stand-in) | approved or needs_review | needs_review | 0.421 | AI is not fully sure — sent to a coordinator |
| 2 | Same photo submitted again | rejected (duplicate) | rejected | – | this photo (or a near copy) was already submitted |
| 3 | Photo of a screen showing a plant image | record the honest result | **PENDING – needs real phone photo** | | |
| 4 | Far location (Mumbai coordinates) | rejected (geofence) | rejected | – | outside the allowed area; this photo (or a near copy) was already submitted |
| 5 | client_time 2 h old | rejected (clock) | rejected | – | photo time does not match server time; this photo (or a near copy) was already submitted |
| 6 | Cleanup, before littered → after clean | approved / needs_review | **PENDING – needs real phone photo** (before + after) | | |
| 7 | Cleanup, after still littered | rejected | **PENDING – needs real phone photo** (before + after) | | |
| 8 | Random photo (wall) as sapling | rejected | rejected | 0.0 | AI could not confirm the action |

**Summary:** 5 of 8 cases have real results (1, 2, 4, 5, 8; all as expected). Cases 3, 6 and 7 are PENDING: no result has been recorded or estimated for them.

Cases 4 and 5 reuse the wall photo from case 8, so they also show the duplicate reason. All reasons are returned to the client by design.
The cleanup logic for cases 6/7 is covered by `tests/test_api.py::test_cleanup_before_after_flow`, but only with mocked YOLO.

## Run 2: real phone photos (WAITING FOR USER)

Take the photos on campus with the phone camera, copy them to the laptop, start the backend on a fresh database and run:
`python scripts/fraud_tests.py --plant plant.jpg --wall wall.jpg --screen screen.jpg --before littered.jpg --after-clean clean.jpg --after-dirty still_littered.jpg`
Paste the printed table here, including any failures.

## What we learned (from run 1)
- The cheap checks (clock, geofence, perceptual-hash duplicate) work without the AI, and they run first, so fraud is caught quickly and cheaply.
- A clear potted plant in a COCO photo only reached 0.421 confidence, below the 0.60 auto-approve line. With COCO stand-in classes, most real eco-actions will land in **needs_review**, so the human reviewer is essential, not optional.
- A photo is remembered even when it is rejected, so the same picture can't be retried with a fixed GPS position or time.
