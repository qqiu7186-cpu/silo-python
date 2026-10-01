# Silo Python SDK Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 构建与 minio 7.2.20 公开 API 完整兼容的 Silo Python SDK，并验证本机调用。

**Architecture:** Silo 继承 Minio。辅助模块将原模块的公开符号直接导出，保持类型身份；网络功能交给上游。

**Tech Stack:** Python >=3.9、minio==7.2.20、setuptools、pytest、build。

**Spec:** design.md

## Global Constraints

- 分发名 silo-python-sdk，导入名 silo；非官方 SDK。
- 不覆盖 Minio 已有方法和构造参数，不改变返回值和异常。
- 不重写 HTTP、S3 签名、分页、分片上传或重试。
- 默认 HTTPS，凭据从环境变量读取，不写进包或日志。
- 只清理 SDK 测试生成的独立桶和数据，不发布 PyPI。
- 实测范围和仅接口核对范围分开说明。

## Review Focus

- 环境变量缺失或 SILO_SECURE 拼错：立即清晰报错，不静默降级 HTTP。
- 下载读取失败：仍关闭响应并释放连接。
- 空字节和非 ASCII 对象名：保持正确上传下载。
- 辅助模块的类身份：与 minio 对象相同，支持子模块导入。
- 干净安装：wheel 可导入，不依赖源代码目录或本机密码文件。

### Task 1: 完整兼容客户端与包结构

Files: pyproject.toml、src/silo/__init__.py、src/silo/client.py、src/silo/py.typed、src/silo/公开辅助模块、tests/test_compatibility.py。

Interfaces: Silo 继承 Minio；构造签名保持一致；辅助模块提供上游同名公开符号；导出 S3Error 和 __version__。

- [x] 写兼容测试：枚举 minio.Minio 全部公开可调用成员，验证 Silo 对应成员身份和 inspect.signature；检查构造签名。
- [x] 写模块测试：枚举 minio 所有非下划线辅助模块和 credentials 子模块，对所有非下划线符号检查存在性和对象身份。
- [x] 运行测试，确认因 Silo 包不存在失败。
- [x] 创建 src 布局及包配置，依赖固定 minio==7.2.20；实现继承与显式辅助模块导出。
- [x] 运行兼容测试，确认全部通过，保存模块和 API 清单。

### Task 2: 环境配置和字节操作

Files: src/silo/client.py、tests/test_client.py。

Interfaces: Silo.from_env() -> Silo；upload_bytes(bucket_name: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> ObjectWriteResult；download_bytes(bucket_name: str, object_name: str) -> bytes。

- [x] 写 from_env 测试：缺失 endpoint/key/secret、默认 HTTPS、显式 true/false、非法布尔值，验证真实客户端配置和异常。
- [x] 写便捷方法测试：空字节和 UTF-8 内容调用上游行为；下载成功或 read 失败均关闭并释放响应。仅网络边界使用替身。
- [x] 运行测试，确认新增方法缺失导致失败。
- [x] 实现配置读取及校验、BytesIO 上传、finally 释放下载响应。不记录凭据。
- [x] 运行完整单元测试，确认所有用例通过。

### Task 3: 真实 Silo 验证、文档与发行产物

Files: tests/test_integration.py、examples/quickstart.py、.env.example、README.md、LICENSE、NOTICE、verification.json、dist/。

Interfaces: 集成测试通过 SILO_* 环境变量连接 Silo；默认无配置时跳过，显式指定集成执行时必须提供凭据。每个测试使用随机桶和 finally 清理。

- [x] 写真实测试：桶管理、字节/文件上传下载、stat、复制、recursive 列举、超过 5MiB 分片上传、预签名 GET/PUT 的实际 HTTP 请求、版本启用和指定版本读取、生命周期、策略、标签和失败 S3Error。
- [x] 运行测试确认新增 SDK 行为在实现前的失败证据；实现后执行完整真实测试。不能运行的功能逐项记录原因。
- [x] 编写中文 README：安装、兼容范围、上游 API 使用、环境配置、原版到 Silo 的迁移、线程/进程使用约束、实测与未实测功能。
- [x] 编写不含凭据的 quickstart 和 .env.example；记录上游 Apache-2.0 依赖及非官方身份。
- [x] 构建 wheel 和 sdist；使用新的 work 虚拟环境安装 wheel，pip check，然后从源目录外执行真实上传下载。
- [x] 保存机器可读验证结果，不含密钥；核对源码归档没有 .env、数据目录或虚拟环境。
- [x] 完成代码自审，运行完整测试，交付 SDK 目录和 wheel 链接。

## Execution

建议在当前会话由主代理直接完成。项目范围小、任务共享客户端接口，无需拆成多个实现代理。此目录不是已有 Git 仓库，不额外创建仓库或提交。
