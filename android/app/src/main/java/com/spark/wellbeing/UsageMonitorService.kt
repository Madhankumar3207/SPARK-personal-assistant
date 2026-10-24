package com.spark.wellbeing

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.app.AppOpsManager
import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.SystemClock
import java.time.LocalDate
import java.time.ZoneId

class UsageMonitorService : Service() {
    private val prefs by lazy { getSharedPreferences(PREFS, Context.MODE_PRIVATE) }
    private val handler = Handler(Looper.getMainLooper())
    private var active = false
    private val poll = object : Runnable { override fun run() { checkUsage(); if (active) handler.postDelayed(this, 15_000) } }

    override fun onBind(intent: Intent?): IBinder? = null
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> { prefs.edit().putBoolean("enabled", false).apply(); stopMonitoring(); return START_NOT_STICKY }
            ACTION_START -> {
                resetSession()
                prefs.edit().putBoolean("enabled", true).apply()
            }
        }
        if (!prefs.getBoolean("enabled", false)) { stopSelf(); return START_NOT_STICKY }
        createChannel()
        startForeground(NOTIFICATION_ID, ongoingNotification("Focus monitoring is on — selected apps only"))
        active = true
        handler.removeCallbacks(poll); handler.post(poll)
        return START_STICKY
    }

    override fun onDestroy() { active = false; handler.removeCallbacks(poll); super.onDestroy() }

    private fun stopMonitoring() { active = false; handler.removeCallbacks(poll); stopForeground(STOP_FOREGROUND_REMOVE); stopSelf() }

    private fun resetSession() {
        prefs.edit().putLong("sessionStartedAt", System.currentTimeMillis()).putLong("sessionStartedElapsed", SystemClock.elapsedRealtime()).putBoolean("warned", false)
            .putString("warningPackage", null).putLong("warningAt", 0L).putBoolean("leftAfterWarning", false)
            .putBoolean("intervened", false).apply()
    }

    private fun checkUsage() {
        try { checkUsageGranted() }
        catch (_: SecurityException) {
            prefs.edit().putBoolean("enabled", false).apply()
            showNotice("SPARK monitoring paused", "Usage Access is no longer available. Re-enable it in Android Settings to resume.", false)
            stopMonitoring()
        }
    }

    private fun checkUsageGranted() {
        if (!(getSystemService(NOTIFICATION_SERVICE) as NotificationManager).areNotificationsEnabled()) {
            prefs.edit().putBoolean("enabled", false).apply()
            stopMonitoring()
            return
        }
        @Suppress("DEPRECATION")
        val appOp = getSystemService(AppOpsManager::class.java).checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS, android.os.Process.myUid(), packageName)
        if (appOp != AppOpsManager.MODE_ALLOWED) throw SecurityException("Usage Access revoked")
        val now = System.currentTimeMillis()
        val elapsedNow = SystemClock.elapsedRealtime()
        val start = prefs.getLong("sessionStartedAt", 0L)
        val elapsedStart = prefs.getLong("sessionStartedElapsed", 0L)
        val sessionLength = prefs.getInt("sessionLengthMinutes", 120).coerceIn(1, 480) * 60_000L
        if (start == 0L || elapsedStart == 0L || elapsedNow - elapsedStart >= sessionLength) {
            prefs.edit().putBoolean("enabled", false).apply(); stopMonitoring(); return
        }
        val selected = prefs.getStringSet("selected", emptySet()).orEmpty()
        val usage = sessionUsage(this, start, now, selected)
        val foreground = foregroundPackage(start, now)
        val state = FocusState(
            warned = prefs.getBoolean("warned", false), warningPackage = prefs.getString("warningPackage", null),
            warningAtMs = prefs.getLong("warningAt", 0L), leftAfterWarning = prefs.getBoolean("leftAfterWarning", false),
            intervened = prefs.getBoolean("intervened", false), lastInterventionAtMs = prefs.getLong("lastInterventionAt", 0L),
        )
        val result = FocusPolicy.evaluate(selected, foreground, usage, prefs.getInt("limitMinutes", 20) * 60_000L,
            prefs.getInt("graceMinutes", 2) * 60_000L, elapsedNow, state)
        prefs.edit().putBoolean("warned", result.state.warned).putString("warningPackage", result.state.warningPackage)
            .putLong("warningAt", result.state.warningAtMs).putBoolean("leftAfterWarning", result.state.leftAfterWarning)
            .putBoolean("intervened", result.state.intervened).putLong("lastInterventionAt", result.state.lastInterventionAtMs).apply()
        if (result.warning) {
            record("Warning · ${result.state.warningPackage} · ${now}")
            val warnedPackage = result.state.warningPackage.orEmpty()
            val label = try { packageManager.getApplicationLabel(packageManager.getApplicationInfo(warnedPackage, 0)).toString() } catch (_: Exception) { warnedPackage }
            val minutes = (usage[warnedPackage] ?: 0L) / 60_000
            val warning = prefs.getString("warningText", "Bro, you've spent too much time here. Come back to your goal. ⚡")
            showNotice("SPARK focus reminder", "$label · $minutes minutes. $warning", false)
        }
        if (result.intervene) {
            record("Intervention · ${result.state.warningPackage} · ${now}")
            showNotice("SPARK focus reminder", "Bro, you already received a warning. Let's return to your work. ⚡", true)
        }
        val app = selected.firstOrNull { (usage[it] ?: 0L) >= prefs.getInt("limitMinutes", 20) * 60_000L }
        val summary = app?.let { "$it crossed its session limit" } ?: "Focus monitoring is on — selected apps only"
        (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).notify(NOTIFICATION_ID, ongoingNotification(summary))
    }

    private fun foregroundPackage(start: Long, now: Long): String? {
        val events = getSystemService(UsageStatsManager::class.java).queryEvents(start, now)
        val event = UsageEvents.Event(); var foreground: String? = null
        while (events.hasNextEvent()) {
            events.getNextEvent(event)
            when (event.eventType) {
                UsageEvents.Event.ACTIVITY_RESUMED, UsageEvents.Event.MOVE_TO_FOREGROUND -> foreground = event.packageName
                UsageEvents.Event.ACTIVITY_PAUSED, UsageEvents.Event.MOVE_TO_BACKGROUND -> if (foreground == event.packageName) foreground = null
            }
        }
        return foreground
    }

    private fun record(value: String) {
        val history = prefs.getStringSet("history", emptySet()).orEmpty().toMutableSet()
        history.add(value); prefs.edit().putStringSet("history", history.takeLast(100).toSet()).apply()
    }

    private fun showNotice(title: String, message: String, intervention: Boolean) {
        val builder = android.app.Notification.Builder(this, CHANNEL_ID).setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title).setContentText(message).setStyle(Notification.BigTextStyle().bigText(message))
            .setAutoCancel(true).setContentIntent(activityIntent())
        if (intervention) {
            val home = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            builder.addAction(android.R.drawable.ic_menu_view, "Go to Home", PendingIntent.getActivity(this, 3, home, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE))
            builder.addAction(android.R.drawable.ic_menu_info_details, "Focus options", activityIntent())
        }
        (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).notify(if (intervention) INTERVENTION_ID else WARNING_ID, builder.build())
    }

    private fun activityIntent() = PendingIntent.getActivity(this, 2, Intent(this, MainActivity::class.java), PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

    private fun ongoingNotification(message: String) = Notification.Builder(this, CHANNEL_ID)
        .setSmallIcon(android.R.drawable.ic_menu_recent_history).setContentTitle("SPARK Wellbeing")
        .setContentText(message).setOngoing(true).setContentIntent(activityIntent()).build()

    private fun createChannel() {
        (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "Focus monitoring", NotificationManager.IMPORTANCE_DEFAULT))
    }

    companion object {
        const val PREFS = "spark_wellbeing_local"
        const val ACTION_START = "com.spark.wellbeing.START"
        const val ACTION_STOP = "com.spark.wellbeing.STOP"
        private const val CHANNEL_ID = "spark_focus"
        private const val NOTIFICATION_ID = 6001
        private const val WARNING_ID = 6002
        private const val INTERVENTION_ID = 6003

        fun sessionUsage(context: Context, start: Long, end: Long, selected: Set<String>): Map<String, Long> {
            val result = mutableMapOf<String, Long>(); val activeSince = mutableMapOf<String, Long>()
            val events = context.getSystemService(UsageStatsManager::class.java).queryEvents(start, end)
            val event = UsageEvents.Event()
            while (events.hasNextEvent()) {
                events.getNextEvent(event)
                val pkg = event.packageName ?: continue
                if (pkg !in selected) continue
                when (event.eventType) {
                    UsageEvents.Event.ACTIVITY_RESUMED, UsageEvents.Event.MOVE_TO_FOREGROUND -> activeSince[pkg] = event.timeStamp
                    UsageEvents.Event.ACTIVITY_PAUSED, UsageEvents.Event.MOVE_TO_BACKGROUND -> {
                        val since = activeSince.remove(pkg)
                        if (since != null && event.timeStamp > since) result[pkg] = (result[pkg] ?: 0L) + event.timeStamp - since
                    }
                }
            }
            activeSince.forEach { (pkg, since) -> if (end > since) result[pkg] = (result[pkg] ?: 0L) + end - since }
            return result
        }

        fun todayUsage(context: Context, selected: Set<String>): Map<String, Long> {
            val start = LocalDate.now().atStartOfDay(ZoneId.systemDefault()).toInstant().toEpochMilli()
            return context.getSystemService(UsageStatsManager::class.java).queryUsageStats(UsageStatsManager.INTERVAL_DAILY, start, System.currentTimeMillis())
                .filter { it.packageName in selected }.associate { it.packageName to it.totalTimeInForeground }
        }
    }
}
