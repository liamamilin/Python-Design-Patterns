# 第 14 章　外观 Facade

> 本章要回答：一件事要用到好几个模块，每个模块都有自己的细节和陷阱时，怎样给使用者一个简单的入口？这个入口应该做多少事，又不该做哪些事？

外观可能是最“不像模式”的模式：它说的无非是“写一个函数或类，把复杂的步骤包起来”。但它有一个容易被忽视的另一半：**入口要简单，但不要把背后的东西锁起来。**

## 眼前的任务

一个小设计工作室把所有文档放在一个共享文件夹里。老板想每天夜里自动备份一次：

- 把整个文件夹打成一个 zip 包，文件名带上日期时间；
- 在包里附一份清单，记下每个文件的 SHA-256 校验值，以后可以检查备份有没有损坏；
- 只保留最近 3 份备份，免得硬盘被占满。

这件事要用到标准库的好几个模块：`pathlib` 遍历文件，`hashlib` 算校验值，`zipfile` 打包，`json` 写清单。

## 不用模式的写法

一位同事写了夜间备份脚本，直接调用这些模块：

```python
def nightly_backup(source: Path, dest: Path, now: datetime) -> Path:
    archive = dest / f"backup-{now:%Y%m%d-%H%M%S}.zip"
    manifest = {}
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                manifest[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
                zf.write(path)  # 忘了 arcname：压缩包里存的是完整路径
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False))
    return archive
```

看起来没问题，打开生成的压缩包却发现：

```text
['var/folders/hr/…/文档/合同/租房.txt', 'manifest.json']
```

这里有好几个只有熟悉这些模块才知道的细节：

1. **`zf.write(path)` 不指定 `arcname` 时，压缩包里存的是文件的完整路径**（去掉开头的 `/`），而不是相对于备份文件夹的路径。恢复时，文件会被解压到一串很深的目录里。
2. **清单用 `path.name` 作键**，“合同/说明.txt”和“照片/说明.txt”只会留下一条，另一个文件的校验值丢了。
3. macOS 在每个文件夹里留下的 `.DS_Store` 也被打包了进去。
4. `path.read_bytes()` 把整个文件一次读进内存，遇到几个 GB 的视频文件就麻烦了。
5. 还没写“只保留 3 份”。

测试 `test_full_paths_and_name_collisions` 复现了前三个问题。

## 变化带来的困难

不久，又有两个地方要用备份功能：

- 工作室的内部网页上要加一个“立即备份”按钮；
- 每周一早上要**校验**最近一份备份，确认它能用。

如果每个地方都直接调用 `zipfile`、`hashlib`、`json`，那么上面五个细节，每个调用方都要知道，都要处理对。漏掉任何一个，就会出现一个“有时候不太对”的备份。而且，打包和校验必须遵守**同一套约定**：清单叫什么名字、键是什么格式、用什么哈希算法。这些约定散落在三处代码里，改一处就要找齐另外两处。

使用者真正想说的只有一句话：“备份这个文件夹。”或者：“检查一下这份备份。”

## 外观：给子系统一个简单的入口

GoF 对外观的描述是：**为子系统中的一组接口提供一个一致的界面，外观模式定义了一个高层接口，这个接口使得这一子系统更加容易使用。**

这里的“子系统”就是 `zipfile`、`hashlib`、`json`、`pathlib` 这几个模块，以及它们之间的约定。外观是一个类，把这些细节和约定集中到一处：

```python
    def run(self, now: datetime) -> Path:
        """备份一次：打包、写清单、只保留最近 keep 份。"""
        self.dest.mkdir(parents=True, exist_ok=True)
        archive = self.dest / f"backup-{now:%Y%m%d-%H%M%S}.zip"
        manifest = {}
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in self._files():
                name = path.relative_to(self.source).as_posix()
                manifest[name] = _sha256(path)
                zf.write(path, arcname=name)
            zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        self._rotate()
        return archive
```

