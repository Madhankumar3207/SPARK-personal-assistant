try:
    import speech_recognition as sr
    import time

except ImportError:
    sr = None




voice_unavailable_reported = False
last_listening_message = 0.0


def listen():

    global voice_unavailable_reported
    global last_listening_message

    if sr is None:

        if not voice_unavailable_reported:

            print(
                "SPARK: Voice support is not installed. "
                "Run: py -m pip install SpeechRecognition PyAudio"
            )

            voice_unavailable_reported = True

        return None

    recognizer = sr.Recognizer()

    try:

        with sr.Microphone() as source:

            if time.monotonic() - last_listening_message >= 10:

                print("🎤 Listening...")

                last_listening_message = time.monotonic()

            recognizer.adjust_for_ambient_noise(
                source,
                duration=1
            )

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=10
            )

    except sr.WaitTimeoutError:

        return ""

    except (OSError, AttributeError):

        if not voice_unavailable_reported:

            print("SPARK: Microphone is not available.")

            voice_unavailable_reported = True

        return None

    try:

        text = recognizer.recognize_google(audio)

        print(f"You: {text}")

        return text.lower().strip()

    except sr.UnknownValueError:

        return ""

    except sr.RequestError:

        return ""
