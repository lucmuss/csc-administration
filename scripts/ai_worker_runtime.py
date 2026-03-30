#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def utc_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append_human_log(log_file: str | None, line: str) -> None:
    if not log_file:
        print(line)
        return
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line)


def log_json(level: str, phase: str, message: str, *, issue: int = 0, log_file: str | None = None, json_log_file: str | None = None) -> None:
    ts = utc_ts()
    if json_log_file:
        Path(json_log_file).parent.mkdir(parents=True, exist_ok=True)
        with open(json_log_file, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"ts": ts, "level": level, "phase": phase, "issue": issue, "msg": message}, ensure_ascii=True) + "\n")
    append_human_log(log_file, f"[{ts}] [{level}] [{phase}] {message}")


def cleanup_artifacts(artifact_root: str, max_age_days: int = 14, max_total_mb: int = 2000) -> None:
    root = Path(artifact_root)
    root.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - max_age_days * 86400
    for child in root.glob("issue-*"):
        try:
            if child.is_dir() and child.stat().st_mtime < cutoff:
                shutil.rmtree(child, ignore_errors=True)
        except FileNotFoundError:
            pass

    size_mb = get_dir_size_mb(root)
    if size_mb > max_total_mb:
        issue_dirs = sorted((p for p in root.glob("issue-*") if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in issue_dirs[19:]:
            shutil.rmtree(old, ignore_errors=True)


def get_dir_size_mb(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        try:
            if child.is_file():
                total += child.stat().st_size
        except FileNotFoundError:
            continue
    return total // (1024 * 1024)


def acquire_lock(lock_file: str, max_wait: int = 300, stale_after: int = 1800, *, issue: int = 0, log_file: str | None = None, json_log_file: str | None = None) -> None:
    path = Path(lock_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    waited = 0
    while path.exists():
        try:
            lock_age = int(time.time() - path.stat().st_mtime)
        except FileNotFoundError:
            break
        if lock_age > stale_after:
            log_json("WARN", "lock", f"Breaking stale worker lock aged {lock_age}s", issue=issue, log_file=log_file, json_log_file=json_log_file)
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            break
        if waited >= max_wait:
            raise SystemExit(f"Could not acquire worker lock after {max_wait}s")
        time.sleep(10)
        waited += 10
    path.write_text(str(os.getpid()), encoding="utf-8")
    log_json("INFO", "lock", f"Acquired worker lock at {lock_file}", issue=issue, log_file=log_file, json_log_file=json_log_file)


def release_lock(lock_file: str, *, issue: int = 0, log_file: str | None = None, json_log_file: str | None = None) -> None:
    path = Path(lock_file)
    if path.exists():
        path.unlink()
        log_json("INFO", "lock", f"Released worker lock at {lock_file}", issue=issue, log_file=log_file, json_log_file=json_log_file)


def run_cmd(command: list[str], *, timeout: int | None = None) -> tuple[int, str]:
    proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def preflight_checks(*, runner_env_file: str | None, forgejo_api_base: str, repo_url: str | None, site_domain: str, require_openai: bool) -> list[str]:
    errors: list[str] = []

    _, df_out = run_cmd(["bash", "-lc", "df -m /home/skymuss | awk 'NR==2 {print $4}'"])
    try:
        available_mb = int(df_out.strip().splitlines()[-1])
        if available_mb < 1000:
            errors.append(f"Disk space low: {available_mb}MB available")
    except Exception:
        errors.append("Could not determine available disk space")

    for cmd in ("python3", "curl", "jq", "timeout", "git"):
        code, _ = run_cmd(["bash", "-lc", f"command -v {cmd} >/dev/null 2>&1"])
        if code != 0:
            errors.append(f"Required command not found: {cmd}")

    env_blob = ""
    if runner_env_file and Path(runner_env_file).exists():
        env_blob = Path(runner_env_file).read_text(encoding="utf-8")
    if require_openai and not os.getenv("OPENAI_API_KEY"):
        errors.append("OPENAI_API_KEY missing")
    if not any((os.getenv("OPENAI_API_KEY"), "OPENROUTER_API_KEY=" in env_blob)):
        errors.append("No AI API keys configured")

    try:
        socket.getaddrinfo(site_domain, 443)
    except socket.gaierror:
        errors.append(f"DNS resolution failed for {site_domain}")

    try:
        request_json(f"{forgejo_api_base.rstrip('/')}/version")
    except Exception:
        errors.append(f"Cannot reach Forgejo API at {forgejo_api_base}")

    if repo_url:
        code, _ = run_cmd(["git", "ls-remote", "--exit-code", repo_url, "HEAD"], timeout=20)
        if code != 0:
            errors.append("Cannot reach repository remote")

    return errors


@dataclass
class ForgejoClient:
    base: str
    repo: str
    token: str

    def _url(self, path: str) -> str:
        return f"{self.base.rstrip('/')}/repos/{self.repo}{path}"

    def request(self, path: str, *, method: str = "GET", data: Any | None = None) -> Any:
        body = None if data is None else json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            self._url(path),
            method=method,
            data=body,
            headers={"Authorization": f"token {self.token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else None

    def labels(self) -> dict[str, int]:
        data = self.request("/labels")
        return {item["name"]: int(item["id"]) for item in data}

    def transition_label(self, issue: int, remove: list[str], add: list[str]) -> None:
        labels = self.labels()
        issue_data = self.request(f"/issues/{issue}")
        current_names = [item["name"] for item in issue_data.get("labels", [])]
        target_names = [name for name in current_names if name not in remove]
        for name in add:
            if name in labels and name not in target_names:
                target_names.append(name)
        target_ids = [labels[name] for name in target_names if name in labels]
        self.request(f"/issues/{issue}/labels", method="PUT", data={"labels": target_ids})

    def patch_issue(self, issue: int, *, state: str | None = None, title: str | None = None, body: str | None = None) -> None:
        payload: dict[str, Any] = {}
        if state is not None:
            payload["state"] = state
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        self.request(f"/issues/{issue}", method="PATCH", data=payload)

    def comment(self, issue: int, body: str) -> None:
        self.request(f"/issues/{issue}/comments", method="POST", data={"body": body})

    def create_pr(self, *, title: str, body: str, head: str, base_branch: str) -> dict[str, Any]:
        return self.request("/pulls", method="POST", data={"title": title, "body": body, "head": head, "base": base_branch})

    def merge_pr(self, pr_number: int, *, merge_message: str) -> Any:
        return self.request(f"/pulls/{pr_number}/merge", method="POST", data={"Do": "merge", "merge_message_field": merge_message})


def request_json(url: str) -> Any:
    with urllib.request.urlopen(url) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else None


def build_success_summary(issue: int, start_ts_file: str, tool_name: str, diff_base: str) -> str:
    start = int(Path(start_ts_file).read_text(encoding="utf-8").strip())
    duration = max(0, int(time.time()) - start)
    files = subprocess.check_output(["git", "diff", "--name-only", f"{diff_base}...HEAD"], text=True).splitlines()
    numstat_lines = subprocess.check_output(["git", "diff", "--numstat", f"{diff_base}...HEAD"], text=True).splitlines()
    insertions = 0
    deletions = 0
    for line in numstat_lines:
        if not line.strip():
            continue
        a, b, *_ = line.split("\t")
        if a.isdigit():
            insertions += int(a)
        if b.isdigit():
            deletions += int(b)
    diffstat = subprocess.check_output(["git", "diff", "--stat", f"{diff_base}...HEAD"], text=True).strip() or "No diffstat available."
    return "\n".join(
        [
            f"## AI Worker — Issue #{issue} abgeschlossen",
            "",
            "| Metrik | Wert |",
            "|--------|------|",
            f"| Dauer | {duration // 60}m {duration % 60}s |",
            f"| Dateien geaendert | {len(files)} |",
            f"| Zeilen hinzugefuegt | +{insertions} |",
            f"| Zeilen entfernt | -{deletions} |",
            f"| Tool | {tool_name} |",
            f"| Branch | `ai/issue-{issue}` -> merged |",
            "",
            "<details>",
            "<summary>Geaenderte Dateien</summary>",
            "",
            "```",
            diffstat,
            "```",
            "</details>",
        ]
    )


def parse_refinement_response(response_file: str, issue_title: str, refined_output: str, json_output: str, body_output: str) -> None:
    import re

    raw = Path(response_file).read_text(encoding="utf-8").strip()
    if not raw:
        raise SystemExit("Refine response was empty.")

    match = re.match(r"^```(?:json|markdown|md|text)?\n(.*)\n```$", raw, re.S)
    cleaned = match.group(1).strip() if match else raw

    payload: dict[str, Any] | None = None
    try:
        loaded = json.loads(cleaned)
        if isinstance(loaded, dict):
            payload = loaded
    except json.JSONDecodeError:
        payload = None

    if payload is None:
        brace_match = re.search(r"\{.*\}", cleaned, re.S)
        if brace_match:
            loaded = json.loads(brace_match.group(0))
            if isinstance(loaded, dict):
                payload = loaded

    if payload is None:
        raise SystemExit("Could not parse refinement output.")

    title = str(payload.get("title") or "").strip() or issue_title.strip()
    body = str(payload.get("body") or "").strip()
    if not body:
        raise SystemExit("Refined issue body is empty.")

    Path(refined_output).write_text(body + "\n", encoding="utf-8")
    Path(body_output).write_text(body + "\n", encoding="utf-8")
    Path(json_output).write_text(json.dumps({"title": title, "body": body}), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("cleanup-artifacts")
    c.add_argument("--artifact-root", required=True)
    c.add_argument("--max-age-days", type=int, default=14)
    c.add_argument("--max-total-mb", type=int, default=2000)

    c = sub.add_parser("log")
    c.add_argument("--level", required=True)
    c.add_argument("--phase", required=True)
    c.add_argument("--message", required=True)
    c.add_argument("--issue", type=int, default=0)
    c.add_argument("--log-file")
    c.add_argument("--json-log-file")

    c = sub.add_parser("acquire-lock")
    c.add_argument("--lock-file", required=True)
    c.add_argument("--max-wait", type=int, default=300)
    c.add_argument("--stale-after", type=int, default=1800)
    c.add_argument("--issue", type=int, default=0)
    c.add_argument("--log-file")
    c.add_argument("--json-log-file")

    c = sub.add_parser("release-lock")
    c.add_argument("--lock-file", required=True)
    c.add_argument("--issue", type=int, default=0)
    c.add_argument("--log-file")
    c.add_argument("--json-log-file")

    c = sub.add_parser("preflight")
    c.add_argument("--runner-env-file")
    c.add_argument("--forgejo-api-base", required=True)
    c.add_argument("--repo-url")
    c.add_argument("--site-domain", default="forgejo.kolibri-kollektiv.eu")
    c.add_argument("--require-openai", action="store_true")

    c = sub.add_parser("label-transition")
    c.add_argument("--base", required=True)
    c.add_argument("--repo", required=True)
    c.add_argument("--token", required=True)
    c.add_argument("--issue", type=int, required=True)
    c.add_argument("--remove", action="append", default=[])
    c.add_argument("--add", action="append", default=[])

    c = sub.add_parser("patch-issue")
    c.add_argument("--base", required=True)
    c.add_argument("--repo", required=True)
    c.add_argument("--token", required=True)
    c.add_argument("--issue", type=int, required=True)
    c.add_argument("--state")
    c.add_argument("--title")
    c.add_argument("--body-file")

    c = sub.add_parser("comment")
    c.add_argument("--base", required=True)
    c.add_argument("--repo", required=True)
    c.add_argument("--token", required=True)
    c.add_argument("--issue", type=int, required=True)
    group = c.add_mutually_exclusive_group(required=True)
    group.add_argument("--body")
    group.add_argument("--body-file")

    c = sub.add_parser("create-pr")
    c.add_argument("--base", required=True)
    c.add_argument("--repo", required=True)
    c.add_argument("--token", required=True)
    c.add_argument("--title", required=True)
    group = c.add_mutually_exclusive_group(required=True)
    group.add_argument("--body")
    group.add_argument("--body-file")
    c.add_argument("--head", required=True)
    c.add_argument("--base-branch", required=True)

    c = sub.add_parser("merge-pr")
    c.add_argument("--base", required=True)
    c.add_argument("--repo", required=True)
    c.add_argument("--token", required=True)
    c.add_argument("--pr-number", type=int, required=True)
    c.add_argument("--merge-message", required=True)

    c = sub.add_parser("success-summary")
    c.add_argument("--issue", type=int, required=True)
    c.add_argument("--start-ts-file", required=True)
    c.add_argument("--tool-name", required=True)
    c.add_argument("--diff-base", default="refs/cache/origin/main")

    c = sub.add_parser("parse-refinement")
    c.add_argument("--response-file", required=True)
    c.add_argument("--issue-title", required=True)
    c.add_argument("--refined-output", required=True)
    c.add_argument("--json-output", required=True)
    c.add_argument("--body-output", required=True)

    c = sub.add_parser("json-field")
    c.add_argument("--json-file", required=True)
    c.add_argument("--field", required=True)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cmd == "cleanup-artifacts":
        cleanup_artifacts(args.artifact_root, args.max_age_days, args.max_total_mb)
        return
    if args.cmd == "log":
        log_json(args.level, args.phase, args.message, issue=args.issue, log_file=args.log_file, json_log_file=args.json_log_file)
        return
    if args.cmd == "acquire-lock":
        acquire_lock(args.lock_file, args.max_wait, args.stale_after, issue=args.issue, log_file=args.log_file, json_log_file=args.json_log_file)
        return
    if args.cmd == "release-lock":
        release_lock(args.lock_file, issue=args.issue, log_file=args.log_file, json_log_file=args.json_log_file)
        return
    if args.cmd == "preflight":
        errors = preflight_checks(
            runner_env_file=args.runner_env_file,
            forgejo_api_base=args.forgejo_api_base,
            repo_url=args.repo_url,
            site_domain=args.site_domain,
            require_openai=args.require_openai,
        )
        if errors:
            print("\n".join(errors))
            raise SystemExit(1)
        print("Pre-flight checks passed")
        return
    if args.cmd in {"label-transition", "patch-issue", "comment", "create-pr", "merge-pr"}:
        client = ForgejoClient(args.base, args.repo, args.token)
        if args.cmd == "label-transition":
            client.transition_label(args.issue, args.remove, args.add)
            return
        if args.cmd == "patch-issue":
            body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else None
            client.patch_issue(args.issue, state=args.state, title=args.title, body=body)
            return
        if args.cmd == "comment":
            body = args.body if args.body is not None else Path(args.body_file).read_text(encoding="utf-8")
            client.comment(args.issue, body)
            return
        if args.cmd == "create-pr":
            body = args.body if args.body is not None else Path(args.body_file).read_text(encoding="utf-8")
            result = client.create_pr(title=args.title, body=body, head=args.head, base_branch=args.base_branch)
            print(json.dumps(result, ensure_ascii=True))
            return
        if args.cmd == "merge-pr":
            result = client.merge_pr(args.pr_number, merge_message=args.merge_message)
            print(json.dumps(result, ensure_ascii=True))
            return
    if args.cmd == "success-summary":
        print(build_success_summary(args.issue, args.start_ts_file, args.tool_name, args.diff_base))
        return
    if args.cmd == "parse-refinement":
        parse_refinement_response(args.response_file, args.issue_title, args.refined_output, args.json_output, args.body_output)
        return
    if args.cmd == "json-field":
        payload = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
        value = payload.get(args.field, "")
        if isinstance(value, (dict, list)):
            print(json.dumps(value, ensure_ascii=True))
        else:
            print(value)
        return


if __name__ == "__main__":
    main()