前面的五个细节，在这里各有着落：

- `arcname=name` 用相对路径存放文件，`as_posix()` 保证在 Windows 上也用 `/` 分隔，这是 zip 格式的约定；
- 清单的键是相对路径，同名文件不会互相覆盖；
- `_files()` 跳过 `.DS_Store` 等系统文件；
- `_sha256` 分块读取文件，不会一次把大文件读进内存：

```python
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

- `_rotate()` 只保留最近的几份。

校验用的是同一个类、同一套约定：

```python
    def verify(self, archive: Path) -> list[str]:
        """检查压缩包里的每个文件是否和清单一致，返回问题列表。"""
        problems = []
        with zipfile.ZipFile(archive) as zf:
            manifest = json.loads(zf.read("manifest.json"))
            for name, digest in manifest.items():
                if hashlib.sha256(zf.read(name)).hexdigest() != digest:
                    problems.append(f"内容不一致：{name}")
        return problems
```

现在，夜间任务、网页按钮、周一的校验，每个调用方都只需要一两行：

```python
        backup = Backup(src, Path(tmp, "备份"))
        archive = backup.run(datetime(2026, 3, 9, 2, 0))
```

```text
['合同/租房.txt', 'manifest.json']
校验： 全部一致
```

连续备份五天，只剩最近三份（测试 `test_keeps_only_the_latest`）；把包里的一个文件改掉，`verify` 能准确指出是哪一个（测试 `test_verify_finds_a_tampered_file`）。

### 外观不是围墙

外观的另一半同样重要：**它提供简单的入口，但不阻止使用者绕过它，直接使用子系统。**

比如，客户找来说上周的一份合同被误删了，要从备份里恢复**一个**文件。`Backup` 没有提供“恢复单个文件”的方法，而且不必提供。外观生成的就是一个标准的 zip 文件，任何人都可以直接用 `zipfile` 打开它，取出需要的那一个（测试 `test_subsystem_is_still_available`）：

```text
with zipfile.ZipFile(archive) as zf:
    zf.read("合同/租房.txt")
```

这正是外观和“封装”的区别。外观的目标是**让常见的事情变简单**，而不是**让所有事情都必须经过它**。它背后的模块依然是公开的，有特殊需求的人可以直接用。

### 角色对照

| GoF 角色 | 本例 | 职责 |
|---|---|---|
| 外观（Facade） | `Backup` | 知道该调用哪些子系统、按什么顺序，把请求转化为对子系统的调用 |
| 子系统类（Subsystem classes） | `zipfile`、`hashlib`、`json`、`pathlib` | 完成实际的工作；它们不知道外观的存在 |

## 代价与边界

- **外观容易越长越大。** 今天加“恢复单个文件”，明天加“上传到网盘”，后天加“发邮件通知”……每一个都“和备份有关”，最后 `Backup` 变成一个什么都管的大类。判断标准是：这个功能是不是大多数使用者都需要、并且必须遵守外观所维护的约定？“恢复单个文件”只是读一个标准 zip，不需要外观；“上传到网盘”和打包无关，应该是另一个模块，由调用方把 `run()` 返回的路径交给它。
- **简单的入口意味着做了选择。** `Backup` 决定了用 SHA-256、跳过哪些文件、清单叫什么名字。需要不同选择的人，要么给外观加参数，要么绕过它。参数加得太多，外观就不再简单了。
- **外观不能替你理解子系统。** 写外观的人仍然需要知道 `arcname` 的陷阱、zip 路径的分隔符约定。外观只是让**使用者**不必知道这些。

**什么时候不该用**：只有一个地方用到这些模块，而且步骤很短。一个十行的函数直接调用 `zipfile` 就很好，不需要再包一层。外观的价值，在第二个、第三个调用方出现时才显现出来。

## Python 角度：模块就是外观

在 Python 里，一个**模块**常常就是最自然的外观。模块里放一个顶层函数给大多数人用，辅助函数也放在同一个模块里，有需要的人照样可以导入。

标准库本身就有很多外观。比如 `shutil.make_archive`，一行就能把一个文件夹打包成 zip 或 tar：

```python
def quick_archive(source: Path, dest: Path) -> Path:
    """标准库里的外观：shutil.make_archive 一行完成打包，但没有清单和轮换。"""
    return Path(shutil.make_archive(str(dest / source.name), "zip", root_dir=source))
