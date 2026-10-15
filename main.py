import speech_recognition as sr
import pyttsx3
import requests
from urllib.parse import quote


recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        print("Listening...")

        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(
            source, 
            timeout=5, 
            phrase_time_limit = 10
        )

    return audio

def recognize_speech(audio):
    command = recognizer.recognize_google(audio)
    print("You said:", command)
    return command.lower().strip()

def get_answer(question):

    search_url = "https://en.wikipedia.org/w/rest.php/v1/search/page"

    headers = {
        "User-Agent": "JarvisVoiceAssisstant/1.0"
    }

    params = {
        "q": question,
        "limit": 1
    }

    response = requests.get(
        search_url,
        headers = headers,
        params = params,
        timeout = 10
    )

    response.raise_for_status()

    results = response.json()["pages"]

    if not results:
        return "Sorry, I couldn't find an answer."

    title = results[0]["title"]
    safe_title = quote(title.replace(" ","_"), safe = "()")

    summary_url = (
        "https://en.wikipedia.org/api/rest_v1/page/summary/" + safe_title
    )

    response = requests.get(
        summary_url,
        headers = headers,
        timeout= 10
    )

    response.raise_for_status()
    data = response.json()

    answer = data.get("extract", "")

    if not answer:
        return "Sorry, I couldn't find a summary,"

    sentences = answer.split(". ")
    return ". ".join(sentences[:3])

if __name__ == "__main__":

    speak("Initializing Jarvis.... Ask me a question...")

    while True:
        try:
            audio = listen()
            command = recognize_speech(audio)

            if command in ("exit", "quit", "stop", "bye"):
                speak("Godspeed Boss!")
                break

            answer = get_answer(command)
            speak(answer)

        except sr.WaitTimeoutError:
            print("I didn't hear anything. Try again.")

        except sr.UnknownValueError:
            speak("Sorry, I couldn't understand you.")

        except sr.RequestError as e:
            print("Speech recognition error:", e)
            speak("I didn't get you sir...do you mind repeating??")

        except requests.RequestException as e:
            print("Wikipedia request error:", e)
            speak("Sorry, I couldn't retrieve an answer.")

        except KeyboardInterrupt:
            print("\nShutting down.")
            break