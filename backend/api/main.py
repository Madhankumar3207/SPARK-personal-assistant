"""FastAPI entry point that exposes SPARK's existing local capabilities."""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from starlette.staticfiles import StaticFiles

from backend.api.schemas import (
    ChatRequest, FileOpenRequest, MemoryRequest, ModeRequest, TaskRequest, TaskUpdate,
    ReminderRequest, ReminderUpdate, SnoozeRequest, SuggestionUpdate,
)
from backend.services import spark_service
from backend.services import reminders, whatsapp
from backend.services.events import events


@asynccontextmanager
async def lifespan(app: FastAPI):
    events.loop = asyncio.get_running_loop()
    spark_service.start_runtime()
    yield
    spark_service.stop_runtime()


app = FastAPI(title="SPARK Local API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health():
    return {"status": "online", "application": "SPARK"}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    result = await run_in_threadpool(spark_service.chat, request.message)
    return result


@app.get("/api/mode")
def get_mode():
    return spark_service.mode_state()


@app.post("/api/mode")
async def set_mode(request: ModeRequest):
    command = f"{request.mode} {'on' if request.enabled else 'off'}"
    response = await run_in_threadpool(spark_service.run_command, command)
    state = spark_service.mode_state()
    events.publish({"type": "mode", **state})
    return {"response": response, **state}


@app.get("/api/tasks")
async def get_tasks():
    return {"tasks": await run_in_threadpool(spark_service.list_tasks)}


@app.post("/api/tasks")
async def post_task(request: TaskRequest):
    response, tasks = await run_in_threadpool(spark_service.add_task, request.task, request.priority, request.due_at)
    return {"response": response, "tasks": tasks}


@app.put("/api/tasks/{task_id}")
async def put_task(task_id: int, request: TaskUpdate):
    response, tasks = await run_in_threadpool(spark_service.update_task, task_id, request.task, request.priority, request.due_at, request.completed)
    if response.startswith("I couldn't find"):
        raise HTTPException(404, response)
    return {"response": response, "tasks": tasks}


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    response, tasks = await run_in_threadpool(spark_service.delete_task, task_id)
    if response.startswith("I couldn't find"):
        raise HTTPException(404, response)
    return {"response": response, "tasks": tasks}


@app.get("/api/memory")
async def get_memory():
    return {"memory": await run_in_threadpool(spark_service.memory_state)}


@app.post("/api/memory")
async def post_memory(request: MemoryRequest):
    response, memory = await run_in_threadpool(spark_service.add_memory, request.key, request.value)
    return {"response": response, "memory": memory}


@app.delete("/api/memory")
async def delete_memory():
    response = await run_in_threadpool(spark_service.clear_all_memory)
    return {"response": response, "memory": {}}


@app.get("/api/system")
async def get_system():
    return await run_in_threadpool(spark_service.system_state)


@app.get("/api/files/search")
async def get_file_search(q: str):
    if not q.strip() or len(q) > 300:
        raise HTTPException(400, "Enter a search term of 1 to 300 characters.")
    response, results = await run_in_threadpool(spark_service.search_files, q.strip())
    return {"response": response, "results": results}


@app.post("/api/files/open")
async def post_file_open(request: FileOpenRequest):
    response = await run_in_threadpool(spark_service.open_file_result, request.id)
    return {"response": response, "success": not response.startswith("I couldn't")}


@app.get("/api/reminders")
async def get_reminders():
    return {"reminders": await run_in_threadpool(reminders.list_reminders)}


@app.post("/api/reminders")
async def post_reminder(request: ReminderRequest):
    try:
        item, created = await run_in_threadpool(
            reminders.create_reminder, request.title, request.scheduled_at,
            request.timezone, request.recurrence,
        )
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    return {"reminder": item, "created": created}


@app.patch("/api/reminders/{reminder_id}")
async def patch_reminder(reminder_id: str, request: ReminderUpdate):
    try:
        updated = await run_in_threadpool(reminders.update_reminder, reminder_id, request.title, request.scheduled_at, request.recurrence)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    if not updated:
        raise HTTPException(404, "Reminder not found.")
    return {"updated": True}


@app.delete("/api/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):
    if not await run_in_threadpool(reminders.cancel_reminder, reminder_id):
        raise HTTPException(404, "Reminder not found.")
    return {"cancelled": True}


@app.post("/api/reminders/{reminder_id}/snooze")
async def snooze_reminder(reminder_id: str, request: SnoozeRequest):
    try:
        updated = await run_in_threadpool(reminders.snooze_reminder, reminder_id, request.minutes)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    if not updated:
        raise HTTPException(404, "Reminder not found.")
    return {"snoozed": True}


@app.post("/api/whatsapp/analyze")
async def analyze_whatsapp(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(400, "Choose a WhatsApp .txt export.")
    content = await file.read(5 * 1024 * 1024 + 1)
    try:
        suggestions = await run_in_threadpool(whatsapp.analyze_export, file.filename, content)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    return {"suggestions": suggestions}


@app.get("/api/whatsapp/suggestions")
async def get_whatsapp_suggestions():
    return {"suggestions": await run_in_threadpool(whatsapp.list_suggestions)}


@app.patch("/api/whatsapp/suggestions/{suggestion_id}")
async def patch_whatsapp_suggestion(suggestion_id: str, request: SuggestionUpdate):
    item = await run_in_threadpool(whatsapp.update_suggestion, suggestion_id, "pending", request.title, request.deadline)
    if not item:
        raise HTTPException(404, "Suggestion not found.")
    return {"suggestion": item}


@app.post("/api/whatsapp/suggestions/{suggestion_id}/approve")
async def approve_whatsapp_suggestion(suggestion_id: str, request: SuggestionUpdate):
    current = next((item for item in await run_in_threadpool(whatsapp.list_suggestions) if item["id"] == suggestion_id), None)
    if not current:
        raise HTTPException(404, "Suggestion not found.")
    deadline = request.deadline or current.get("deadline")
    if not deadline:
        raise HTTPException(400, "This suggestion has no reliable deadline. Edit it with a date and time before approval.")
    title = request.title or current["title"]
    try:
        reminder, _ = await run_in_threadpool(reminders.create_reminder, title, deadline,
                                               current.get("timezone") or "Asia/Kolkata", None,
                                               "whatsapp", f"whatsapp:{suggestion_id}")
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    task_response, _ = await run_in_threadpool(spark_service.add_task, title)
    if task_response.startswith("I couldn't"):
        raise HTTPException(500, "The reminder was saved, but SPARK couldn't save its task. The suggestion remains pending; retry approval after checking task storage.")
    item = await run_in_threadpool(whatsapp.update_suggestion, suggestion_id, "approved", title, deadline)
    if not item:
        raise HTTPException(409, "This suggestion was already reviewed. Check the existing task and reminder before retrying.")
    return {"suggestion": item, "task_response": task_response, "reminder": reminder}


@app.post("/api/whatsapp/suggestions/{suggestion_id}/reject")
async def reject_whatsapp_suggestion(suggestion_id: str):
    item = await run_in_threadpool(whatsapp.update_suggestion, suggestion_id, "rejected")
    if not item:
        raise HTTPException(404, "Suggestion not found.")
    return {"rejected": True}


@app.delete("/api/whatsapp/suggestions")
async def clear_whatsapp_suggestions():
    await run_in_threadpool(whatsapp.clear_suggestions)
    return {"cleared": True}


@app.websocket("/ws/spark")
async def spark_socket(websocket: WebSocket):
    await events.connect(websocket)
    await websocket.send_json({"type": "mode", **spark_service.mode_state()})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await events.disconnect(websocket)


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
