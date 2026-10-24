import os
import shutil
import ssl
import sys
import urllib.error
import urllib.request

from voicesynth.exceptions import ModelDownloadError

_CA_BUNDLES = (
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/ssl/certs/ca-bundle.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
    "/etc/ssl/cert.pem",
)


def _ssl_contexts():
    yield ssl.create_default_context()
    try:
        import certifi

        yield ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for bundle in _CA_BUNDLES:
        if os.path.isfile(bundle):
            yield ssl.create_default_context(cafile=bundle)


def _open(url: str):
    last_error = None
    for context in _ssl_contexts():
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "voicesynth"}), context=context, timeout=60
            )
        except urllib.error.HTTPError as error:
            raise ModelDownloadError(f"Could not download {url}: HTTP {error.code}") from error
        except urllib.error.URLError as error:
            if not isinstance(error.reason, ssl.SSLError):
                raise ModelDownloadError(f"Could not download {url}: {error.reason}") from error
            last_error = error
    raise ModelDownloadError(f"SSL verification failed for {url}: {last_error.reason}")


def _progress(done: int, total: int) -> None:
    if total:
        percent = done * 100 // total
        bar = "#" * (percent // 4)
        sys.stderr.write(f"\r[{bar:<25}] {percent:3d}% {done / 1e6:.1f}/{total / 1e6:.1f} MB")
    else:
        sys.stderr.write(f"\r{done / 1e6:.1f} MB")
    sys.stderr.flush()


def download_file(url: str, destination: str, show_progress: bool = True) -> None:
    directory = os.path.dirname(os.path.abspath(destination))
    os.makedirs(directory, exist_ok=True)
    partial = f"{destination}.part"

    try:
        with _open(url) as response, open(partial, "wb") as output:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                output.write(chunk)
                done += len(chunk)
                if show_progress:
                    _progress(done, total)
        if total and done != total:
            raise ModelDownloadError(f"Incomplete download of {url}: got {done} of {total} bytes")
        shutil.move(partial, destination)
    except BaseException:
        if os.path.exists(partial):
            os.remove(partial)
        raise
    finally:
        if show_progress:
            sys.stderr.write("\n")
