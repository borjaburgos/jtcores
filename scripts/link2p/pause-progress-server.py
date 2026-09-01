#!/usr/bin/env python3
"""Serve a read-only LAN dashboard for private Link2P pause simulations."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


CASE_NAME = re.compile(r"^[a-z0-9_-]+$")


def read_key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(errors="replace").splitlines()
    except FileNotFoundError:
        return values
    for line in lines:
        for token in line.split():
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            if key:
                values[key] = value
    return values


def integer(value: str | None, default: int = 0) -> int:
    try:
        return int(value or default)
    except ValueError:
        return default


class ProgressModel:
    def __init__(self, artifact_root: Path):
        self.artifact_root = artifact_root.resolve()

    def latest_run(self) -> Path | None:
        candidates = [
            path
            for path in self.artifact_root.glob("pause-*")
            if path.is_dir() and (path / "plan.txt").is_file()
        ]
        return max(candidates, key=lambda path: (path / "plan.txt").stat().st_mtime, default=None)

    def status(self) -> dict[str, object]:
        run = self.latest_run()
        if run is None:
            return {
                "state": "waiting",
                "message": "Waiting for the first pause experiment run.",
                "cases": [],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        plan = read_key_values(run / "plan.txt")
        requested = integer(plan.get("requested_frames"))
        case_names = [name for name in plan.get("cases", "").split() if CASE_NAME.fullmatch(name)]
        cases: list[dict[str, object]] = []
        newest_mtime = (run / "plan.txt").stat().st_mtime

        for name in case_names:
            case_root = run / name
            progress_path = case_root / "frames" / "progress.txt"
            pause_result_path = case_root / "pause-result.txt"
            final_result_path = case_root / "result.txt"
            progress = read_key_values(progress_path)
            pause_result = read_key_values(pause_result_path)
            final_result = read_key_values(final_result_path)
            relative_frame = integer(progress.get("relative_frame"), -1)
            recorded_frames = integer(progress.get("recorded_frames"))
            percent = 0.0
            if requested > 0:
                basis = max(relative_frame, recorded_frames, 0)
                percent = min(100.0, 100.0 * basis / requested)

            if final_result_path.is_file():
                case_state = "pass" if final_result.get("observable_rejoin") == "PASS" else "fail"
            elif pause_result.get("result") == "FAIL":
                case_state = "fail"
            elif pause_result.get("result") == "PASS":
                case_state = "verified"
            elif progress:
                case_state = "running"
            elif (case_root / "run.log").is_file():
                case_state = "starting"
            else:
                case_state = "queued"

            for path in (progress_path, pause_result_path, final_result_path, case_root / "run.log"):
                if path.exists():
                    newest_mtime = max(newest_mtime, path.stat().st_mtime)

            cases.append(
                {
                    "name": name,
                    "hold_frames": integer(progress.get("hold_frames"), integer(name.removeprefix("hold_"))),
                    "state": case_state,
                    "phase": progress.get("phase", "queued"),
                    "relative_frame": relative_frame,
                    "recorded_frames": recorded_frames,
                    "requested_frames": requested,
                    "verified_frames": integer(progress.get("verified_frames")),
                    "requested_verify_frames": integer(plan.get("pause_verify_frames")),
                    "latest_crc32": progress.get("latest_crc32", "—"),
                    "percent": round(percent, 1),
                    "result_reason": pause_result.get("reason", ""),
                    "has_preview": (case_root / "frames" / "latest-a.ppm").is_file()
                    and (case_root / "frames" / "latest-b.ppm").is_file(),
                }
            )

        top_result = read_key_values(run / "result.txt")
        if top_result.get("result") == "PASS":
            state = "pass"
            message = "All staggered pause cases visibly rejoined."
        elif any(case["state"] == "fail" for case in cases):
            state = "fail"
            message = "At least one pause duration failed to rejoin."
        elif any(case["state"] in {"running", "starting", "verified"} for case in cases):
            state = "running"
            message = "Simulation is running. Preview divergence is expected during staggered holds."
        else:
            state = "building"
            message = "Compiling the dual-JTBUBL Verilator model."

        return {
            "state": state,
            "message": message,
            "run": run.name,
            "commit": plan.get("jtcores_commit", "unknown")[:12],
            "pause_start_frame": integer(plan.get("pause_start_frame")),
            "settle_frames": integer(plan.get("pause_settle_frames")),
            "verify_frames": integer(plan.get("pause_verify_frames")),
            "cases": cases,
            "updated_at": datetime.fromtimestamp(newest_mtime, timezone.utc).isoformat(),
        }

    def preview(self, case_name: str, side: str) -> bytes | None:
        run = self.latest_run()
        if run is None or not CASE_NAME.fullmatch(case_name) or side not in {"a", "b"}:
            return None
        plan = read_key_values(run / "plan.txt")
        if case_name not in plan.get("cases", "").split():
            return None
        path = run / case_name / "frames" / f"latest-{side}.ppm"
        try:
            return path.read_bytes()
        except FileNotFoundError:
            return None


def handler_factory(model: ProgressModel, dashboard: bytes):
    class Handler(BaseHTTPRequestHandler):
        def send_body(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:",
            )
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self.send_body(HTTPStatus.OK, "text/html; charset=utf-8", dashboard)
                return
            if parsed.path == "/api/status":
                body = json.dumps(model.status(), separators=(",", ":")).encode()
                self.send_body(HTTPStatus.OK, "application/json", body)
                return
            if parsed.path == "/api/preview":
                query = parse_qs(parsed.query)
                content = model.preview(query.get("case", [""])[0], query.get("side", [""])[0])
                if content is None:
                    self.send_body(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", b"preview unavailable\n")
                else:
                    self.send_body(HTTPStatus.OK, "image/x-portable-pixmap", content)
                return
            self.send_body(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", b"not found\n")

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    if not args.artifact_root.is_dir():
        raise SystemExit(f"artifact root does not exist: {args.artifact_root}")
    dashboard_path = Path(__file__).with_name("pause-dashboard.html")
    dashboard = dashboard_path.read_bytes()
    server = ThreadingHTTPServer((args.bind, args.port), handler_factory(ProgressModel(args.artifact_root), dashboard))
    print(f"Link2P pause dashboard listening on http://{args.bind}:{args.port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
