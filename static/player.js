const qs = new URLSearchParams(window.location.search);
const token = qs.get('token');

const meEl = document.getElementById('me');
const statusEl = document.getElementById('myStatus');
const boardAEl = document.getElementById('boardA');
const boardBEl = document.getElementById('boardB');
const turnAEl = document.getElementById('turnA');
const turnBEl = document.getElementById('turnB');
const res1El = document.getElementById('res1');
const res2El = document.getElementById('res2');
const res3El = document.getElementById('res3');
const res4El = document.getElementById('res4');
const dropATopEl = document.getElementById('dropA-top');
const dropABottomEl = document.getElementById('dropA-bottom');
const dropBTopEl = document.getElementById('dropB-top');
const dropBBottomEl = document.getElementById('dropB-bottom');

let lastState = null;
let selected = null; // { board: "A"|"B", coord: "e2" }
let dropSelected = null; // "P"|"N"|"B"|"R"|"Q"

const PLAYER_META = {
  '1': { board: 'A', color: 'WHITE', top: false },
  '4': { board: 'A', color: 'BLACK', top: true },
  '2': { board: 'B', color: 'WHITE', top: true },
  '3': { board: 'B', color: 'BLACK', top: false },
};

// Добавьте ПРЯМО ПОСЛЕ строки "const pieceSymbols = { ... }"
// (примерно после строки 25 в вашем коде)

function showGameOverModal(gameOver, isWinner) {
  const modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:10000;';
  
  const color = isWinner ? '#4ade80' : '#ef4444';
  const title = isWinner ? '🎉 ПОБЕДА!' : '❌ ПОРАЖЕНИЕ';
  
  modal.innerHTML = `
    <div style="background:white;padding:20px;border-radius:10px;max-width:400px;text-align:center;border:3px solid ${color}">
      <h2 style="color:${color}; margin: 0 0 15px 0;">${title}</h2>
      <p style="color:#333; margin: 0 0 15px 0; font-size: 16px;">${gameOver.reason || 'Игра завершена'}</p>
      <div style="background:#f5f5f5;padding:10px;border-radius:5px;margin:15px 0;color:#333;font-size:14px;">
        Победители: Игроки ${gameOver.team?.join(' и ')}
      </div>
      <button onclick="this.closest('div[style]').parentElement.remove()" style="background:${color};color:white;border:none;padding:10px 30px;border-radius:5px;cursor:pointer;font-size:16px;">
        OK
      </button>
    </div>
  `;
  
  document.body.appendChild(modal);

}
function pieceImgSrc(sym) {
  if (!sym || sym === '.') return null;
  const isWhite = sym === sym.toUpperCase();
  const letter = sym.toUpperCase(); // K,Q,R,B,N,P
  const prefix = isWhite ? 'w' : 'b';
  return `/chess_figures/${prefix}${letter}.png`;
}

function colorName(c) {
  return c === 'WHITE' ? 'белые' : 'чёрные';
}

function coordFromRC(row, col) {
  // row 0..7 соответствует рангу 8..1
  const file = String.fromCharCode('a'.charCodeAt(0) + col);
  const rank = (8 - row).toString();
  return file + rank;
}

function isMyBoard(boardName) {
  return lastState?.me?.board === boardName;
}

function isMyTurnOn(boardName) {
  if (!lastState) return false;
  const b = lastState.boards?.[boardName];
  return b?.currentPlayer === lastState.me?.color;
}

function isMyPiece(sym) {
  if (!sym || sym === '.') return false;
  const meColor = lastState?.me?.color;
  if (meColor === 'WHITE') return sym === sym.toUpperCase();
  if (meColor === 'BLACK') return sym === sym.toLowerCase();
  return false;
}

function squareClass(row, col) {
  const light = (row + col) % 2 === 0;
  return light ? 'sq light' : 'sq dark';
}

function getTeammatePlayerId(playerId) {
  // Определяем ID сокомандника
  const partnerMap = { '1': '3', '3': '1', '2': '4', '4': '2' };
  return partnerMap[String(playerId)];
}

function shouldRotateBoard(boardName, playerId) {
  if (!playerId) return false;
  const pid = String(playerId);

  // Явные правила поворота по комнате игрока
  const rotateRules = {
    '1': ['B'],
    '2': ['A'],
    '3': ['B'],
    '4': ['A'],
  };

  const forced = rotateRules[pid];
  if (forced) {
    return forced.includes(boardName);
  }

  // Запасная логика по старому правилу top
  const meta = PLAYER_META[pid];
  if (!meta) return false;

  if (meta.board === boardName) {
    return meta.top;
  }

  const teammateId = getTeammatePlayerId(pid);
  const teammateMeta = PLAYER_META[teammateId];
  if (teammateMeta && teammateMeta.board === boardName) {
    return teammateMeta.top;
  }

  return false;
}

