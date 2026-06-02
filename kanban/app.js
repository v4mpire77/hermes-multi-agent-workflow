// kanban/app.js — pure-JS, no dependencies. Loads board.json, renders cards,
// supports drag/drop (mouse + keyboard), edit dialog, and "Propose change" export.

(() => {
  'use strict';

  const COLUMNS = [
    { id: 'todo', title: 'To Do', el: null, list: null },
    { id: 'in_progress', title: 'In Progress', el: null, list: null },
    { id: 'done', title: 'Done', el: null, list: null },
  ];

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const state = { board: null };

  function setStatus(msg, kind = 'info') {
    const el = $('#status');
    el.textContent = msg;
    el.dataset.kind = kind;
  }

  function escapeHTML(s) {
    return String(s ?? '').replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    })[c]);
  }

  function fmtDate(iso) {
    if (!iso) return null;
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return null;
    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  }

  function dueClass(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '';
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const diff = Math.floor((d - today) / 86400000);
    if (diff < 0) return 'overdue';
    if (diff <= 2) return 'urgent';
    return '';
  }

  function renderCard(card) {
    const li = document.createElement('li');
    li.className = 'card';
    li.draggable = true;
    li.dataset.id = card.id;
    li.dataset.column = card.column;
    li.setAttribute('aria-label', `Card: ${card.title}. Column: ${COLUMNS.find(c=>c.id===card.column)?.title || card.column}.`);

    const dueCls = dueClass(card.due_date);
    const meta = [];
    if (card.assignee) meta.push(`<span class="pill assignee">@${escapeHTML(card.assignee)}</span>`);
    if (card.due_date) meta.push(`<span class="pill due ${dueCls}">Due ${escapeHTML(fmtDate(card.due_date))}</span>`);

    const subs = Array.isArray(card.subtasks) ? card.subtasks : [];
    const subHTML = subs.length
      ? `<ul class="subtasks">${subs.map(s => `<li class="${s.done ? 'done' : ''}">${s.done ? '☑' : '☐'} ${escapeHTML(s.text)}</li>`).join('')}</ul>`
      : '';

    li.innerHTML = `
      <h3 class="card-title">${escapeHTML(card.title)}</h3>
      ${card.description ? `<p class="card-desc">${escapeHTML(card.description)}</p>` : ''}
      <div class="card-meta">${meta.join('')}</div>
      ${subHTML}
    `;

    li.addEventListener('dblclick', () => openDialog(card));
    li.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); openDialog(card); }
    });
    li.tabIndex = 0;

    // Drag
    li.addEventListener('dragstart', (e) => {
      li.classList.add('dragging');
      e.dataTransfer.setData('text/plain', card.id);
      e.dataTransfer.effectAllowed = 'move';
    });
    li.addEventListener('dragend', () => li.classList.remove('dragging'));

    return li;
  }

  function renderBoard() {
    for (const c of COLUMNS) {
      c.list = document.getElementById(`list-${c.id}`);
      c.list.innerHTML = '';
    }
    const cards = (state.board?.cards || []).slice();
    cards.sort((a, b) => (a.order || 0) - (b.order || 0));
    for (const card of cards) {
      const col = COLUMNS.find(c => c.id === card.column);
      if (col?.list) col.list.appendChild(renderCard(card));
    }
    setStatus(`${cards.length} cards loaded from board.json`, 'ok');
  }

  function attachDropTargets() {
    for (const c of COLUMNS) {
      const target = c.list;
      target.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        target.classList.add('drop-target');
      });
      target.addEventListener('dragleave', () => target.classList.remove('drop-target'));
      target.addEventListener('drop', (e) => {
        e.preventDefault();
        target.classList.remove('drop-target');
        const id = e.dataTransfer.getData('text/plain');
        if (!id) return;
        const card = (state.board.cards || []).find(x => x.id === id);
        if (!card || card.column === c.id) return;
        card.column = c.id;
        card.updated_at = new Date().toISOString();
        renderBoard();
        setStatus(`Moved "${card.title}" to ${c.title}. Export board.json to commit.`, 'info');
      });
    }
  }

  // ------- Dialog (add/edit) -------
  const dialog = $('#card-dialog');
  const form = $('#card-form');

  function openDialog(card) {
    $('#dialog-title').textContent = card ? 'Edit card' : 'Add card';
    $('#f-id').value = card?.id || '';
    $('#f-title').value = card?.title || '';
    $('#f-description').value = card?.description || '';
    $('#f-assignee').value = card?.assignee || '';
    $('#f-due').value = card?.due_date || '';
    $('#f-column').value = card?.column || 'todo';
    $('#f-subtasks').value = (card?.subtasks || []).map(s => `${s.done ? '[x]' : '[ ]'} ${s.text}`).join('\n');
    $('#delete-btn').hidden = !card;
    dialog.showModal();
    setTimeout(() => $('#f-title').focus(), 50);
  }

  function parseSubtasks(text) {
    return text.split('\n').map(l => l.trim()).filter(Boolean).map(l => {
      const m = l.match(/^\[(x| )\]\s*(.*)$/i);
      if (m) return { done: m[1].toLowerCase() === 'x', text: m[2] };
      return { done: false, text: l };
    });
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const id = $('#f-id').value || `c_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
    const card = {
      id,
      title: $('#f-title').value.trim(),
      description: $('#f-description').value.trim(),
      assignee: $('#f-assignee').value.trim().replace(/^@/, ''),
      due_date: $('#f-due').value || null,
      column: $('#f-column').value,
      subtasks: parseSubtasks($('#f-subtasks').value),
      order: 0,
      updated_at: new Date().toISOString(),
    };
    const existing = (state.board.cards || []).findIndex(c => c.id === id);
    if (existing >= 0) state.board.cards[existing] = { ...state.board.cards[existing], ...card };
    else state.board.cards = [...(state.board.cards || []), card];
    renumberOrder();
    renderBoard();
    dialog.close();
    setStatus('Card updated locally. Export board.json to commit.', 'info');
  });

  $('#delete-btn').addEventListener('click', () => {
    const id = $('#f-id').value;
    if (!id) return;
    state.board.cards = (state.board.cards || []).filter(c => c.id !== id);
    renderBoard();
    dialog.close();
    setStatus('Card deleted locally. Export board.json to commit.', 'info');
  });

  $('#cancel-btn').addEventListener('click', () => dialog.close());
  $('#add-card-btn').addEventListener('click', () => openDialog(null));

  function renumberOrder() {
    state.board.cards.forEach((c, i) => { c.order = i + 1; });
  }

  // ------- Commit proposal export -------
  const commitDialog = $('#commit-dialog');
  $('#commit-btn').addEventListener('click', () => {
    $('#snippet').value = JSON.stringify(state.board, null, 2);
    commitDialog.showModal();
  });
  $('#close-commit-btn').addEventListener('click', () => commitDialog.close());
  $('#copy-btn').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText($('#snippet').value);
      setStatus('Copied board.json to clipboard.', 'ok');
    } catch {
      $('#snippet').select();
      document.execCommand('copy');
      setStatus('Copied (fallback).', 'ok');
    }
  });
  $('#download-btn').addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(state.board, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'board.json'; a.click();
    URL.revokeObjectURL(url);
  });

  // ------- Boot -------
  async function loadBoard() {
    try {
      const res = await fetch('board.json', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      state.board = await res.json();
      $('#board-subtitle').textContent = state.board.description || 'No description set.';
      $('#commit-btn').hidden = false;
      renderBoard();
    } catch (err) {
      $('#board-subtitle').textContent = `Failed to load board.json: ${err.message}. Open from the repo or serve via a static server.`;
      setStatus('Failed to load board.json', 'err');
    }
  }

  function boot() {
    for (const c of COLUMNS) { c.el = document.querySelector(`[data-column="${c.id}"]`); }
    attachDropTargets();
    loadBoard();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    // DOM already ready (defer missed DOMContentLoaded) — boot now.
    boot();
  }
})();
