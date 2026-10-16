import pyttsx3

engine = pyttsx3.init()

answer = (
    "Donald Trump is an American politician."
     


)

print("Speaking now...")
engine.say(answer)
engine.runAndWait()
print("Speech call completed.")