function viewToModel(boardName, viewRow, viewCol) {
  // Поворачиваем доску если нужно, чтобы стартовая позиция была снизу
  const playerId = lastState?.me?.playerId;
  const shouldRotate = shouldRotateBoard(boardName, playerId);
  
  if (shouldRotate) {
    return { row: 7 - viewRow, col: 7 - viewCol };
  }
  return { row: viewRow, col: viewCol };
}

function renderBoard(boardName, mountEl) {
  const grid = lastState?.boards?.[boardName]?.grid;
  if (!grid) return;

  mountEl.innerHTML = '';
  const interactive = isMyBoard(boardName);
  mountEl.classList.toggle('boardDisabled', !interactive);
  
  const boardState = lastState?.boards?.[boardName];
  const inCheck = boardState?.inCheck || false;
  const kingInCheck = boardState?.kingInCheck || null;

  for (let viewRow = 0; viewRow < 8; viewRow++) {
    for (let viewCol = 0; viewCol < 8; viewCol++) {
      const model = viewToModel(boardName, viewRow, viewCol);
      const sym = grid[model.row][model.col];
      const coord = coordFromRC(model.row, model.col);

      const d = document.createElement('div');
      d.className = squareClass(viewRow, viewCol);
      d.dataset.board = boardName;
      d.dataset.coord = coord;

      if (selected && selected.board === boardName && selected.coord === coord) {
        d.classList.add('selected');
      }
      
      // Подсветка короля при шахе
      if (inCheck && kingInCheck && coord === kingInCheck) {
        d.classList.add('inCheck');
      }

      const piece = document.createElement('div');
      piece.className = 'piece';
      const src = pieceImgSrc(sym);
      if (src) {
        const img = document.createElement('img');
        img.className = 'pieceImg';
        img.alt = sym;
        img.src = src;
        piece.appendChild(img);
      } else {
        // оставим пусто
        piece.textContent = '';
      }

      d.appendChild(piece);

      if (interactive) {
        d.addEventListener('click', () => onSquareClick(boardName, coord, sym));
      }

      mountEl.appendChild(d);
    }
  }
}

async function onSquareClick(boardName, coord, sym) {
  if (!isMyBoard(boardName)) return;
  if (!isMyTurnOn(boardName)) {
    statusEl.textContent = 'Сейчас не ваш ход.';
    return;
  }

  // DROP режим: выбрали фигуру из резерва → клик по клетке
  if (dropSelected) {
    if (sym && sym !== '.') {
      statusEl.textContent = 'Нельзя поставить фигуру: клетка занята.';
      return;
    }
    const piece = dropSelected;
    statusEl.textContent = `Дроп: ${piece} на ${coord}...`;
    try {
      const resp = await fetch('/api/drop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, piece, square: coord }),
      });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data?.error || 'Ошибка дропа');
    // Обновление состояния придет через WebSocket, но обновим локально для быстрого отклика
    lastState = data;
    dropSelected = null;
    selected = null;
    statusEl.textContent = `OK: дроп ${piece} на ${coord}`;
    render();
    } catch (e) {
      statusEl.textContent = 'Ошибка: ' + (e?.message || e);
      render();
    }
    return;
  }

  // первый клик — выбрать свою фигуру
  if (!selected) {
    if (!isMyPiece(sym)) {
      statusEl.textContent = 'Выберите свою фигуру.';
      return;
    }
    selected = { board: boardName, coord };
    statusEl.textContent = `Выбрано: ${coord}. Теперь кликните клетку назначения.`;
    render();
    return;
  }

  // второй клик — попытаться сделать ход
  const from = selected.coord;
  const to = coord;
  selected = null;
  render();

  statusEl.textContent = `Ход: ${from} → ${to}...`;
  try {
    let resp = await fetch('/api/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, from, to }),
    });
    let data = await resp.json();

    // Превращение пешки: сервер вернул список фигур для выбора
    if (resp.status === 409 && data?.error === 'promotion_required') {
      const promotion = data?.promotion;
      const options = promotion?.options || [];
      if (!options.length) throw new Error('Нет доступных фигур для превращения');
      
      const pieceSymbols = {
        'R': '♜',  // черная ладья
        'N': '♞',  // черный конь  
        'B': '♝',  // черный слон
        'Q': '♛',  // черный ферзь
        'K': '♚'   // черный король
      };
      // Простое окно выбора (минимально, без верстки модалки)
        const listText = options
        .map((o, i) => `${i + 1}) ${pieceSymbols[o.piece] || o.piece} ${o.square}`)
        .join('\n');

      const choice = window.prompt(
        `Пешка достигла последней горизонтали.\nВыберите фигуру игрока ${promotion.victimPlayerId} (кроме ♚ и ♟):\n\n${listText}\n\nВведите номер:`
      );

      const idx = Number(choice) - 1;
      if (!Number.isFinite(idx) || idx < 0 || idx >= options.length) {
        throw new Error('Превращение отменено/неверный выбор');
      }

      const picked = options[idx];
      // Повторяем ход, но уже с выбранной фигурой
      resp = await fetch('/api/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          from,
          to,
          victimPlayerId: promotion.victimPlayerId,
          victimSquare: picked.square,
        }),
      });
      data = await resp.json();
    }

    if (!resp.ok) throw new Error(data?.detail || data?.error || 'Ошибка хода');
    // Обновление состояния придет через WebSocket, но обновим локально для быстрого отклика
    lastState = data;
    statusEl.textContent = `OK: ${from} → ${to}`;
    render();
  } catch (e) {
    statusEl.textContent = 'Ошибка: ' + (e?.message || e);
  }
}

