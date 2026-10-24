import http.client
import os
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterator, Optional, Tuple

from voicesynth.exceptions import ModelDownloadError

_CA_BUNDLES = (
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/ssl/certs/ca-bundle.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
    "/etc/ssl/cert.pem",
)

_TRANSIENT = (OSError, http.client.HTTPException)


def _ssl_contexts() -> Iterator[ssl.SSLContext]:
    yield ssl.create_default_context()
    try:
        import certifi

        yield ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for bundle in _CA_BUNDLES:
        if os.path.isfile(bundle):
            yield ssl.create_default_context(cafile=bundle)


def _open(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 60) -> Any:
    request_headers = {"User-Agent": "voicesynth"}
    request_headers.update(headers or {})
    last_error: Optional[urllib.error.URLError] = None
    for context in _ssl_contexts():
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=request_headers), context=context, timeout=timeout
            )
        except urllib.error.HTTPError:
            raise
        except urllib.error.URLError as error:
            if not isinstance(error.reason, ssl.SSLError):
                raise
            last_error = error
    assert last_error is not None
    raise ModelDownloadError(f"SSL verification failed for {url}: {last_error.reason}")


def _progress(done: int, total: int) -> None:
    if total:
        percent = done * 100 // total
        bar = "#" * (percent // 4)
        sys.stderr.write(f"\r[{bar:<25}] {percent:3d}% {done / 1e6:.1f}/{total / 1e6:.1f} MB")
    else:
        sys.stderr.write(f"\r{done / 1e6:.1f} MB")
    sys.stderr.flush()


def _parse_total(response: Any, offset: int) -> Tuple[int, int]:
    status = getattr(response, "status", 200)
    length = int(response.headers.get("Content-Length") or 0)
    if status == 206:
        content_range = response.headers.get("Content-Range", "")
        total_text = content_range.rsplit("/", 1)[-1]
        total = int(total_text) if total_text.isdigit() else offset + length
        return offset, total
    return 0, length


def _attempt(url: str, partial: str, show_progress: bool) -> None:
    offset = os.path.getsize(partial) if os.path.exists(partial) else 0
    headers = {"Range": f"bytes={offset}-"} if offset else {}

    try:
        response = _open(url, headers)
    except urllib.error.HTTPError as error:
        if error.code == 416 and offset:
            os.remove(partial)
            return _attempt(url, partial, show_progress)
        raise

    with response:
        offset, total = _parse_total(response, offset)
        mode = "ab" if offset else "wb"
        done = offset
        with open(partial, mode) as output:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                output.write(chunk)
                done += len(chunk)
                if show_progress:
                    _progress(done, total)

    if total and done != total:
        raise http.client.IncompleteRead(b"", total - done)


def download_file(url: str, destination: str, show_progress: bool = True, retries: int = 4, backoff: float = 1.0) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
    partial = f"{destination}.part"
    last_error: Optional[BaseException] = None

    try:
        for attempt in range(retries + 1):
            try:
                _attempt(url, partial, show_progress)
                break
            except urllib.error.HTTPError as error:
                if error.code < 500:
                    raise ModelDownloadError(f"Could not download {url}: HTTP {error.code}") from error
                last_error = error
            except ModelDownloadError:
                raise
            except _TRANSIENT as error:
                last_error = error
            if attempt < retries:
                time.sleep(min(2 ** attempt, 8) * backoff)
        else:
            raise ModelDownloadError(
                f"Could not download {url}: {last_error}. Run again to resume from {partial}"
            ) from last_error
        shutil.move(partial, destination)
    finally:
        if show_progress:
            sys.stderr.write("\n")
