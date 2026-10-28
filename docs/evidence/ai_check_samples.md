# D1-T9 AI check on 2 local images (`python scripts/check_ai.py sapling <plant> <wall>`)

Images: `coco_139_plant.jpg` = COCO val2017 image 000000000139 (a living room containing a potted plant, CC-BY licence via cocodataset.org);
`synthetic_wall.jpg` = a generated plain beige wall texture (no real wall photo was available; real campus photos come in D3-T5).

| Image | Action | Key detections | Confidence | Decision |
|---|---|---|---|---|
| coco_139_plant.jpg | sapling | potted plant 0.421 (also tv 0.927, chairs, person, vase 0.392) | 0.421 | needs_review |
| synthetic_wall.jpg | sapling | none | 0.000 | rejected |

Model: YOLOv8n pretrained on COCO (`yolov8n-coco`), default conf threshold 0.25.
