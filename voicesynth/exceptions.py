class VoiceSynthError(Exception):
    """
    Base class for Synthesizer exceptions.
    """

    pass


class IncorrectModel(VoiceSynthError):
    """
    Incorrect model parameters
    """

    pass


class IncorrectModelPath(IncorrectModel):
    """
    Incorrect model path
    """

    pass


class IncorrectSpeaker(IncorrectModel):
    """
    Incorrect speaker parameters
    """

    pass


class AudioError(VoiceSynthError):
    """
    Audio error
    """
    pass


class AudioPlayingError(AudioError):
    """
    Audio playing error
    """
    pass


class InvalidAudioFormat(AudioError):
    """
    Invalid audio formatting
    """
    pass


class InvalidAudioPath(AudioError):
    """
    Invalid path for audio playing
    """
    pass


class SynthesisError(AudioError):
    """
    Error synthesizing Audio
    """
    pass


class PackageError(VoiceSynthError):
    """
    Error in manual package installation
    """
    pass


class PackageInstallatioError(PackageError):
    """
    Class for package installation errors
    """
    pass
