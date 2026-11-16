GAME_HOOK = r'''(function () {
  window.__board = null;

  function grab(s) {
    if (typeof s !== 'string' || s.length < 100) return;
    try {
      const p = JSON.parse(s);
      const state = Array.isArray(p) ? p[0] : p;
      if (state && Array.isArray(state.board)) {
        window.__board = state.board.map(r => r.map(c => c ? c.value : 0));
      }
    } catch {}
  }

  const _btoa = window.btoa;
  window.btoa = function (s) { grab(s); return _btoa.apply(this, arguments); };

  if (window.TextEncoder) {
    const _enc = TextEncoder.prototype.encode;
    TextEncoder.prototype.encode = function (s) {
      if (typeof s === 'string') grab(s);
      return _enc.apply(this, arguments);
    };
  }
})();
'''