function renderReserves() {
  if (!lastState) return;
  const r = lastState?.reserves || {};
  const myPlayerId = String(lastState.me.playerId);
  const teammateId = getTeammatePlayerId(myPlayerId);
  
  // Определяем метаданные для текущего игрока и сокомандника
  const myMeta = PLAYER_META[myPlayerId];
  const teammateMeta = PLAYER_META[teammateId];
  
  // Показываем запасы текущего игрока и его сокомандника
  // Первый блок - текущий игрок
  if (res1El && res1El.closest('.resBox')) {
    const box1 = res1El.closest('.resBox');
    const key1 = box1.querySelector('.resKey');
    if (key1) {
      key1.textContent = `Игрок ${myPlayerId} (доска ${myMeta.board})`;
      res1El.textContent = r[myPlayerId] ?? '';
      box1.style.display = '';
    }
  }
  
  // Второй блок - сокомандник
  if (res3El && res3El.closest('.resBox')) {
    const box3 = res3El.closest('.resBox');
    const key3 = box3.querySelector('.resKey');
    if (key3) {
      key3.textContent = `Игрок ${teammateId} (доска ${teammateMeta.board})`;
      res3El.textContent = r[teammateId] ?? '';
      box3.style.display = '';
    }
  }
}

function isTopSeat(playerId) {
  return playerId === 2 || playerId === 4;
}

function clearDropBars() {
  for (const el of [dropATopEl, dropABottomEl, dropBTopEl, dropBBottomEl]) {
    if (!el) continue;
    el.innerHTML = '';
    el.hidden = false; // должны быть видны всем
  }
}

function renderDropBarFor(el, playerId) {
  if (!el) return;
  const meta = PLAYER_META[String(playerId)];
  if (!meta) return;

  const reserveCountsAll = lastState?.reserveCounts || {};
  const counts = reserveCountsAll[String(playerId)] || {};
  const pieces = ['P', 'Q', 'N', 'B', 'R']; // без короля

  const isOwner = Number(playerId) === Number(lastState?.me?.playerId);
  const ownerTurn = isOwner && isMyTurnOn(meta.board);

  for (const p of pieces) {
    const count = Number(counts[p] ?? 0);

    const item = document.createElement('div');
    item.className = 'dropPiece';
    if (count <= 0) item.classList.add('disabled');
    if (isOwner && dropSelected === p) item.classList.add('selected');
    if (!isOwner) item.classList.add('readonly');
    item.title = `Player ${playerId} drop ${p} (${count})`;

    const img = document.createElement('img');
    img.className = 'pieceImg';
    img.alt = p;
    img.src = `/chess_figures/${meta.color === 'WHITE' ? 'w' : 'b'}${p}.png`;
    item.appendChild(img);

    if (count > 0) {
      const badge = document.createElement('div');
      badge.className = 'dropBadge';
      badge.textContent = String(count);
      item.appendChild(badge);
    }

    // Кликать можно только в своей полоске
    if (isOwner) {
      item.addEventListener('click', () => {
        if (!ownerTurn) {
          statusEl.textContent = 'Сейчас не ваш ход.';
          return;
        }
        if (count <= 0) return;

        // переключение выбора
        selected = null; // сбрасываем режим хода
        dropSelected = (dropSelected === p) ? null : p;
        statusEl.textContent = dropSelected
          ? `Выбран дроп ${dropSelected}. Кликните клетку на вашей доске.`
          : 'Отмена дропа.';
        render();
      });
    }

    el.appendChild(item);
  }
}