```

它在内部替你处理了 `zipfile` 的细节，包括相对路径。但它没有清单、没有轮换，也不会跳过 `.DS_Store`（测试 `test_shortcuts`）。如果需求只是“打个包”，用它就够了，根本不需要自己写外观。本章的 `Backup` 之所以存在，是因为工作室有自己的约定（清单、轮换、校验），而这些约定需要一个地方来维护。

外观可以是类，也可以是函数。本章用类，是因为“源文件夹、目标文件夹、保留几份”这组配置在 `run`、`verify`、`archives` 之间共用。如果只有 `run` 一个操作，一个带参数的函数就够了。对只想“现在备份一下”的调用方，甚至可以在外观之上再给一个更简单的入口：

```python
def backup_folder(source: Path, dest: Path, keep: int = 3) -> Path:
    """给只想“备份一下”的调用方：用当前时间，其他全用默认值。"""
    return Backup(source, dest, keep).run(datetime.now())
```

注意，“当前时间”只在这个最外层的便捷函数里获取。`Backup.run` 本身接收 `now` 参数，这样测试可以传入固定的时间，得到确定的文件名。这是[第 01 章](../part-01/01-data-and-processing.md)讲过的做法：把“时间”这种外部输入推到最外层。

## 小结

- 当一件事需要协调好几个模块，每个模块都有自己的细节和陷阱，而且有多个调用方时，外观提供一个简单的入口，把细节和约定集中到一处。
- 外观让常见的事情变简单，但不阻止使用者直接使用子系统。它不是围墙。
- 外观容易膨胀。只把需要遵守同一套约定的操作放进去，其他功能做成独立的模块。
- 在 Python 里，模块本身就是天然的外观；标准库里也有现成的外观，比如 `shutil.make_archive`，需求简单时直接用它。

## 练习

工作室决定把备份同时上传到一个网盘。网盘的 SDK 提供 `upload(local_path, remote_name)`。

1. 上传应该放进 `Backup.run` 里，还是放在外面？各有什么后果？
2. 如果网盘上传失败了，本地备份算成功还是失败？“只保留 3 份”的轮换应该在上传之前还是之后执行？
3. 如果放在外面，夜间任务的代码会是什么样子？

**思路提示**：放进 `run` 里，`Backup` 就要依赖网盘 SDK，测试时也要处理网络；没有网盘的另一个办公室就用不了这个类。放在外面，`run` 只负责本地备份并返回压缩包路径，夜间任务再调用上传：`archive = backup.run(now)`，然后 `cloud.upload(archive, archive.name)`。这样两件事可以分别测试、分别失败。第 2 问是一个真正的业务问题：如果先轮换再上传，而上传又失败了，可能删掉了网盘上唯一还没有的那一份。把两个步骤分开之后，这些顺序问题就变得清楚，可以在夜间任务里显式地写出来。外观负责一组**紧密相关、共享约定**的操作，不负责所有“顺便要做”的事。

完整代码：
- [`examples/ch14_backup_v1.py`](../../examples/ch14_backup_v1.py)：直接调用各模块的夜间备份（含错误）
- [`examples/ch14_facade.py`](../../examples/ch14_facade.py)：`Backup` 外观
- [`examples/ch14_pythonic.py`](../../examples/ch14_pythonic.py)：便捷函数与 `shutil.make_archive`

测试：[`tests/test_ch14_facade.py`](../../tests/test_ch14_facade.py)。
