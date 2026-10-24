package com.spark.wellbeing

import org.junit.Assert.*
import org.junit.Test

class FocusPolicyTest {
    private val instagram = "com.instagram.android"
    private val games = setOf(instagram, "com.example.game")
    private val limit = 60_000L

    @Test fun unselectedAppDoesNothing() {
        assertFalse(FocusPolicy.evaluate(games, "com.example.chat", mapOf("com.example.chat" to 999_000L), limit, 30_000L, 10L, FocusState()).warning)
    }

    @Test fun thresholdWarnsExactlyOnce() {
        val first = FocusPolicy.evaluate(games, instagram, mapOf(instagram to limit), limit, 30_000L, 10L, FocusState())
        assertTrue(first.warning)
        val repeated = FocusPolicy.evaluate(games, instagram, mapOf(instagram to limit + 10_000), limit, 30_000L, 20L, first.state)
        assertFalse(repeated.warning)
        assertFalse(repeated.intervene)
    }

    @Test fun leavingAndReturningTriggersOneIntervention() {
        val warned = FocusPolicy.evaluate(games, instagram, mapOf(instagram to limit), limit, 30_000L, 10L, FocusState()).state
        val away = FocusPolicy.evaluate(games, "com.example.work", mapOf(instagram to limit), limit, 30_000L, 20L, warned).state
        val returned = FocusPolicy.evaluate(games, instagram, mapOf(instagram to limit), limit, 30_000L, 30L, away)
        assertTrue(returned.intervene)
        assertFalse(FocusPolicy.evaluate(games, instagram, mapOf(instagram to limit), limit, 30_000L, 40L, returned.state).intervene)
    }

    @Test fun gracePeriodTriggersOneIntervention() {
        val warned = FocusPolicy.evaluate(games, instagram, mapOf(instagram to limit), limit, 30_000L, 100L, FocusState()).state
        assertTrue(FocusPolicy.evaluate(games, instagram, mapOf(instagram to limit), limit, 30_000L, 30_100L, warned).intervene)
    }

    @Test fun newSessionResetsState() {
        val fresh = FocusState()
        assertFalse(FocusPolicy.evaluate(games, instagram, mapOf(instagram to limit), limit, 30_000L, 10L, fresh).state.intervened)
    }

    @Test fun disabledOrUnpermittedMonitoringDoesNothing() {
        val current = FocusState(warned = true, warningPackage = instagram, warningAtMs = 10L)
        assertEquals(current, FocusPolicy.evaluate(games, instagram, mapOf(instagram to limit), limit, 0L, 50L, current, enabled = false).state)
        assertFalse(FocusPolicy.evaluate(games, instagram, mapOf(instagram to limit), limit, 0L, 50L, current, permissionGranted = false).intervene)
    }

    @Test fun missingUsageAccessShowsSetupInstructions() {
        assertTrue(usageAccessGuidance(false).contains("Settings"))
        assertTrue(usageAccessGuidance(true).contains("granted"))
    }
}
