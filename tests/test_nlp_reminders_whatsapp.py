import tempfile
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from agents.brain import understand_command
from backend.services import nlp, reminders, whatsapp
from tools import router
from memory import context as memory
from main import process_user_command
from backend.services.diagnostics import classify_result


class SPARKUpgradeTests(unittest.TestCase):
    def setUp(self):
        # Keep test DBs inside the writable project tree; sandboxed Windows
        # temp directories may be protected from the test process.
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.original_db = reminders.DB_PATH
        reminders.DB_PATH = Path(self.temp.name) / "test.sqlite3"
        reminders.initialize()

    def tearDown(self):
        reminders.DB_PATH = self.original_db
        self.temp.cleanup()

    def test_intent_variants_and_clarification(self):
        self.assertEqual(nlp.interpret("Hello SPARK, how are you?")["intent"], "conversation")
        self.assertEqual(nlp.interpret("En pending tasks enna?")["intent"], "list_tasks")
        parsed = nlp.interpret("Remind me tomorrow at 5 PM to submit my assignment")
        self.assertEqual(parsed["intent"], "create_reminder")
        self.assertEqual(parsed["entities"]["timezone"], "Asia/Kolkata")
        ambiguous = nlp.interpret("Remind me tomorrow to submit my assignment")
        self.assertTrue(ambiguous["clarification"])
        tanglish = nlp.interpret("Naalaikku evening 5 manikku assignment submit panna remind pannu")
        self.assertEqual(tanglish["intent"], "create_reminder")
        self.assertIn("assignment submit", tanglish["entities"]["title"])
        self.assertEqual(datetime.fromisoformat(tanglish["entities"]["scheduled_at"]).hour, 17)
        self.assertEqual(understand_command("shutdown computer")["action"], "POWER_CONTROL_DISABLED")

    def test_typos_greetings_memory_and_app_routing(self):
        cases = {
            "hi bro": "hi",
            "bro": "hello",
            "heyyyy": "hey",
            "wwhat is mmy name": "what is my name",
            "what is my nnamme": "what is my name",
            "find my resme": "find my resume",
            "open calculater": "open calculator",
            "the second one": "open second",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                normalized = nlp.normalize_language(raw)
                self.assertEqual(normalized, expected)
        self.assertEqual(understand_command(nlp.normalize_language("open calculater"))["target"], "calculator")
        self.assertEqual(nlp.interpret("who am i")["intent"], "recall")
        self.assertNotEqual(nlp.interpret("why i am")["intent"], "recall")
        self.assertEqual(nlp.interpret("my name is Madhankumar")["entities"]["value"], "Madhankumar")
        self.assertEqual(nlp.interpret("naalaiku assignment submit panna remind pannu")["intent"], "create_reminder")
        self.assertTrue(nlp.interpret("naalaiku assignment submit panna remind pannu")["clarification"])
        self.assertEqual(nlp.interpret("what can you do")["intent"], "conversation")
        self.assertEqual(nlp.interpret("find my resume and open it")["intent"], "existing_file_command")
        self.assertEqual(nlp.interpret("show pending works and finish the first one")["intent"], "ambiguous")
        self.assertEqual(nlp.interpret("Show pending tasks. Also find my resume.")["intent"], "ambiguous")
        self.assertIn("C:\\Users\\Madhan\\My resme.docx", nlp.normalize_language("open C:\\Users\\Madhan\\My resme.docx"))

    def test_memory_reports_failed_persistence_without_false_success(self):
        original_file = memory.MEMORY_FILE
        memory.MEMORY_FILE = Path(self.temp.name) / "memory.json"
        try:
            self.assertIn("remember", memory.remember("name", "Madhankumar").lower())
            self.assertEqual(memory.load_memory()["name"], "Madhankumar")
            self.assertIn("Madhankumar", process_user_command("who i am"))
            with mock.patch.object(memory, "save_memory", return_value=False):
                self.assertIn("couldn't save", memory.remember("city", "Chennai"))
            self.assertEqual(memory.load_memory()["name"], "Madhankumar")
        finally:
            memory.MEMORY_FILE = original_file

    def test_chat_and_voice_mode_controls_remain_mutually_exclusive(self):
        import main
        old_voice, old_chat = main.voice_enabled.is_set(), main.chat_enabled.is_set()
        try:
            main.voice_enabled.clear(); main.chat_enabled.set()
            with mock.patch.object(main, "start_voice_listener"):
                main.process_user_command("chat off")
                self.assertTrue(main.voice_enabled.is_set())
                self.assertFalse(main.chat_enabled.is_set())
                main.process_user_command("voice off")
                self.assertFalse(main.voice_enabled.is_set())
                self.assertTrue(main.chat_enabled.is_set())
        finally:
            main.voice_enabled.set() if old_voice else main.voice_enabled.clear()
            main.chat_enabled.set() if old_chat else main.chat_enabled.clear()

    def test_api_result_classification_does_not_claim_failed_actions_succeeded(self):
        self.assertEqual(classify_result("Opening Chrome.")[0], True)
        self.assertEqual(classify_result("I couldn't find any matching files.")[1], "not_found_or_unsupported_target")
        self.assertEqual(classify_result("Please tell me what you want me to open.")[1], "clarification_required")

    def test_power_variants_stay_disabled_and_normal_sleep_talk_is_not_a_command(self):
        for phrase in ("shutdown computer", "put my laptop to sleep", "restart my pc", "sign me out", "turn my computer off"):
            with self.subTest(phrase=phrase):
                self.assertEqual(nlp.interpret(phrase)["intent"], "disabled_power_control")
        self.assertNotEqual(nlp.interpret("tell me about sleep mode")["intent"], "disabled_power_control")
        self.assertEqual(process_user_command("put my laptop to sleep"), "I don't have computer power controls enabled.")

    def test_targeted_nlp_calculator_pattern_and_power_regressions(self):
        original_memory_file = memory.MEMORY_FILE
        memory.MEMORY_FILE = Path(self.temp.name) / "identity-memory.json"
        try:
            memory.remember("name", "Madhankumar")
            self.assertIn("Madhankumar", process_user_command("wha i am"))
            self.assertIn("Madhankumar", process_user_command("tell me who i am"))
        finally:
            memory.MEMORY_FILE = original_memory_file

        self.assertEqual(process_user_command("calculate 24*50"), "Answer: 1200")
        pattern = process_user_command("analyse 1 3 5 7")
        self.assertTrue("arithmetic progression" in pattern.lower() or "arithmetic sequence" in pattern.lower())
        self.assertIn("+2", pattern)
        self.assertIn("9", pattern)

        protected = (
            "shutdown computer", "ahutdown computer", "shut down computer",
            "restart computer", "lock computer", "sleep computer",
            "hibernate computer", "sign out",
        )
        with mock.patch.object(router, "learn_and_execute") as learn:
            for phrase in protected:
                with self.subTest(power_phrase=phrase):
                    self.assertEqual(
                        process_user_command(phrase),
                        "I don't have computer power controls enabled.",
                    )
            learn.assert_not_called()

    def test_unknown_harmless_command_still_uses_controlled_learning(self):
        with mock.patch.object(router, "learn_and_execute", return_value="controlled learning") as learn:
            self.assertEqual(process_user_command("invent a teleportation device"), "controlled learning")
        learn.assert_called_once_with("invent a teleportation device")

    def test_latest_follow_up_uses_search_context_and_context_expires(self):
        import os
        first = Path(self.temp.name) / "old.txt"
        second = Path(self.temp.name) / "new.txt"
        first.write_text("old")
        second.write_text("new")
        os.utime(first, (100, 100)); os.utime(second, (200, 200))
        router._remember_search_results([first, second])
        opened = []
        original_startfile = getattr(os, "startfile", None)
        os.startfile = lambda path: opened.append(path)
        try:
            self.assertIn("new.txt", router.open_search_result("latest one"))
            self.assertEqual(opened, [str(second)])
            router._remember_search_results([first, second])
            self.assertIn("new.txt", router.open_search_result("second"))
            self.assertEqual(opened[-1], str(second))
            router._remember_search_results([first])
            router.last_search_results_at = 0
            self.assertEqual(router.open_search_result("first"), "Please search for a file first.")
        finally:
            if original_startfile is None:
                del os.startfile
            else:
                os.startfile = original_startfile

    def test_reminder_persistence_dedup_and_claim_once(self):
        scheduled = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
        first, created = reminders.create_reminder("Submit work", scheduled, "Asia/Kolkata", dedupe_key="same-action")
        duplicate, duplicate_created = reminders.create_reminder("Submit work", scheduled, "Asia/Kolkata", dedupe_key="same-action")
        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(first["id"], duplicate["id"])
        due_at = datetime.fromisoformat(scheduled).astimezone(timezone.utc) + timedelta(seconds=1)
        claimed = reminders.claim_due(due_at)
        self.assertEqual(len(claimed), 1)
        self.assertEqual(reminders.claim_due(due_at), [])
        self.assertEqual(reminders.list_reminders()[0]["status"], "delivered")

    def test_whatsapp_parse_and_duplicate_import(self):
        export = (
            "[12/10/26, 9:30 AM] Kavin: Bro, submit the project report tomorrow at 3 PM.\n"
            "continued in a second line\n"
            "[12/10/26, 10:00 AM] Kavin: Please bring the document next week.\n"
        ).encode("utf-8-sig")
        messages = whatsapp.parse_export("chat.txt", export)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["sender"], "Kavin")
        self.assertIn("second line", messages[0]["text"])
        first = whatsapp.analyze_export("chat.txt", export)
        second = whatsapp.analyze_export("chat.txt", export)
        self.assertEqual(len(first), 2)
        self.assertEqual([item["id"] for item in first], [item["id"] for item in second])
        self.assertTrue(any(item["needs_clarification"] for item in first))
        with self.assertRaises(ValueError):
            whatsapp.parse_export("chat.pdf", export)
        with self.assertRaises(ValueError):
            whatsapp.parse_export("chat.txt", b"x" * (whatsapp.MAX_CHAT_BYTES + 1))


if __name__ == "__main__":
    unittest.main()
