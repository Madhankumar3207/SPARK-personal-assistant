import { useCallback, useEffect, useRef, useState } from 'react'

const sections = ['Home', 'Chat', 'Tasks', 'Reminders', 'Digital Wellbeing', 'Files', 'WhatsApp Analysis', 'Memory', 'System', 'Settings']

async function api(path, options = {}) {
  const response = await fetch(path, options)
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || 'The SPARK backend could not complete the request.')
  return data
}

export default function App() {
  const [page, setPage] = useState('Home')
  const [online, setOnline] = useState(false)
  const [mode, setMode] = useState({ voice_enabled: false, chat_enabled: true })
  const [messages, setMessages] = useState([{ role: 'spark', text: 'Hello bro! ⚡ I’m ready to help.' }])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [tasks, setTasks] = useState([])
  const [taskFilter, setTaskFilter] = useState('pending')
  const [reminders, setReminders] = useState([])
  const [memory, setMemory] = useState({})
  const [system, setSystem] = useState({})
  const [query, setQuery] = useState('')
  const [files, setFiles] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const chatEnd = useRef(null)

  const refresh = useCallback(async () => {
    try {
      const [health, taskData, reminderData, memoryData, modeData, systemData, suggestionData] = await Promise.all([
        api('/api/health'), api('/api/tasks'), api('/api/reminders'), api('/api/memory'), api('/api/mode'), api('/api/system'), api('/api/whatsapp/suggestions'),
      ])
      setOnline(health.status === 'online'); setTasks(taskData.tasks); setReminders(reminderData.reminders)
      setMemory(memoryData.memory); setMode(modeData); setSystem(systemData); setSuggestions(suggestionData.suggestions); setError('')
    } catch (err) { setOnline(false); setError(err.message) }
  }, [])

  useEffect(() => { refresh() }, [refresh])
  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, busy])
  useEffect(() => {
    const socket = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/spark`)
    socket.onmessage = event => {
      const item = JSON.parse(event.data)
      if (item.type === 'reminder') {
        setNotice(`Reminder: ${item.title}`)
        if ('Notification' in window && Notification.permission === 'granted') new Notification('SPARK reminder', { body: item.title })
        refresh()
      }
      if (item.type === 'mode') setMode(item)
      if (item.type === 'voice_result' && item.command) setMessages(current => [...current, { role: 'you', text: item.command }, { role: 'spark', text: item.response }])
    }
    return () => socket.close()
  }, [refresh])

  async function sendMessage(event) {
    event?.preventDefault()
    const message = text.trim()
    if (!message || busy) return
    setText(''); setMessages(current => [...current, { role: 'you', text: message }]); setBusy(true); setError('')
    try {
      const result = await api('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message }) })
      setMessages(current => [...current, { role: 'spark', text: result.response }]); setFiles(result.results || []); await refresh()
    } catch (err) { setError(err.message); setMessages(current => [...current, { role: 'spark', text: err.message }]) }
    finally { setBusy(false) }
  }

  async function setInputMode(which, enabled) {
    try { const result = await api('/api/mode', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: which, enabled }) }); setMode(result) }
    catch (err) { setError(err.message) }
  }

  async function addTask(event) {
    event.preventDefault(); const form = event.currentTarget; const value = form.elements.task.value.trim(); if (!value) return
    try { const data = await api('/api/tasks', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ task: value, priority: form.elements.priority.value, due_at: form.elements.due_at.value ? new Date(form.elements.due_at.value).toISOString() : null }) }); setTasks(data.tasks); form.reset() }
    catch (err) { setError(err.message) }
  }

  async function editTask(task) {
    const title = prompt('Edit task', task.task)
    if (!title) return
    const priority = prompt('Priority: low, normal, or high', task.priority || 'normal')
    if (!priority) return
    try { await api(`/api/tasks/${task.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ task: title, priority: priority.toLowerCase() }) }); await refresh() }
    catch (err) { setError(err.message) }
  }

  async function createReminder(event) {
    event.preventDefault(); const form = event.currentTarget; const title = form.elements.title.value.trim(); const local = form.elements.when.value
    if (!title || !local) return
    try { await api('/api/reminders', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, scheduled_at: new Date(local).toISOString(), timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata', recurrence: form.elements.recurrence.value || null }) }); form.reset(); await refresh() }
    catch (err) { setError(err.message) }
  }

  async function searchFiles(event) {
    event.preventDefault()
    try { const data = await api(`/api/files/search?q=${encodeURIComponent(query)}`); setFiles(data.results); setNotice(data.response) }
    catch (err) { setError(err.message) }
  }

  async function openFile(id) {
    try { const data = await api('/api/files/open', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) }); setNotice(data.response) }
    catch (err) { setError(err.message) }
  }

  async function importChat(event) {
    event.preventDefault(); const file = event.currentTarget.elements.chat.files[0]; if (!file) return
    const body = new FormData(); body.append('file', file)
    try { const result = await api('/api/whatsapp/analyze', { method: 'POST', body }); setSuggestions(result.suggestions); setNotice(`Analyzed locally. ${result.suggestions.length} suggestion(s) need review.`) }
    catch (err) { setError(err.message) }
  }

  async function suggestionAction(item, action) {
    try {
      if (action === 'reject') await api(`/api/whatsapp/suggestions/${item.id}/reject`, { method: 'POST' })
      else if (action === 'edit') {
        const title = prompt('Edit the suggested action', item.title)
        if (!title) return
        const deadline = prompt('Set a deadline with timezone, e.g. 2026-10-13T17:00:00+05:30', item.deadline || '')
        if (!deadline) return
        await api(`/api/whatsapp/suggestions/${item.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, deadline }) })
      }
      else {
        let deadline = item.deadline
        if (!deadline) deadline = new Date(prompt('This item needs a deadline. Enter an ISO date and time with timezone, e.g. 2026-10-13T17:00:00+05:30') || '').toISOString()
        await api(`/api/whatsapp/suggestions/${item.id}/approve`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ deadline }) })
      }
      await refresh()
    } catch (err) { setError(err.message) }
  }

  const pending = tasks.filter(task => !task.completed)
  const visibleTasks = tasks.filter(task => taskFilter === 'all' || (taskFilter === 'pending' && !task.completed) || (taskFilter === 'completed' && task.completed) || (taskFilter === 'overdue' && !task.completed && task.due_at && new Date(task.due_at) < new Date()))
  const localTime = value => new Date(value).toLocaleString()

  return <div className="shell">
    <aside className="sidebar"><div className="brand"><span className="brand-mark">⚡</span><span>SPARK<small>PERSONAL ASSISTANT</small></span></div>
      <nav>{sections.map(item => <button key={item} className={page === item ? 'nav active' : 'nav'} onClick={() => setPage(item)}>{item}</button>)}</nav>
      <div className="mode-box"><span className={online ? 'dot on' : 'dot'} />{online ? 'Backend online' : 'Backend offline'}<div className="mode-row"><button onClick={() => setInputMode('voice', !mode.voice_enabled)}>Voice {mode.voice_enabled ? 'On' : 'Off'}</button><button onClick={() => setInputMode('chat', !mode.chat_enabled)}>Chat {mode.chat_enabled ? 'On' : 'Off'}</button></div></div>
    </aside>
    <main className="main"><header><div><div className="eyebrow">YOUR LOCAL ASSISTANT</div><h1>{page}</h1></div><div className="header-right"><span className="pill">{pending.length} pending tasks</span><span className="avatar">S</span></div></header>
      {error && <div className="alert error">{error}<button onClick={() => setError('')}>×</button></div>}{notice && <div className="alert">{notice}<button onClick={() => setNotice('')}>×</button></div>}
      {page === 'Home' && <><section className="welcome card"><div><div className="eyebrow">SPARK IS {online ? 'READY' : 'WAITING FOR BACKEND'}</div><h2>Good to see you.</h2><p>Your private desktop assistant, ready for tasks, files and reminders.</p><button className="primary" onClick={() => setPage('Chat')}>Open chat <span>→</span></button></div><div className="orb">✦</div></section><section className="stats"><Stat label="Pending tasks" value={pending.length} /><Stat label="Upcoming reminders" value={reminders.filter(item => item.status === 'scheduled').length} /><Stat label="Saved memories" value={Object.keys(memory).length} /></section><div className="two-col"><section className="card"><SectionTitle title="Upcoming reminders" action={() => setPage('Reminders')} />{reminders.filter(item => item.status === 'scheduled').slice(0, 4).map(item => <ReminderRow key={item.id} item={item} />)}{!reminders.length && <Empty>No reminders scheduled yet.</Empty>}</section><section className="card"><SectionTitle title="Pending tasks" action={() => setPage('Tasks')} />{pending.slice(0, 5).map(task => <TaskRow key={task.id} task={task} onComplete={async () => { await api(`/api/tasks/${task.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ completed: true }) }); refresh() }} />)}{!pending.length && <Empty>You’re all caught up.</Empty>}</section></div></>}
      {page === 'Chat' && <section className="card chat-card"><div className="chat-log">{messages.map((message, index) => <div key={index} className={`message ${message.role}`}><span>{message.role === 'you' ? 'YOU' : 'SPARK'}</span><p>{message.text}</p></div>)}{busy && <div className="typing">SPARK is thinking<span>•••</span></div>}<div ref={chatEnd} /></div>{files.length > 0 && <div className="file-results">{files.map(file => <button key={file.id} onClick={() => openFile(file.id)}><span>{file.name}</span><small>{file.type} · Open</small></button>)}</div>}<form className="composer" onSubmit={sendMessage}><textarea value={text} onChange={event => setText(event.target.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage() } }} placeholder="Ask SPARK anything…" aria-label="Message SPARK" /><button className="primary" disabled={busy}>Send ↑</button></form><div className="hint">Enter to send · Shift+Enter for a new line</div></section>}
      {page === 'Tasks' && <section className="card"><SectionTitle title="Your tasks" /><form className="inline-form task-form" onSubmit={addTask}><input name="task" placeholder="Add a task…" maxLength="500"/><select name="priority"><option value="normal">Normal</option><option value="high">High</option><option value="low">Low</option></select><input type="datetime-local" name="due_at" aria-label="Optional task deadline"/><button className="primary">Add task</button></form><div className="filters">{['pending','completed','overdue','all'].map(filter => <button className={taskFilter === filter ? 'selected' : ''} key={filter} onClick={() => setTaskFilter(filter)}>{filter}</button>)}</div>{visibleTasks.map(task => <TaskRow key={task.id} task={task} onEdit={() => editTask(task)} onComplete={async () => { await api(`/api/tasks/${task.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ completed: !task.completed }) }); refresh() }} onDelete={async () => { await api(`/api/tasks/${task.id}`, { method: 'DELETE' }); refresh() }} />)}{!visibleTasks.length && <Empty>No tasks in this view.</Empty>}</section>}
      {page === 'Reminders' && <section className="card"><SectionTitle title="Reminders" /><form className="reminder-form" onSubmit={createReminder}><input name="title" placeholder="What should SPARK remind you about?" required/><input type="datetime-local" name="when" required/><select name="recurrence"><option value="">One time</option><option value="daily">Daily</option><option value="weekly">Weekly</option></select><button className="primary">Create reminder</button></form><p className="muted">Reminders are delivered in-app while the backend is running. The backend must remain open for delivery.</p>{reminders.map(item => <ReminderRow key={item.id} item={item} onCancel={async () => { await api(`/api/reminders/${item.id}`, { method: 'DELETE' }); refresh() }} onSnooze={async () => { await api(`/api/reminders/${item.id}/snooze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ minutes: 10 }) }); refresh() }} />)}</section>}
      {page === 'Digital Wellbeing' && <section className="card"><SectionTitle title="Phone-native focus monitoring" /><div className="alert">This React/PWA dashboard cannot inspect or control other phone apps. Monitoring runs locally in the separate Android companion; it does not depend on this laptop or internet.</div><h3>Android companion status</h3><p className="muted">The Android companion is in <code>android/</code>. It monitors only apps you select and keeps usage and warning history on-device. This web page does not receive that data.</p><ol><li>Open the <code>android/</code> folder in Android Studio and run the <code>app</code> configuration on your phone.</li><li>In SPARK Wellbeing, select the apps yourself and set per-app session threshold, warning grace, and focus-session length.</li><li>Grant Usage Access in Android Settings and allow SPARK notifications; start a focus session explicitly.</li></ol><p className="muted">The Android OS limits background app launches. At a second violation SPARK sends a notification with a user-tapped “Go to Home” action; it does not force-stop apps or automatically take over the screen. Device-specific behavior and foreground-service eligibility require real-device testing. Schedule-based starts and daily caps are not implemented yet.</p><p className="muted">Usage Access is sensitive special access. Read the in-app disclosure and grant it only if you want the feature. You can pause monitoring or revoke access at any time.</p></section>}
      {page === 'Files' && <section className="card"><SectionTitle title="Search files" /><form className="inline-form" onSubmit={searchFiles}><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Try photos, resume, PDF…"/><button className="primary">Search</button></form>{files.map(file => <button className="file-row" key={file.id} onClick={() => openFile(file.id)}><span>{file.name}</span><small>{file.path}</small></button>)}</section>}
      {page === 'WhatsApp Analysis' && <section className="card"><SectionTitle title="Review a chat export" /><p className="muted">Choose a WhatsApp .txt export. It is parsed locally and the original file is not kept. Suggestions remain pending until you approve them.</p><form className="inline-form" onSubmit={importChat}><input name="chat" type="file" accept=".txt,text/plain" required/><button className="primary">Analyze export</button></form>{suggestions.map(item => <article className="suggestion" key={item.id}><div className="confidence">{Math.round(item.confidence * 100)}%</div><h3>{item.title}</h3><blockquote>{item.evidence}</blockquote><p className="muted">{item.sender || 'Unknown sender'} · {item.message_time || 'Timestamp unavailable'}{item.deadline ? ` · ${localTime(item.deadline)}` : ' · Deadline needs clarification'}</p><div className="actions"><button onClick={() => suggestionAction(item, 'approve')}>Approve reminder</button><button onClick={() => suggestionAction(item, 'edit')}>Edit</button><button className="quiet" onClick={() => suggestionAction(item, 'reject')}>Reject</button></div></article>)}</section>}
      {page === 'Memory' && <section className="card"><SectionTitle title="Saved memory" action={async () => { await api('/api/memory', { method: 'DELETE' }); refresh() }} actionText="Clear memory" /><form className="inline-form" onSubmit={async event => { event.preventDefault(); const form = event.currentTarget; try { await api('/api/memory', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: form.elements.key.value, value: form.elements.value.value }) }); form.reset(); refresh() } catch (err) { setError(err.message) } }}><input name="key" placeholder="Memory key" required/><input name="value" placeholder="Value" required/><button className="primary">Save</button></form>{Object.entries(memory).map(([key, value]) => <div className="data-row" key={key}><b>{key}</b><span>{value}</span></div>)}{!Object.keys(memory).length && <Empty>No saved memory.</Empty>}</section>}
      {page === 'System' && <section className="card"><SectionTitle title="System information" /><div className="system-grid">{Object.entries(system).filter(([, value]) => typeof value !== 'object').map(([key, value]) => <div className="data-row" key={key}><b>{key.replaceAll('_', ' ')}</b><span>{String(value)}</span></div>)}</div></section>}
      {page === 'Settings' && <section className="card"><SectionTitle title="Local settings" /><div className="data-row"><b>Timezone</b><span>{Intl.DateTimeFormat().resolvedOptions().timeZone}</span></div><div className="data-row"><b>Backend</b><span>Local API · {online ? 'connected' : 'disconnected'}</span></div><button onClick={() => { if ('Notification' in window) Notification.requestPermission().then(value => setNotice(`Browser notification permission: ${value}`)) }}>Enable browser notifications</button><p className="muted">Microphone and browser notifications may require HTTPS or localhost. LAN access is not enabled by default.</p></section>}
    </main>
  </div>
}

