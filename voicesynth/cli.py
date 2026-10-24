import argparse
import sys
from typing import List, Optional

from voicesynth import __version__
from voicesynth.exceptions import VoiceSynthError
from voicesynth.log import disable_logging
from voicesynth.models import DEFAULT_MODEL, get_model_info, show_available_models


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="voicesynth", description="Realistic offline voice synthesis")
    parser.add_argument("--version", action="version", version=f"voicesynth {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    listing = commands.add_parser("models", help="list available models")
    listing.add_argument("-l", "--language", help="filter by language")

    speakers = commands.add_parser("speakers", help="list speakers of a model")
    speakers.add_argument("model")

    say = commands.add_parser("say", help="synthesize text and play it")
    say.add_argument("text", nargs="?", help="text to say, read from stdin when omitted")
    say.add_argument("-m", "--model", default=DEFAULT_MODEL)
    say.add_argument("-s", "--speaker")
    say.add_argument("-o", "--output", help="save audio to this .wav file")
    say.add_argument("--no-play", action="store_true", help="do not play the audio")
    say.add_argument("--rate", type=int, default=100, help="speaking speed in percent")
    say.add_argument("--sample-rate", type=int, default=48000, choices=(8000, 24000, 48000))
    say.add_argument("--ssml", action="store_true", help="treat the text as SSML")
    say.add_argument("--model-path", help="where the model file is stored")
    say.add_argument("--threads", type=int)
    say.add_argument("--quiet", action="store_true", help="disable logging")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    arguments = _parser().parse_args(argv)

    if arguments.command == "models":
        show_available_models(arguments.language)
        return 0

    if arguments.command == "speakers":
        try:
            info = get_model_info(arguments.model)
        except VoiceSynthError as error:
            print(error, file=sys.stderr)
            return 1
        print("\n".join(info["speakers"]))
        return 0

    if arguments.quiet:
        disable_logging()

    if arguments.no_play and not arguments.output:
        print("--no-play requires --output", file=sys.stderr)
        return 2

    text = arguments.text if arguments.text is not None else sys.stdin.read()

    try:
        from voicesynth.voicesynth import Model, Synthesizer

        model = Model(arguments.model, arguments.model_path, speaker=arguments.speaker)
        synthesizer = Synthesizer(model, threads=arguments.threads, sample_rate=arguments.sample_rate)
        if arguments.no_play:
            synthesizer.synthesize(text, arguments.output, arguments.rate, ssml=arguments.ssml)
        else:
            synthesizer.say(text, arguments.output, arguments.rate, ssml=arguments.ssml)
    except VoiceSynthError as error:
        print(f"voicesynth: {error}", file=sys.stderr)
        return 1
    return 0
