#!/usr/bin/env python3
"""
anki_quiz_builder.py — 재사용 가능한 Anki SRS 퀴즈 HTML 빌더
================================================================

■ 포함 기능
  - SRS 평가 버튼: 🔴(1분) / 🟠(5분) / 🟢(10분→×2 숙달) / 🔵(24시간)
  - 필기 도구: 펜, 형광펜, 지우개, 이동(선택) 도구
  - 도형 스냅: 2초 이상 그리면 직선/직사각형 자동 변환 + 리사이즈
  - 이미지 잘라내기(Crop) + 원본 복원
  - 편집 모드: 이미지 드래그앤드롭 / 붙여넣기(Ctrl+V) 지원
  - 퀴즈 모드: 카운트다운 대기, 추가 퀴즈(숙달 카드 재시험)
  - 3연타 전체 초기화 (iOS confirm 우회)
  - 사이드바 네비게이션 + 모바일 반응형
  - localStorage 상태 영속화 (SRS / 편집 / 필기 / 히스토리)
  - Catppuccin 다크 테마 + 밝은 답안 영역

■ 사용법
    from anki_quiz_builder import QuizBuilder

    cards = [
        {
            "id": "c1",          # 고유 식별자
            "num": 1,            # 문제 번호
            "q": "질문 텍스트",
            "a": "<p>정답 HTML</p>",
            "g": "<p>Study Guide HTML</p>",  # 선택사항 (직접 HTML)
            "pages": [1, 2],     # 선택사항 (page_images 키)
        },
    ]

    builder = QuizBuilder(
        cards=cards,
        title="내 퀴즈 제목",
        storage_prefix="my_quiz",   # localStorage 키 접두사
        page_images={1: "base64...", 2: "base64..."},  # 선택사항
    )
    builder.write("output.html")

■ Card 필드 설명
  id    : 고유 식별자 (영문+숫자)
  num   : 문제 번호 (정수)
  q     : 질문 텍스트 (plain text 또는 inline HTML)
  a     : 정답 HTML
  g     : Study Guide HTML (직접 지정, pages보다 우선)
  pages : 페이지 번호 목록 (page_images에서 이미지를 가져옴)

■ PDF에서 퀴즈 만들기 예시
    import pdfplumber
    from pdf2image import convert_from_path
    import base64, io

    # 1) 텍스트 추출 → cards 리스트 작성
    # 2) 페이지 이미지 생성
    images = convert_from_path("pretest.pdf", dpi=200)
    page_images = {}
    for i, img in enumerate(images, 1):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        page_images[i] = base64.b64encode(buf.getvalue()).decode()

    builder = QuizBuilder(cards=cards, title="Pretest", page_images=page_images)
    builder.write("quiz.html")
"""

import html as html_lib
import json
import os


def build_card_guide(card, page_images):
    """카드의 Study Guide HTML 생성 — 해당 페이지 이미지를 포함"""
    parts = []
    for p in card.get("pages", []):
        if p in page_images:
            parts.append(f'<img src="data:image/png;base64,{page_images[p]}" style="max-width:100%;border-radius:8px;margin:8px 0;" alt="Page {p}">')
    return "\n".join(parts) if parts else "<p>해설 이미지 없음</p>"


def build_html(cards, page_images, title="Anki 퀴즈", storage_prefix="quiz"):
    """최종 HTML 조립"""

    num_cards = len(cards)
    title_html = html_lib.escape(title)
    storage_prefix_js = json.dumps(f"{storage_prefix}_")

    # Build QUIZ_DATA JS object
    quiz_data_items = []
    for c in cards:
        guide_html = build_card_guide(c, page_images).replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        answer_html = c["a"].replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        quiz_data_items.append(f'"{c["id"]}": {{ num: `{c["num"]}`, q: `{c["q"]}`, a: `{answer_html}`, g: `{guide_html}` }}')

    quiz_data_js = "const QUIZ_DATA = {\n" + ",\n".join(quiz_data_items) + "\n};"

    # Build ALL_IDS
    all_ids = [f'"{c["id"]}"' for c in cards]
    all_ids_js = f"const ALL_IDS = [{', '.join(all_ids)}];"

    # Build card HTML for card view
    card_html_parts = []
    for c in cards:
        card_html_parts.append(f"""
        <div class="card" id="card-{c['id']}">
            <div class="card-header">
                <span class="card-num">{c['num']}</span>
                <span class="card-title">{c['q']}</span>
                <button class="draw-btn" onclick="toggleDraw('{c['id']}')" title="필기 모드">🍎</button>
                <button class="edit-btn" onclick="toggleEdit('{c['id']}')" title="편집">✏️</button>
                <button class="copy-btn" onclick="copyQA('{c['id']}')" title="문제+답 복사">📋</button>
            </div>
            <div class="card-body">
                <button class="toggle-btn" onclick="toggleAnswer('{c['id']}')">정답 보기 ▼</button>
                <div class="answer-area" id="ans-{c['id']}" style="display:none">
                    <div class="draw-toolbar" id="draw-toolbar-{c['id']}"></div>
                    <div style="position:relative;">
                        <div class="answer-content" id="ans-content-{c['id']}">{c['a']}</div>
                        <canvas class="draw-canvas" id="draw-canvas-{c['id']}" style="display:none;"></canvas>
                    </div>
                    <button class="save-btn" id="save-{c['id']}" style="display:none" onclick="saveEdit('{c['id']}')">💾 저장</button>
                </div>
                <button class="toggle-btn guide-btn" onclick="toggleGuide('{c['id']}')">📖 Study Guide</button>
                <div class="guide-area" id="guide-{c['id']}" style="display:none">
                    <!-- guide images loaded dynamically -->
                </div>
                <button class="done-btn" id="done-{c['id']}" onclick="toggleDone('{c['id']}')">✓ 완료</button>
            </div>
        </div>""")

    cards_html = "\n".join(card_html_parts)

    # Sidebar items
    sidebar_items = []
    for c in cards:
        sidebar_items.append(f'<div class="sb-item" onclick="scrollToCard(\'{c["id"]}\')">{c["num"]}. {c["q"][:20]}…</div>')
    sidebar_html = "\n".join(sidebar_items)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_html}</title>
<style>
:root {{
    --bg: #1e2030;
    --card-bg: #232640;
    --card-border: #363a5c;
    --accent: #89b4fa;
    --accent2: #7c8ec4;
    --text: #cdd6f4;
    --text-dim: #8892b3;
    --green: #94e2d5;
    --orange: #f9e2af;
    --red: #f38ba8;
    --blue: #89b4fa;
    --sidebar-bg: #181a2a;
    --sidebar-w: 260px;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
}}

/* ── Sidebar ── */
.sidebar {{
    position: fixed; left: 0; top: 0; bottom: 0;
    width: var(--sidebar-w);
    background: var(--sidebar-bg);
    overflow-y: auto;
    z-index: 100;
    border-right: 1px solid var(--card-border);
    transition: transform 0.3s;
    padding: 16px 0;
}}
.sidebar.collapsed {{ transform: translateX(calc(-1 * var(--sidebar-w) + 40px)); }}
.sidebar.collapsed .sb-inner {{ opacity: 0; pointer-events: none; }}
.sb-toggle {{
    position: absolute; right: 8px; top: 8px;
    background: var(--accent); border: none; color: #fff;
    width: 28px; height: 28px; border-radius: 50%;
    cursor: pointer; font-size: 14px; z-index: 101;
}}
.sb-inner {{ padding: 8px 12px; transition: opacity 0.2s; }}
.sb-title {{ font-size: 16px; font-weight: 700; margin-bottom: 12px; color: var(--accent); }}
.sb-item {{
    padding: 6px 8px; margin: 2px 0;
    border-radius: 6px; cursor: pointer;
    font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    color: var(--text-dim);
}}
.sb-item:hover {{ background: var(--card-border); color: var(--text); }}

/* Progress bar */
.progress-wrap {{ margin: 12px 0; }}
.progress-bar {{ height: 6px; background: #333; border-radius: 3px; overflow: hidden; }}
.progress-fill {{ height: 100%; background: var(--green); transition: width 0.3s; }}
.progress-label {{ font-size: 12px; color: var(--text-dim); margin-top: 4px; }}

/* Quiz start buttons */
.sb-quiz-btns {{ margin-top: 16px; display:flex; flex-direction:column; gap:8px; }}
.sb-quiz-btns button {{
    padding: 10px; border: none; border-radius: 8px;
    font-size: 14px; font-weight: 600; cursor: pointer;
    color: #fff;
}}
.btn-review {{ background: var(--green); }}
.btn-reset {{ background: var(--accent); }}

/* ── Main content ── */
.main {{
    margin-left: var(--sidebar-w);
    padding: 24px;
    transition: margin-left 0.3s;
}}
.main.expanded {{ margin-left: 40px; }}

/* ── Card grid ── */
.card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
    gap: 20px;
}}
.card {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    overflow: hidden;
}}
.card.done {{ opacity: 0.5; }}
.card-header {{
    padding: 14px 16px;
    display: flex; align-items: center; gap: 10px;
    border-bottom: 1px solid var(--card-border);
}}
.card-num {{
    background: var(--accent);
    color: #fff; font-weight: 700; font-size: 14px;
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}}
.card-title {{ font-size: 14px; font-weight: 600; flex: 1; }}
.edit-btn, .copy-btn {{
    background: none; border: none; cursor: pointer; font-size: 16px;
    opacity: 0.5; transition: opacity 0.2s;
}}
.edit-btn:hover, .copy-btn:hover {{ opacity: 1; }}

