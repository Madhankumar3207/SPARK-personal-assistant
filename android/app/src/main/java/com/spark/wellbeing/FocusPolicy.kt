package com.spark.wellbeing

/** Pure deterministic two-stage policy. Elapsed-realtime values drive grace-period checks. */
data class FocusState(
    val warned: Boolean = false,
    val warningPackage: String? = null,
    val warningAtMs: Long = 0,
    val leftAfterWarning: Boolean = false,
    val intervened: Boolean = false,
    val lastInterventionAtMs: Long = 0,
)

data class PolicyResult(val state: FocusState, val warning: Boolean = false, val intervene: Boolean = false)

object FocusPolicy {
    fun evaluate(
        selectedPackages: Set<String>,
        foregroundPackage: String?,
        usageMsByPackage: Map<String, Long>,
        limitMs: Long,
        graceMs: Long,
        nowMs: Long,
        state: FocusState,
        enabled: Boolean = true,
        permissionGranted: Boolean = true,
    ): PolicyResult {
        if (!enabled || !permissionGranted) return PolicyResult(state)
        val active = selectedPackages.firstOrNull { usageMsByPackage[it]?.let { ms -> ms >= limitMs } == true }
            ?: return PolicyResult(if (state.warned && foregroundPackage != state.warningPackage) state.copy(leftAfterWarning = true) else state)

        if (!state.warned) {
            return PolicyResult(FocusState(true, active, nowMs, false, false, 0), warning = true)
        }
        if (state.intervened) return PolicyResult(state)

        val left = state.leftAfterWarning || (foregroundPackage != null && foregroundPackage != state.warningPackage)
        val returned = left && foregroundPackage == state.warningPackage
        val graceExpired = foregroundPackage == state.warningPackage && nowMs - state.warningAtMs >= graceMs
        return if (returned || graceExpired) {
            PolicyResult(state.copy(leftAfterWarning = left, intervened = true, lastInterventionAtMs = nowMs), intervene = true)
        } else PolicyResult(state.copy(leftAfterWarning = left))
    }
}

fun usageAccessGuidance(granted: Boolean): String = if (granted) {
    "Usage Access is granted. Monitoring is limited to apps selected by you."
} else {
    "Usage Access is not granted. Tap Explain and grant Usage Access, then enable SPARK in Android Settings → Special app access → Usage access."
}