function renderDropBars() {
  clearDropBars();
  if (!lastState) return;

  const myPlayerId = String(lastState.me.playerId);

  // "Нормальный" порядок панелей (как на доске без поворота):
  // - Доска A: сверху черные (4), снизу белые (1)
  // - Доска B: сверху черные (3), снизу белые (2)
  const normal = {
    A: { top: 4, bottom: 1 },
    B: { top: 3, bottom: 2 },
  };

  // Панели должны соответствовать ориентации конкретной доски в UI:
  // если доска перевёрнута (shouldRotateBoard == true) — меняем top/bottom местами.
  const aRotated = shouldRotateBoard('A', myPlayerId);
  const bRotated = shouldRotateBoard('B', myPlayerId);

  const boardAOrder = aRotated
    ? { top: normal.A.bottom, bottom: normal.A.top }
    : normal.A;

  const boardBOrder = bRotated
    ? { top: normal.B.bottom, bottom: normal.B.top }
    : normal.B;

  renderDropBarFor(dropATopEl, boardAOrder.top);
  renderDropBarFor(dropABottomEl, boardAOrder.bottom);
  renderDropBarFor(dropBTopEl, boardBOrder.top);
  renderDropBarFor(dropBBottomEl, boardBOrder.bottom);
}

function render() {
  if (!lastState) return;
  meEl.textContent = `Вы: игрок ${lastState.me.playerId} · доска ${lastState.me.board} · ${colorName(lastState.me.color)}`;
  
  const myBoard = lastState.me.board;
  const myPlayerId = String(lastState.me.playerId);
  const teammateId = getTeammatePlayerId(myPlayerId);
  const teammateMeta = PLAYER_META[teammateId];
  const teammateBoard = teammateMeta ? teammateMeta.board : (myBoard === 'A' ? 'B' : 'A');
  
  // Всегда рендерим доски в их исходные контейнеры
  renderBoard('A', boardAEl);
  renderBoard('B', boardBEl);
  
  // Обновляем заголовки
  const boardAWrap = boardAEl.closest('.boardWrap');
  const boardBWrap = boardBEl.closest('.boardWrap');
  const titleA = boardAWrap.querySelector('.boardTitle');
  const titleB = boardBWrap.querySelector('.boardTitle');
  const turnA = boardAWrap.querySelector('.boardTurn');
  const turnB = boardBWrap.querySelector('.boardTurn');
  
  turnA.textContent = `Ход: ${colorName(lastState.boards.A.currentPlayer)}`;
  turnB.textContent = `Ход: ${colorName(lastState.boards.B.currentPlayer)}`;
  
  // Устанавливаем размеры и порядок
  const boardsContainer = document.querySelector('.boards');
  
  if (myBoard === 'A') {
    // Игрок на доске A: доска A слева (полная), доска B справа (маленькая)
    titleA.textContent = 'Доска A';
    titleB.textContent = 'Доска B';
    boardAWrap.classList.remove('boardSmall');
    boardBWrap.classList.add('boardSmall');
    boardAWrap.classList.add('boardMy');
    boardBWrap.classList.remove('boardMy');
    // Порядок: A, затем B
    if (boardsContainer.firstChild !== boardAWrap) {
      boardsContainer.insertBefore(boardAWrap, boardBWrap);
    }
  } else {
    // Игрок на доске B: доска B слева (полная), доска A справа (маленькая)
    titleA.textContent = 'Доска A';
    titleB.textContent = 'Доска B';
    boardAWrap.classList.add('boardSmall');
    boardBWrap.classList.remove('boardSmall');
    boardAWrap.classList.remove('boardMy');
    boardBWrap.classList.add('boardMy');
    // Порядок: B, затем A
    if (boardsContainer.firstChild !== boardBWrap) {
      boardsContainer.insertBefore(boardBWrap, boardAWrap);
    }
  }
  
  renderReserves();
  renderDropBars();

  // если выбран дроп, но фигур больше нет — сбросим
  if (dropSelected) {
    const c = Number(lastState.myReserve?.[dropSelected] ?? 0);
    if (c <= 0) dropSelected = null;
  }

  const myTurn = isMyTurnOn(myBoard);
  if (myTurn) {
    statusEl.textContent ||= 'Ваш ход. Можно сделать ход или выбрать дроп.';
  }
}

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let isConnecting = false;

