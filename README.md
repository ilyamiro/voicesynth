README for voicesynth <br>
<strong>Voice Synthesizing Library</strong>
## How to use:
First, install the package
```
pip install voicesynth
```
Then import it into your code and go ahead and use it:
```python
from voicesynth import Model, Synthesizer, show_available_models

show_available_models() # Showcase of all tts models available

# initializing the model
model = Model("v4_ru")
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
synthesizer.play("audio.wav")
```
All models support simple ssml tags:
```python
synthesizer.say("В н+едрах т+ундры в+ыдры п+ели п+есни", prosody_rate=90)   
# I added prosody as a parameter, so that people who are not familiar with ssml tags
# could change speaking speed without knowing how to manually do it
```

By default, logging is enabled. If it bothers you, you can set logging to False.
```python
import voicesynth

voicesynth.logging_enabled(False)
```
