package com.spark.wellbeing

import android.Manifest
import android.app.Activity
import android.app.AppOpsManager
import android.app.AlertDialog
import android.app.NotificationManager
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast

class MainActivity : Activity() {
    private val prefs by lazy { getSharedPreferences(UsageMonitorService.PREFS, Context.MODE_PRIVATE) }
    private lateinit var status: TextView
    private lateinit var apps: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        render()
        requestNotificationsIfNeeded()
    }

    override fun onResume() { super.onResume(); if (::status.isInitialized) refresh() }

    private fun render() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; setPadding(28, 28, 28, 24); gravity = Gravity.TOP
        }
        fun text(value: String, size: Float = 16f): TextView = TextView(this).apply {
            this.text = value; textSize = size; setPadding(0, 8, 0, 8)
        }
        fun button(label: String, action: () -> Unit) { root.addView(Button(this).apply { text = label; setOnClickListener { action() } }) }

        root.addView(text("SPARK Digital Wellbeing", 25f))
        root.addView(text("Monitoring uses Android Usage Access to read foreground app time only for apps you select. SPARK stores app IDs, durations and focus state locally; it does not read messages, screenshots or keystrokes, and does not upload usage data."))
        status = text(""); root.addView(status)
        apps = text(""); root.addView(apps)
        button("Choose distracting apps") { chooseApps() }
        button("Configure session length, app limit and warning grace") { configureLimits() }
        button("Set first-warning text") { configureWarningText() }
        button("Explain and grant Usage Access") { explainUsageAccess() }
        button("Enable SPARK notifications") { requestNotificationsIfNeeded(); if (Build.VERSION.SDK_INT >= 26) startActivity(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, packageName)) }
        button("Start focus session") { startSession() }
        button("Pause / end focus session") { stopService(Intent(this, UsageMonitorService::class.java)); prefs.edit().putBoolean("enabled", false).apply(); refresh() }
        button("View today's selected-app usage") { showTodayUsage() }
        button("View warning and intervention history") { showHistory() }
        button("Refresh status") { refresh() }
        setContentView(root)
        refresh()
    }

    private fun requestNotificationsIfNeeded() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 41)
        }
    }

    private fun hasUsageAccess(): Boolean {
        val ops = getSystemService(AppOpsManager::class.java)
        @Suppress("DEPRECATION")
        val mode = ops.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, android.os.Process.myUid(), packageName)
        return mode == AppOpsManager.MODE_ALLOWED
    }

    private fun explainUsageAccess() {
        AlertDialog.Builder(this).setTitle("Usage Access is needed")
            .setMessage("Android Usage Access lets SPARK read foreground-duration events for only the apps you select. It cannot read their message content. The data stays on this phone. You can revoke access or disable monitoring any time. Tap Continue to open Android Settings and enable SPARK manually.")
            .setNegativeButton("Not now", null).setPositiveButton("Continue") { _, _ ->
                try { startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)) }
                catch (_: Exception) { Toast.makeText(this, "Open Android Settings → Special app access → Usage access → SPARK Wellbeing", Toast.LENGTH_LONG).show() }
            }.show()
    }

    private fun chooseApps() {
        val launchIntent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        val activities = packageManager.queryIntentActivities(launchIntent, PackageManager.MATCH_ALL)
            .filter { it.activityInfo.packageName != packageName }
            .distinctBy { it.activityInfo.packageName }
            .sortedBy { it.loadLabel(packageManager).toString().lowercase() }
        if (activities.isEmpty()) { Toast.makeText(this, "No launchable apps are visible to SPARK on this device.", Toast.LENGTH_LONG).show(); return }
        val selected = prefs.getStringSet("selected", emptySet()).orEmpty().toMutableSet()
        val labels = activities.map { "${it.loadLabel(packageManager)} (${it.activityInfo.packageName})" }.toTypedArray()
        val checks = BooleanArray(activities.size) { selected.contains(activities[it].activityInfo.packageName) }
        AlertDialog.Builder(this).setTitle("Select apps you want to monitor")
            .setMultiChoiceItems(labels, checks) { _, index, checked ->
                val pkg = activities[index].activityInfo.packageName
                if (checked) selected.add(pkg) else selected.remove(pkg)
            }.setNegativeButton("Cancel", null).setPositiveButton("Save selected apps") { _, _ ->
                prefs.edit().putStringSet("selected", selected).apply(); refresh()
            }.show()
    }

    private fun configureLimits() {
        val fields = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(36, 8, 36, 0) }
        val session = android.widget.EditText(this).apply { hint = "Usage threshold per selected app (minutes)"; inputType = 2; setText(prefs.getInt("limitMinutes", 20).toString()) }
        val grace = android.widget.EditText(this).apply { hint = "Warning grace period (minutes)"; inputType = 2; setText(prefs.getInt("graceMinutes", 2).toString()) }
        val sessionLength = android.widget.EditText(this).apply { hint = "Focus session length (minutes)"; inputType = 2; setText(prefs.getInt("sessionLengthMinutes", 120).toString()) }
        fields.addView(session); fields.addView(grace); fields.addView(sessionLength)
        AlertDialog.Builder(this).setTitle("Focus session limits").setView(fields).setNegativeButton("Cancel", null)
            .setPositiveButton("Save") { _, _ ->
                val limit = session.text.toString().toIntOrNull()?.coerceIn(1, 480) ?: 20
                val wait = grace.text.toString().toIntOrNull()?.coerceIn(0, 60) ?: 2
                val duration = sessionLength.text.toString().toIntOrNull()?.coerceIn(1, 480) ?: 120
                prefs.edit().putInt("limitMinutes", limit).putInt("graceMinutes", wait).putInt("sessionLengthMinutes", duration).apply(); refresh()
            }.show()
    }

    private fun configureWarningText() {
        val input = android.widget.EditText(this).apply {
            hint = "Warning shown when an app first crosses its limit"
            setText(prefs.getString("warningText", "Bro, you've spent too much time here. Come back to your goal. ⚡"))
        }
        AlertDialog.Builder(this).setTitle("Focus warning message").setView(input).setNegativeButton("Cancel", null)
            .setPositiveButton("Save") { _, _ ->
                val value = input.text.toString().trim().take(240)
                if (value.isNotBlank()) prefs.edit().putString("warningText", value).apply()
            }.show()
    }

    private fun startSession() {
        if (!hasUsageAccess()) { explainUsageAccess(); return }
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(this, "Enable notifications before starting so focus warnings can reach you.", Toast.LENGTH_LONG).show()
            startActivity(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, packageName)); return
        }
        if (prefs.getStringSet("selected", emptySet()).isNullOrEmpty()) {
            Toast.makeText(this, "Select at least one app first.", Toast.LENGTH_LONG).show(); return
        }
        prefs.edit().putBoolean("enabled", true).apply()
        try { startForegroundService(Intent(this, UsageMonitorService::class.java).setAction(UsageMonitorService.ACTION_START)) }
        catch (_: Exception) { prefs.edit().putBoolean("enabled", false).apply(); Toast.makeText(this, "Android did not allow the monitor to start. Open SPARK and try again.", Toast.LENGTH_LONG).show() }
        refresh()
    }

    private fun showTodayUsage() {
        if (!hasUsageAccess()) { explainUsageAccess(); return }
        val selected = prefs.getStringSet("selected", emptySet()).orEmpty()
        val today = UsageMonitorService.todayUsage(this, selected)
        val rows = today.entries.sortedByDescending { it.value }.joinToString("\n") { (pkg, ms) -> "$pkg — ${ms / 60_000} min" }
        AlertDialog.Builder(this).setTitle("Today's selected-app usage")
            .setMessage(rows.ifBlank { "No usage data available yet. Android may take time to provide usage history." })
            .setPositiveButton("OK", null).show()
    }

    private fun showHistory() {
        val entries = prefs.getStringSet("history", emptySet()).orEmpty().sortedByDescending { it.substringAfterLast("·").trim().toLongOrNull() ?: 0L }
        AlertDialog.Builder(this).setTitle("Local focus history")
            .setMessage(entries.joinToString("\n") { it.substringBeforeLast("·").trim() }.ifBlank { "No warnings or interventions this session." })
            .setPositiveButton("OK", null).show()
    }

    private fun refresh() {
        if (!::status.isInitialized) return
        val enabled = prefs.getBoolean("enabled", false)
        status.text = "${usageAccessGuidance(hasUsageAccess())}\nFocus session: ${if (enabled) "enabled" else "off"}\nLimit: ${prefs.getInt("limitMinutes", 20)} minutes per selected app · warning grace: ${prefs.getInt("graceMinutes", 2)} minutes\nSession length: ${prefs.getInt("sessionLengthMinutes", 120)} minutes\nSession reset: when you end it or its configured session length elapses. Restart recovery uses Android usage-event history; OS/device gaps may affect totals."
        val selected = prefs.getStringSet("selected", emptySet()).orEmpty()
        apps.text = "Selected apps (${selected.size}):\n" + selected.sorted().joinToString("\n").ifBlank { "None yet — apps are never auto-selected." }
    }
}
