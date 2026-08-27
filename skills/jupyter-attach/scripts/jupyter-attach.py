"""jupyter-attach: 长驻 Jupyter 内核管理工具

通过标准 Jupyter 协议 (jupyter_client) 与一个常驻 ipykernel 进程交互，
实现跨调用/跨会话的持久 Python 状态（tmux 式 attach 语义）。

用法:
  jupyter-attach.py start                启动长驻内核（默认 .venvs/jupyter 解释器）
  jupyter-attach.py exec "code"          附接执行代码，输出 JSON 结果
  jupyter-attach.py vars                 列出内核中的用户变量
  jupyter-attach.py status               检查内核心跳与进程存活
  jupyter-attach.py stop                 优雅关闭内核
"""
import json
import shutil
import os
import socket
import sys
import time
from pathlib import Path

CONN_DIR = Path.home() / ".jupyter-attach"
CONN_FILE = CONN_DIR / "kernel.json"
STATE_FILE = CONN_DIR / "state.json"
LOCK_FILE = CONN_DIR / "start.lock"
LOG_FILE = CONN_DIR / "kernel.log"
DEFAULT_PY = Path.home() / ".venvs" / "jupyter" / "Scripts" / "python.exe"
DEFAULT_TIMEOUT = 120
LOCK_TIMEOUT = 30  # 等待锁的最长时间（秒）

_kc = None  # 模块级缓存客户端


