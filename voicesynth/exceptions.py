class VoiceSynthError(Exception):
    pass


class IncorrectModel(VoiceSynthError):
    pass


class IncorrectModelPath(IncorrectModel):
    pass


class IncorrectSpeaker(IncorrectModel):
    pass


class AudioError(VoiceSynthError):
    pass


class AudioPlayingError(AudioError):
    pass


class InvalidAudioFormat(AudioError):
    pass


class InvalidAudioPath(AudioError):
    pass


class SynthesisError(AudioError):
    pass


class PackageError(VoiceSynthError):
    pass


class PackageInstallationError(PackageError):
    pass


class ModelDownloadError(VoiceSynthError):
    pass


class ModelIntegrityError(ModelDownloadError):
    pass


PackageInstallatioError = PackageInstallationError