function Stat({ label, value }) { return <div className="stat card"><span>{label}</span><b>{value}</b></div> }
function SectionTitle({ title, action, actionText = 'View all' }) { return <div className="section-title"><h2>{title}</h2>{action && <button className="text-button" onClick={action}>{actionText} →</button>}</div> }
function Empty({ children }) { return <div className="empty">{children}</div> }
function TaskRow({ task, onComplete, onDelete, onEdit }) { return <div className="task-row"><button className={task.completed ? 'check checked' : 'check'} onClick={onComplete} aria-label={task.completed ? 'Reopen task' : 'Complete task'}>{task.completed ? '✓' : ''}</button><span className={task.completed ? 'done' : ''}>{task.task}<small className="task-meta">{task.priority || 'normal'} priority{task.due_at ? ` · due ${new Date(task.due_at).toLocaleString()}` : ''}</small></span>{onEdit && <button className="quiet" onClick={onEdit}>Edit</button>}{onDelete && <button className="remove" onClick={onDelete} aria-label="Cancel task">×</button>}</div> }
function ReminderRow({ item, onCancel, onSnooze }) { return <div className="reminder-row"><span className="calendar">◷</span><div><b>{item.title}</b><small>{new Date(item.scheduled_at).toLocaleString()} · {item.status}{item.recurrence ? ` · ${item.recurrence}` : ''}</small></div><div className="row-actions">{onSnooze && item.status === 'scheduled' && <button onClick={onSnooze}>Snooze 10m</button>}{onCancel && item.status === 'scheduled' && <button className="quiet" onClick={onCancel}>Cancel</button>}</div></div> }
