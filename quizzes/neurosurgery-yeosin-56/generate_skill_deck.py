"""Build reviewed 56 cards with the existing shared Anki skill QuizBuilder."""
from pathlib import Path
import hashlib
import html
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from anki_quiz_builder import QuizBuilder, run_rails
from anki_backup_restore import inject_backup_restore

TITLE = '신경외과 여신 완성본 · 56문제 Anki'
PREFIX = 'neurosurgery_yeosin_56_anki'
VERSION = '2026-09-17.skill.8-source-answers'

def replace_once(text, old, new):
    assert text.count(old) == 1, f'Builder marker changed: {old[:70]}'
    return text.replace(old, new, 1)

def source_question_html(item, card):
    q = '<div class="source-question"><p class="source-question-text">' + html.escape(item['text']) + '</p></div>'
    if item.get('fullText'):
        q += '<details class="source-question-detail" open><summary>원문 상세 지문</summary><div class="source-question-full">' + html.escape(item['fullText']) + '</div></details>'
    images = json.loads((ROOT/'question-images.json').read_text()).get(card['id'], card.get('questionImages', []))
    if images:
        q += '<div class="question-images">'
    for index, im in enumerate(images, 1):
        p = ROOT / im['src']
        assert p.is_file() and p.resolve().is_relative_to(ROOT)
        src = html.escape(im['src'], quote=True)
        label = html.escape(im.get('label', f'원문 그림 {index}'))
        q += f'<figure class="question-image"><button type="button" class="question-image-open" aria-label="{label} 확대"><img src="{src}" alt="{label}" decoding="async"></button><figcaption>{label} · 눌러서 확대</figcaption></figure>'
    if images:
        q += '</div>'
    q += '<p class="question-source-link"><a href="' + html.escape(card['sourceUrl'], quote=True) + '" target="_blank" rel="noopener">원문 확인 · ' + html.escape(str(item['sourceSet'])) + '세트 ' + str(item['num']) + '번</a></p>'
    assert not any(x in q for x in ['`', '${', '\\', '</script>'])
    return q

def source_answer_html(card, images):
    result = '<section class="source-answer-guide"><p><strong>여신 원문 답안</strong></p><p class="source-answer-note">원문 그대로의 캡처입니다. 교정된 내용은 정답 필기를 함께 확인하세요.</p><div class="source-answer-images">'
    for index, item in enumerate(images, 1):
        path = ROOT / item['src']
        assert path.is_file() and path.resolve().is_relative_to(ROOT)
        src = html.escape(item['src'], quote=True)
        label = f'여신 원문 답안 {index} · PDF {int(item["page"])}쪽'
        result += f'<figure class="question-image source-answer-image"><button type="button" class="question-image-open" data-image-kind="answer" aria-label="{label} 확대"><img src="{src}" alt="{label}" loading="lazy" decoding="async"></button><figcaption>{label} · 눌러서 확대</figcaption></figure>'
    result += '</div></section>'
    assert not any(x in result for x in ['`', '${', '\\', '</script>'])
    return result

def card_data(source):
    cards = []
    originals = json.loads((ROOT/'original-notes.json').read_text())
    supplements = json.loads((ROOT/'original-supplements.json').read_text())
    questions = json.loads((ROOT/'original-questions.json').read_text())
    answer_images = json.loads((ROOT/'answer-images.json').read_text())
    assert set(originals) == {c['id'] for c in source}
    assert set(questions['all']) == set(originals)
    assert set(answer_images) == set(originals) and all(answer_images.values())
    for c in source:
        q = source_question_html(questions['all'][c['id']], c)
        answer = '<div class="original-note">' + originals[c['id']] + '</div>'
        if c['id'] in supplements:
            answer += '<aside class="note-correction"><strong>보충·교정</strong><p>' + html.escape(supplements[c['id']]) + '</p></aside>'
        guide = source_answer_html(c, answer_images[c['id']])
        guide += '<details><summary>요점·보충 답안</summary>' + c['answerHtml'] + '</details>'
        if c['terms']:
            guide += '<details class="term-guide"><summary>용어 풀이</summary><dl>'
            for t in c['terms']:
                guide += f'<dt><strong>{html.escape(t["term"])}</strong></dt><dd>{html.escape(t["definition"])}</dd>'
            guide += '</dl></details>'
        guide += f'<p class="source-link"><a href="{html.escape(c["sourceUrl"], quote=True)}" target="_blank" rel="noopener">원문 필기 · PDF {c["sourcePage"]}쪽</a></p>'
        cards.append({'id': c['id'], 'num': c['num'], 'q': q, 'a': answer, 'g': guide})
    return cards

