#!/usr/bin/env python3
"""通过 QQ 官方机器人向个人用户（C2C）发送文件/图片/文本的命令行工具。

为什么存在：官方 SDK 只封装了 URL 直传，未封装本地文件分片上传；
本工具补齐本地文件上传，并以一次性 CLI 供 agent 通过 bash 直接调用。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import requests
import websocket

# 接口地址与协议常量
API_BASE_URL = "https://api.sgroup.qq.com"
TOKEN_REFRESH_URL = "https://bots.qq.com/app/getAppAccessToken"
C2C_INTENTS = 1 << 25
C2C_EVENT = "C2C_MESSAGE_CREATE"
READY_EVENT = "READY"
HELLO_OP = 10
IDENTIFY_OP = 2
HEARTBEAT_OP = 1
PREFIX_10M_BYTES = 10002432
MAX_FILE_SIZE = 200 * 1024 * 1024
READ_CHUNK_BYTES = 1024 * 1024
FILE_TYPE_IMAGE = 1
FILE_TYPE_FILE = 4
MSG_TYPE_TEXT = 0
MSG_TYPE_MEDIA = 7

CONFIG_DIR = Path.home() / ".qq-send"
CONFIG_PATH = CONFIG_DIR / "config.json"
TOKEN_PATH = CONFIG_DIR / "token.json"
OPENID_PATH = CONFIG_DIR / "openid.json"


@dataclass
class Config:
    """机器人凭据配置。"""

    appid: str
    client_secret: str


def mask(value: str) -> str:
    """脱敏显示 appid。"""
    if len(value) <= 6:
        return value[:1] + "****"
    return f"{value[:4]}****{value[-2:]}"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config() -> Config:
    """从 config.json 与环境变量读取凭据，缺失时报错退出。"""
    data = _read_json(CONFIG_PATH) or {}
    appid = os.environ.get("QQ_BOT_APPID") or data.get("appid")
    secret = os.environ.get("QQ_BOT_SECRET") or data.get("client_secret")
    if not appid or not secret:
        raise SystemExit(
            f"缺少 appid/client_secret，请写入 {CONFIG_PATH} "
            "或设置环境变量 QQ_BOT_APPID / QQ_BOT_SECRET"
        )
    return Config(appid=str(appid), client_secret=str(secret))


def get_access_token(config: Config) -> str:
    """返回可用 access_token，本地缓存过期时自动刷新。"""
    cached = _read_json(TOKEN_PATH) or {}
    token = cached.get("access_token")
    if token and time.time() < float(cached.get("expires_at", 0)):
        return str(token)
    response = requests.post(
        TOKEN_REFRESH_URL,
        json={"appId": config.appid, "clientSecret": config.client_secret},
        timeout=10,
    )
    if response.status_code != 200:
        raise RuntimeError(f"刷新 access_token 失败: {response.status_code} {response.text}")
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("access_token 响应缺失字段")
    expires_in = int(payload.get("expires_in", 7200))
    _write_json(TOKEN_PATH, {"access_token": token, "expires_at": time.time() + expires_in - 60})
    return str(token)


def auth_headers(config: Config) -> dict[str, str]:
    return {"Authorization": f"QQBot {get_access_token(config)}", "Content-Type": "application/json"}


def http_request(
    config: Config,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """请求官方 API 并解析 JSON，非 200 统一抛错。"""
    url = f"{API_BASE_URL}{path}"
    kwargs: dict[str, Any] = {"headers": auth_headers(config), "timeout": timeout}
    if method == "GET":
        response = requests.get(url, **kwargs)
    else:
        kwargs["json"] = payload
        response = requests.post(url, **kwargs)
    if response.status_code != 200:
        raise RuntimeError(f"{method} {path} 失败: {response.status_code} {response.text}")
    return response.json() or {}


def new_msg_seq() -> int:
    """生成主动消息去重序号。"""
    return (int(time.time() * 1000) % 100000000) % 65536


def _recv_json(ws: websocket.WebSocket) -> dict[str, Any] | None:
    """收一帧并解析，超时返回 None。"""
    try:
        raw = ws.recv()
    except Exception:
        return None
    return json.loads(raw) if raw else None


def open_gateway(config: Config) -> tuple[websocket.WebSocket, float]:
    """连接网关完成鉴权，收到 READY 后返回连接与心跳间隔秒数。"""
    gateway = http_request(config, "GET", "/gateway", timeout=10)
    ws_url = gateway.get("url")
    if not ws_url:
        raise RuntimeError("网关响应缺少 url")
    ws = websocket.create_connection(ws_url, timeout=30)
    hello = json.loads(ws.recv())
    heartbeat_s = int(hello["d"]["heartbeat_interval"]) / 1000.0
    ws.send(
        json.dumps(
            {
                "op": IDENTIFY_OP,
                "d": {
                    "token": f"QQBot {get_access_token(config)}",
                    "intents": C2C_INTENTS,
                    "shard": [0, 1],
                },
            }
        )
    )
    ws.settimeout(0.2)
    deadline = time.time() + 15
    while time.time() < deadline:
        packet = _recv_json(ws)
        if packet and packet.get("t") == READY_EVENT:
            return ws, heartbeat_s
    ws.close()
    raise RuntimeError("网关鉴权超时，未收到 READY")


def wait_event(
    ws: websocket.WebSocket,
    heartbeat_s: float,
    target: str,
    timeout: float,
) -> dict[str, Any] | None:
    """循环收包直到命中目标事件或超时，期间发送心跳。"""
    deadline = time.time() + timeout
    next_beat = time.time() + heartbeat_s
    while time.time() < deadline:
        now = time.time()
        if now >= next_beat:
            ws.send(json.dumps({"op": HEARTBEAT_OP, "d": None}))
            next_beat = now + heartbeat_s
        packet = _recv_json(ws)
        if packet and packet.get("t") == target:
            return packet.get("d") or {}
    return None


def capture_openid(config: Config, timeout: float) -> tuple[str, str] | None:
    """连接网关等待一次 C2C 私聊，解析并缓存 openid。"""
    ws, heartbeat_s = open_gateway(config)
    try:
        event = wait_event(ws, heartbeat_s, C2C_EVENT, timeout)
    finally:
        ws.close()
    if not event:
        return None
    author = event.get("author") or {}
    openid = author.get("user_openid")
    if not openid:
        return None
    username = str(author.get("username") or "unknown")
    _write_json(OPENID_PATH, {"openid": openid, "username": username, "updated_at": time.time()})
    return str(openid), username


def resolve_openid(explicit: str | None) -> str:
    """优先用显式 openid，否则读缓存，都没有则提示先 listen。"""
    if explicit:
        return explicit.strip()
    cached = _read_json(OPENID_PATH) or {}
    openid = cached.get("openid")
    if openid:
        return str(openid)
    raise SystemExit("未找到目标用户 openid：请先运行 listen 捕获，或传 --openid")


def compute_digests(path: Path) -> tuple[str, str, str]:
    """返回 (全文 md5, 全文 sha1, 前 10MB md5)。"""
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    md5_10m = hashlib.md5()
    remaining = PREFIX_10M_BYTES
    with path.open("rb") as handle:
        while chunk := handle.read(READ_CHUNK_BYTES):
            md5.update(chunk)
            sha1.update(chunk)
            if remaining > 0:
                md5_10m.update(chunk[:remaining])
                remaining -= len(chunk)
    return md5.hexdigest(), sha1.hexdigest(), md5_10m.hexdigest()


def _upload_part(
    config: Config,
    openid: str,
    upload_id: str,
    part: dict[str, Any],
    chunk: bytes,
) -> None:
    """PUT 单个分片到预签名 URL，并通知平台该分片完成。"""
    index = int(part["index"])
    part_size = int(part["block_size"])
    put = requests.put(part["presigned_url"], data=chunk, timeout=120)
    if put.status_code not in (200, 204):
        raise RuntimeError(f"分片 {index} PUT 失败: {put.status_code}")
    http_request(
        config,
        "POST",
        f"/v2/users/{openid}/upload_part_finish",
        {
            "upload_id": upload_id,
            "part_index": index,
            "block_size": str(part_size),
            "md5": hashlib.md5(chunk).hexdigest(),
        },
    )


def upload_local_file(config: Config, openid: str, path: Path, file_type: int) -> str:
    """按官方分片流程上传本地文件，返回 file_info。"""
    size = path.stat().st_size
    md5, sha1, md5_10m = compute_digests(path)
    prepare = http_request(
        config,
        "POST",
        f"/v2/users/{openid}/upload_prepare",
        {
            "file_type": file_type,
            "file_size": str(size),
            "file_name": path.name,
            "md5": md5,
            "sha1": sha1,
            "md5_10m": md5_10m,
        },
    )
    upload_id = str(prepare["upload_id"])
    with path.open("rb") as handle:
        for part in prepare["parts"]:
            chunk = handle.read(int(part["block_size"]))
            _upload_part(config, openid, upload_id, part, chunk)
    merged = http_request(
        config,
        "POST",
        f"/v2/users/{openid}/files",
        {
            "file_type": file_type,
            "srv_send_msg": False,
            "file_name": path.name,
            "upload_id": upload_id,
        },
    )
    file_info = merged.get("file_info")
    if not file_info:
        raise RuntimeError("上传成功但未返回 file_info")
    return str(file_info)


def send_media_message(config: Config, openid: str, file_info: str, content: str) -> None:
    """发送富媒体消息，附带可选说明文字。"""
    payload: dict[str, Any] = {
        "msg_type": MSG_TYPE_MEDIA,
        "media": {"file_info": file_info},
        "msg_seq": new_msg_seq(),
    }
    if content:
        payload["content"] = content
    http_request(config, "POST", f"/v2/users/{openid}/messages", payload)


def _send_local_media(
    config: Config,
    openid: str,
    path_str: str,
    file_type: int,
    content: str,
) -> None:
    """校验本地文件、临时上线、上传并发送。"""
    path = Path(path_str).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"文件不存在: {path}")
    if path.stat().st_size > MAX_FILE_SIZE:
        raise SystemExit("文件超过 200MB 上限")
    ws, _ = open_gateway(config)
    try:
        file_info = upload_local_file(config, openid, path, file_type)
        send_media_message(config, openid, file_info, content)
    finally:
        ws.close()
    print("发送成功")


def cmd_status(args: argparse.Namespace, config: Config) -> int:
    cached = _read_json(OPENID_PATH) or {}
    print(f"配置目录: {CONFIG_DIR}")
    print(f"appid: {mask(config.appid)}")
    print(f"openid: {cached.get('openid') or '未捕获，请先运行 listen'}")
    print(f"来源用户: {cached.get('username', '未知')}")
    return 0


def cmd_listen(args: argparse.Namespace, config: Config) -> int:
    print(f"请在 {args.timeout} 秒内用目标 QQ 给机器人发一条私聊消息...")
    result = capture_openid(config, args.timeout)
    if not result:
        raise SystemExit("等待超时，未捕获到私聊消息")
    openid, username = result
    print(f"已捕获 openid: {openid} (用户: {username})")
    return 0


def cmd_text(args: argparse.Namespace, config: Config) -> int:
    openid = resolve_openid(args.openid)
    ws, _ = open_gateway(config)
    try:
        http_request(
            config,
            "POST",
            f"/v2/users/{openid}/messages",
            {"msg_type": MSG_TYPE_TEXT, "content": args.content, "msg_seq": new_msg_seq()},
        )
    finally:
        ws.close()
    print("发送成功")
    return 0


def cmd_file(args: argparse.Namespace, config: Config) -> int:
    openid = resolve_openid(args.openid)
    if args.url:
        ws, _ = open_gateway(config)
        try:
            name = args.name or Path(args.url).name or "file"
            file_info = str(
                http_request(
                    config,
                    "POST",
                    f"/v2/users/{openid}/files",
                    {"file_type": FILE_TYPE_FILE, "url": args.url, "srv_send_msg": False, "file_name": name},
                ).get("file_info")
            )
            send_media_message(config, openid, file_info, args.content or "")
        finally:
            ws.close()
        print("发送成功")
        return 0
    _send_local_media(config, openid, args.path, FILE_TYPE_FILE, args.content or "")
    return 0


def cmd_image(args: argparse.Namespace, config: Config) -> int:
    openid = resolve_openid(args.openid)
    _send_local_media(config, openid, args.path, FILE_TYPE_IMAGE, args.content or "")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="通过 QQ 官方机器人向个人用户发送消息/文件")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="查看配置与 openid 缓存状态").set_defaults(handler=cmd_status)

    p_listen = sub.add_parser("listen", help="监听一次私聊，捕获并缓存目标 openid")
    p_listen.add_argument("--timeout", type=float, default=120.0, help="等待秒数，默认 120")
    p_listen.set_defaults(handler=cmd_listen)

    p_text = sub.add_parser("text", help="发送文本消息")
    p_text.add_argument("--content", required=True, help="文本内容")
    p_text.add_argument("--openid", help="目标用户 openid，缺省用缓存")
    p_text.set_defaults(handler=cmd_text)

    p_file = sub.add_parser("file", help="发送文件（本地分片上传或 URL 直传）")
    source = p_file.add_mutually_exclusive_group(required=True)
    source.add_argument("--path", help="本地文件路径")
    source.add_argument("--url", help="文件公网 URL，与 --path 二选一")
    p_file.add_argument("--name", help="URL 直传时的文件名")
    p_file.add_argument("--content", default="", help="文件说明文字")
    p_file.add_argument("--openid", help="目标用户 openid，缺省用缓存")
    p_file.set_defaults(handler=cmd_file)

    p_image = sub.add_parser("image", help="发送图片")
    p_image.add_argument("--path", required=True, help="图片路径")
    p_image.add_argument("--content", default="", help="图片说明文字")
    p_image.add_argument("--openid", help="目标用户 openid，缺省用缓存")
    p_image.set_defaults(handler=cmd_image)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: Callable[[argparse.Namespace, Config], int] | None = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    config = load_config()
    try:
        return handler(args, config)
    except (requests.RequestException, RuntimeError, websocket.WebSocketException) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
