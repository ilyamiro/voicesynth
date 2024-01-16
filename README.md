<h2>VoiceSynth</h2> 
<strong>Voice Synthesizing Library</strong> <br>

<h3> How to use: </h3>
First, install the package

```bash
pip install voicesynth
```
Then import it into your code and go ahead and use it:
```python
from voicesynth import Model, Synthesizer, show_available_models

show_available_models() # Showcase of all tts models available

# initializing the model
# setting show_download to False does not show model downloading progress
model = Model("v4_ru", model_path="model.pt", show_download=False)  
model.set_speaker("eugene")

# creating a synthesizer instance
synthesizer = Synthesizer(model)
synthesizer.say("Я представить себе не могу, что это действительно случилось!")
```
Instead of using .say() method, you can synthesize an audio and then play it whenever you want

```python
import time

synthesizer.synthesize("Всем привет!", path="audio.wav")
time.sleep(3)
synthesizer.play_playsound("audio.wav")
```
There are multiple ways to play a synthesized audio:
```python
synthesizer.say("Как дела?", module="pygame") # Using pygame.mixer to play the audio
synthesizer.say("Хорошо, а твои как?", module="pydub") # Using pydub to play the audio
```
There are three ways to play the audio:
```python
synthesizer.audio.play_playsound("audio.wav")
synthesizer.audio.play_pygame("audio.wav")
synthesizer.audio.play_pydub("audio.wav")
```
All models support simple ssml tags:
```python
synthesizer.say("В н+едрах т+ундры в+ыдры п+ели п+есни", prosody_rate=90)   
# I added prosody as a parameter, so that people who are not familiar with ssml tags
# could change speaking speed without knowing how to manually do it
```

By default, logging is enabled. If it bothers you, you can disable it
```python
from voicesynth import disable_logging

disable_logging()
```
