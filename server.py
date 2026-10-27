"""
FastAPI Server for Texas Hold'em Poker Web Game.
Supports both WebSocket real-time game loop and REST API fallback.
"""
import asyncio
import os
from typing import List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from engine.game import TexasHoldemGame, GamePhase

app = FastAPI(title="Royal Felt - Texas Hold'em Poker")

# Global Game Instance
game = TexasHoldemGame(small_blind=10, big_blind=20, starting_chips=1000)

# Active WebSocket Connections
connected_clients: Set[WebSocket] = set()
ai_task_running = False


async def broadcast_state():
    """Broadcasts current game state to all connected WebSocket clients."""
    if not connected_clients:
        return
    state = game.to_dict()
    payload = {"type": "state", "data": state}
    disconnected = set()
    for ws in connected_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        connected_clients.discard(ws)


async def run_ai_turns_loop():
    """
    Background loop that paces AI turns with natural delays (800ms - 1200ms)
    until it is the human player's turn or the hand concludes.
    """
    global ai_task_running
    if ai_task_running:
        return
    ai_task_running = True

    try:
        while True:
            # Check if hand is active
            if game.phase in (GamePhase.IDLE, GamePhase.SHOWDOWN, GamePhase.HAND_OVER):
                break

            cur_idx = game.current_player_idx
            if cur_idx < 0 or cur_idx >= len(game.players):
                break

            cur_p = game.players[cur_idx]
            # Stop if human player's turn or player can't act
            if cur_p.is_human or cur_p.folded or cur_p.all_in or cur_p.sitting_out:
                break

            # Broadcast AI thinking event
            for ws in list(connected_clients):
                try:
                    await ws.send_json({
                        "type": "thinking",
                        "player_id": cur_p.id,
                        "player_name": cur_p.name
                    })
                except Exception:
                    pass

            # Natural human-like pause for bot decision
            await asyncio.sleep(0.9)

            # Execute AI move
            result = game.trigger_ai_turn_if_needed()
            await broadcast_state()

            if not result or not result.get("success"):
                break

            # Small pause between bot actions
            await asyncio.sleep(0.5)

    finally:
        ai_task_running = False


# ===================== REST API ENDPOINTS =====================

class ActionRequest(BaseModel):
    action: str  # fold, check, call, raise
    amount: int = 0


@app.get("/api/state")
def get_state():
    return game.to_dict()


@app.post("/api/start_hand")
async def start_hand():
    success = game.start_new_hand()
    if not success:
        raise HTTPException(status_code=400, detail="Não foi possível iniciar uma nova mão.")
    await broadcast_state()
    asyncio.create_task(run_ai_turns_loop())
    return {"success": True, "state": game.to_dict()}


@app.post("/api/action")
async def take_action(req: ActionRequest):
    human = game.get_human_player()
    if not human:
        raise HTTPException(status_code=400, detail="Jogador humano não encontrado.")

    success = game.player_action(human.id, req.action, req.amount)
    if not success:
        raise HTTPException(status_code=400, detail="Ação inválida ou fora de turno.")

    await broadcast_state()
    asyncio.create_task(run_ai_turns_loop())
    return {"success": True, "state": game.to_dict()}


@app.post("/api/ai_step")
async def ai_step():
    """Manual step for AI turn via REST."""
    result = game.trigger_ai_turn_if_needed()
    await broadcast_state()
    return {"result": result, "state": game.to_dict()}


@app.post("/api/rebuy")
async def rebuy():
    game.rebuy_human(1000)
    await broadcast_state()
    return {"success": True, "state": game.to_dict()}


def reset_game_instance():
    global game
    game = TexasHoldemGame(small_blind=10, big_blind=20, starting_chips=1000)
    return game


@app.post("/api/reset_table")
async def reset_table():
    reset_game_instance()
    await broadcast_state()
    return {"success": True, "state": game.to_dict()}


# ===================== WEBSOCKET ENDPOINT =====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    # Send initial state immediately
    await websocket.send_json({"type": "state", "data": game.to_dict()})

    try:
        while True:
            msg = await websocket.receive_json()
            msg_type = msg.get("type")

            if msg_type == "start_hand":
                if game.start_new_hand():
                    await broadcast_state()
                    asyncio.create_task(run_ai_turns_loop())

            elif msg_type == "action":
                human = game.get_human_player()
                if human:
                    action = msg.get("action")
                    amount = int(msg.get("amount", 0))
                    if game.player_action(human.id, action, amount):
                        await broadcast_state()
                        asyncio.create_task(run_ai_turns_loop())

            elif msg_type == "rebuy":
                game.rebuy_human(1000)
                await broadcast_state()

            elif msg_type == "reset":
                reset_game_instance()
                await broadcast_state()

            elif msg_type == "get_state":
                await websocket.send_json({"type": "state", "data": game.to_dict()})

    except WebSocketDisconnect:
        connected_clients.discard(websocket)
    except Exception:
        connected_clients.discard(websocket)


# Mount static files and frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"message": "Royal Felt Poker API ativa. Crie o frontend em /static/index.html"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