def resolve_python() -> Path | None:
    """解析内核解释器：环境变量优先，其次默认 venv，最后回退到系统 python"""
    env = os.environ.get("JUPYTER_ATTACH_PYTHON")
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.append(DEFAULT_PY)
    for c in candidates:
        if c.exists():
            return c
    for name in ("python", "python3"):
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def ensure_deps(python: Path) -> list[str]:
    """检查解释器是否具备 ipykernel 与 jupyter_client，返回缺失项列表"""
    probe = """import importlib.util as u
for m in ('ipykernel', 'jupyter_client'):
    if u.find_spec(m) is None:
        print(m)
"""
    import subprocess

    try:
        r = subprocess.run(
            [str(python), "-c", probe],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        return ["ipykernel", "jupyter_client"]
    return [line.strip() for line in r.stdout.splitlines() if line.strip()]


def uv_hint() -> str:
    """返回安装 uv 的命令（按平台给对应命令，保证可直接复制执行）"""
    if os.name == "nt":
        return ('powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"\n'
                '      或 git-bash: curl -LsSf https://astral.sh/uv/install.sh | sh')
    return "curl -LsSf https://astral.sh/uv/install.sh | sh"


def check(silent: bool = False) -> list[dict]:
    """环境自检：解释器、依赖、内核状态，返回检查项列表"""
    items = []
    python = resolve_python()
    if python is None:
        if shutil.which("uv"):
            fix = "uv venv ~/.venvs/jupyter --python 3.13 && uv pip install --python ~/.venvs/jupyter/Scripts/python.exe ipykernel jupyter_client"
        else:
            fix = f"先安装 uv：{uv_hint()}\n      然后运行 jupyter-attach setup"
        items.append({"check": "python", "ok": False, "detail": "未找到可用解释器", "fix": fix})
    else:
        items.append({"check": "python", "ok": True, "detail": str(python)})
        missing = ensure_deps(python)
        if missing:
            if shutil.which("uv"):
                fix = f"uv pip install --python {python} {' '.join(missing)}"
            else:
                fix = f"先安装 uv：{uv_hint()}\n      然后运行 jupyter-attach setup"
            items.append({"check": "deps", "ok": False, "detail": f"缺失: {', '.join(missing)}", "fix": fix})
        else:
            items.append({"check": "deps", "ok": True, "detail": "ipykernel + jupyter_client 就绪"})
    items.append({"check": "kernel", "ok": kernel_ready(), "detail": "已运行" if kernel_ready() else "未启动"})
    if not silent:
        for it in items:
            mark = "OK" if it["ok"] else "XX"
            print(f"[{mark}] {it['check']}: {it['detail']}")
            if not it["ok"] and it.get("fix"):
                print(f"     修复: {it['fix']}")
    return items


def cmd_setup() -> None:
    """通过 uv 一键配置环境：建 venv（含自动下载解释器）并安装依赖，幂等"""
    import subprocess

    if not shutil.which("uv"):
        print(json.dumps({"error": "未找到 uv", "hint": uv_hint()}))
        sys.exit(1)
    steps = []
    if not DEFAULT_PY.exists():
        venv_root = DEFAULT_PY.parent.parent
        r = subprocess.run(
            ["uv", "venv", str(venv_root), "--python", "3.13"],
            capture_output=True, text=True, timeout=180,
        )
        if r.returncode != 0:
            print(json.dumps({"error": "uv venv 失败", "detail": r.stderr or r.stdout}))
            sys.exit(1)
        steps.append(f"venv 已创建: {venv_root}")
    missing = ensure_deps(DEFAULT_PY)
    if missing:
        r = subprocess.run(
            ["uv", "pip", "install", "--python", str(DEFAULT_PY), *missing],
            capture_output=True, text=True, timeout=300,
        )
        if r.returncode != 0:
            print(json.dumps({"error": "依赖安装失败", "detail": r.stderr or r.stdout}))
            sys.exit(1)
        steps.append(f"依赖已安装: {' '.join(missing)}")
    print(json.dumps({"status": "ready", "python": str(DEFAULT_PY), "steps": steps}, ensure_ascii=False))


def jupyter_client():
    """延迟导入 jupyter_client，失败时给出可操作的提示"""
    try:
        import jupyter_client

        return jupyter_client
    except ImportError:
        print(json.dumps({"error": "未安装 jupyter_client", "hint": "先执行 jupyter-attach check 查看修复命令"}))
        sys.exit(1)


def load_state() -> dict:
    """读取内核状态文件（pid/端口/启动时间）"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(state: dict) -> None:
    """写内核状态文件"""
    CONN_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_state() -> None:
    """删除状态文件（内核已死时清理）"""
    STATE_FILE.unlink(missing_ok=True)


def port_open(port: int) -> bool:
    """TCP 探测端口是否可连"""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except OSError:
        return False


def pid_alive(pid: int) -> bool:
    """按 OS 分别探测进程存活"""
    try:
        if os.name == "nt":
            import subprocess

            r = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                encoding="gbk",
                errors="replace",
                timeout=5,
            )
            return str(pid) in r.stdout
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def kernel_ready() -> bool:
    """内核就绪 = 状态文件有效 且 心跳端口存活 且 进程存活"""
    st = load_state()
    if not st or not st.get("hb_port"):
        return False
    return port_open(st["hb_port"]) and pid_alive(st.get("pid", -1))


def acquire_lock() -> bool:
    """原子方式获取启动锁（O_CREAT|O_EXCL，仅一个进程可以成功），成功返回 True"""
    CONN_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + LOCK_TIMEOUT
    while time.time() < deadline:
        try:
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            # 锁被占用：如果持锁进程已死则视为死锁，可抢占
            try:
                holder = int(LOCK_FILE.read_text(encoding="utf-8").strip())
            except Exception:
                holder = -1
            if holder > 0 and not pid_alive(holder):
                LOCK_FILE.unlink(missing_ok=True)
                continue
            time.sleep(0.3)
    return False


def release_lock() -> None:
    """释放启动锁"""
    LOCK_FILE.unlink(missing_ok=True)


def cmd_start() -> None:
    """启动长驻内核进程（已就绪则直接返回）"""
    if kernel_ready():
        print(json.dumps({"status": "already_running", "conn_file": str(CONN_FILE)}))
        return
    if not acquire_lock():
        print(json.dumps({"error": "等待启动锁超时，可能是其他进程正在启动内核", "hint": "稍后重试或检查残留进程"}))
        sys.exit(1)
    try:
        _start_kernel()
    finally:
        release_lock()


def _start_kernel() -> None:
    """持锁状态下启动内核并写状态文件"""
    # 持锁后再次检查：可能等待期间已有其他进程完成启动
    if kernel_ready():
        print(json.dumps({"status": "already_running", "conn_file": str(CONN_FILE)}))
        return
    python = resolve_python()
    if python is None:
        print(json.dumps({"error": "未找到可用的 Python 解释器", "hint": "运行 jupyter-attach check 查看诊断"}))
        sys.exit(1)
    missing = ensure_deps(python)
    if missing:
        print(json.dumps({"error": f"解释器缺少依赖: {', '.join(missing)}",
                          "hint": f"uv pip install --python {python} {' '.join(missing)}"}))
        sys.exit(1)

    CONN_DIR.mkdir(parents=True, exist_ok=True)
    CONN_FILE.unlink(missing_ok=True)
    clear_state()

    import subprocess

    log_f = open(LOG_FILE, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(python), "-m", "ipykernel_launcher", "-f", str(CONN_FILE)],
        stdout=log_f,
        stderr=log_f,
        stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        env={**os.environ, "JUPYTER_NO_INTERRUPT": "1"},
    )
    # 等待 connection file 生成且内容非空（ipykernel 先建文件后写内容）
    deadline = time.time() + 20
    cfg = None
    while time.time() < deadline:
        if CONN_FILE.exists() and CONN_FILE.stat().st_size > 10:
            try:
                cfg = json.loads(CONN_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                cfg = None
            if cfg:
                break
        time.sleep(0.3)
    if cfg is None:
        print(json.dumps({"error": "内核启动超时或连接文件无效", "log": str(LOG_FILE)}))
        sys.exit(1)
    st = {
        "pid": proc.pid,
        "hb_port": cfg["hb_port"],
        "shell_port": cfg["shell_port"],
        "started_at": int(time.time()),
        "python": str(python),
    }
    save_state(st)
    if not kernel_ready():
        print(json.dumps({"status": "kernel_exited", "log": str(LOG_FILE)}))
        sys.exit(1)

    print(json.dumps({"status": "started", "pid": proc.pid, "hb_port": cfg["hb_port"], "conn_file": str(CONN_FILE)}))


def _client():
    """创建并连接 BlockingKernelClient（复用连接）"""
    global _kc
    jc = jupyter_client()
    if _kc is None:
        _kc = jc.BlockingKernelClient()
        _kc.load_connection_file(str(CONN_FILE))
        _kc.start_channels()
        _kc.wait_for_ready(timeout=15)
    return _kc


def unescape_code(raw: str) -> str:
    """把 CLI 传入的 \\n 字面量还原为换行，便于一行传多行代码"""
    return raw.replace("\\n", "\n")


def cmd_exec(code: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    """附接执行代码，收集输出为 JSON"""
    """附接执行代码，收集输出为 JSON"""
    if not kernel_ready():
        print(json.dumps({"error": "内核未运行", "hint": "先执行 jupyter-attach start"}))
        sys.exit(1)
    kc = _client()
    msg_id = kc.execute(code)
    result = {"stdout": "", "stderr": "", "result": None, "error": None}
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            msg = kc.get_iopub_msg(timeout=1)
        except Exception:
            continue
        if msg.get("parent_header", {}).get("msg_id") != msg_id:
            continue
        content = msg.get("content", {})
        mtype = msg["msg_type"]
        if mtype == "stream":
            result[content["name"]] += content["text"]
        elif mtype == "execute_result":
            result["result"] = content.get("data", {}).get("text/plain")
        elif mtype == "error":
            result["error"] = "\n".join(content.get("traceback", []))
        elif mtype == "status" and content.get("execution_state") == "idle":
            break
    print(json.dumps(result, ensure_ascii=False))


def cmd_vars() -> None:
    """列出内核用户命名空间的变量"""
    cmd_exec("print(sorted(k for k in globals() if not k.startswith('__')))")


def cmd_status() -> None:
    """输出内核状态摘要"""
    st = load_state()
    ok = kernel_ready()
    print(json.dumps({"running": ok, "state": st, "conn_file": str(CONN_FILE)}, ensure_ascii=False))


def cmd_stop() -> None:
    """优雅关闭内核（发送 shutdown 请求）"""
    if not kernel_ready():
        clear_state()
        print(json.dumps({"status": "not_running"}))
        return
    try:
        _client().shutdown()
    except Exception:
        pass
    time.sleep(1)
    clear_state()
    print(json.dumps({"status": "stopped"}))


def main() -> None:
    """命令行入口"""
    args = sys.argv[1:]
    if not args:
        print("用法: jupyter-attach.py start|exec <code>|vars|status|stop|check|setup")
        sys.exit(2)
    cmd, rest = args[0], args[1:]
    if cmd == "start":
        cmd_start()
    elif cmd == "check":
        check()
    elif cmd == "setup":
        cmd_setup()
    elif cmd == "exec" and rest:
        code = Path(rest[1]).read_text(encoding="utf-8") if rest[0] == "-f" else unescape_code(rest[0])
        cmd_exec(code)
    elif cmd == "vars":
        cmd_vars()
    elif cmd == "status":
        cmd_status()
    elif cmd == "stop":
        cmd_stop()
    else:
        print(json.dumps({"error": f"未知命令: {cmd}"}))
        sys.exit(2)


if __name__ == "__main__":
    main()
