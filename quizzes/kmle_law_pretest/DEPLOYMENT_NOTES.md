# KMLE Medical Law Pretest Site

Generated 2026-05-26 from 10 medical-law study screenshots plus one overview screenshot.

## Structure
- `index.html`: lightweight launcher + quiz runtime
- `cards.json`: source card data, 86 cards
- `assets/`: optimized JPG source-image assets, opened only from answer/source guide

## UX/QC policy
- Sequential and random modes included
- First study recommendation: sequential
- SRS buttons: again / hard / good / easy
- Original image assets are not base64-embedded in HTML
- Source images are answer-side/guide-side to reduce front-side answer leakage
