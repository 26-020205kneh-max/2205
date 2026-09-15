import os
import random
import time
from datetime import datetime

import streamlit as st
from supabase import create_client, Client
import streamlit.components.v1 as components


# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="🐍 지렁이 게임",
    page_icon="🐍",
    layout="centered",
)


# ============================================================
# Supabase 연결
# ============================================================

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)


try:
    supabase = get_supabase()
    db_available = True
except Exception:
    supabase = None
    db_available = False


# ============================================================
# 랭킹 함수
# ============================================================

def save_score(player_name, score):
    """점수를 Supabase에 저장"""

    if not db_available:
        return False

    try:
        supabase.table("scores").insert({
            "player_name": player_name,
            "score": int(score),
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        return True

    except Exception:
        return False


def get_ranking(limit=10):
    """점수순 랭킹 가져오기"""

    if not db_available:
        return []

    try:
        result = (
            supabase
            .table("scores")
            .select("player_name, score, created_at")
            .order("score", desc=True)
            .limit(limit)
            .execute()
        )

        return result.data or []

    except Exception:
        return []


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .sub-title {
        text-align: center;
        color: #777;
        margin-bottom: 25px;
    }

    .score-box {
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: white;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 15px;
    }

    .score-number {
        font-size: 35px;
        font-weight: 800;
    }

    .ranking-title {
        font-size: 25px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 제목
# ============================================================

st.markdown(
    '<div class="main-title">🐍 지렁이 게임</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">먹이를 먹고 최대한 오래 살아남으세요!</div>',
    unsafe_allow_html=True
)


# ============================================================
# 플레이어 이름
# ============================================================

player_name = st.text_input(
    "플레이어 이름",
    value="플레이어",
    max_chars=20,
)


# ============================================================
# 게임 HTML / JavaScript
# ============================================================

game_html = r"""
<!DOCTYPE html>
<html>
<head>

<meta charset="UTF-8">

<style>

body {
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: Arial, sans-serif;
}

#game-wrapper {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
}

#game {
    background: #111827;
    border: 5px solid #374151;
    border-radius: 15px;
    display: block;
    max-width: 100%;
}

#info {
    width: 100%;
    max-width: 420px;
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
    font-size: 18px;
    font-weight: bold;
}

#message {
    margin-top: 10px;
    text-align: center;
    font-size: 18px;
    color: #ef4444;
    min-height: 25px;
}

button {
    margin-top: 12px;
    padding: 12px 25px;
    border: none;
    border-radius: 10px;
    background: #22c55e;
    color: white;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    background: #16a34a;
}

.controls {
    margin-top: 15px;
    display: grid;
    grid-template-columns: 60px 60px 60px;
    grid-template-rows: 50px 50px;
    gap: 5px;
    justify-content: center;
}

.control-button {
    width: 60px;
    height: 50px;
    padding: 0;
    margin: 0;
    font-size: 25px;
    background: #374151;
}

.control-button:hover {
    background: #4b5563;
}

.empty {
    visibility: hidden;
}

</style>

</head>

<body>

<div id="game-wrapper">

    <canvas id="game" width="400" height="400"></canvas>

    <div id="info">
        <div>점수: <span id="score">0</span></div>
        <div>최고점수: <span id="highscore">0</span></div>
    </div>

    <div id="message">
        방향키를 눌러 게임을 시작하세요!
    </div>

    <button onclick="restartGame()">
        🔄 다시 시작
    </button>

    <div class="controls">

        <button class="control-button empty"></button>

        <button
            class="control-button"
            onclick="changeDirection('up')">
            ⬆️
        </button>

        <button class="control-button empty"></button>

        <button
            class="control-button"
            onclick="changeDirection('left')">
            ⬅️
        </button>

        <button
            class="control-button"
            onclick="changeDirection('down')">
            ⬇️
        </button>

        <button
            class="control-button"
            onclick="changeDirection('right')">
            ➡️
        </button>

    </div>

</div>


<script>

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const gridSize = 20;
const tileCount = canvas.width / gridSize;

let snake;
let food;
let dx;
let dy;
let score;
let gameRunning;
let gameOver;
let gameLoop;

let highscore =
    Number(localStorage.getItem("snakeHighscore")) || 0;

document.getElementById("highscore").textContent = highscore;


// ============================================================
// 게임 초기화
// ============================================================

function initGame() {

    snake = [
        {x: 10, y: 10},
        {x: 9, y: 10},
        {x: 8, y: 10}
    ];

    food = createFood();

    dx = 0;
    dy = 0;

    score = 0;

    gameRunning = false;
    gameOver = false;

    document.getElementById("score").textContent = score;

    document.getElementById("message").textContent =
        "방향키를 눌러 게임을 시작하세요!";

    draw();

}


// ============================================================
// 먹이 생성
// ============================================================

function createFood() {

    let newFood;

    while (true) {

        newFood = {
            x: Math.floor(Math.random() * tileCount),
            y: Math.floor(Math.random() * tileCount)
        };

        let collision = snake &&
            snake.some(part =>
                part.x === newFood.x &&
                part.y === newFood.y
            );

        if (!collision) {
            return newFood;
        }
    }
}


// ============================================================
// 방향 변경
// ============================================================

function changeDirection(direction) {

    if (gameOver) {
        return;
    }

    if (direction === "up" && dy === 0) {
        dx = 0;
        dy = -1;
    }

    if (direction === "down" && dy === 0) {
        dx = 0;
        dy = 1;
    }

    if (direction === "left" && dx === 0) {
        dx = -1;
        dy = 0;
    }

    if (direction === "right" && dx === 0) {
        dx = 1;
        dy = 0;
    }

    if (!gameRunning) {

        gameRunning = true;

        document.getElementById("message").textContent = "";

        gameLoop = setInterval(updateGame, 100);
    }
}


// ============================================================
// 키보드 조작
// ============================================================

document.addEventListener("keydown", function(event) {

    if (
        event.key === "ArrowUp" ||
        event.key === "w" ||
        event.key === "W"
    ) {

        event.preventDefault();
        changeDirection("up");

    }

    else if (
        event.key === "ArrowDown" ||
        event.key === "s" ||
        event.key === "S"
    ) {

        event.preventDefault();
        changeDirection("down");

    }

    else if (
        event.key === "ArrowLeft" ||
        event.key === "a" ||
        event.key === "A"
    ) {

        event.preventDefault();
        changeDirection("left");

    }

    else if (
        event.key === "ArrowRight" ||
        event.key === "d" ||
        event.key === "D"
    ) {

        event.preventDefault();
        changeDirection("right");

    }

});


// ============================================================
// 게임 업데이트
// ============================================================

function updateGame() {

    if (!gameRunning || gameOver) {
        return;
    }

    const head = {
        x: snake[0].x + dx,
        y: snake[0].y + dy
    };


    // 벽 충돌

    if (
        head.x < 0 ||
        head.x >= tileCount ||
        head.y < 0 ||
        head.y >= tileCount
    ) {

        endGame();
        return;
    }


    // 자기 몸 충돌

    for (let i = 0; i < snake.length; i++) {

        if (
            head.x === snake[i].x &&
            head.y === snake[i].y
        ) {

            endGame();
            return;
        }
    }


    snake.unshift(head);


    // 먹이 먹음

    if (
        head.x === food.x &&
        head.y === food.y
    ) {

        score += 10;

        document.getElementById("score").textContent = score;

        if (score > highscore) {

            highscore = score;

            localStorage.setItem(
                "snakeHighscore",
                highscore
            );

            document.getElementById("highscore").textContent =
                highscore;
        }

        food = createFood();

    }

    else {

        snake.pop();

    }


    draw();
}


// ============================================================
// 게임 종료
// ============================================================

function endGame() {

    gameOver = true;
    gameRunning = false;

    clearInterval(gameLoop);

    document.getElementById("message").textContent =
        "💀 게임 오버! 점수: " + score;

    // Streamlit으로 점수 전달
    window.parent.postMessage(
        {
            type: "snake_game_over",
            score: score
        },
        "*"
    );

    draw();
}


// ============================================================
// 다시 시작
// ============================================================

function restartGame() {

    clearInterval(gameLoop);

    initGame();
}


// ============================================================
// 그리기
// ============================================================

function draw() {

    // 배경

    ctx.fillStyle = "#111827";

    ctx.fillRect(
        0,
        0,
        canvas.width,
        canvas.height
    );


    // 격자

    ctx.strokeStyle = "#1f2937";
    ctx.lineWidth = 1;

    for (let x = 0; x < canvas.width; x += gridSize) {

        ctx.beginPath();

        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);

        ctx.stroke();
    }

    for (let y = 0; y < canvas.height; y += gridSize) {

        ctx.beginPath();

        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);

        ctx.stroke();
    }


    // 먹이

    ctx.fillStyle = "#ef4444";

    ctx.beginPath();

    ctx.arc(
        food.x * gridSize + gridSize / 2,
        food.y * gridSize + gridSize / 2,
        gridSize / 2 - 2,
        0,
        Math.PI * 2
    );

    ctx.fill();


    // 지렁이

    snake.forEach(function(part, index) {

        if (index === 0) {
            ctx.fillStyle = "#4ade80";
        }

        else {
            ctx.fillStyle = "#22c55e";
        }

        ctx.fillRect(
            part.x * gridSize + 1,
            part.y * gridSize + 1,
            gridSize - 2,
            gridSize - 2
        );

    });

}


// 시작

initGame();

</script>

</body>
</html>
"""


# ============================================================
# 게임 표시
# ============================================================

components.html(
    game_html,
    height=590,
    scrolling=False,
)


# ============================================================
# 안내
# ============================================================

st.info(
    "💡 PC에서는 방향키 또는 WASD를 사용하세요. "
    "휴대폰에서는 아래 방향 버튼을 사용할 수 있습니다."
)


# ============================================================
# 랭킹
# ============================================================

st.markdown(
    '<div class="ranking-title">🏆 실시간 랭킹 TOP 10</div>',
    unsafe_allow_html=True
)


if not db_available:

    st.warning(
        "현재 랭킹 데이터베이스가 연결되지 않았습니다. "
        "Supabase 설정을 완료하면 온라인 랭킹이 활성화됩니다."
    )

else:

    ranking = get_ranking(10)

    if ranking:

        for index, player in enumerate(ranking):

            rank = index + 1

            if rank == 1:
                medal = "🥇"
            elif rank == 2:
                medal = "🥈"
            elif rank == 3:
                medal = "🥉"
            else:
                medal = f"{rank}위"

            name = player.get("player_name", "익명")
            score_value = player.get("score", 0)

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    padding:12px;
                    margin:5px 0;
                    background:#f3f4f6;
                    border-radius:10px;
                ">
                    <div style="font-weight:bold;">
                        {medal} {name}
                    </div>

                    <div style="
                        font-weight:bold;
                        color:#16a34a;
                    ">
                        {score_value}점
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.write("아직 등록된 점수가 없습니다.")


# ============================================================
# 새로고침 버튼
# ============================================================

if st.button("🔄 랭킹 새로고침"):

    st.rerun()


# ============================================================
# 데이터베이스 안내
# ============================================================

with st.expander("ℹ️ 개발자 설정 안내"):

    st.write(
        """
        이 게임은 다음 구조로 동작합니다.

        1. 사용자가 게임을 플레이합니다.
        2. 게임이 끝나면 점수가 생성됩니다.
        3. 점수를 데이터베이스에 저장합니다.
        4. 모든 사용자가 같은 랭킹을 확인할 수 있습니다.

        GitHub에는 Supabase 비밀번호를 절대로 직접 작성하지 마세요.
        Streamlit의 Secrets 기능을 사용하는 것을 권장합니다.
        """
    )
