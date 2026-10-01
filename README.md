# Silo Python SDK

面向 [PGSTY Silo](https://github.com/pgsty/silo) 的**非官方** Python SDK，复用官方 [MinIO Python SDK](https://github.com/minio/minio-py)。Python 3.9+。

## 安装

已发布至 [PyPI：silo-python-sdk](https://pypi.org/project/silo-python-sdk/)，当前版本为 **0.1.0**，支持 Python 3.9+。

```bash
python -m pip install silo-python-sdk
```

需要固定版本时：

```bash
python -m pip install silo-python-sdk==0.1.0
```

**安装名是 `silo-python-sdk`，Python 导入名始终是 `silo`：**

```python
from silo import Silo
```

安装时会自动安装固定版本的 `minio==7.2.20` 及其依赖。发布后的包已从 PyPI 在全新环境中安装，并通过本机 Silo 上传、下载验证。

也可以从仓库目录安装：

```bash
python -m pip install .
```

或安装仓库中附带的 wheel：

```bash
python -m pip install dist/silo_python_sdk-0.1.0-py3-none-any.whl
```

## 连接和迁移

```python
import os
from silo import Silo
from silo.error import S3Error

client = Silo(
    endpoint="localhost:9000",  # host:port，不包含 http://
    access_key=os.environ["SILO_ACCESS_KEY"],
    secret_key=os.environ["SILO_SECRET_KEY"],
    secure=False,               # 仅本机 HTTP 实例；默认值为 True
)

if not client.bucket_exists("example"):
    client.make_bucket("example")

client.fput_object("example", "hello.txt", "./hello.txt")
client.fget_object("example", "hello.txt", "./download.txt")
for obj in client.list_objects("example", recursive=True):
    print(obj.object_name, obj.size)
```

迁移原代码时，将 `from minio import Minio` 换为 `from silo import Silo`，构造调用改为 `Silo(...)`；已有方法调用不变。辅助模块可把 `minio.commonconfig` 等改为 `silo.commonconfig`。`from silo import Minio` 也可用，它是上游原类。

`Silo` 继承 `Minio`，**63 个公开方法全部保持原方法、参数签名、返回类型和异常类型**，包括桶管理、对象操作、复制与合成、分片上传、删除、分页、版本控制、生命周期、访问策略、标签、通知、预签名 GET/PUT/POST、加密、对象锁、保留策略、法律保留、复制配置、Select、Snowball、append、prompt 等。25 个辅助模块的全部公开符号直接引用上游对象，包含 `credentials` 子模块、`minioadmin`、错误、配置和数据模型。

完整清单和签名见 [docs/api-inventory.json](docs/api-inventory.json)。高级参数、凭据 Provider、session_token、自定义 http_client、region、cert_check 均沿用上游构造接口。管理类可从 `silo.minioadmin` 导入，SDK 并未承诺所有管理调用都能在 Silo 服务端执行。

这份兼容承诺针对 **minio 7.2.20**。依赖固定该版本；升级时需重跑兼容及服务端测试。它不是独立重写的 S3 协议库。

## 环境变量和便捷操作

```bash
export SILO_ENDPOINT=localhost:9000
export SILO_ACCESS_KEY=silo-admin
export SILO_SECRET_KEY='填入实际密码'
export SILO_SECURE=false
```

```python
from silo import Silo

client = Silo.from_env()
client.upload_bytes("example", "folder/中文.txt", "你好 Silo".encode(), "text/plain")
content = client.download_bytes("example", "folder/中文.txt")
print(content.decode())
```

前三个变量必填，缺失或全空白抛出 `ValueError`；密钥原文保持不变。`SILO_SECURE` 默认 `true`，只接受 `true`/`false`（大小写不敏感，可带首尾空白），拼写错误报错。示例 `.env.example` 供参考，SDK 不自动读取 `.env` 文件。

`upload_bytes` 返回上游 `ObjectWriteResult`。`download_bytes` 在成功或异常时关闭响应并释放连接，内容全部读入内存。大文件、版本读取、加密和元数据操作请使用完整的上游 `put_object`、`get_object`、`fput_object`、`fget_object` 接口。例如：

```python
response = client.get_object("example", "hello.txt", version_id="实际版本 ID")
try:
    for chunk in response.stream(1024 * 1024):
        print(len(chunk))
finally:
    response.close()
    response.release_conn()
```

异常原样传播，使用 `silo.error.S3Error` 或 `minio.error.S3Error` 捕获结果相同。客户端可在线程间共享；不可在多个进程间共享同一个实例，应每个进程独立创建。首次使用前自行创建目标桶；SDK 不修改既有桶策略。

## 验证与限制

完整对照核验见 [docs/compatibility-report.md](docs/compatibility-report.md)：官方原版和 Silo 各有 114 项单元测试通过（2 项 locale 跳过），官方功能测试各有 49 项实执行通过（1 项 AWS 区域不适用）。官方功能测试新增实测了条件复制、预签名过期/响应头、线程读写、Select 和 Snowball；预签名 POST 仅生成策略，尚未实测 POST 上传。

API 保留和服务端支持是不同的保证。兼容测试遍历并检查所有方法和辅助符号；本机服务端测试覆盖：

- 创建/查询/删除桶，空字节和中文对象名，文件和字节上传下载。
- 元数据、范围读取、复制、合成，7 MiB 分片上传。
- 实际预签名 GET/PUT 请求，1005 个对象的跨页列举。
- 版本启用、指定版本读取、删除标记和版本清理。
- 生命周期配置、桶策略、桶/对象标签、空通知配置及相应删除操作。
- 未找到对象和错误凭据的真实 `S3Error`。

Python 3.9.25 和 3.13.3 上各有 67 项 SDK 测试通过；最低 Python 版本与原版一致为 3.9。

实测对象为本机 Silo `RELEASE.2026-09-16T00-00-00Z`，HTTP、单节点。**未实测**外部身份 Provider、管理员 API、加密/KMS、对象锁/保留/法律保留、跨站复制、真实通知投递/监听、预签名 POST、append、prompt、AWS 加速/双栈、TLS、集群和故障恢复。这些接口仍完整保留，能否执行取决于服务端配置和功能支持。没有把兼容测试描述为这些功能的端到端证明。

## 重跑测试和构建

```bash
python -m pip install '.[test]' build
python -m pytest                         # 单元和兼容测试；跳过真实服务端测试
# 先设置上述四个 SILO_* 环境变量
python -m pytest --run-integration       # 完整测试；缺少配置会报错
python -m build
```

集成测试使用随机 `silo-sdk-test-*` 桶，结束时删除本次生成的对象和桶；不会操作原有业务桶。验证证据见 `verification.json`。快速示例为 `examples/quickstart.py`；它保留新建示例桶和上传文件，便于在控制台查看。

## 许可

本包的封装代码采用 MIT。`minio` 是独立安装的 Apache-2.0 依赖，辅助模块仅导出其对象，没有复制上游实现。Silo 服务端为单独的软件项目，其许可不由本 SDK 改变。参见 LICENSE 和 NOTICE。