/* Edit toolbar (image hint) */
.edit-toolbar {{
    display: flex; gap: 4px; padding: 5px 10px;
    background: #dce0e8; border: 1px solid #bcc0cc;
    border-radius: 6px; margin-bottom: 6px;
    flex-wrap: wrap; align-items: center;
}}
.edit-toolbar span {{ font-size: 11px; color: #6c6f85; }}

/* Contenteditable active state */
.answer-area[contenteditable="true"],
.answer-area .editing {{
    outline: 2px dashed #1e66f5 !important;
    border-radius: 4px;
}}
.card-body {{ padding: 12px 16px; }}

/* Toggle buttons */
.toggle-btn {{
    display: block; width: 100%;
    padding: 10px; margin: 6px 0;
    background: var(--card-border); border: none; border-radius: 8px;
    color: var(--text); font-size: 13px; cursor: pointer;
    text-align: center;
}}
.toggle-btn:hover {{ background: #2e3358; }}
.guide-btn {{ background: #2a3050; }}

/* Answer area */
.answer-area {{
    background: #eff1f5;
    color: #4c4f69;
    border-radius: 8px; padding: 14px; margin: 8px 0;
    font-size: 13px; line-height: 1.7;
}}
.answer-area table {{
    width: 100%; border-collapse: collapse; margin: 8px 0;
}}
.answer-area th, .answer-area td {{
    border: 1px solid #bcc0cc; padding: 6px 8px; font-size: 12px; text-align: left;
    color: #4c4f69;
}}
.answer-area th {{ background: #dce0e8; font-weight: 600; color: #4c4f69; }}
.answer-area h4 {{ color: #1e66f5; margin: 10px 0 6px; font-size: 14px; }}
.answer-area h5 {{ color: #df8e1d; margin: 8px 0 4px; font-size: 13px; }}
.answer-area b {{ color: #333; }}
.answer-area img {{ max-width: 100%; border-radius: 6px; }}

/* Guide area */
.guide-area {{
    background: #171928;
    border-radius: 8px; padding: 10px; margin: 8px 0;
}}
.guide-area img {{ max-width: 100%; border-radius: 6px; }}

/* Done button */
.done-btn {{
    display: inline-block;
    padding: 6px 16px; margin-top: 8px;
    background: transparent; border: 2px solid var(--green);
    border-radius: 20px; color: var(--green);
    font-size: 13px; cursor: pointer;
}}
.done-btn.checked {{ background: var(--green); color: #fff; }}

/* Save button */
.save-btn {{
    display: block; margin: 8px auto 0;
    padding: 8px 24px; background: var(--green);
    border: none; border-radius: 8px;
    color: #fff; font-size: 14px; cursor: pointer;
}}

/* ── Quiz Mode ── */
.quiz-overlay {{
    display: none;
    position: fixed; inset: 0;
    background: var(--bg);
    z-index: 200;
    overflow-y: auto;
}}
.quiz-overlay.active {{ display: flex; flex-direction: column; }}
.quiz-header {{
    position: sticky; top: 0;
    background: var(--sidebar-bg);
    padding: 12px 20px;
    display: flex; align-items: center; gap: 16px;
    border-bottom: 1px solid var(--card-border);
    flex-wrap: wrap;
    z-index: 201;
}}
.quiz-header .stat {{ font-size: 14px; }}
.quiz-header .back-btn {{
    background: var(--accent); border: none; color: #fff;
    padding: 6px 14px; border-radius: 6px; cursor: pointer;
    font-size: 13px;
}}
.quiz-card {{
    max-width: 800px; width: 100%;
    margin: 40px auto; padding: 24px;
}}
.quiz-q {{
    font-size: 20px; font-weight: 700;
    margin-bottom: 20px;
    display: flex; align-items: center; gap: 10px;
}}
.quiz-q .card-num {{ width: 40px; height: 40px; font-size: 18px; }}
.quiz-answer {{
    background: #eff1f5; color: #4c4f69; border-radius: 12px; padding: 20px;
    font-size: 14px; line-height: 1.8;
    display: none;
}}
.quiz-answer.visible {{ display: block; }}
.quiz-answer table {{ width: 100%; border-collapse: collapse; margin: 8px 0; }}
.quiz-answer th, .quiz-answer td {{ border: 1px solid #bcc0cc; padding: 6px 8px; font-size: 12px; text-align: left; color: #4c4f69; }}
.quiz-answer th {{ background: #dce0e8; font-weight: 600; color: #4c4f69; }}
.quiz-answer h4 {{ color: #1e66f5; margin: 10px 0 6px; }}
.quiz-answer h5 {{ color: #df8e1d; margin: 8px 0 4px; }}
.quiz-answer b {{ color: #333; }}
.quiz-answer img {{ max-width: 100%; border-radius: 6px; }}
.quiz-guide {{
    margin-top: 16px;
    max-height: 50vh;
    overflow-y: auto;
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 8px;
}}
.quiz-guide img {{ max-width: 100%; border-radius: 6px; }}

.quiz-answer .rating-btns {{
    position: sticky;
    bottom: 0;
    background: #eff1f5;
    padding: 16px 0 8px;
    z-index: 10;
}}

.show-answer-btn {{
    display: block; margin: 20px auto;
    padding: 14px 40px; background: var(--accent);
    border: none; border-radius: 10px;
    color: #fff; font-size: 16px; font-weight: 600;
    cursor: pointer;
}}

/* Rating buttons */
.rating-btns {{
    display: flex; gap: 10px; justify-content: center;
    margin-top: 20px; flex-wrap: wrap;
}}
.rating-btns button {{
    padding: 10px 20px; border: none; border-radius: 8px;
    font-size: 14px; font-weight: 600; cursor: pointer; color: #fff;
    min-width: 100px;
}}
.btn-again {{ background: #f38ba8; color: #1e2030; }}
.btn-hard {{ background: #f9e2af; color: #1e2030; }}
.btn-good {{ background: #94e2d5; color: #1e2030; }}
.btn-master {{ background: #a6e3a1; color: #1e2030; }}
.btn-tomorrow {{ background: #89b4fa; color: #1e2030; }}

/* Waiting screen */
.waiting-screen {{
    text-align: center; padding: 60px 20px;
    font-size: 18px;
}}
.waiting-screen .countdown {{ font-size: 48px; font-weight: 700; color: var(--accent); margin: 20px 0; }}
.waiting-screen button {{
    padding: 12px 30px; background: var(--orange);
    border: none; border-radius: 8px;
    color: #333; font-size: 16px; font-weight: 600; cursor: pointer;
}}

/* Session complete */
.session-complete {{
    text-align: center; padding: 60px 20px;
}}
.session-complete h2 {{ font-size: 28px; margin-bottom: 16px; }}
.session-complete .bonus-btn {{
    margin-top: 20px; padding: 14px 30px;
    background: var(--orange); border: none; border-radius: 8px;
    color: #333; font-size: 16px; font-weight: 600; cursor: pointer;
}}

/* Undo button */
.undo-btn {{
    background: transparent; border: 1px solid var(--text-dim);
    color: var(--text-dim); padding: 4px 10px; border-radius: 4px;
    cursor: pointer; font-size: 12px;
}}
.undo-btn:disabled {{ opacity: 0.3; cursor: default; }}

/* editing mode */
.editing {{ outline: 2px dashed var(--accent) !important; min-height: 100px; }}

/* ── Drawing / Apple Pencil Mode ── */
.draw-btn {{
    background: none; border: none; cursor: pointer; font-size: 16px;
    opacity: 0.5; transition: opacity 0.2s;
}}
.draw-btn:hover {{ opacity: 1; }}

.draw-canvas-wrap {{
    position: relative;
    display: none;
}}
.draw-canvas-wrap.active {{
    display: block;
}}
.draw-canvas {{
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: 10;
    touch-action: none;
    cursor: crosshair;
    -webkit-user-select: none;
    user-select: none;
    -webkit-touch-callout: none;
}}
.answer-area {{ position: relative; }}
.answer-area.draw-active {{
    -webkit-user-select: none;
    user-select: none;
    -webkit-touch-callout: none;
    overflow: hidden;
}}
/* Block all selection in entire page when drawing */
body.drawing-active {{
    -webkit-user-select: none;
    user-select: none;
    -webkit-touch-callout: none;
}}
body.drawing-active * {{
    -webkit-user-select: none;
    user-select: none;
    -webkit-touch-callout: none;
}}

/* Draw toolbar */
.draw-toolbar {{
    display: none;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    background: #dce0e8;
    border-radius: 10px;
    margin-bottom: 8px;
    flex-wrap: wrap;
    border: 1px solid #bcc0cc;
    position: relative; z-index: 20;
}}
.draw-toolbar.active {{ display: flex; }}

.draw-toolbar .tool-btn {{
    width: 32px; height: 32px;
    border: 2px solid transparent;
    border-radius: 8px;
    background: #eff1f5;
    cursor: pointer;
    font-size: 15px;
    display: flex; align-items: center; justify-content: center;
    transition: border-color 0.15s, background 0.15s;
    color: #4c4f69;
}}
.draw-toolbar .tool-btn.active {{
    border-color: #1e66f5;
    background: #ccd0da;
}}
.draw-toolbar .tool-btn:hover {{ background: #ccd0da; }}

.draw-toolbar .color-dot {{
    width: 22px; height: 22px;
    border-radius: 50%;
    border: 2px solid transparent;
    cursor: pointer;
    transition: border-color 0.15s, transform 0.15s;
}}
.draw-toolbar .color-dot:hover {{ transform: scale(1.2); }}
.draw-toolbar .color-dot.active {{ border-color: #4c4f69; transform: scale(1.2); }}

.draw-toolbar .divider {{
    width: 1px; height: 24px;
    background: #bcc0cc;
    margin: 0 4px;
}}

.draw-toolbar .size-slider {{
    width: 60px; height: 4px;
    -webkit-appearance: none;
    appearance: none;
    background: #9ca0b0;
    border-radius: 2px;
    outline: none;
}}
.draw-toolbar .size-slider::-webkit-slider-thumb {{
    -webkit-appearance: none;
    width: 14px; height: 14px;
    background: #1e66f5;
    border-radius: 50%;
    cursor: pointer;
}}

.draw-toolbar .size-label {{
    font-size: 11px; color: #6c6f85; min-width: 28px; text-align: center;
}}

.draw-toolbar .draw-undo-btn,
.draw-toolbar .draw-redo-btn {{
    padding: 4px 8px;
    background: #5c5f77;
    color: #fff;
    border: none; border-radius: 6px;
    font-size: 11px;
    cursor: pointer;
    min-width: 30px;
}}
.draw-toolbar .draw-undo-btn:disabled,
.draw-toolbar .draw-redo-btn:disabled {{
    opacity: 0.3; cursor: default;
}}

.draw-toolbar .clear-all-btn {{
    padding: 4px 10px;
    background: #e64553;
    color: #fff;
    border: none; border-radius: 6px;
    font-size: 11px; font-weight: 600;
    cursor: pointer;
    margin-left: auto;
}}

/* ── Image Crop Tool ── */
.img-wrapper {{
    position: relative;
    display: inline-block;
    margin: 8px 0;
}}
.img-wrapper img {{
    display: block;
    max-width: 100%;
    border-radius: 6px;
}}
.crop-btn {{
    position: absolute; top: 8px; right: 8px;
    background: rgba(30,32,48,0.85); border: 1px solid var(--accent);
    color: var(--accent); width: 34px; height: 34px;
    border-radius: 8px; cursor: pointer; font-size: 16px;
    display: flex; align-items: center; justify-content: center;
    opacity: 0; transition: opacity 0.2s;
    z-index: 5;
}}
.img-wrapper:hover .crop-btn {{ opacity: 1; }}
.crop-btn:hover {{ background: var(--accent); color: #1e2030; }}

.crop-overlay {{
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.85);
    z-index: 500;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
}}
.crop-toolbar {{
    display: flex; gap: 10px; margin-bottom: 12px;
}}
.crop-toolbar button {{
    padding: 8px 20px; border: none; border-radius: 8px;
    font-size: 14px; font-weight: 600; cursor: pointer;
}}
.crop-toolbar .crop-confirm {{ background: var(--green); color: #1e2030; }}
.crop-toolbar .crop-cancel {{ background: #555; color: #eee; }}
.crop-toolbar .crop-reset {{ background: var(--orange); color: #1e2030; }}
.crop-container {{
    position: relative;
    max-width: 90vw; max-height: 75vh;
    overflow: hidden;
    cursor: crosshair;
    border-radius: 8px;
}}
.crop-container img {{
    display: block;
    max-width: 90vw; max-height: 75vh;
    object-fit: contain;
    user-select: none;
    -webkit-user-drag: none;
}}
.crop-selection {{
    position: absolute;
    border: 2px solid var(--accent);
    background: rgba(137,180,250,0.15);
    pointer-events: none;
    display: none;
}}
.crop-dim {{
    position: absolute; inset: 0;
    pointer-events: none;
}}

/* floating mobile toggle */
.sb-mobile-toggle {{
    display: none;
    position: fixed; left: 10px; top: 10px;
    background: var(--accent); border: none; color: #fff;
    width: 36px; height: 36px; border-radius: 50%;
    cursor: pointer; font-size: 18px; z-index: 200;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    align-items: center; justify-content: center;
}}
.sb-overlay {{
    display: none;
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.5);
    z-index: 99;
}}
.sb-overlay.active {{ display: block; }}

/* responsive */
@media (max-width: 1100px) {{
    .sb-mobile-toggle {{ display: flex; }}
    .sidebar {{
        transform: translateX(-100%);
        z-index: 150;
    }}
    .sidebar.mobile-open {{
        transform: translateX(0);
    }}
    .sidebar .sb-toggle {{ display: none; }}
    .main {{ margin-left: 0 !important; padding: 12px; padding-top: 56px; }}
}}
@media (max-width: 768px) {{
    .card-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<!-- Mobile sidebar toggle -->
<button class="sb-mobile-toggle" id="sbMobileToggle" onclick="toggleMobileSidebar()">☰</button>
<div class="sb-overlay" id="sbOverlay" onclick="toggleMobileSidebar()"></div>

<!-- Sidebar -->
<div class="sidebar" id="sidebar">
    <button class="sb-toggle" onclick="toggleSidebar()">☰</button>
    <div class="sb-inner">
        <div class="sb-title">{title_html}</div>
        <div class="progress-wrap">
            <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width:0%"></div></div>
            <div class="progress-label" id="progressLabel">0 / {num_cards} 완료</div>
        </div>
        <div class="sb-quiz-btns">
            <button class="btn-review" id="btnReview" onclick="startReview()">복습 시작 (0개)</button>
            <button class="btn-reset" id="btnReset" onclick="handleResetTap()">전체 다시 풀기<br><small>[3연타 시 초기화]</small></button>
        </div>
        <div style="margin-top:12px;">
            {sidebar_html}
        </div>
    </div>
</div>

<!-- Main card view -->
<div class="main" id="mainContent">
    <div class="card-grid">
        {cards_html}
    </div>
</div>

<!-- Quiz overlay -->
<div class="quiz-overlay" id="quizOverlay">
    <div class="quiz-header" id="quizHeader">
        <button class="back-btn" onclick="exitQuiz()">← 카드 뷰</button>
        <span class="stat" id="statRed">🔴 0</span>
        <span class="stat" id="statOrange">🟠 0</span>
        <span class="stat" id="statGreen">🟢 0</span>
        <span class="stat" id="statMaster">😊 0</span>
        <span class="stat" id="statBlue">🔵 0</span>
        <button class="undo-btn" id="undoBtn" onclick="undoLast()" disabled>↩ 되돌리기</button>
    </div>
    <div id="quizBody"></div>
</div>

<script>
// ── Data ──
{quiz_data_js}
{all_ids_js}

const STORAGE_PREFIX = {storage_prefix_js};
const SRS_KEY = STORAGE_PREFIX + 'srs_v1';
const HIST_KEY = STORAGE_PREFIX + 'hist_v1';
const EDITS_KEY = STORAGE_PREFIX + 'edits_v1';

// ── SRS State ──
let srs = JSON.parse(localStorage.getItem(SRS_KEY) || '{{}}');
let history = JSON.parse(localStorage.getItem(HIST_KEY) || '[]');
let edits = JSON.parse(localStorage.getItem(EDITS_KEY) || '{{}}');
let doneSet = new Set();
let queue = [];
let pending = [];
let bonusMode = false;
let bonusSrs = {{}};
let waitTimer = null;

function saveSrs() {{ localStorage.setItem(SRS_KEY, JSON.stringify(srs)); }}
function saveHist() {{ localStorage.setItem(HIST_KEY, JSON.stringify(history)); }}
function saveEdits() {{ localStorage.setItem(EDITS_KEY, JSON.stringify(edits)); }}

// ── Card View Functions ──
function toggleAnswer(id) {{
    const el = document.getElementById('ans-' + id);
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
}}

function toggleGuide(id) {{
    const el = document.getElementById('guide-' + id);
    if (el.style.display === 'none') {{
        el.style.display = 'block';
        if (!el.dataset.loaded) {{
            el.innerHTML = QUIZ_DATA[id].g;
            el.dataset.loaded = '1';
        }}
    }} else {{
        el.style.display = 'none';
    }}
}}

function toggleDone(id) {{
    const btn = document.getElementById('done-' + id);
    const card = document.getElementById('card-' + id);
    if (doneSet.has(id)) {{
        doneSet.delete(id);
        btn.classList.remove('checked');
        btn.textContent = '✓ 완료';
        card.classList.remove('done');
    }} else {{
        doneSet.add(id);
        btn.classList.add('checked');
        btn.textContent = '✓ 완료됨';
        card.classList.add('done');
    }}
    updateProgress();
}}

function updateProgress() {{
    const n = doneSet.size;
    const total = ALL_IDS.length;
    document.getElementById('progressFill').style.width = (n/total*100) + '%';
    document.getElementById('progressLabel').textContent = n + ' / ' + total + ' 완료';
}}

function scrollToCard(id) {{
    document.getElementById('card-' + id).scrollIntoView({{ behavior: 'smooth', block: 'start' }});
}}

// ── Image Insert (drag, drop, paste) ──
function readAndInsertImage(file, targetEl) {{
    const reader = new FileReader();
    reader.onload = (ev) => {{
        targetEl.focus();
        const imgHtml = '<img src="' + ev.target.result + '" style="max-width:100%;height:auto;border-radius:4px;margin:6px 0;display:block">';
        document.execCommand('insertHTML', false, imgHtml);
    }};
    reader.readAsDataURL(file);
}}

function enableImageDrop(el) {{
    if (el._imgDropEnabled) return; // prevent double-binding
    el._imgDropEnabled = true;
    el.addEventListener('dragover', (e) => {{
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    }});
    el.addEventListener('drop', (e) => {{
        e.preventDefault();
        const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
        files.forEach(file => readAndInsertImage(file, el));
    }});
    el.addEventListener('paste', (e) => {{
        const items = Array.from(e.clipboardData.items || []).filter(i => i.type.startsWith('image/'));
        if (items.length === 0) return;
        e.preventDefault();
        items.forEach(item => {{
            const file = item.getAsFile();
            if (file) readAndInsertImage(file, el);
        }});
    }});
}}

function showEditToolbar(container, targetEl, toolbarId) {{
    removeEditToolbar(toolbarId);
    const tb = document.createElement('div');
    tb.id = 'edit-toolbar-' + toolbarId;
    tb.className = 'edit-toolbar';
    tb.innerHTML = '<span>✏️ 편집 중 &nbsp;|&nbsp; 📷 이미지: 드래그 또는 붙여넣기(Ctrl+V)</span>';
    const wrapper = targetEl.parentNode;
    if (wrapper && wrapper.parentNode === container) {{
        container.insertBefore(tb, wrapper);
    }} else {{
        container.insertBefore(tb, container.firstChild);
    }}
}}
function removeEditToolbar(toolbarId) {{
    const el = document.getElementById('edit-toolbar-' + toolbarId);
    if (el) el.remove();
}}

// ── Edit Mode ──
function toggleEdit(id) {{
    const content = document.getElementById('ans-content-' + id);
    const saveBtn = document.getElementById('save-' + id);
    const ansArea = document.getElementById('ans-' + id);
    ansArea.style.display = 'block';

    const canvas = document.getElementById('draw-canvas-' + id);
    if (content.contentEditable === 'true') {{
        content.contentEditable = 'false';
        content.classList.remove('editing');
        removeEditToolbar(id);
        saveBtn.style.display = 'none';
        if (canvas) showStaticDraw(id);
    }} else {{
        if (canvas) canvas.style.display = 'none';
        showEditToolbar(ansArea, content, id);
        content.contentEditable = 'true';
        content.classList.add('editing');
        enableImageDrop(content);
        saveBtn.style.display = 'block';
        content.focus();
    }}
}}

function saveEdit(id) {{
    const content = document.getElementById('ans-content-' + id);
    content.contentEditable = 'false';
    content.classList.remove('editing');
    removeEditToolbar(id);
    document.getElementById('save-' + id).style.display = 'none';
    edits[id] = content.innerHTML;
    saveEdits();
}}

// ── Copy Q&A for AI ──
function copyQA(id) {{
    const card = document.getElementById('card-' + id);
    const q = card.querySelector('.card-title').textContent;
    const num = card.querySelector('.card-num').textContent;
    const ansEl = document.getElementById('ans-content-' + id);
    const a = ansEl.innerText || ansEl.textContent;
    const text = `Q${{num}}. ${{q}}\n\n${{a}}`;
    navigator.clipboard.writeText(text).then(() => {{
        const btn = card.querySelector('.copy-btn');
        if (btn) {{ btn.textContent = '✅'; setTimeout(() => btn.textContent = '📋', 1500); }}
    }}).catch(() => {{
        const ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta);
        ta.select(); document.execCommand('copy');
        document.body.removeChild(ta);
        const btn = card.querySelector('.copy-btn');
        if (btn) {{ btn.textContent = '✅'; setTimeout(() => btn.textContent = '📋', 1500); }}
    }});
}}

// Apply saved edits on load
function applyEdits() {{
    for (const id in edits) {{
        const el = document.getElementById('ans-content-' + id);
        if (el) el.innerHTML = edits[id];
    }}
}}

// ── Sidebar ──
function toggleSidebar() {{
    const sb = document.getElementById('sidebar');
    const main = document.getElementById('mainContent');
    sb.classList.toggle('collapsed');
    main.classList.toggle('expanded');
    localStorage.setItem('sb_collapsed', sb.classList.contains('collapsed'));
}}
function toggleMobileSidebar() {{
    const sb = document.getElementById('sidebar');
    const overlay = document.getElementById('sbOverlay');
    const btn = document.getElementById('sbMobileToggle');
    const isOpen = sb.classList.toggle('mobile-open');
    overlay.classList.toggle('active', isOpen);
    btn.textContent = isOpen ? '✕' : '☰';
}}

// ── Quiz Mode ──
function getSrs(id) {{
    if (!srs[id]) srs[id] = {{ greenStreak: 0, redCount: 0, lastRating: null, mastered: false, nextReview: 0 }};
    return srs[id];
}}

function getReviewDue() {{
    const now = Date.now();
    return ALL_IDS.filter(id => {{
        const s = getSrs(id);
        return s.nextReview && s.nextReview <= now && !s.mastered;
    }});
}}

function updateReviewBtn() {{
    const due = getReviewDue();
    document.getElementById('btnReview').textContent = '복습 시작 (' + due.length + '개)';
}}

function startReview() {{
    const due = getReviewDue();
    if (due.length === 0) {{
        // Start with all cards
        startQuizWith([...ALL_IDS]);
    }} else {{
        startQuizWith(due);
    }}
}}

let _resetTaps = 0, _resetTimer = null;
function handleResetTap() {{
    _resetTaps++;
    clearTimeout(_resetTimer);
    const btn = document.getElementById('btnReset');
    if (_resetTaps === 1) {{
        if (btn) btn.innerHTML = '전체 다시 풀기<br><small style="color:var(--orange)">2번 더 누르면 초기화</small>';
    }} else if (_resetTaps === 2) {{
        if (btn) btn.innerHTML = '전체 다시 풀기<br><small style="color:var(--red)">⚠️ 한 번 더!</small>';
    }} else if (_resetTaps >= 3) {{
        _resetTaps = 0;
        if (btn) btn.innerHTML = '전체 다시 풀기<br><small>[3연타 시 초기화]</small>';
        doResetQuiz();
        return;
    }}
    _resetTimer = setTimeout(() => {{
        _resetTaps = 0;
        const b = document.getElementById('btnReset');
        if (b) b.innerHTML = '전체 다시 풀기<br><small>[3연타 시 초기화]</small>';
    }}, 1000);
}}
function doResetQuiz() {{
    srs = {{}};
    history = [];
    ALL_IDS.forEach(id => {{ srs[id] = {{ greenStreak: 0, redCount: 0, nextReview: null, mastered: false, lastRating: null }}; }});
    saveSrs();
    saveHist();
    startQuizWith([...ALL_IDS]);
}}

function startQuizWith(ids) {{
    bonusMode = false;
    queue = [...ids];
    pending = [];
    // Shuffle
    for (let i = queue.length - 1; i > 0; i--) {{
        const j = Math.floor(Math.random() * (i + 1));
        [queue[i], queue[j]] = [queue[j], queue[i]];
    }}
    document.getElementById('quizOverlay').classList.add('active');
    showNextCard();
}}

function exitQuiz() {{
    if (waitTimer) {{ clearInterval(waitTimer); waitTimer = null; }}
    document.getElementById('quizOverlay').classList.remove('active');
    updateReviewBtn();
}}

function showNextCard() {{
    if (waitTimer) {{ clearInterval(waitTimer); waitTimer = null; }}
    const now = Date.now();

    // Move due pending cards to front of queue
    const dueCards = pending.filter(p => p.dueTime <= now).sort((a, b) => a.dueTime - b.dueTime);
    pending = pending.filter(p => p.dueTime > now);

    for (const dc of dueCards.reverse()) {{
        queue.unshift(dc.id);
    }}

    updateStats();

    if (queue.length > 0) {{
        renderQuizCard(queue.shift());
    }} else if (pending.length > 0) {{
        renderWaiting();
    }} else {{
        renderComplete();
    }}
}}

function renderQuizCard(id) {{
    const data = QUIZ_DATA[id];
    const s = getSrs(id);

    // Read answer from page DOM (includes edits)
    const ansHtml = document.getElementById('ans-content-' + id)?.innerHTML || edits[id] || data.a;
    // Read guide: try page DOM first, fall back to QUIZ_DATA
    let guideHtml = '';
    const guideEl = document.getElementById('guide-' + id);
    if (guideEl && guideEl.dataset.loaded) {{
        guideHtml = guideEl.innerHTML;
    }} else {{
        guideHtml = data.g || '';
    }}

    let badge = '';
    if (bonusMode) badge = '<span style="background:rgba(255,212,59,.2);color:#ffd43b;padding:1px 6px;border-radius:4px;font-size:11px;font-weight:700">⭐ 추가퀴즈</span>';
    else if (s.mastered) badge = '<span style="background:rgba(255,212,59,.2);color:#ffd43b;padding:1px 6px;border-radius:4px;font-size:11px;font-weight:700">😊 숙달</span>';
    else if (s.redCount >= 2) badge = '<span style="background:rgba(255,107,107,.2);color:#ff6b6b;padding:1px 6px;border-radius:4px;font-size:11px;font-weight:700">🤬 어려움</span>';

    const curStreak = bonusMode ? 0 : s.greenStreak;
    const greenLabel = curStreak >= 1 ? '🟢 숙달<br><small>내일</small>' : '🟢 보통<br><small>10분</small>';

    const guideSection = guideHtml.trim() ? `
        <button class="guide-btn" onclick="toggleQuizGuide()" style="width:100%;text-align:left;background:transparent;border:none;border-top:1px solid var(--card-border);padding:8px 14px;color:#cc5de8;font-size:12px;cursor:pointer;">📖 Study Guide 보기</button>
        <div class="quiz-guide" id="quizGuide" style="display:none;">${{guideHtml}}</div>` : '';

    document.getElementById('quizBody').innerHTML = `
        <div class="quiz-card">
            <div class="quiz-q">
                <span class="card-num">Q${{data.num}}</span>
                <span>${{data.q}}</span>
                ${{badge}}
                <button class="draw-btn" onclick="toggleQuizDraw('${{id}}')" title="필기 모드">🍎</button>
                <button class="edit-btn" onclick="toggleQuizEdit('${{id}}')" title="편집">✏️</button>
                <button class="copy-btn" onclick="copyQA('${{id}}')" title="문제+답 복사">📋</button>
            </div>
            <button class="show-answer-btn" id="showAnsBtn" onclick="showQuizAnswer()">정답 보기 ▼</button>
            <div class="quiz-answer" id="quizAnswer">
                <div class="draw-toolbar" id="draw-toolbar-quiz"></div>
                <div style="position:relative;">
                    <div id="quizAnsContent">${{ansHtml}}</div>
                    <canvas class="draw-canvas" id="draw-canvas-quiz" style="display:none;"></canvas>
                </div>
                ${{guideSection}}
                <div class="rating-btns" id="ratingBtns" style="display:none;">
                    <button class="btn-again" onclick="rate('${{id}}','r')">🔴 다시<br><small>1분</small></button>
                    <button class="btn-hard" onclick="rate('${{id}}','o')">🟠 어려움<br><small>5분</small></button>
                    <button class="btn-good" onclick="rate('${{id}}','g')">${{greenLabel}}</button>
                    <button class="btn-tomorrow" onclick="rate('${{id}}','b')">🔵 내일<br><small>1일</small></button>
                </div>
            </div>
        </div>
    `;
    updateStats();
}}

function showQuizAnswer() {{
    document.getElementById('quizAnswer').classList.add('visible');
    document.getElementById('showAnsBtn').style.display = 'none';
    const rr = document.getElementById('ratingBtns');
    if (rr) rr.style.display = 'flex';
}}

function toggleQuizGuide() {{
    const g = document.getElementById('quizGuide');
    const btn = g?.previousElementSibling;
    if (!g) return;
    if (g.style.display === 'none') {{
        g.style.display = 'block';
        if (btn) btn.textContent = '📖 Study Guide 닫기';
    }} else {{
        g.style.display = 'none';
        if (btn) btn.textContent = '📖 Study Guide 보기';
    }}
}}

function toggleQuizEdit(id) {{
    const content = document.getElementById('quizAnsContent');
    const quizAnswer = document.getElementById('quizAnswer');
    if (!content || !quizAnswer) return;
    if (content.contentEditable === 'true') {{
        content.contentEditable = 'false';
        content.classList.remove('editing');
        removeEditToolbar('quiz-' + id);
        edits[id] = content.innerHTML;
        saveEdits();
        // Sync card view
        const cardContent = document.getElementById('ans-content-' + id);
        if (cardContent) cardContent.innerHTML = edits[id];
    }} else {{
        if (!quizAnswer.classList.contains('visible')) quizAnswer.classList.add('visible');
        showEditToolbar(quizAnswer, content, 'quiz-' + id);
        content.contentEditable = 'true';
        content.classList.add('editing');
        enableImageDrop(content);
        content.focus();
    }}
}}

function rate(id, rating) {{
    const s = getSrs(id);
    const now = Date.now();
    const MIN = 60000;

    if (bonusMode) {{
        if (!bonusSrs[id]) bonusSrs[id] = {{ greenStreak: 0 }};
        const bs = bonusSrs[id];
        let interval;
        if (rating === 'r') {{ interval = 1 * MIN; bs.greenStreak = 0; }}
        else if (rating === 'o') {{ interval = 5 * MIN; bs.greenStreak = 0; }}
        else if (rating === 'g') {{ bs.greenStreak++; if (bs.greenStreak >= 2) interval = 0; else interval = 10 * MIN; }}
        else if (rating === 'b') {{ interval = 0; }}
        if (interval > 0) pending.push({{ id, dueTime: now + interval }});
        updateStats(); showNextCard();
        return;
    }}

    // Save to undo history
    history.push({{
        id,
        prev: JSON.parse(JSON.stringify(s)),
        pendingSnapshot: JSON.parse(JSON.stringify(pending)),
        queueSnapshot: [...queue]
    }});
    if (history.length > 20) history.shift();
    saveHist();
    document.getElementById('undoBtn').disabled = false;

    let newLastRating = rating;
    let interval;

    if (rating === 'r') {{
        interval = 1 * MIN; s.redCount++; s.greenStreak = 0;
    }} else if (rating === 'o') {{
        interval = 5 * MIN; s.greenStreak = 0;
    }} else if (rating === 'g') {{
        interval = 10 * MIN; s.greenStreak++;
        if (s.greenStreak >= 2) {{
            s.mastered = true;
            interval = 24 * 60 * MIN;
            newLastRating = 'master';
        }}
    }} else if (rating === 'b') {{
        interval = 24 * 60 * MIN;
    }}

    s.nextReview = now + interval;
    s.lastRating = newLastRating;

    // Re-queue if not mastered/tomorrow
    if (rating === 'r' || rating === 'o' || (rating === 'g' && !s.mastered)) {{
        pending.push({{ id, dueTime: now + interval }});
    }}

    saveSrs(); showNextCard();
}}

function undoLast() {{
    if (history.length === 0) return;
    const entry = history.pop();
    srs[entry.id] = entry.prev;
    pending = entry.pendingSnapshot;
    queue = entry.queueSnapshot;
    queue.unshift(entry.id);
    saveSrs();
    saveHist();
    document.getElementById('undoBtn').disabled = history.length === 0;
    showNextCard();
}}

function updateStats() {{
    let red = 0, orange = 0, green = 0, master = 0, blue = 0;
    ALL_IDS.forEach(id => {{
        const s = srs[id];
        if (!s || !s.lastRating) return;
        const lr = s.lastRating;
        if (lr === 'r' || lr === 'red') red++;
        else if (lr === 'o' || lr === 'orange') orange++;
        else if (lr === 'g' || lr === 'green') green++;
        else if (lr === 'master' || lr === 'mastered') master++;
        else if (lr === 'b' || lr === 'blue') blue++;
    }});
    const el = document.getElementById('statRed'); if (el) el.textContent = '🔴 ' + red;
    const el2 = document.getElementById('statOrange'); if (el2) el2.textContent = '🟠 ' + orange;
    const el3 = document.getElementById('statGreen'); if (el3) el3.textContent = '🟢 ' + green;
    const el4 = document.getElementById('statMaster'); if (el4) el4.textContent = '😊 ' + master;
    const el5 = document.getElementById('statBlue'); if (el5) el5.textContent = '🔵 ' + blue;
}}

function renderWaiting() {{
    if (waitTimer) {{ clearInterval(waitTimer); waitTimer = null; }}
    const body = document.getElementById('quizBody');
    const minDue = Math.min(...pending.map(p => p.dueTime));
    const waitCount = pending.length;

    function tick() {{
        const sec = Math.max(0, Math.ceil((minDue - Date.now()) / 1000));
        if (sec <= 0) {{
            clearInterval(waitTimer); waitTimer = null;
            showNextCard();
            return;
        }}
        body.innerHTML = `
            <div class="waiting-screen">
                <p>다음 카드까지 대기 중... (⏳ ${{waitCount}}개 대기)</p>
                <div class="countdown">${{sec}}초</div>
                <button onclick="skipWait()">⚡ 바로보기</button>
            </div>
        `;
    }}
    tick();
    waitTimer = setInterval(tick, 1000);
}}

function skipWait() {{
    if (waitTimer) {{ clearInterval(waitTimer); waitTimer = null; }}
    if (pending.length === 0) return;
    pending.sort((a, b) => a.dueTime - b.dueTime);
    const next = pending.shift();
    if (next) {{ queue.unshift(next.id); showNextCard(); }}
}}

function renderComplete() {{
    const masteredIds = ALL_IDS.filter(id => srs[id] && srs[id].mastered);
    const bonusSection = bonusMode
        ? '<p style="color:var(--green);margin-top:12px;font-size:16px">🌟 추가 퀴즈 완료!</p>'
        : (masteredIds.length > 0
            ? `<p style="margin-top:16px"><button class="bonus-btn" onclick="startBonus()">⭐ 추가 퀴즈 (숙달 ${{masteredIds.length}}장)</button></p>`
            : '');
    document.getElementById('quizBody').innerHTML = `
        <div class="session-complete">
            <h2>${{bonusMode ? '⭐ 추가 퀴즈 완료!' : '🎉 세션 완료!'}}</h2>
            <p>숙달 카드: ${{masteredIds.length}} / ${{ALL_IDS.length}}</p>
            ${{bonusSection}}
            <p style="margin-top:16px"><button class="back-btn" onclick="exitQuiz()" style="font-size:16px;padding:12px 24px;">← 카드 뷰로 돌아가기</button></p>
        </div>
    `;
}}

function startBonus() {{
    bonusMode = true;
    bonusSrs = {{}};
    const masteredIds = ALL_IDS.filter(id => srs[id] && srs[id].mastered);
    queue = [...masteredIds];
    pending = [];
    for (let i = queue.length - 1; i > 0; i--) {{
        const j = Math.floor(Math.random() * (i + 1));
        [queue[i], queue[j]] = [queue[j], queue[i]];
    }}
    showNextCard();
}}

// ── Image drag & paste support in edit mode ──
document.addEventListener('paste', function(e) {{
    const active = document.activeElement;
    if (!active || active.contentEditable !== 'true') return;
    const items = e.clipboardData.items;
    for (const item of items) {{
        if (item.type.startsWith('image/')) {{
            e.preventDefault();
            const blob = item.getAsFile();
            const reader = new FileReader();
            reader.onload = function(ev) {{
                const img = document.createElement('img');
                img.src = ev.target.result;
                img.style.maxWidth = '100%';
                img.style.borderRadius = '6px';
                const sel = window.getSelection();
                if (sel.rangeCount) {{
                    sel.getRangeAt(0).insertNode(img);
                }}
            }};
            reader.readAsDataURL(blob);
            break;
        }}
    }}
}});

document.addEventListener('drop', function(e) {{
    const target = e.target.closest('[contenteditable="true"]');
    if (!target) return;
    e.preventDefault();
    const files = e.dataTransfer.files;
    for (const file of files) {{
        if (file.type.startsWith('image/')) {{
            const reader = new FileReader();
            reader.onload = function(ev) {{
                const img = document.createElement('img');
                img.src = ev.target.result;
                img.style.maxWidth = '100%';
                img.style.borderRadius = '6px';
                target.appendChild(img);
            }};
            reader.readAsDataURL(file);
        }}
    }}
}});

document.addEventListener('dragover', function(e) {{
    if (e.target.closest('[contenteditable="true"]')) {{
        e.preventDefault();
    }}
}});

// ── Drawing / Apple Pencil Mode (Stroke-based) ──
const DRAW_KEY = STORAGE_PREFIX + 'draw_v2';
let drawData = JSON.parse(localStorage.getItem(DRAW_KEY) || '{{}}');
// drawData[cardId] = [ {{ mode:'pen'|'highlighter', color, size, points:[{{x,y}},...] }}, ... ]
function saveDrawData() {{ localStorage.setItem(DRAW_KEY, JSON.stringify(drawData)); }}

const PEN_COLORS = ['#e64553','#1e66f5','#4c4f69','#40a02b','#fe640b'];
const HL_COLORS = ['#df8e1d','#e64553','#179299','#1e66f5','#40a02b'];

let activeDrawId = null; // card id currently in draw mode (or 'quiz')
let drawCtx = null;
let drawMode = 'pen';
let drawColor = PEN_COLORS[0];
let drawSize = 2;
let isDrawing = false;
let currentStroke = null; // {{ mode, color, size, points }}
let canvasW = 0, canvasH = 0; // logical (CSS) size for current canvas
let drawStartTime = 0;
let activeResizeRect = null; // {{ cardId, strokeIdx }}
let resizeDragHandle = null; // 'tl'|'tr'|'bl'|'br'
let longPressTimer = null;
let shapeSnapTimer = null;
let shapeSnapMode = null; // 'line'|'rect' during live shape
let shapeSnapData = null; // line: {{startX,startY}}, rect: {{x,y,w,h,handle}}

// ── Laser pointer pen (temporary glowing strokes) ──
let laserStrokes = []; // temporary strokes that vanish after 1s idle
let laserFadeTimer = null;
function startLaserFade() {{
    if (laserFadeTimer) clearTimeout(laserFadeTimer);
    laserFadeTimer = setTimeout(() => {{
        laserStrokes = [];
        redrawCurrent();
    }}, 1000);
}}
function renderLaserStrokes(ctx) {{
    if (laserStrokes.length === 0) return;
    ctx.save();
    ctx.shadowColor = '#ff0000';
    ctx.shadowBlur = 12;
    ctx.strokeStyle = '#ff0000';
    ctx.globalAlpha = 0.9;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = 3;
    laserStrokes.forEach(s => {{
        if (!s.points || s.points.length < 2) return;
        ctx.beginPath();
        ctx.moveTo(s.points[0].x, s.points[0].y);
        for (let i = 1; i < s.points.length; i++) ctx.lineTo(s.points[i].x, s.points[i].y);
        ctx.stroke();
    }});
    // Outer glow
    ctx.shadowColor = '#ff3333';
    ctx.shadowBlur = 24;
    ctx.globalAlpha = 0.4;
    ctx.lineWidth = 8;
    laserStrokes.forEach(s => {{
        if (!s.points || s.points.length < 2) return;
        ctx.beginPath();
        ctx.moveTo(s.points[0].x, s.points[0].y);
        for (let i = 1; i < s.points.length; i++) ctx.lineTo(s.points[i].x, s.points[i].y);
        ctx.stroke();
    }});
    ctx.restore();
}}
let selectedStrokes = null; // {{ cardId, indices:[], bbox:{{x,y,w,h}} }}
let isMovingSelection = false;
let moveStartPos = null;
let selectionPath = [];

// ── Undo / Redo stacks (per card) ──
let drawUndoStack = {{}};  // cardId -> [snapshot, ...]
let drawRedoStack = {{}};  // cardId -> [snapshot, ...]
function pushDrawUndo(cid) {{
    if (!cid) return;
    if (!drawUndoStack[cid]) drawUndoStack[cid] = [];
    drawUndoStack[cid].push(JSON.parse(JSON.stringify(getStrokes(cid))));
    if (drawUndoStack[cid].length > 50) drawUndoStack[cid].shift();
    drawRedoStack[cid] = [];
    updateUndoRedoBtns();
}}
function drawUndo() {{
    const cid = realDrawId();
    if (!cid || !drawUndoStack[cid] || drawUndoStack[cid].length === 0) return;
    if (!drawRedoStack[cid]) drawRedoStack[cid] = [];
    drawRedoStack[cid].push(JSON.parse(JSON.stringify(getStrokes(cid))));
    drawData[cid] = drawUndoStack[cid].pop();
    saveDrawData();
    activeResizeRect = null;
    selectedStrokes = null;
    redrawCurrent();
    updateUndoRedoBtns();
}}
function drawRedo() {{
    const cid = realDrawId();
    if (!cid || !drawRedoStack[cid] || drawRedoStack[cid].length === 0) return;
    if (!drawUndoStack[cid]) drawUndoStack[cid] = [];
    drawUndoStack[cid].push(JSON.parse(JSON.stringify(getStrokes(cid))));
    drawData[cid] = drawRedoStack[cid].pop();
    saveDrawData();
    activeResizeRect = null;
    selectedStrokes = null;
    redrawCurrent();
    updateUndoRedoBtns();
}}
function updateUndoRedoBtns() {{
    const cid = realDrawId();
    document.querySelectorAll('.draw-undo-btn').forEach(b => b.disabled = !cid || !drawUndoStack[cid] || drawUndoStack[cid].length === 0);
    document.querySelectorAll('.draw-redo-btn').forEach(b => b.disabled = !cid || !drawRedoStack[cid] || drawRedoStack[cid].length === 0);
}}

// ── Get the real card id (handles 'quiz' proxy) ──
function realDrawId() {{
    return activeDrawId === 'quiz' ? quizDrawCardId : activeDrawId;
}}
function getStrokes(cardId) {{
    if (!drawData[cardId]) drawData[cardId] = [];
    return drawData[cardId];
}}

// ── Apply stroke style (shared) ──
function applyStrokeStyle(ctx, s) {{
    if (s.mode === 'pen') {{
        ctx.strokeStyle = s.color;
        ctx.lineWidth = s.size;
        ctx.globalAlpha = 1.0;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
    }} else {{
        ctx.strokeStyle = s.color;
        ctx.lineWidth = s.size * 6;
        ctx.globalAlpha = 0.35;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
    }}
}}

// ── Render all strokes onto canvas ──
function renderStrokes(ctx, strokes, w, h) {{
    ctx.clearRect(0, 0, w, h);
    for (const s of strokes) {{
        if (s.type === 'rect') {{
            ctx.beginPath();
            ctx.rect(s.x, s.y, s.w, s.h);
            applyStrokeStyle(ctx, s);
            ctx.stroke();
            ctx.globalAlpha = 1.0;
        }} else if (s.type === 'line') {{
            if (!s.points || s.points.length < 2) continue;
            ctx.beginPath();
            ctx.moveTo(s.points[0].x, s.points[0].y);
            ctx.lineTo(s.points[1].x, s.points[1].y);
            applyStrokeStyle(ctx, s);
            ctx.stroke();
            ctx.globalAlpha = 1.0;
        }} else {{
            if (!s.points || s.points.length < 2) continue;
            ctx.beginPath();
            ctx.moveTo(s.points[0].x, s.points[0].y);
            for (let i = 1; i < s.points.length; i++) {{
                ctx.lineTo(s.points[i].x, s.points[i].y);
            }}
            applyStrokeStyle(ctx, s);
            ctx.stroke();
            ctx.globalAlpha = 1.0;
        }}
    }}
}}

// ── Resize handles for rectangles ──
function getRectHandles(s) {{
    return {{
        tl: {{ x: s.x, y: s.y }},
        tr: {{ x: s.x + s.w, y: s.y }},
        bl: {{ x: s.x, y: s.y + s.h }},
        br: {{ x: s.x + s.w, y: s.y + s.h }}
    }};
}}
function drawResizeHandles(ctx, s) {{
    const handles = getRectHandles(s);
    ctx.globalAlpha = 1.0;
    ctx.lineWidth = 1.5;
    for (const h of Object.values(handles)) {{
        ctx.fillStyle = '#1e66f5';
        ctx.fillRect(h.x - 6, h.y - 6, 12, 12);
        ctx.strokeStyle = '#fff';
        ctx.strokeRect(h.x - 6, h.y - 6, 12, 12);
    }}
}}
function pointInRect(pos, s) {{
    const x1 = Math.min(s.x, s.x + s.w), x2 = Math.max(s.x, s.x + s.w);
    const y1 = Math.min(s.y, s.y + s.h), y2 = Math.max(s.y, s.y + s.h);
    return pos.x >= x1 && pos.x <= x2 && pos.y >= y1 && pos.y <= y2;
}}

// ── Hit-test: is point (px,py) near any segment of stroke? ──
function strokeHitTest(stroke, px, py, threshold) {{
    const r = threshold + (stroke.mode === 'highlighter' ? stroke.size * 3 : stroke.size / 2);
    if (stroke.type === 'rect') {{
        const x1 = stroke.x, y1 = stroke.y, x2 = stroke.x + stroke.w, y2 = stroke.y + stroke.h;
        if (distToSegment(px, py, x1, y1, x2, y1) < r) return true;
        if (distToSegment(px, py, x2, y1, x2, y2) < r) return true;
        if (distToSegment(px, py, x2, y2, x1, y2) < r) return true;
        if (distToSegment(px, py, x1, y2, x1, y1) < r) return true;
        return false;
    }}
    if (stroke.type === 'line') {{
        const pts = stroke.points;
        if (!pts || pts.length < 2) return false;
        return distToSegment(px, py, pts[0].x, pts[0].y, pts[1].x, pts[1].y) < r;
    }}
    const pts = stroke.points;
    if (!pts) return false;
    for (let i = 0; i < pts.length - 1; i++) {{
        if (distToSegment(px, py, pts[i].x, pts[i].y, pts[i+1].x, pts[i+1].y) < r) return true;
    }}
    return false;
}}
function distToSegment(px, py, x1, y1, x2, y2) {{
    const dx = x2 - x1, dy = y2 - y1;
    const lenSq = dx*dx + dy*dy;
    let t = lenSq === 0 ? 0 : Math.max(0, Math.min(1, ((px-x1)*dx + (py-y1)*dy) / lenSq));
    const cx = x1 + t*dx, cy = y1 + t*dy;
    return Math.sqrt((px-cx)*(px-cx) + (py-cy)*(py-cy));
}}

// ── Segment-segment intersection ──
function segCross(ox, oy, ax, ay, bx, by) {{
    return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox);
}}
function segmentsIntersect(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2) {{
    const d1 = segCross(bx1, by1, bx2, by2, ax1, ay1);
    const d2 = segCross(bx1, by1, bx2, by2, ax2, ay2);
    const d3 = segCross(ax1, ay1, ax2, ay2, bx1, by1);
    const d4 = segCross(ax1, ay1, ax2, ay2, bx2, by2);
    if (((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) &&
        ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0))) return true;
    return false;
}}

// ── Get segments from any stroke type ──
function getStrokeSegments(stroke) {{
    if (stroke.type === 'rect') {{
        const x1 = stroke.x, y1 = stroke.y, x2 = stroke.x + stroke.w, y2 = stroke.y + stroke.h;
        return [
            {{x1, y1, x2, y2: y1}}, {{x1: x2, y1, x2, y2}},
            {{x1: x2, y1: y2, x2: x1, y2}}, {{x1, y1: y2, x2: x1, y2: y1}}
        ];
    }}
    const pts = stroke.points || [];
    const segs = [];
    for (let i = 0; i < pts.length - 1; i++) {{
        segs.push({{x1: pts[i].x, y1: pts[i].y, x2: pts[i+1].x, y2: pts[i+1].y}});
    }}
    return segs;
}}

// ── Does a selection path intersect a stroke? ──
function strokeIntersectsPath(stroke, path) {{
    // Point proximity check (catches thick strokes)
    const thresh = 4;
    for (let k = 0; k < path.length; k += 3) {{
        if (strokeHitTest(stroke, path[k].x, path[k].y, thresh)) return true;
    }}
    // Segment intersection check
    const strokeSegs = getStrokeSegments(stroke);
    for (let i = 0; i < path.length - 1; i++) {{
        for (const seg of strokeSegs) {{
            if (segmentsIntersect(path[i].x, path[i].y, path[i+1].x, path[i+1].y,
                seg.x1, seg.y1, seg.x2, seg.y2)) return true;
        }}
    }}
    return false;
}}

// ── Bounding box of selected strokes ──
function computeSelectionBBox(strokes, indices) {{
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const idx of indices) {{
        const s = strokes[idx];
        if (s.type === 'rect') {{
            minX = Math.min(minX, s.x, s.x + s.w); minY = Math.min(minY, s.y, s.y + s.h);
            maxX = Math.max(maxX, s.x, s.x + s.w); maxY = Math.max(maxY, s.y, s.y + s.h);
        }} else if (s.points) {{
            for (const p of s.points) {{
                minX = Math.min(minX, p.x); minY = Math.min(minY, p.y);
                maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y);
            }}
        }}
    }}
    const pad = 10;
    return {{ x: minX - pad, y: minY - pad, w: maxX - minX + pad * 2, h: maxY - minY + pad * 2 }};
}}

// ── Draw selection UI ──
function drawSelectionBox() {{
    if (!selectedStrokes || !drawCtx) return;
    const b = selectedStrokes.bbox;
    drawCtx.save();
    drawCtx.setLineDash([6, 4]);
    drawCtx.strokeStyle = '#4c4f69';
    drawCtx.lineWidth = 1.5;
    drawCtx.globalAlpha = 1.0;
    drawCtx.strokeRect(b.x, b.y, b.w, b.h);
    drawCtx.restore();
}}
function drawSelectionLine() {{
    if (!selectionPath.length || !drawCtx) return;
    drawCtx.save();
    drawCtx.setLineDash([4, 4]);
    drawCtx.strokeStyle = '#000';
    drawCtx.lineWidth = 1.5;
    drawCtx.globalAlpha = 0.7;
    drawCtx.beginPath();
    drawCtx.moveTo(selectionPath[0].x, selectionPath[0].y);
    for (let i = 1; i < selectionPath.length; i++) drawCtx.lineTo(selectionPath[i].x, selectionPath[i].y);
    drawCtx.stroke();
    drawCtx.restore();
}}

// ── Move selected strokes by delta ──
function moveSelectedStrokes(dx, dy) {{
    if (!selectedStrokes) return;
    const cid = selectedStrokes.cardId;
    const strokes = getStrokes(cid);
    for (const idx of selectedStrokes.indices) {{
        const s = strokes[idx];
        if (s.type === 'rect') {{ s.x += dx; s.y += dy; }}
        else if (s.points) {{ for (const p of s.points) {{ p.x += dx; p.y += dy; }} }}
    }}
    selectedStrokes.bbox.x += dx;
    selectedStrokes.bbox.y += dy;
}}

// ── Shape snap: convert freehand to shape at 2s mark ──
function triggerShapeSnap() {{
    if (!currentStroke || currentStroke.points.length < 5) return;
    const pts = currentStroke.points;
    const startPt = pts[0];
    const endPt = pts[pts.length - 1];
    const startEndDist = Math.sqrt((endPt.x - startPt.x) ** 2 + (endPt.y - startPt.y) ** 2);
    let pathLen = 0;
    for (let i = 1; i < pts.length; i++) {{
        pathLen += Math.sqrt((pts[i].x - pts[i-1].x) ** 2 + (pts[i].y - pts[i-1].y) ** 2);
    }}
    if (pathLen <= 0) return;

    if (startEndDist < pathLen / 10) {{
        // Rectangle
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (const p of pts) {{
            minX = Math.min(minX, p.x); minY = Math.min(minY, p.y);
            maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y);
        }}
        shapeSnapMode = 'rect';
        shapeSnapData = {{ x: minX, y: minY, w: maxX - minX, h: maxY - minY, handle: 'br' }};
        // Find closest corner to current finger
        const cp = endPt;
        const corners = {{ tl: {{x: minX, y: minY}}, tr: {{x: maxX, y: minY}}, bl: {{x: minX, y: maxY}}, br: {{x: maxX, y: maxY}} }};
        let best = 'br', bestD = Infinity;
        for (const [k, h] of Object.entries(corners)) {{
            const d = Math.sqrt((cp.x - h.x) ** 2 + (cp.y - h.y) ** 2);
            if (d < bestD) {{ bestD = d; best = k; }}
        }}
        shapeSnapData.handle = best;
    }} else {{
        // Horizontal line
        const avgY = (startPt.y + endPt.y) / 2;
        shapeSnapMode = 'line';
        shapeSnapData = {{ startX: startPt.x, startY: avgY, endX: endPt.x }};
    }}
    currentStroke = null; // switch from freehand to shape mode
    // Immediate visual feedback
    const cid = realDrawId();
    renderStrokes(drawCtx, getStrokes(cid), canvasW, canvasH);
    drawLiveShape();
}}

// ── Draw live shape preview while dragging ──
function drawLiveShape() {{
    if (!shapeSnapData || !drawCtx) return;
    const style = {{ mode: drawMode, color: drawColor, size: drawSize }};
    if (shapeSnapMode === 'line') {{
        drawCtx.beginPath();
        drawCtx.moveTo(shapeSnapData.startX, shapeSnapData.startY);
        drawCtx.lineTo(shapeSnapData.endX, shapeSnapData.startY);
        applyStrokeStyle(drawCtx, style);
        drawCtx.stroke();
        drawCtx.globalAlpha = 1.0;
    }} else if (shapeSnapMode === 'rect') {{
        const d = shapeSnapData;
        drawCtx.beginPath();
        drawCtx.rect(d.x, d.y, d.w, d.h);
        applyStrokeStyle(drawCtx, style);
        drawCtx.stroke();
        drawCtx.globalAlpha = 1.0;
        drawResizeHandles(drawCtx, d);
    }}
}}

// ── Toolbar builder (shared for card & quiz) ──
function buildDrawToolbar(tbId) {{
    const tb = document.getElementById(tbId);
    if (!tb || tb.dataset.built) return;
    tb.dataset.built = '1';

    const penBtn = mkToolBtn('🖊️', 'pen');
    const hlBtn = mkToolBtn('🖍️', 'highlighter');
    const eraserBtn = mkToolBtn('🧹', 'eraser');
    const laserBtn = mkToolBtn('🔴', 'laser');
    const moveBtn = mkToolBtn('☩', 'move');
    tb.appendChild(penBtn);
    tb.appendChild(hlBtn);
    tb.appendChild(eraserBtn);
    tb.appendChild(laserBtn);
    tb.appendChild(moveBtn);
    tb.appendChild(mkDivider());

    const palette = document.createElement('span');
    palette.className = 'draw-palette';
    palette.style.display = 'flex';
    palette.style.gap = '4px';
    palette.style.alignItems = 'center';
    PEN_COLORS.forEach((c, i) => {{
        const dot = document.createElement('span');
        dot.className = 'color-dot' + (i === 0 ? ' active' : '');
        dot.style.background = c;
        dot.dataset.color = c;
        dot.onclick = () => {{
            drawColor = dot.dataset.color;
            palette.querySelectorAll('.color-dot').forEach(d => d.classList.remove('active'));
            dot.classList.add('active');
        }};
        palette.appendChild(dot);
    }});
    tb.appendChild(palette);
    tb.appendChild(mkDivider());

    const sizeLabel = document.createElement('span');
    sizeLabel.className = 'size-label';
    sizeLabel.textContent = '2px';
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.className = 'size-slider';
    slider.min = '1';
    slider.max = '12';
    slider.value = '2';
    slider.oninput = () => {{ drawSize = parseInt(slider.value); sizeLabel.textContent = drawSize + 'px'; }};
    tb.appendChild(slider);
    tb.appendChild(sizeLabel);
    tb.appendChild(mkDivider());

    // Undo / Redo buttons
    const undoBtn = document.createElement('button');
    undoBtn.className = 'draw-undo-btn';
    undoBtn.textContent = '↩';
    undoBtn.title = '되돌리기';
    undoBtn.disabled = true;
    undoBtn.onclick = () => drawUndo();
    tb.appendChild(undoBtn);

    const redoBtn = document.createElement('button');
    redoBtn.className = 'draw-redo-btn';
    redoBtn.textContent = '↪';
    redoBtn.title = '앞으로';
    redoBtn.disabled = true;
    redoBtn.onclick = () => drawRedo();
    tb.appendChild(redoBtn);
    tb.appendChild(mkDivider());

    const clearBtn = document.createElement('button');
    clearBtn.className = 'clear-all-btn';
    clearBtn.textContent = '전체 지우기';
    clearBtn.onclick = () => {{
        const cid = realDrawId();
        if (cid && getStrokes(cid).length > 0) {{
            pushDrawUndo(cid);
            drawData[cid] = [];
            activeResizeRect = null;
            selectedStrokes = null;
            saveDrawData();
            redrawCurrent();
        }}
    }};
    tb.appendChild(clearBtn);

    const zoomResetBtn = document.createElement('button');
    zoomResetBtn.className = 'clear-all-btn';
    zoomResetBtn.style.background = '#5c5f77';
    zoomResetBtn.textContent = '🔍 1×';
    zoomResetBtn.title = '확대/축소 초기화';
    zoomResetBtn.onclick = () => {{
        currentZoomScale = 1;
        currentZoomTX = 0;
        currentZoomTY = 0;
        const container = getZoomContainer();
        if (container) container.style.transform = '';
    }};
    tb.appendChild(zoomResetBtn);

    penBtn.classList.add('active');
    function setTool(tool) {{
        drawMode = tool;
        // Clear selection when switching tools
        selectedStrokes = null;
        selectionPath = [];
        isMovingSelection = false;
        [penBtn, hlBtn, eraserBtn, laserBtn, moveBtn].forEach(b => b.classList.remove('active'));
        if (tool === 'pen') {{ penBtn.classList.add('active'); updatePaletteColors(PEN_COLORS, palette); }}
        else if (tool === 'highlighter') {{ hlBtn.classList.add('active'); updatePaletteColors(HL_COLORS, palette); }}
        else if (tool === 'laser') {{ laserBtn.classList.add('active'); }}
        else if (tool === 'move') {{ moveBtn.classList.add('active'); }}
        else {{ eraserBtn.classList.add('active'); }}
        redrawCurrent();
    }}
    penBtn.onclick = () => setTool('pen');
    hlBtn.onclick = () => setTool('highlighter');
    eraserBtn.onclick = () => setTool('eraser');
    laserBtn.onclick = () => setTool('laser');
    moveBtn.onclick = () => setTool('move');
}}

function updatePaletteColors(colors, palette) {{
    const dots = palette.querySelectorAll('.color-dot');
    dots.forEach((dot, i) => {{ dot.style.background = colors[i]; dot.dataset.color = colors[i]; }});
    drawColor = colors[0];
    dots.forEach(d => d.classList.remove('active'));
    if (dots[0]) dots[0].classList.add('active');
}}

function mkToolBtn(emoji, tool) {{
    const btn = document.createElement('button');
    btn.className = 'tool-btn';
    btn.textContent = emoji;
    btn.title = tool;
    return btn;
}}
function mkDivider() {{
    const d = document.createElement('span');
    d.className = 'divider';
    return d;
}}

// ── Redraw current active canvas ──
function redrawCurrent() {{
    if (!drawCtx) return;
    const cid = realDrawId();
    renderStrokes(drawCtx, getStrokes(cid), canvasW, canvasH);
    // Draw laser strokes on top
    renderLaserStrokes(drawCtx);
    // Draw resize handles if active on this card
    if (activeResizeRect && activeResizeRect.cardId === cid) {{
        const rs = getStrokes(cid)[activeResizeRect.strokeIdx];
        if (rs && rs.type === 'rect') {{
            drawResizeHandles(drawCtx, rs);
        }} else {{
            activeResizeRect = null;
        }}
    }}
    // Draw selection box if active
    if (selectedStrokes && selectedStrokes.cardId === cid) {{
        drawSelectionBox();
    }}
}}

// ── Setup canvas helper ──
function setupCanvas(canvas, contentEl) {{
    const rect = contentEl.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvasW = rect.width;
    canvasH = rect.height;
    canvas.width = canvasW * dpr;
    canvas.height = canvasH * dpr;
    canvas.style.width = canvasW + 'px';
    canvas.style.height = canvasH + 'px';
    canvas.style.display = 'block';
    drawCtx = canvas.getContext('2d');
    drawCtx.scale(dpr, dpr);
    canvas.onpointerdown = handlePointerDown;
    canvas.onpointermove = handlePointerMove;
    canvas.onpointerup = handlePointerUp;
    canvas.onpointerleave = handlePointerUp;
    canvas.ondblclick = (e) => e.preventDefault();
    canvas.onselectstart = (e) => e.preventDefault();
    canvas.oncontextmenu = (e) => e.preventDefault();
    canvas.ontouchstart = (e) => {{ if (e.touches.length < 2) e.preventDefault(); }};
}}

// ── Card view toggle ──
function toggleDraw(id) {{
    const canvas = document.getElementById('draw-canvas-' + id);
    const toolbar = document.getElementById('draw-toolbar-' + id);
    const ansArea = document.getElementById('ans-' + id);
    ansArea.style.display = 'block';

    if (canvas.style.display === 'none' || !canvas.style.display) {{
        activeDrawId = id;
        buildDrawToolbar('draw-toolbar-' + id);
        toolbar.classList.add('active');
        ansArea.classList.add('draw-active');
        document.body.classList.add('drawing-active');
        const content = document.getElementById('ans-content-' + id);
        setupCanvas(canvas, content);
        canvas.style.pointerEvents = 'auto';
        renderStrokes(drawCtx, getStrokes(id), canvasW, canvasH);
        updateUndoRedoBtns();
    }} else {{
        saveDrawData();
        canvas.style.display = 'none';
        toolbar.classList.remove('active');
        ansArea.classList.remove('draw-active');
        document.body.classList.remove('drawing-active');
        activeResizeRect = null;
        selectedStrokes = null;
        shapeSnapMode = null;
        shapeSnapData = null;
        // Re-render as static (no pointer events)
        showStaticDraw(id);
        activeDrawId = null;
        drawCtx = null;
    }}
}}

// ── Pointer events ──
function getDrawPos(e) {{
    const canvas = e.target;
    const rect = canvas.getBoundingClientRect();
    // When zoomed, rect is scaled but canvas logical size stays the same
    // Divide by zoom ratio to convert screen coords → logical coords
    const scaleX = canvas.offsetWidth / rect.width;
    const scaleY = canvas.offsetHeight / rect.height;
    return {{
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY
    }};
}}

// ── Pinch-to-Zoom + Pan ──
let activePointers = new Map(); // pointerId -> {{ type, x, y }}
let pinchStartDist = 0;
let pinchStartScale = 1;
let pinchStartMidX = 0, pinchStartMidY = 0;
let pinchStartTX = 0, pinchStartTY = 0;
let currentZoomScale = 1;
let currentZoomTX = 0, currentZoomTY = 0; // translate in px
// Touch input is fully blocked from drawing (Apple Pencil / mouse only)

function getZoomContainer() {{
    if (!activeDrawId) return null;
    const canvasId = activeDrawId === 'quiz' ? 'draw-canvas-quiz' : 'draw-canvas-' + activeDrawId;
    const canvas = document.getElementById(canvasId);
    return canvas ? canvas.parentElement : null;
}}

function applyZoom() {{
    const container = getZoomContainer();
    if (container) {{
        container.style.transformOrigin = '0 0';
        container.style.transform = `translate(${{currentZoomTX}}px, ${{currentZoomTY}}px) scale(${{currentZoomScale}})`;
    }}
}}

function pinchDist(a, b) {{
    const dx = a.x - b.x, dy = a.y - b.y;
    return Math.sqrt(dx * dx + dy * dy);
}}
function pinchMid(a, b) {{
    return {{ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }};
}}

function handlePointerDown(e) {{
    e.preventDefault();
    e.stopPropagation();
    activePointers.set(e.pointerId, {{ type: e.pointerType, x: e.clientX, y: e.clientY }});

    // Touch input → only used for pinch-to-zoom, never for drawing
    if (e.pointerType === 'touch') {{
        const touchPtrs = [...activePointers.entries()].filter(([,v]) => v.type === 'touch');
        if (touchPtrs.length === 2) {{
            // Cancel any in-progress drawing
            if (isDrawing) {{
                isDrawing = false;
                currentStroke = null;
                if (longPressTimer) {{ clearTimeout(longPressTimer); longPressTimer = null; }}
                if (shapeSnapTimer) {{ clearTimeout(shapeSnapTimer); shapeSnapTimer = null; }}
                redrawCurrent();
            }}
            pinchStartDist = pinchDist(touchPtrs[0][1], touchPtrs[1][1]);
            pinchStartScale = currentZoomScale;
            const mid = pinchMid(touchPtrs[0][1], touchPtrs[1][1]);
            pinchStartMidX = mid.x;
            pinchStartMidY = mid.y;
            pinchStartTX = currentZoomTX;
            pinchStartTY = currentZoomTY;
        }}
        return; // touch never draws
    }}

    // pen (Apple Pencil) or mouse → draw
    drawStart(e);
}}

function handlePointerMove(e) {{
    e.preventDefault();
    if (activePointers.has(e.pointerId)) {{
        activePointers.get(e.pointerId).x = e.clientX;
        activePointers.get(e.pointerId).y = e.clientY;
    }}

    // Touch → only pinch zoom + pan
    if (e.pointerType === 'touch') {{
        const touchPtrs = [...activePointers.entries()].filter(([,v]) => v.type === 'touch');
        if (touchPtrs.length === 2 && pinchStartDist > 0) {{
            e.preventDefault();
            const dist = pinchDist(touchPtrs[0][1], touchPtrs[1][1]);
            const newScale = Math.max(0.5, Math.min(5, pinchStartScale * (dist / pinchStartDist)));
            const mid = pinchMid(touchPtrs[0][1], touchPtrs[1][1]);
            // Pan: follow finger midpoint movement
            const panDX = mid.x - pinchStartMidX;
            const panDY = mid.y - pinchStartMidY;
            // Zoom around pinch center: adjust translate so pinch center stays fixed
            const container = getZoomContainer();
            if (container) {{
                const rect = container.parentElement.getBoundingClientRect();
                // Pinch center relative to container's parent
                const cx = pinchStartMidX - rect.left;
                const cy = pinchStartMidY - rect.top;
                // New translate = old translate + pan + zoom-center correction
                currentZoomTX = pinchStartTX + panDX + (cx - pinchStartTX) * (1 - newScale / pinchStartScale);
                currentZoomTY = pinchStartTY + panDY + (cy - pinchStartTY) * (1 - newScale / pinchStartScale);
            }}
            currentZoomScale = newScale;
            applyZoom();
        }}
        return;
    }}

    drawMove(e);
}}

function handlePointerUp(e) {{
    activePointers.delete(e.pointerId);
    const touchCount = [...activePointers.values()].filter(p => p.type === 'touch').length;
    if (touchCount < 2) pinchStartDist = 0;

    // Touch never triggers drawEnd
    if (e.pointerType === 'touch') return;

    drawEnd(e);
}}

function drawStart(e) {{
    e.preventDefault();
    const pos = getDrawPos(e);
    drawStartTime = Date.now();

    // ── Check resize handle click first ──
    if (activeResizeRect) {{
        const cid = realDrawId();
        const strokes = getStrokes(cid);
        const rs = strokes[activeResizeRect.strokeIdx];
        if (rs && rs.type === 'rect') {{
            const handles = getRectHandles(rs);
            for (const [key, h] of Object.entries(handles)) {{
                if (Math.abs(pos.x - h.x) < 14 && Math.abs(pos.y - h.y) < 14) {{
                    pushDrawUndo(cid);
                    resizeDragHandle = key;
                    isDrawing = true;
                    return;
                }}
            }}
        }}
        activeResizeRect = null;
        redrawCurrent();
    }}

    isDrawing = true;

    // ── Move tool ──
    if (drawMode === 'move') {{
        // If tapping inside existing selection → start move drag
        if (selectedStrokes && selectedStrokes.cardId === realDrawId()) {{
            const b = selectedStrokes.bbox;
            if (pos.x >= b.x && pos.x <= b.x + b.w && pos.y >= b.y && pos.y <= b.y + b.h) {{
                pushDrawUndo(realDrawId());
                isMovingSelection = true;
                moveStartPos = pos;
                return;
            }}
        }}
        // Otherwise start new lasso selection
        selectedStrokes = null;
        selectionPath = [pos];
        return;
    }}

    if (drawMode === 'laser') {{
        if (laserFadeTimer) clearTimeout(laserFadeTimer);
        currentStroke = {{ mode: 'laser', color: '#ff1a1a', size: 3, points: [pos] }};
        return;
    }}

    if (drawMode === 'eraser') {{
        eraseAt(pos.x, pos.y);
    }} else {{
        currentStroke = {{ mode: drawMode, color: drawColor, size: drawSize, points: [pos] }};

        // ── Long-press timer: 1s on existing rect → activate resize ──
        if (longPressTimer) clearTimeout(longPressTimer);
        longPressTimer = setTimeout(() => {{
            longPressTimer = null;
            const cid = realDrawId();
            const strokes = getStrokes(cid);
            for (let i = strokes.length - 1; i >= 0; i--) {{
                if (strokes[i].type === 'rect' && pointInRect(pos, strokes[i])) {{
                    activeResizeRect = {{ cardId: cid, strokeIdx: i }};
                    currentStroke = null;
                    isDrawing = false;
                    if (shapeSnapTimer) {{ clearTimeout(shapeSnapTimer); shapeSnapTimer = null; }}
                    redrawCurrent();
                    return;
                }}
            }}
        }}, 1000);

        // ── Shape snap timer: 2s → convert to line/rect ──
        if (shapeSnapTimer) clearTimeout(shapeSnapTimer);
        shapeSnapTimer = setTimeout(() => {{
            shapeSnapTimer = null;
            triggerShapeSnap();
        }}, 2000);
    }}
}}

function drawMove(e) {{
    if (!isDrawing || !drawCtx) return;
    e.preventDefault();
    const pos = getDrawPos(e);

    // ── Move tool: drag selection or draw lasso ──
    if (drawMode === 'move') {{
        if (isMovingSelection && moveStartPos) {{
            const dx = pos.x - moveStartPos.x;
            const dy = pos.y - moveStartPos.y;
            moveSelectedStrokes(dx, dy);
            moveStartPos = pos;
            redrawCurrent();
            drawSelectionBox();
        }} else {{
            selectionPath.push(pos);
            const cid = realDrawId();
            renderStrokes(drawCtx, getStrokes(cid), canvasW, canvasH);
            drawSelectionLine();
        }}
        return;
    }}

    // Cancel long-press if finger moved
    if (longPressTimer && currentStroke && currentStroke.points.length > 0) {{
        const s = currentStroke.points[0];
        if (Math.abs(pos.x - s.x) > 8 || Math.abs(pos.y - s.y) > 8) {{
            clearTimeout(longPressTimer);
            longPressTimer = null;
        }}
    }}

    // ── Resize drag ──
    if (resizeDragHandle && activeResizeRect) {{
        const cid = realDrawId();
        const rs = getStrokes(cid)[activeResizeRect.strokeIdx];
        if (rs) {{
            const h = resizeDragHandle;
            if (h === 'tl') {{ rs.w += rs.x - pos.x; rs.h += rs.y - pos.y; rs.x = pos.x; rs.y = pos.y; }}
            else if (h === 'tr') {{ rs.w = pos.x - rs.x; rs.h += rs.y - pos.y; rs.y = pos.y; }}
            else if (h === 'bl') {{ rs.w += rs.x - pos.x; rs.x = pos.x; rs.h = pos.y - rs.y; }}
            else if (h === 'br') {{ rs.w = pos.x - rs.x; rs.h = pos.y - rs.y; }}
            redrawCurrent();
        }}
        return;
    }}

    // ── Live shape mode (after 2s snap) ──
    if (shapeSnapMode) {{
        const cid = realDrawId();
        if (shapeSnapMode === 'line') {{
            shapeSnapData.endX = pos.x;
        }} else if (shapeSnapMode === 'rect') {{
            const d = shapeSnapData;
            const h = d.handle;
            if (h === 'tl') {{ d.w += d.x - pos.x; d.h += d.y - pos.y; d.x = pos.x; d.y = pos.y; }}
            else if (h === 'tr') {{ d.w = pos.x - d.x; d.h += d.y - pos.y; d.y = pos.y; }}
            else if (h === 'bl') {{ d.w += d.x - pos.x; d.x = pos.x; d.h = pos.y - d.y; }}
            else if (h === 'br') {{ d.w = pos.x - d.x; d.h = pos.y - d.y; }}
        }}
        renderStrokes(drawCtx, getStrokes(cid), canvasW, canvasH);
        drawLiveShape();
        return;
    }}

    if (drawMode === 'laser' && currentStroke) {{
        currentStroke.points.push(pos);
        redrawCurrent();
        // Draw current laser stroke live
        drawCtx.save();
        drawCtx.shadowColor = '#ff0000';
        drawCtx.shadowBlur = 12;
        drawCtx.strokeStyle = '#ff0000';
        drawCtx.globalAlpha = 0.9;
        drawCtx.lineCap = 'round';
        drawCtx.lineJoin = 'round';
        drawCtx.lineWidth = 3;
        drawCtx.beginPath();
        if (currentStroke.points.length > 0) drawCtx.moveTo(currentStroke.points[0].x, currentStroke.points[0].y);
        for (let i = 1; i < currentStroke.points.length; i++) drawCtx.lineTo(currentStroke.points[i].x, currentStroke.points[i].y);
        drawCtx.stroke();
        drawCtx.restore();
        return;
    }}

    if (drawMode === 'eraser') {{
        eraseAt(pos.x, pos.y);
    }} else if (currentStroke) {{
        currentStroke.points.push(pos);
        const cid = realDrawId();
        renderStrokes(drawCtx, getStrokes(cid), canvasW, canvasH);
        drawSingleStroke(drawCtx, currentStroke);
    }}
}}

function drawEnd(e) {{
    if (!isDrawing) return;
    isDrawing = false;
    if (longPressTimer) {{ clearTimeout(longPressTimer); longPressTimer = null; }}
    if (shapeSnapTimer) {{ clearTimeout(shapeSnapTimer); shapeSnapTimer = null; }}

    // ── Move tool end ──
    if (drawMode === 'move') {{
        if (isMovingSelection) {{
            isMovingSelection = false;
            moveStartPos = null;
            saveDrawData();
            redrawCurrent();
            if (selectedStrokes) drawSelectionBox();
        }} else if (selectionPath.length >= 2) {{
            // Find strokes intersecting the lasso path
            const cid = realDrawId();
            const strokes = getStrokes(cid);
            const indices = [];
            for (let i = 0; i < strokes.length; i++) {{
                if (strokeIntersectsPath(strokes[i], selectionPath)) indices.push(i);
            }}
            if (indices.length > 0) {{
                selectedStrokes = {{ cardId: cid, indices, bbox: computeSelectionBBox(strokes, indices) }};
            }} else {{
                selectedStrokes = null;
            }}
            selectionPath = [];
            redrawCurrent();
            if (selectedStrokes) drawSelectionBox();
        }}
        return;
    }}

    // ── Finish resize drag ──
    if (resizeDragHandle) {{
        resizeDragHandle = null;
        saveDrawData();
        redrawCurrent();
        return;
    }}

    // ── Finish live shape ──
    if (shapeSnapMode) {{
        const cid = realDrawId();
        pushDrawUndo(cid);
        if (shapeSnapMode === 'line') {{
            const lineStroke = {{
                mode: drawMode, color: drawColor, size: drawSize,
                type: 'line',
                points: [{{ x: shapeSnapData.startX, y: shapeSnapData.startY }},
                         {{ x: shapeSnapData.endX || shapeSnapData.startX + 20, y: shapeSnapData.startY }}]
            }};
            getStrokes(cid).push(lineStroke);
        }} else if (shapeSnapMode === 'rect') {{
            const d = shapeSnapData;
            const rectStroke = {{
                mode: drawMode, color: drawColor, size: drawSize,
                type: 'rect', x: d.x, y: d.y, w: d.w, h: d.h
            }};
            getStrokes(cid).push(rectStroke);
            activeResizeRect = {{ cardId: cid, strokeIdx: getStrokes(cid).length - 1 }};
        }}
        shapeSnapMode = null;
        shapeSnapData = null;
        saveDrawData();
        redrawCurrent();
        return;
    }}

    // ── Laser stroke end → add to temporary list, start fade timer ──
    if (drawMode === 'laser' && currentStroke && currentStroke.points.length >= 2) {{
        laserStrokes.push(currentStroke);
        currentStroke = null;
        startLaserFade();
        redrawCurrent();
        return;
    }}

    // ── Normal stroke end ──
    if (drawMode !== 'eraser' && drawMode !== 'laser' && currentStroke && currentStroke.points.length >= 2) {{
        const cid = realDrawId();
        pushDrawUndo(cid);
        getStrokes(cid).push(currentStroke);
        saveDrawData();
    }}
    currentStroke = null;
    redrawCurrent();
}}

function drawSingleStroke(ctx, s) {{
    if (!s.points || s.points.length < 2) return;
    ctx.beginPath();
    ctx.moveTo(s.points[0].x, s.points[0].y);
    for (let i = 1; i < s.points.length; i++) ctx.lineTo(s.points[i].x, s.points[i].y);
    applyStrokeStyle(ctx, s);
    ctx.stroke();
    ctx.globalAlpha = 1.0;
}}

function eraseAt(px, py) {{
    const cid = realDrawId();
    const strokes = getStrokes(cid);
    const threshold = 12;
    for (let i = strokes.length - 1; i >= 0; i--) {{
        if (strokeHitTest(strokes[i], px, py, threshold)) {{
            pushDrawUndo(cid);
            // If erasing the active resize rect, clear it
            if (activeResizeRect && activeResizeRect.cardId === cid && activeResizeRect.strokeIdx === i) {{
                activeResizeRect = null;
            }} else if (activeResizeRect && activeResizeRect.cardId === cid && activeResizeRect.strokeIdx > i) {{
                activeResizeRect.strokeIdx--; // adjust index after splice
            }}
            strokes.splice(i, 1);
            saveDrawData();
            redrawCurrent();
            return;
        }}
    }}
}}

// ── Show saved strokes as static (non-interactive) overlay ──
function showStaticDraw(id) {{
    const strokes = drawData[id];
    if (!strokes || strokes.length === 0) return;
    const canvas = document.getElementById('draw-canvas-' + id);
    if (!canvas) return;
    const content = document.getElementById('ans-content-' + id);
    if (!content) return;
    const rect = content.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    canvas.style.display = 'block';
    canvas.style.pointerEvents = 'none';
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    renderStrokes(ctx, strokes, rect.width, rect.height);
}}

// ── Quiz draw ──
let quizDrawCardId = null;
function toggleQuizDraw(id) {{
    const canvas = document.getElementById('draw-canvas-quiz');
    const toolbar = document.getElementById('draw-toolbar-quiz');

    if (canvas.style.display === 'none' || !canvas.style.display) {{
        quizDrawCardId = id;
        activeDrawId = 'quiz';
        buildDrawToolbar('draw-toolbar-quiz');
        toolbar.classList.add('active');
        const content = document.getElementById('quizAnsContent');
        const quizAns = document.getElementById('quizAnswer');
        if (quizAns) quizAns.classList.add('draw-active');
        document.body.classList.add('drawing-active');
        setupCanvas(canvas, content);
        canvas.style.pointerEvents = 'auto';
        renderStrokes(drawCtx, getStrokes(id), canvasW, canvasH);
        updateUndoRedoBtns();
    }} else {{
        saveDrawData();
        canvas.style.display = 'none';
        toolbar.classList.remove('active');
        const quizAns = document.getElementById('quizAnswer');
        if (quizAns) quizAns.classList.remove('draw-active');
        document.body.classList.remove('drawing-active');
        activeDrawId = null;
        drawCtx = null;
    }}
}}

// ── Indicators ──
function showDrawIndicators() {{
    ALL_IDS.forEach(id => {{
        const btn = document.querySelector('#card-' + id + ' .draw-btn');
        if (btn) {{
            const has = drawData[id] && drawData[id].length > 0;
            btn.style.opacity = has ? '1' : '';
            btn.textContent = has ? '🍎✨' : '🍎';
        }}
    }});
}}

// ── Restore static drawings when answer toggled open ──
const origToggleAnswer = toggleAnswer;
toggleAnswer = function(id) {{
    origToggleAnswer(id);
    const ansEl = document.getElementById('ans-' + id);
    if (ansEl.style.display !== 'none' && drawData[id] && drawData[id].length > 0 && activeDrawId !== id) {{
        setTimeout(() => showStaticDraw(id), 50);
    }}
}};

// ── Image Crop Tool ──
const CROP_EDITS_KEY = STORAGE_PREFIX + 'crop_edits_v1';
const CROP_ORIG_KEY = STORAGE_PREFIX + 'crop_orig_v1';
let cropEdits = JSON.parse(localStorage.getItem(CROP_EDITS_KEY) || '{{}}');
let cropOriginals = JSON.parse(localStorage.getItem(CROP_ORIG_KEY) || '{{}}');
function saveCropEdits() {{ localStorage.setItem(CROP_EDITS_KEY, JSON.stringify(cropEdits)); }}
function saveCropOriginals() {{ localStorage.setItem(CROP_ORIG_KEY, JSON.stringify(cropOriginals)); }}

let cropState = null; // {{ imgEl, startX, startY, selection }}

function wrapGuideImages() {{
    // Wrap all guide-area and quiz-guide images with crop button
    document.querySelectorAll('.guide-area img, .quiz-guide img').forEach(img => {{
        if (img.parentElement.classList.contains('img-wrapper')) return;
        // Remember original src for restoration
        if (!img.dataset.originalSrc) img.dataset.originalSrc = img.src;
        const wrapper = document.createElement('div');
        wrapper.className = 'img-wrapper';
        img.parentElement.insertBefore(wrapper, img);
        wrapper.appendChild(img);

        const btn = document.createElement('button');
        btn.className = 'crop-btn';
        btn.textContent = '✂️';
        btn.title = '이미지 자르기';
        btn.onclick = function(e) {{
            e.stopPropagation();
            openCropTool(img);
        }};
        wrapper.appendChild(btn);
    }});
}}

function openCropTool(imgEl) {{
    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'crop-overlay';
    overlay.id = 'cropOverlay';

    const toolbar = document.createElement('div');
    toolbar.className = 'crop-toolbar';
    toolbar.innerHTML = `
        <button class="crop-confirm" id="cropConfirm" disabled>✂️ 자르기</button>
        <button class="crop-reset" id="cropReset">↺ 원본 복원</button>
        <button class="crop-cancel" id="cropCancel">✕ 취소</button>
    `;

    const container = document.createElement('div');
    container.className = 'crop-container';
    container.id = 'cropContainer';

    const img = document.createElement('img');
    img.src = imgEl.src;
    img.id = 'cropImage';
    img.draggable = false;

    const selection = document.createElement('div');
    selection.className = 'crop-selection';
    selection.id = 'cropSelection';

    container.appendChild(img);
    container.appendChild(selection);
    overlay.appendChild(toolbar);
    overlay.appendChild(container);
    document.body.appendChild(overlay);

    // State
    cropState = {{ imgEl, selection, container, img, overlay, dragging: false, sx: 0, sy: 0 }};

    // Events
    container.addEventListener('mousedown', cropMouseDown);
    container.addEventListener('mousemove', cropMouseMove);
    container.addEventListener('mouseup', cropMouseUp);

    // Touch support
    container.addEventListener('touchstart', cropTouchStart, {{ passive: false }});
    container.addEventListener('touchmove', cropTouchMove, {{ passive: false }});
    container.addEventListener('touchend', cropTouchEnd);

    document.getElementById('cropConfirm').addEventListener('click', cropConfirm);
    document.getElementById('cropCancel').addEventListener('click', cropCancel);
    document.getElementById('cropReset').addEventListener('click', function() {{ cropReset(imgEl); }});

    // ESC to cancel
    overlay._escHandler = function(e) {{ if (e.key === 'Escape') cropCancel(); }};
    document.addEventListener('keydown', overlay._escHandler);
}}

function getContainerPos(e) {{
    const rect = cropState.container.getBoundingClientRect();
    return {{
        x: Math.max(0, Math.min(e.clientX - rect.left, rect.width)),
        y: Math.max(0, Math.min(e.clientY - rect.top, rect.height))
    }};
}}

function cropMouseDown(e) {{
    e.preventDefault();
    const pos = getContainerPos(e);
    cropState.dragging = true;
    cropState.sx = pos.x;
    cropState.sy = pos.y;
    cropState.selection.style.display = 'none';
    document.getElementById('cropConfirm').disabled = true;
}}

function cropMouseMove(e) {{
    if (!cropState || !cropState.dragging) return;
    const pos = getContainerPos(e);
    const x = Math.min(cropState.sx, pos.x);
    const y = Math.min(cropState.sy, pos.y);
    const w = Math.abs(pos.x - cropState.sx);
    const h = Math.abs(pos.y - cropState.sy);
    const sel = cropState.selection;
    sel.style.display = 'block';
    sel.style.left = x + 'px';
    sel.style.top = y + 'px';
    sel.style.width = w + 'px';
    sel.style.height = h + 'px';
}}

function cropMouseUp(e) {{
    if (!cropState || !cropState.dragging) return;
    cropState.dragging = false;
    const sel = cropState.selection;
    const w = parseInt(sel.style.width);
    const h = parseInt(sel.style.height);
    if (w > 10 && h > 10) {{
        document.getElementById('cropConfirm').disabled = false;
    }}
}}

// Touch handlers
function cropTouchStart(e) {{
    e.preventDefault();
    const touch = e.touches[0];
    cropMouseDown({{ clientX: touch.clientX, clientY: touch.clientY, preventDefault: () => {{}} }});
}}
function cropTouchMove(e) {{
    e.preventDefault();
    const touch = e.touches[0];
    cropMouseMove({{ clientX: touch.clientX, clientY: touch.clientY }});
}}
function cropTouchEnd(e) {{
    cropMouseUp(e);
}}

function cropConfirm() {{
    if (!cropState) return;
    const sel = cropState.selection;
    const img = cropState.img;
    const imgRect = img.getBoundingClientRect();
    const containerRect = cropState.container.getBoundingClientRect();

    // Calculate scale between displayed image and natural size
    const scaleX = img.naturalWidth / img.width;
    const scaleY = img.naturalHeight / img.height;

    // Offset of image within container (if centered)
    const imgOffsetX = img.offsetLeft;
    const imgOffsetY = img.offsetTop;

    const cropX = (parseInt(sel.style.left) - imgOffsetX) * scaleX;
    const cropY = (parseInt(sel.style.top) - imgOffsetY) * scaleY;
    const cropW = parseInt(sel.style.width) * scaleX;
    const cropH = parseInt(sel.style.height) * scaleY;

    // Use canvas to crop
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(cropW));
    canvas.height = Math.max(1, Math.round(cropH));
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, Math.round(cropX), Math.round(cropY), Math.round(cropW), Math.round(cropH), 0, 0, canvas.width, canvas.height);

    const newSrc = canvas.toDataURL('image/png');

    // Apply to the original image
    cropState.imgEl.src = newSrc;

    // Save crop edit (identify by image index in parent)
    const parent = cropState.imgEl.closest('.guide-area, .quiz-guide');
    if (parent) {{
        const cardEl = parent.closest('.card, .quiz-card');
        if (cardEl) {{
            const cardId = cardEl.id.replace('card-', '');
            const imgs = parent.querySelectorAll('img');
            const idx = Array.from(imgs).indexOf(cropState.imgEl);
            // Save original BEFORE first crop (so we can always restore)
            if (!cropOriginals[cardId]) cropOriginals[cardId] = {{}};
            if (!cropOriginals[cardId][idx]) {{
                cropOriginals[cardId][idx] = cropState.imgEl.dataset.originalSrc || cropState.img.src;
            }}
            saveCropOriginals();
            if (!cropEdits[cardId]) cropEdits[cardId] = {{}};
            cropEdits[cardId][idx] = newSrc;
            saveCropEdits();
        }}
    }}

    closeCropOverlay();
}}

function cropCancel() {{
    closeCropOverlay();
}}

function cropReset(imgEl) {{
    const parent = imgEl.closest('.guide-area, .quiz-guide');
    if (parent) {{
        const cardEl = parent.closest('.card, .quiz-card');
        if (cardEl) {{
            const cardId = cardEl.id.replace('card-', '');
            const imgs = parent.querySelectorAll('img');
            const idx = Array.from(imgs).indexOf(imgEl);

            // 1) Try saved original first
            if (cropOriginals[cardId] && cropOriginals[cardId][idx]) {{
                imgEl.src = cropOriginals[cardId][idx];
                delete cropOriginals[cardId][idx];
                if (Object.keys(cropOriginals[cardId]).length === 0) delete cropOriginals[cardId];
                saveCropOriginals();
            }} else {{
                // 2) Fallback: re-parse from QUIZ_DATA
                const data = QUIZ_DATA[cardId];
                if (data) {{
                    const temp = document.createElement('div');
                    temp.innerHTML = data.g;
                    const origImgs = temp.querySelectorAll('img');
                    if (origImgs[idx]) imgEl.src = origImgs[idx].src;
                }}
            }}
            // Remove saved crop
            if (cropEdits[cardId]) {{
                delete cropEdits[cardId][idx];
                if (Object.keys(cropEdits[cardId]).length === 0) delete cropEdits[cardId];
                saveCropEdits();
            }}
        }}
    }}
    closeCropOverlay();
}}

function closeCropOverlay() {{
    const overlay = document.getElementById('cropOverlay');
    if (overlay) {{
        document.removeEventListener('keydown', overlay._escHandler);
        overlay.remove();
    }}
    cropState = null;
}}

function applyCropEdits() {{
    // Apply saved crop edits to guide images
    for (const cardId in cropEdits) {{
        const guideEl = document.getElementById('guide-' + cardId);
        if (guideEl && guideEl.dataset.loaded) {{
            const imgs = guideEl.querySelectorAll('img');
            for (const idx in cropEdits[cardId]) {{
                if (imgs[idx]) imgs[idx].src = cropEdits[cardId][idx];
            }}
        }}
    }}
}}

// Observe guide areas being opened to apply crops and wrap images
const guideObserver = new MutationObserver(function(mutations) {{
    mutations.forEach(function(m) {{
        if (m.type === 'childList' || m.type === 'attributes') {{
            setTimeout(() => {{
                wrapGuideImages();
                applyCropEdits();
            }}, 50);
        }}
    }});
}});

// ── Init ──
window.addEventListener('DOMContentLoaded', function() {{
    applyEdits();
    updateReviewBtn();
    showDrawIndicators();

    // Restore sidebar state
    if (localStorage.getItem('sb_collapsed') === 'true') {{
        document.getElementById('sidebar').classList.add('collapsed');
        document.getElementById('mainContent').classList.add('expanded');
    }}

    // Observe all guide areas for content changes (lazy loading)
    document.querySelectorAll('.guide-area').forEach(el => {{
        guideObserver.observe(el, {{ childList: true, subtree: true }});
    }});

    // Also observe quiz body for quiz mode guide images
    guideObserver.observe(document.getElementById('quizBody'), {{ childList: true, subtree: true }});
}});
</script>
</body>
</html>"""
    return html



class QuizBuilder:
    """카드 목록을 받아 단일 HTML 파일로 출력하는 빌더."""

    def __init__(self, cards, title="Anki 퀴즈", storage_prefix="quiz",
                 subtitle=None, page_images=None):
        """
        Parameters
        ----------
        cards          : 카드 딕셔너리 목록 (id/num/q/a + 선택: g, pages)
        title          : 페이지 제목
        storage_prefix : localStorage 키 접두사 (기본 "quiz")
        subtitle       : 부제목 (선택, 없으면 자동 생성)
        page_images    : {페이지번호: base64문자열} 딕셔너리 (선택)
        """
        self.cards = cards
        self.title = title
        self.storage_prefix = storage_prefix
        self.subtitle = subtitle or f"{title} — {len(cards)}문제"
        self.page_images = page_images or {}

        # Populate 'g' field from page_images if not directly provided
        for c in self.cards:
            if "g" not in c or not c["g"]:
                c["g"] = ""  # will be built from pages in build_html

    def build(self) -> str:
        """완성된 HTML 문자열 반환"""
        return build_html(self.cards, self.page_images, self.title, self.storage_prefix)

    def write(self, path: str) -> None:
        """HTML을 파일로 저장"""
        html = self.build()
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f"✅ 생성 완료: {path}  ({size_mb:.1f} MB, {len(self.cards)}문항)")


if __name__ == "__main__":
    # 데모: 간단한 2문항 퀴즈 생성
    demo_cards = [
        {
            "id": "c1", "num": 1,
            "q": "파이썬에서 리스트와 튜플의 차이는?",
            "a": """<h4>핵심 차이</h4>
<table><tr><th></th><th>list</th><th>tuple</th></tr>
<tr><td>가변성</td><td>Mutable</td><td>Immutable</td></tr>
<tr><td>문법</td><td>[ ]</td><td>( )</td></tr>
<tr><td>속도</td><td>느림</td><td>빠름</td></tr></table>""",
            "g": "<p><b>한 줄 요약:</b> list = 변경 가능, tuple = 변경 불가</p>",
        },
        {
            "id": "c2", "num": 2,
            "q": "HTTP 상태 코드 200, 404, 500의 의미는?",
            "a": "<p><b>200</b> OK — 요청 성공<br><b>404</b> Not Found — 리소스 없음<br><b>500</b> Internal Server Error — 서버 오류</p>",
            "g": "",
        },
    ]

    builder = QuizBuilder(
        cards=demo_cards,
        title="데모 퀴즈",
        storage_prefix="demo_quiz",
    )
    builder.write("demo_quiz.html")