function connectWebSocket() {
  if (!token) {
    statusEl.textContent = 'Нет token в ссылке. Вернитесь на главную и создайте игру.';
    return;
  }

  // Предотвращаем множественные попытки подключения
  if (isConnecting || (ws && ws.readyState === WebSocket.CONNECTING)) {
    return;
  }
  
  // Закрываем старое соединение если оно есть
  if (ws && ws.readyState !== WebSocket.CLOSED) {
    ws.close();
  }

  isConnecting = true;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/${token}`;
  
  console.log('Подключение к WebSocket:', wsUrl);
  ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    isConnecting = false;
    reconnectAttempts = 0;
    console.log('WebSocket подключен');
    statusEl.textContent = 'Подключено к серверу';
  };
  
  ws.onmessage = (event) => {
    try {
      // Проверяем, является ли сообщение JSON или простым текстом (pong)
      if (typeof event.data === 'string' && event.data === 'pong') {
        // Это ответ на ping, просто игнорируем
        return;
      }
      
      const message = JSON.parse(event.data);
      console.log('WebSocket сообщение:', message.type);
      if (message.type === 'state_update') {
        // Получаем состояние для текущего игрока
        const myPlayerId = String(lastState?.me?.playerId || '1');
        const myState = message.states[myPlayerId];
        if (myState) {
          lastState = myState;
          render();
          

          // Проверяем, завершена ли игра
          if (message.gameOver) {
            const gameOver = message.gameOver;
            const myPlayerIdNum = parseInt(myPlayerId);
            const isWinner = gameOver.team && gameOver.team.includes(myPlayerIdNum);
            
            // Показываем всплывающее окно
            showGameOverModal(gameOver, isWinner);
            
            // Обновляем статус бар
            if (isWinner) {
              statusEl.textContent = `🎉 ПОБЕДА! ${gameOver.reason || 'Игра завершена'}`;
              statusEl.style.color = '#4ade80';
            } else if (gameOver.winner === 'draw') {
              statusEl.textContent = `🤝 НИЧЬЯ: ${gameOver.reason || 'Игра завершена'}`;
              statusEl.style.color = '#f59e0b';
            } else {
              statusEl.textContent = `❌ ПОРАЖЕНИЕ: ${gameOver.reason || 'Игра завершена'}`;
              statusEl.style.color = '#ef4444';
            }
            statusEl.style.fontWeight = 'bold';
          }




        }
      }
    } catch (e) {
      // Игнорируем ошибки парсинга для не-JSON сообщений (например, "pong")
      if (event.data !== 'pong') {
        console.error('Ошибка обработки сообщения:', e, 'Data:', event.data);
      }
    }
  };
  
  ws.onerror = (error) => {
    isConnecting = false;
    console.error('WebSocket ошибка:', error);
  };
  
  ws.onclose = (event) => {
    isConnecting = false;
    console.log('WebSocket закрыт:', event.code, event.reason);
    // Пытаемся переподключиться только если это не было нормальное закрытие
    if (event.code !== 1000 && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      reconnectAttempts++;
      statusEl.textContent = `Переподключение... (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`;
      setTimeout(connectWebSocket, 2000 * reconnectAttempts);
    } else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      statusEl.textContent = 'Соединение потеряно. Обновите страницу.';
    }
  };
}

// Начальная загрузка состояния (на случай если WebSocket не подключится сразу)
async function initialFetch() {
  if (!token) {
    statusEl.textContent = 'Нет token в ссылке. Вернитесь на главную и создайте игру.';
    return;
  }
  try {
    const resp = await fetch('/api/state?token=' + encodeURIComponent(token));
    const data = await resp.json();
    if (!resp.ok) throw new Error(data?.error || 'Не удалось получить состояние');
    lastState = data;
    render();
  } catch (e) {
    statusEl.textContent = 'Ошибка: ' + (e?.message || e);
  }
}

// Начальное подключение
initialFetch();
connectWebSocket();

// Heartbeat для поддержания соединения
setInterval(() => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000); // каждые 30 секунд

// Закрываем соединение при закрытии страницы
window.addEventListener('beforeunload', () => {
  if (ws) {
    ws.close();
  }
});