def decorate(text):
    text = inject_backup_restore(text, site_id='neurosurgery-yeosin-56-anki', download_prefix='신경외과_여신56_Anki_백업')
    text = replace_once(text, '</title>', '</title>\n<link rel="icon" href="../../assets/icons/favicon.svg">\n<meta name="deck-version" content="' + VERSION + '">')
    text = replace_once(text, 'data-order="random">랜덤 퀴즈</button>', 'data-order="ordered">순서대로 퀴즈</button>')
    text = replace_once(text, "ENABLE_ORDER_MODES ? '랜덤 (' + count + ')' : label", "ENABLE_ORDER_MODES ? '순서대로 (' + count + ')' : label")
    text = replace_once(text, '<div class="card-grid">', '''<div class="deck-note">선택한 범위로 Anki 학습<br><small>정답 공개 → 🔴 1분 · 🟠 5분 · 🟢 10분/숙달 · 🔵 내일<br>학습 기록은 세트별 · 수정 답안·필기는 공통 보존</small></div>
<div class="card-grid">''')
    text = replace_once(text, '</style>', (ROOT/'deck-layout.css').read_text() + '\n</style>')
    # The local adapter does not modify the shared builder or any other decks.
    text = text.replace('localStorage.', 'deckStorage.')
    # Backup restoration must throw on quota failure so the shared helper can
    # roll back its multi-key transaction. Never use best-effort storage here.
    start = text.index('function replaceSiteStorage(data) {')
    end = text.index('async function importBackupFile(file)', start)
    text = text[:start] + text[start:end].replace('deckStorage.', 'window.localStorage.') + text[end:]
    # Do not overwrite an imported session with the pre-import in-memory queue
    # while reloading after a successful backup restore.
    text = replace_once(text, '        location.reload();', "        window.removeEventListener('pagehide', saveQuizSession);\n        window.removeEventListener('beforeunload', saveQuizSession);\n        location.reload();")
    for key, fallback in [('SRS_KEY','{}'),('HIST_KEY','[]'),('EDITS_KEY','{}'),('USER_ANS_KEY','{}'),('DRAW_KEY','{}'),('CROP_EDITS_KEY','{}'),('CROP_ORIG_KEY','{}')]:
        text = text.replace(f"JSON.parse(deckStorage.getItem({key}) || '{fallback}')", f'deckStoredJson({key}, {fallback})')
    text = replace_once(text, 'const STORAGE_PREFIX = ', (ROOT/'storage-adapter.js').read_text() + '\nconst STORAGE_PREFIX = ')
    text = replace_once(text, '// ── Init ──', (ROOT/'skill-adapter.js').read_text() + '\n// ── Init ──')
    categories = {c['id']: c['category'] for c in json.loads((ROOT/'deck.json').read_text())}
    browse = 'const DECK_CATEGORIES = ' + json.dumps(categories, ensure_ascii=False) + ';\n'
    exam_sets = json.loads((ROOT/'exam-sets.json').read_text())
    for exam in exam_sets.values():
        assert len(exam['items']) == 20 and len({i['id'] for i in exam['items']}) == 20
        assert [i['num'] for i in exam['items']] == list(range(1, 21))
        assert all(i['id'] in categories for i in exam['items'])
    source_cards = {c['id']: c for c in json.loads((ROOT/'deck.json').read_text())}
    questions = json.loads((ROOT/'original-questions.json').read_text())
    scoped_questions = {scope: {cid: source_question_html(item, source_cards[cid]) for cid,item in questions[scope].items()} for scope in exam_sets}
    scope_init = 'const DECK_EXAM_SETS = ' + json.dumps(exam_sets, ensure_ascii=False) + ';\nconst DECK_SOURCE_QUESTIONS = ' + json.dumps(scoped_questions,ensure_ascii=False) + ';\n' + (ROOT/'study-scope-init.js').read_text()
    text = replace_once(text, 'const SRS_KEY = ', scope_init + '\nlet SRS_KEY = ')
    text = text.replace("STORAGE_PREFIX + 'srs_v1'", "scopeStorageKey('srs_v1')").replace("const HIST_KEY = STORAGE_PREFIX + 'hist_v1'", "let HIST_KEY = scopeStorageKey('hist_v1')").replace("const QUIZ_SESSION_KEY = STORAGE_PREFIX + 'quiz_session_v1'", "let QUIZ_SESSION_KEY = scopeStorageKey('quiz_session_v1')")
    for name in ['getStudyPlan', 'doResetQuiz', 'updateStats', 'renderComplete', 'startBonus']:
        start = text.index('function ' + name + '(')
        end = text.find('\nfunction ', start + 1)
        text = text[:start] + text[start:end].replace('ALL_IDS', 'studyIds()') + text[end:]
    text = replace_once(text, 'const n = Number(data.num);', 'const n = Number(studyNumber(id));')
    text = replace_once(text, '<span class="card-num">Q${data.num}</span>', '<span class="card-num">${studyLabel()} · Q${studyNumber(id)}</span>')
    text = replace_once(text, '<div class="quiz-q-text">${data.q}</div>', '<div class="quiz-q-text">${studyQuestion(id)}</div>')
    text = replace_once(text, "const q = card?.querySelector('.card-title')?.textContent || stripHtml(data.q || '');", "const inQuiz = document.getElementById('quizOverlay').classList.contains('active');\n    const q = inQuiz ? stripHtml(studyQuestion(id)) : (card?.querySelector('.card-title')?.textContent || stripHtml(data.q || ''));")
    text = replace_once(text, "const num = card?.querySelector('.card-num')?.textContent || data.num || id;", "const num = inQuiz ? studyNumber(id) : (card?.querySelector('.card-num')?.textContent || data.num || id);")
    text = replace_once(text, '// ── Init ──', (ROOT/'study-scope-adapter.js').read_text() + '\n// ── Init ──')
    browse += (ROOT/'browse-adapter.js').read_text()
    browse += '\n' + (ROOT/'question-image-viewer.js').read_text()
    text = replace_once(text, '</script>\n</body>', browse + '\n</script>\n</body>')
    return text

