# Database schema (SQLite, `backend/biomantra.db`)

The schema comes from `backend/app/db.py` (`SCHEMA`). Tables are created with `CREATE TABLE IF NOT EXISTS` on startup, and seeded once when `institutions` is empty. Photos aren't stored in the database: they go to `backend/uploads/<uuid>.jpg`, and only the file name is stored. Diagram: `../diagrams/05_er_diagram.mmd`.

## institutions
| Column | Type | Key / constraint |
|---|---|---|
| id | INTEGER | PRIMARY KEY |
| name | TEXT | UNIQUE, NOT NULL |

Seed: CSE-DS, CSE-AI, CSE-AIML, CSE-IT, ECE.

## users
| Column | Type | Key / constraint |
|---|---|---|
| id | INTEGER | PRIMARY KEY |
| name | TEXT | NOT NULL |
| institution_id | INTEGER | FOREIGN KEY → institutions(id) |

Seed: two demo users per institution (10 users). There are no passwords; the app uses a simple user picker.

## actions
| Column | Type | Key / constraint | Meaning |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | |
| user_id | INTEGER | NOT NULL, FOREIGN KEY → users(id) | who submitted |
| action_type | TEXT | NOT NULL, CHECK IN ('sapling','segregated_bin','cleanup','dumping_report') | |
| photo_path | TEXT | NOT NULL | file name in uploads/ (the "after" photo for a cleanup) |
| before_photo_path | TEXT | | cleanup only |
| lat, lon | REAL | NOT NULL | phone GPS |
| client_time | TEXT | NOT NULL | phone time as sent (ISO 8601) |
| server_time | TEXT | NOT NULL | server UTC time (ISO 8601) |
| phash | TEXT | NOT NULL | 64-bit perceptual hash (hex), stored even when rejected |
| status | TEXT | NOT NULL, CHECK IN ('approved','needs_review','rejected') | |
| reasons | TEXT | NOT NULL | JSON list of reason strings |
| confidence | REAL | | AI confidence (NULL if the AI didn't run) |
| detections | TEXT | | JSON list `{name, conf, box}` |
| model_version | TEXT | | `yolov8n-coco` |
| points | INTEGER | DEFAULT 0 | set when approved |
| reviewed_by, reviewed_at | TEXT | | set by the admin review |

## hotspots
| Column | Type | Key / constraint | Meaning |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | |
| action_id | INTEGER | FOREIGN KEY → actions(id) | the approved dumping report |
| lat, lon | REAL | | location |
| created_at | TEXT | | approval time |
| cleaned_action_id | INTEGER | (no FK constraint) | the approved cleanup within 150 m that closed it |
| cleaned_at | TEXT | | NULL while the hotspot is open |

## Relationships
- An institution has many users (1 : N).
- A user has many actions (1 : N).
- An approved `dumping_report` action creates one hotspot (1 : 0..1).
- An approved `cleanup` action can close one open hotspot within 150 m (0..1 : 0..1, via `cleaned_action_id`).
