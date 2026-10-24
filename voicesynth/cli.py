import argparse
import sys
from typing import List, Optional

from voicesynth import __version__, cache
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
    speakers.add_argument("--load", action="store_true", help="download and load the model to list its real speakers")

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
    say.add_argument("--max-chars", type=int, default=500, help="split text into chunks of at most this length")
    say.add_argument("--pause", type=float, default=0.25, help="seconds of silence between chunks")
    say.add_argument("--quiet", action="store_true", help="disable logging")

    store = commands.add_parser("cache", help="manage downloaded models")
    actions = store.add_subparsers(dest="action", required=True)
    actions.add_parser("list", help="show downloaded models")
    actions.add_parser("path", help="print the cache directory")
    fetch = actions.add_parser("download", help="download models without using them")
    fetch.add_argument("models", nargs="+")
    remove = actions.add_parser("remove", help="delete downloaded models")
    remove.add_argument("models", nargs="+")
    check = actions.add_parser("verify", help="check integrity of downloaded models")
    check.add_argument("models", nargs="*")
    actions.add_parser("clear", help="delete every downloaded model")
    return parser


def _human(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def _cache(arguments: argparse.Namespace) -> int:
    if arguments.action == "path":
        print(cache.cache_dir())
    elif arguments.action == "list":
        entries = cache.cached_models()
        if not entries:
            print("No models downloaded")
        for entry in entries:
            print(f"{entry.name:<24} {_human(entry.size):>10}  {entry.path}")
    elif arguments.action == "download":
        for name in arguments.models:
            print(cache.download(name))
    elif arguments.action == "remove":
        for name in arguments.models:
            print(f"{name}: {'removed' if cache.remove(name) else 'not downloaded'}")
    elif arguments.action == "verify":
        names = arguments.models or [entry.name for entry in cache.cached_models()]
        failed = False
        for name in names:
            try:
                cache.verify(name)
                print(f"{name}: ok")
            except VoiceSynthError as error:
                failed = True
                print(f"{name}: {error}")
        return 1 if failed else 0
    elif arguments.action == "clear":
        print(f"Removed {cache.clear()} models")
    return 0


def _speakers(arguments: argparse.Namespace) -> int:
    info = get_model_info(arguments.model)
    if arguments.load:
        from voicesynth.voicesynth import Model

        names = Model(arguments.model).fetch_speakers()
    else:
        names = info["speakers"]
        if not info["exhaustive"]:
            print("# incomplete list, use --load for every speaker", file=sys.stderr)
    print("\n".join(names))
    return 0


def _say(arguments: argparse.Namespace) -> int:
    if arguments.no_play and not arguments.output:
        print("--no-play requires --output", file=sys.stderr)
        return 2
    if arguments.quiet:
        disable_logging()

    text = arguments.text if arguments.text is not None else sys.stdin.read()

    from voicesynth.voicesynth import Model, Synthesizer

    model = Model(arguments.model, arguments.model_path, speaker=arguments.speaker)
    synthesizer = Synthesizer(
        model,
        threads=arguments.threads,
        sample_rate=arguments.sample_rate,
        max_chars=arguments.max_chars,
        pause=arguments.pause,
    )
    if arguments.no_play:
        synthesizer.synthesize(text, arguments.output, arguments.rate, ssml=arguments.ssml)
    else:
        synthesizer.say(text, arguments.output, arguments.rate, ssml=arguments.ssml)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    arguments = _parser().parse_args(argv)

    try:
        if arguments.command == "models":
            show_available_models(arguments.language)
            return 0
        if arguments.command == "speakers":
            return _speakers(arguments)
        if arguments.command == "cache":
            return _cache(arguments)
        return _say(arguments)
    except VoiceSynthError as error:
        print(f"voicesynth: {error}", file=sys.stderr)
        return 1
