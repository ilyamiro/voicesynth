import io
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import pytest

import voicesynth.voicesynth as core
from voicesynth.log import logger


def make_package(size: int = 4096) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("tts_models/model.pkl", bytes(range(256)) * (size // 256))
    return buffer.getvalue()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        return

    def do_GET(self):
        server = self.server
        server.requests.append(dict(self.headers))
        payload = server.files.get(self.path)
        if payload is None:
            self.send_error(404)
            return
        if server.fail_status and server.fail_budget > 0:
            server.fail_budget -= 1
            self.send_error(server.fail_status)
            return

        start = 0
        header = self.headers.get("Range")
        if header and server.support_range:
            start = int(header.split("=")[1].split("-")[0])
            if start >= len(payload):
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{len(payload)}")
                self.end_headers()
                return
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(payload) - 1}/{len(payload)}")
        else:
            self.send_response(200)
        body = payload[start:]
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        if server.truncate_budget > 0:
            server.truncate_budget -= 1
            self.wfile.write(body[: len(body) // 2])
            self.wfile.flush()
            self.close_connection = True
            return
        self.wfile.write(body)


class FileServer(ThreadingHTTPServer):
    def __init__(self):
        super().__init__(("127.0.0.1", 0), Handler)
        self.files = {}
        self.requests = []
        self.support_range = True
        self.truncate_budget = 0
        self.fail_status = 0
        self.fail_budget = 0
        self.thread = threading.Thread(target=self.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()

    def url(self, path):
        return f"http://127.0.0.1:{self.server_address[1]}{path}"


@pytest.fixture
def server():
    instance = FileServer()
    yield instance
    instance.shutdown()
    instance.server_close()


@pytest.fixture
def package():
    return make_package()


@pytest.fixture(autouse=True)
def quiet_logging():
    logger.disabled = True
    yield
    logger.disabled = False


@pytest.fixture
def cache_home(tmp_path, monkeypatch):
    home = tmp_path / "cache"
    monkeypatch.setenv("VOICESYNTH_HOME", str(home))
    return home


class FakeEngine:
    def __init__(self, speakers=None):
        self.speakers = speakers if speakers is not None else ["aidar", "baya", "random"]
        self.calls = []
        self.device = None

    def to(self, device):
        self.device = device

    def apply_tts(self, **kwargs):
        self.calls.append(kwargs)
        text = kwargs.get("text") or kwargs.get("ssml_text")
        return np.full(max(1, len(text)) * 10, 0.5, dtype=np.float32)


@pytest.fixture
def engine():
    return FakeEngine()


@pytest.fixture
def fake_model(cache_home, server, package, monkeypatch):
    from voicesynth.models import models

    server.files["/v3_es.pt"] = package
    monkeypatch.setitem(models["v3_es"], "url", server.url("/v3_es.pt"))
    return "v3_es"


@pytest.fixture
def synthesizer(fake_model, engine, monkeypatch):
    monkeypatch.setattr(core, "_load_engine", lambda path, device, threads: engine)
    model = core.Model(fake_model, show_download=False)
    return core.Synthesizer(model, sample_rate=8000, pause=0.1)


