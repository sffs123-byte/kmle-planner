// Read-only source-image viewer. Does not touch answers, SRS or annotations.
window.addEventListener('DOMContentLoaded', function () {
    const dialog = document.createElement('dialog');
    dialog.id = 'questionImageDialog';
    dialog.setAttribute('aria-labelledby', 'questionImageTitle');
    dialog.innerHTML = `<div class="question-image-toolbar">
      <strong id="questionImageTitle">원문 문제 그림</strong>
      <button type="button" id="questionImageZoom" aria-pressed="false">2배 확대</button>
      <button type="button" id="questionImageClose" aria-label="원문 그림 닫기">닫기 ×</button>
    </div><div class="question-image-viewport"><img id="questionImageFull" alt=""></div>`;
    document.body.appendChild(dialog);
    const full = dialog.querySelector('#questionImageFull');
    const viewport = dialog.querySelector('.question-image-viewport');
    const zoom = dialog.querySelector('#questionImageZoom');
    let opener = null;
    function setZoom(expanded) {
        dialog.classList.toggle('image-zoomed', expanded);
        zoom.setAttribute('aria-pressed', String(expanded));
        zoom.textContent = expanded ? '화면에 맞추기' : '2배 확대';
        full.style.width = expanded ? Math.round(Math.max(1, viewport.clientWidth - 24) * 2) + 'px' : '';
    }
    document.addEventListener('click', function (event) {
        const button = event.target.closest?.('.question-image-open');
        if (!button) return;
        const img = button.querySelector('img');
        if (!img) return;
        event.preventDefault();
        opener = button;
        full.src = img.currentSrc || img.src;
        full.alt = img.alt;
        dialog.querySelector('#questionImageTitle').textContent = img.alt;
        setZoom(false);
        dialog.showModal();
        viewport.scrollTo(0, 0);
    });
    dialog.querySelector('#questionImageClose').onclick = () => dialog.close();
    zoom.onclick = () => setZoom(zoom.getAttribute('aria-pressed') !== 'true');
    dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('close', function () {
        setZoom(false);
        full.removeAttribute('src');
        if (opener?.isConnected) opener.focus({preventScroll:true});
        opener = null;
    });
});
