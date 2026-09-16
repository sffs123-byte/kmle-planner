"""Publish the reviewed deck JSON as a static JS data file (no network)."""
from pathlib import Path
import json,re

def build(root: Path):
    cards=json.loads((root/'deck.json').read_text())
    assert len(cards)==56, 'Expected 56 deduplicated question groups'
    assert len({c['id'] for c in cards})==56
    assert sorted(c['num'] for c in cards)==list(range(1,57))
    for c in cards:
        for key in ['id','category','question','answerHtml','explanationHtml','sourceUrl']:
            assert isinstance(c[key],str) and c[key].strip(), (c['id'],key)
        for key in ['answerHtml','explanationHtml']:
            assert not re.search(r'<script|on\w+\s*=|javascript:|data-note-comment-author',c[key],re.I),c['id']
        assert 'cnu-preventive-medicine-private.vercel.app/notes/neurosurgery-yeosin-complete' in c['sourceUrl']
    raw=json.dumps(cards,ensure_ascii=False,separators=(',',':'))
    assert not re.search(r'/Users/|/Volumes/|@gmail\.com|PREVMED_LOCAL_SECRET|[0-9]{6}-[1-4][0-9]{6}',raw), 'Private metadata in public deck'
    (root/'deck.js').write_text('window.YEOSIN_DECK = '+raw.replace('</','<\\/')+';\n')
    print(json.dumps({'cards':len(cards),'uniqueIds':len({c['id'] for c in cards}),'bytes':len(raw.encode()),'status':'pass'}))

if __name__=='__main__':build(Path(__file__).parent)
