"""Repeatable API-only preflight; never claims a UI or pitch-laptop rehearsal.

Run from the repository with its backend dependencies installed::

    python scripts/round3/rehearse_demo.py --output docs/round3/evidence/api-rehearsal.json

Add ``--full-output PATH`` to save a separate report with complete response bodies.
The default report stores response SHA-256 digests and compact results for review.

Uses an empty temporary SQLite DB, temporary rules/model files, recorded DemoClient
responses, and FastAPI TestClient. External IPv4/IPv6 connections and DNS are blocked
inside this process; loopback socket pairs are allowed for the Windows event loop.
The existing source files and their fixed requested dates are preserved.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import hashlib
import ipaddress
from importlib.metadata import PackageNotFoundError, version
import json
import math
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
from time import perf_counter
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    "emails/dk-odense-order.txt",
    "photos/se-handwritten-1.jpg",
    "excel/se-goteborg-materiallista.xlsx",
    "pdf/dk-nordhavn-materialeliste.pdf",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def stock_rows(body: dict) -> dict:
    return {
        (warehouse["code"], item["sku"]): warehouse
        for item in body["items"]
        for warehouse in item["warehouses"]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="JSON evidence file")
    parser.add_argument("--full-output", type=Path, help="Optional separate JSON report containing complete API responses")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    full_output = args.full_output
    if full_output is not None and not full_output.is_absolute():
        full_output = ROOT / full_output
    if full_output is not None and full_output.resolve() == output.resolve():
        parser.error("--full-output must differ from the compact --output file")
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    began = perf_counter()
    packages = {}
    for name in ("fastapi", "starlette", "httpx", "SQLAlchemy", "scikit-learn", "pypdf", "openpyxl"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = "not installed"
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    protected = [ROOT / "data/rules.json"]
    protected += sorted((ROOT / "samples/fixtures").glob("*.json"))
    protected += [ROOT / "samples/video-demo" / name for name in SOURCES]
    protected_hashes = {str(path.relative_to(ROOT)): digest(path) for path in protected}
    report = {
        "scope": "API technical preflight on the current computer; not the pitch laptop, browser UI, shell startup, or physical offline rehearsal",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_at_vietnam": datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds"),
        "git_revision": revision,
        "environment": {
            "os": platform.platform(), "python": platform.python_version(),
            "dependencies": packages, "ai_mode": "demo", "transport": "FastAPI TestClient (in process)",
            "inbox": "samples/video-demo", "database": "fresh temporary SQLite",
            "rules": "temporary copy; real GET/PUT API used without changing data/rules.json",
            "network": "process-level DNS and external IPv4/IPv6 sockets blocked; loopback allowed for the Windows event loop",
        },
        "protected_file_sha256": protected_hashes,
        "network_attempts": [], "allowed_loopback_operations": 0, "steps": [], "orders": [], "errors": [],
        "limitations": [
            "Current computer is not the laptop that will be taken to the pitch.",
            "No browser/UI, camera/screen recording, shell start command, or physical network disconnection verified.",
            "No Salesforce login/import or live CRM synchronization performed.",
            "API timings do not measure frontend rendering or production latency.",
        ],
    }
    full_steps = []

    def deny_dns(*_args, **_kwargs):
        report["network_attempts"].append({"operation": "DNS"})
        raise RuntimeError("External DNS disabled for the API preflight")

    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_sendto = socket.socket.sendto

    def deny_inet(original):
        def guarded(sock, *call_args, **call_kwargs):
            if sock.family in (socket.AF_INET, socket.AF_INET6):
                address = call_args[0] if original.__name__ != "sendto" else call_args[-1]
                try:
                    loopback = isinstance(address, tuple) and ipaddress.ip_address(address[0]).is_loopback
                except ValueError:
                    loopback = False
                if loopback:
                    report["allowed_loopback_operations"] += 1
                    return original(sock, *call_args, **call_kwargs)
                report["network_attempts"].append({"operation": original.__name__})
                raise RuntimeError("External IPv4/IPv6 network access disabled for the API preflight")
            return original(sock, *call_args, **call_kwargs)
        return guarded

    engine = None
    try:
        with tempfile.TemporaryDirectory(prefix="oneorder-api-rehearsal-") as directory, ExitStack() as stack:
            temporary = Path(directory)
            temporary_rules = temporary / "rules.json"
            shutil.copy2(ROOT / "data/rules.json", temporary_rules)
            stack.enter_context(patch.dict(os.environ, {
                "AI_MODE": "demo", "DATABASE_URL": f"sqlite:///{temporary / 'orders.db'}",
                "RULES_PATH": str(temporary_rules), "INBOX_DIR": str(ROOT / "samples/video-demo"),
            }))
            stack.enter_context(patch.object(socket, "getaddrinfo", deny_dns))
            stack.enter_context(patch.object(socket.socket, "connect", deny_inet(original_connect)))
            stack.enter_context(patch.object(socket.socket, "connect_ex", deny_inet(original_connect_ex)))
            stack.enter_context(patch.object(socket.socket, "sendto", deny_inet(original_sendto)))

            from fastapi.testclient import TestClient
            from backend.ai import get_ai_client
            from backend.db import engine as database_engine
            from backend.main import app
            from backend.services.eta import model as eta_model
            from backend.services.intake.demo_client import DemoClient
            from backend.services.matching import clear_catalog_cache
            from backend.services.orchestration import clear_rules_cache

            engine = database_engine
            model_source = eta_model.MODEL_PATH
            model_target = temporary / "model.joblib"
            if model_source.exists():
                shutil.copy2(model_source, model_target)
            stack.enter_context(patch.object(eta_model, "MODEL_PATH", model_target))
            eta_model.clear_model_cache()
            clear_catalog_cache()
            clear_rules_cache()
            previous_overrides = app.dependency_overrides.copy()
            app.dependency_overrides[get_ai_client] = lambda: DemoClient(ROOT / "samples/fixtures")
            stack.callback(lambda: (app.dependency_overrides.clear(), app.dependency_overrides.update(previous_overrides)))
            stack.callback(eta_model.clear_model_cache)
            stack.callback(clear_rules_cache)
            stack.callback(engine.dispose)

            with TestClient(app) as client:
                report["in_process_setup_ms"] = round((perf_counter() - began) * 1000, 2)

                def call(label: str, method: str, url: str, payload=None, expected=200):
                    started = perf_counter()
                    response = client.request(method, url, **({"json": payload} if payload is not None else {}))
                    elapsed = round((perf_counter() - started) * 1000, 2)
                    body = response.json()
                    step = {
                        "label": label, "method": method, "path": url,
                        "request_json": payload, "status_code": response.status_code,
                        "expected_status": expected, "duration_ms": elapsed,
                        "response_sha256": hashlib.sha256(response.content).hexdigest(),
                    }
                    if response.status_code >= 400:
                        step["response_json"] = body
                    report["steps"].append(step)
                    if full_output is not None:
                        full_steps.append({**step, "response_json": body})
                    require(response.status_code == expected, f"{label}: HTTP {response.status_code}, expected {expected}: {body}")
                    return body

                health = call("Health (demo)", "GET", "/api/health")
                require(health["ai_mode"] == "demo", "AI mode must be demo")
                inbox = call("List video inbox", "GET", "/api/inbox")
                require({item["id"] for item in inbox} == set(SOURCES), "Video inbox must contain exactly four sources")
                before = call("Stock before all confirmations", "GET", "/api/stock")
                imported = [call(f"Import {source}", "POST", "/api/inbox/import", {"id": source}) for source in SOURCES]
                confirmed = []
                total_allocations = defaultdict(float)

                for index, draft in enumerate(imported):
                    url = f"/api/orders/{draft['id']}"
                    order = call(f"Read order {index + 1}", "GET", url)
                    if index:
                        lines = [{
                            "line_index": line["line_index"], "sku": line["matched_sku"],
                            "description": line["description"],
                            "quantity": 25 if index == 2 and line["line_index"] == 2 else line["quantity"],
                            "confirmed": True if index in (1, 2) or line["line_index"] in (3, 4) else line["confirmed"],
                        } for line in order["lines"]]
                        correction = {"lines": lines}
                        if index == 1:
                            correction["customer_phone"] = "+46 70 555 12 34"
                        elif index == 2:
                            correction["customer"] = "Bygg Väst AB"
                        else:
                            correction["customer"] = "Lars Byg ApS"
                        order = call(f"Review/Edit draft order {index + 1}", "PATCH", url, correction)
                    approved = call(f"Approve order {index + 1}", "POST", url + "/approve", {})
                    require(approved["status"] == "approved", "Approval did not persist")
                    if index == 2:
                        call("Excel rejects missing site", "POST", url + "/plan", {}, expected=422)
                    plan_payload = {"site_id": "SITE-SE-02"} if index == 2 else {}
                    plan = call(f"Plan order {index + 1}", "POST", url + "/plan", plan_payload)
                    require(plan["fully_sourced"] and not plan["shortages"], "Initial plan must fully source the order")
                    require(plan.get("order_eta") is not None, "ETA unavailable")

                    if index == 3:
                        require(any(s["cross_border"] for s in plan["shipments"]), "PDF should source cross-border")
                        require(any(s["crane_required"] for s in plan["shipments"]), "PDF should require crane")
                        rules = call("Read temporary rules", "GET", "/api/rules")
                        rules["sourcing"]["allow_cross_border"] = False
                        call("Disable cross-border in temporary rules", "PUT", "/api/rules", rules)
                        shortage = call("PDF re-plan cross-border disabled", "POST", url + "/plan", {})
                        require(not shortage["fully_sourced"] and shortage["shortages"], "Disabling cross-border must show shortages")
                        require({"TIM-SE-PINE45", "ARM-BEAM-HEA200"} <= {s["sku"] for s in shortage["shortages"]}, "PDF shortage SKUs differ from script")
                        rules["sourcing"]["allow_cross_border"] = True
                        call("Restore cross-border in temporary rules", "PUT", "/api/rules", rules)
                        plan = call("PDF re-plan cross-border restored", "POST", url + "/plan", {})
                        require(plan["fully_sourced"] and not plan["shortages"], "Restored rules must fully source PDF")
                        for earlier in confirmed:
                            frozen = call("Read earlier confirmed plan after rules change", "GET", f"/api/orders/{earlier['id']}")
                            require(frozen["plan"] == earlier["plan"], "Rules edit changed a confirmed plan")

                    late = plan["order_eta"]["risk"] == "late"
                    if late:
                        rejection = call(f"Order {index + 1} rejects unaccepted late risk", "POST", url + "/confirm", {}, expected=409)
                        require("accept_late_risk" in rejection["detail"], "Expected late-risk confirmation guard")
                    final = call(f"Confirm order {index + 1}", "POST", url + "/confirm", {"accept_late_risk": True} if late else {})
                    require(final["status"] == "confirmed", "Confirm did not persist")
                    require(final["plan"] == plan, "Confirm changed the planned commitment")
                    planned_quantities = defaultdict(float)
                    reserved_quantities = defaultdict(float)
                    for shipment in plan["shipments"]:
                        for line in shipment["lines"]:
                            key = (shipment["origin_warehouse"], line["sku"])
                            planned_quantities[key] += line["quantity"]
                            total_allocations[key] += line["quantity"]
                    for reservation in final["reservations"]:
                        reserved_quantities[(reservation["warehouse_code"], reservation["sku"])] += reservation["quantity"]
                    require(planned_quantities == reserved_quantities, "Reservations do not match plan allocations")
                    confirmed.append(final)
                    report["orders"].append({
                        "id": final["id"], "source": SOURCES[index], "customer": final["customer"],
                        "customer_phone": final["customer_phone"], "status": final["status"],
                        "site_id": plan["site"]["id"], "requested_date": final["requested_date"],
                        "eta": plan["order_eta"], "accept_late_risk": late,
                        "shipment_count": len(plan["shipments"]), "reservations": final["reservations"],
                    })

                after = call("Stock after all confirmations", "GET", "/api/stock")
                opening, closing = stock_rows(before), stock_rows(after)
                deltas = []
                for (warehouse, sku), quantity in sorted(total_allocations.items()):
                    first, last = opening[(warehouse, sku)], closing[(warehouse, sku)]
                    require(math.isclose(first["available"] - last["available"], quantity), f"Available delta incorrect: {warehouse}/{sku}")
                    require(math.isclose(last["reserved"] - first["reserved"], quantity), f"Reserved delta incorrect: {warehouse}/{sku}")
                    deltas.append({"warehouse": warehouse, "sku": sku, "newly_reserved": quantity,
                                   "available_before": first["available"], "available_after": last["available"],
                                   "reserved_before": first["reserved"], "reserved_after": last["reserved"]})
                report["stock_deltas"] = deltas
                report["stock_verified"] = True
                report["confirmed_orders"] = len(confirmed)
                require(len(confirmed) == 4, "Must confirm all four orders")
                require(not report["network_attempts"], "Application attempted network access")
    except Exception as exc:
        report["errors"].append({"type": type(exc).__name__, "message": str(exc)})
    finally:
        if engine is not None:
            engine.dispose()
        changed = [name for name, before_hash in protected_hashes.items() if digest(ROOT / name) != before_hash]
        report["protected_files_unchanged"] = not changed
        if changed:
            report["errors"].append({"type": "ProtectedFileChanged", "files": changed})
        report["total_duration_ms"] = round((perf_counter() - began) * 1000, 2)
        report["result"] = "passed" if not report["errors"] else "failed"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if full_output is not None:
            full_output.parent.mkdir(parents=True, exist_ok=True)
            full_output.write_text(json.dumps({**report, "steps": full_steps}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"result": report["result"], "confirmed_orders": report.get("confirmed_orders", 0),
                      "api_steps": len(report["steps"]), "report": str(output), "errors": report["errors"]}, ensure_ascii=False))
    return 0 if report["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