def build(root=ROOT):
    source=json.loads((root/'deck.json').read_text())
    assert len(source)==56 and len({c['id'] for c in source})==56
    assert [c['num'] for c in source]==list(range(1,57))
    cards=card_data(source)
    report=run_rails(cards,mode='basic',strict=True)
    report.print_report()
    assert not report.has_errors
    builder=QuizBuilder(cards=cards,title=TITLE,storage_prefix=PREFIX,enable_self_answer=False,
                        enable_order_modes=True,enable_rail=True,rail_mode='basic',rail_strict=True)
    generated='\n'.join(line.rstrip() for line in decorate(builder.build()).splitlines())+'\n'
    assert len(re.findall(r'class="card" id="card-',generated))==56
    assert not re.search(r'/Users/|/Volumes/|@gmail[.]com|PREVMED_LOCAL_SECRET',generated)
    assert 'window.YEOSIN_DECK' not in generated
    (root/'index.html').write_text(generated)
    qc={'version':VERSION,'cards':56,'builder':'../anki_quiz_builder.py',
        'builderSha256':hashlib.sha256((ROOT.parent/'anki_quiz_builder.py').read_bytes()).hexdigest(),
        'sourceSha256':hashlib.sha256((root/'deck.json').read_bytes()).hexdigest(),
        'originalNotesSha256':hashlib.sha256((root/'original-notes.json').read_bytes()).hexdigest(),
        'originalQuestionsSha256':hashlib.sha256((root/'original-questions.json').read_bytes()).hexdigest(),
        'images':sum(len(v) for v in json.loads((root/'question-images.json').read_text()).values()),
        'questionImagesSha256':hashlib.sha256((root/'question-images.json').read_bytes()).hexdigest(),
        'answerImageCards':len(json.loads((root/'answer-images.json').read_text())),
        'answerImages':sum(len(v) for v in json.loads((root/'answer-images.json').read_text()).values()),
        'answerImagesSha256':hashlib.sha256((root/'answer-images.json').read_bytes()).hexdigest(),
        'terms':sum(len(c['terms']) for c in source),'railErrors':0,
        'htmlSha256':hashlib.sha256(generated.encode()).hexdigest()}
    (root/'build-qc.json').write_text(json.dumps(qc,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(qc,ensure_ascii=False))

if __name__=='__main__': build()
