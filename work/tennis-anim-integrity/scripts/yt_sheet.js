// Chat 4 reference helper for the Browser pane (paste into javascript_tool on a youtube.com watch page).
// Nothing is downloaded: frames are drawn onto an on-page canvas, id-stamped, and read with a screenshot.
// Sidebar / end screen hidden (no non-tennis recommendations on screen), video muted, autoplay off, pause on end.
window.__tai = {
  info() { const r = window.ytInitialPlayerResponse; const v = document.querySelector('video'); return { id: r?.videoDetails?.videoId, title: r?.videoDetails?.title, len: r?.videoDetails?.lengthSeconds, author: r?.videoDetails?.author, vw: v?.videoWidth, vh: v?.videoHeight, rs: v?.readyState, ad: !!document.querySelector('.ad-showing'), url: location.href }; },
  hideRecs() { for (const s of ['#secondary', '#related', 'ytd-watch-next-secondary-results-renderer', '#comments', '.ytp-endscreen-content', '.ytp-ce-element']) document.querySelectorAll(s).forEach(e => e.style.display = 'none'); },
  prep() {
    Object.defineProperty(document, 'visibilityState', { get: () => 'visible', configurable: true }); Object.defineProperty(document, 'hidden', { get: () => false, configurable: true }); document.hasFocus = () => true; document.dispatchEvent(new Event('visibilitychange'));
    const v = document.querySelector('video'); if (v) { v.muted = true; v.addEventListener('ended', () => v.pause()); v.loop = false; }
    const t = document.querySelector('.ytp-autonav-toggle-button'); if (t && t.getAttribute('aria-checked') === 'true') t.click();
    try { document.querySelector('#movie_player').setPlaybackQualityRange('hd1080', 'hd1080'); } catch (e) { } this.hideRecs();
  },
  async grab(v, t) { v.playbackRate = 0.1; v.currentTime = t; await new Promise(r => { const f = () => { v.removeEventListener('seeked', f); r(); }; v.addEventListener('seeked', f); setTimeout(r, 3000); }); try { await v.play(); } catch (e) { } await new Promise(r => setTimeout(r, 180)); v.pause(); return v.currentTime; },
  async sheet(times, cols, label, crop) {
    const v = document.querySelector('video'); const id = window.ytInitialPlayerResponse?.videoDetails?.videoId;
    if (!location.href.includes(id)) return 'ID MISMATCH';
    if (document.querySelector('.ad-showing')) return 'AD SHOWING';
    let c = document.getElementById('__taiCanvas'); if (!c) { c = document.createElement('canvas'); c.id = '__taiCanvas'; c.style.cssText = 'position:fixed;left:0;top:0;z-index:2147483647;background:#000'; document.documentElement.appendChild(c); }
    const W = innerWidth || 1024, H = innerHeight || 768; c.width = W * 2; c.height = H * 2; c.style.width = W + 'px'; c.style.height = H + 'px'; const g = c.getContext('2d'); g.fillStyle = '#000'; g.fillRect(0, 0, c.width, c.height);
    const rows = Math.ceil(times.length / cols); const cw = c.width / cols, ch = (c.height - 40) / rows;
    g.fillStyle = '#ff0'; g.font = '28px Arial'; g.fillText(id + '  ' + (label || ''), 8, 30);
    const out = [];
    for (let k = 0; k < times.length; k++) {
      const t = await this.grab(v, times[k]); out.push(t.toFixed(2));
      const vw = v.videoWidth, vh = v.videoHeight; let sx = 0, sy = 0, sw = vw, sh = vh; if (crop) { sx = crop[0] * vw; sy = crop[1] * vh; sw = crop[2] * vw; sh = crop[3] * vh; }
      const s = Math.min(cw / sw, ch / sh); const dw = sw * s, dh = sh * s; const x = (k % cols) * cw + (cw - dw) / 2, y = 40 + Math.floor(k / cols) * ch + (ch - dh) / 2;
      g.drawImage(v, sx, sy, sw, sh, x, y, dw, dh); g.fillStyle = '#ff0'; g.font = '26px Arial'; g.fillText(t.toFixed(2) + 's', x + 6, y + 28);
    }
    return out.join(' ');
  },
  async survey(n, cols) { this.prep(); await new Promise(r => setTimeout(r, 2500)); this.hideRecs(); const i = this.info(); const L = +i.len; const ts = []; for (let k = 0; k < n; k++) ts.push(+(0.3 + k * (L - 0.8) / (n - 1)).toFixed(2)); const r = await this.sheet(ts, cols, (i.title || '').slice(0, 60) + ' len ' + L + ' by ' + i.author); await new Promise(r => setTimeout(r, 900)); return [i.id, i.len, i.vw, i.vh, i.author, r]; },
  hide() { const c = document.getElementById('__taiCanvas'); if (c) c.remove(); }
};
