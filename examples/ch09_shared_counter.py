"""第 09 章：跨进程唯一的号码。计数状态放在进程之外的 SQLite 文件里。"""
from __future__ import annotations

import multiprocessing
import sqlite3
from concurrent.futures import ProcessPoolExecutor
from contextlib import closing
from pathlib import Path


def create_counter(path: Path) -> None:
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("CREATE TABLE counter (n INTEGER NOT NULL)")
        conn.execute("INSERT INTO counter VALUES (0)")


def take_from(path: Path) -> str:
    conn = sqlite3.connect(path, isolation_level=None, timeout=10)
    try:
        conn.execute("BEGIN IMMEDIATE")  # 立即加写锁，其他进程要等这次取号结束
        conn.execute("UPDATE counter SET n = n + 1")
        (n,) = conn.execute("SELECT n FROM counter").fetchone()
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()
    return f"A{n:03d}"


def take_many_from(path: Path, n: int) -> list[str]:
    return [take_from(path) for _ in range(n)]


def take_in_new_process(path: Path, n: int) -> list[str]:
    spawn = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=1, mp_context=spawn) as pool:
        return pool.submit(take_many_from, path, n).result()


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "tickets.db"
        create_counter(db)
        print("进程一：", take_in_new_process(db, 2))
        print("进程二：", take_in_new_process(db, 2))
