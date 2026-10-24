from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class TaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=500)
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")
    due_at: str | None = None


class TaskUpdate(BaseModel):
    task: str | None = Field(default=None, min_length=1, max_length=500)
    priority: str | None = Field(default=None, pattern="^(low|normal|high)$")
    due_at: str | None = None
    completed: bool | None = None


class MemoryRequest(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=1000)


class FileOpenRequest(BaseModel):
    id: int = Field(ge=1)


class ModeRequest(BaseModel):
    mode: str = Field(pattern="^(voice|chat)$")
    enabled: bool


class ReminderRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    scheduled_at: str
    timezone: str = "Asia/Kolkata"
    recurrence: str | None = None


class ReminderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    scheduled_at: str | None = None
    recurrence: str | None = None


class SnoozeRequest(BaseModel):
    minutes: int = Field(ge=1, le=10080)


class SuggestionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    deadline: str | None = None
