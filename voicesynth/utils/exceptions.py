
class VoiceSynthError(Exception):
    """
    Base class for Synthesizer exceptions.
    """
    def __init__(self, message: str):
        super().__init__(message)


class IncorrectModel(VoiceSynthError):
    """
    Incorrect model parameters
    """
    def __init__(self, message: str):
        super().__init__(message)


class IncorrectModelPath(IncorrectModel):
    """
    Incorrect model path
    """
    def __init__(self, message: str):
        super().__init__(message)


class IncorrectSpeaker(IncorrectModel):
    """
    Incorrect speaker parameters
    """
    def __init__(self, message: str):
        super().__init__(message)


class AudioError(VoiceSynthError):
    """
    Audio error
    """
    def __init__(self, message: str):
        super().__init__(message)


class AudioPlayingError(AudioError):
    """
    Audio playing error
    """
    def __init__(self, message: str):
        super().__init__(message)


class InvalidAudioFormat(AudioError):
    """
    Invalid audio formatting
    """
    def __init__(self, message: str):
        super().__init__(message)


class InvalidAudioPath(AudioError):
    """
    Invalid path for audio playing
    """
    def __init__(self, message: str):
        super().__init__(message)


class SynthesisError(AudioError):
    """
    Error synthesizing Audio
    """
    def __init__(self, message: str):
        super().__init__(message)


class PackageError(VoiceSynthError):
    """
    Error in manual package installation
    """
    def __init__(self, message: str):
        super().__init__(message)


class PackageInstallatioError(PackageError):
    """
    Class for package installation errors
    """
    def __init__(self, message: str):
        super().__init__(message)