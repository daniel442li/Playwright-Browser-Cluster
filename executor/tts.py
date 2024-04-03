import pyttsx3

def text_to_speech_instant(text):
    engine = pyttsx3.init()  # Initialize the converter
    engine.say(text)  # Add the text you want to convert to speech
    engine.runAndWait()  # Process and play the speech

