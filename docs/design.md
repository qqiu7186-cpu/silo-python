# Silo Python SDK 设计

目标：基于官方 minio Python SDK，提供可安装的 Silo 客户端，保留上游所有公开功能，增加少量便捷方法。

## 兼容原则

- Python 导入入口为 `from silo import Silo`，分发包名为 `silo-python-sdk`，不声明是官方 SDK。
- Silo 直接继承 minio.Minio，不改写上游已有方法和构造参数。既有 API 的参数、返回对象、异常及同步语义保持上游行为。
- 上游版本在构建和兼容测试中固定；发布新版本时显式升级依赖并重新验证。完整性承诺针对该版本的公开 Python API，不能承诺未来未经测试的版本。
- 提供 silo.error、silo.commonconfig、silo.datatypes、silo.credentials、silo.sse、silo.lifecycleconfig、silo.notificationconfig、silo.retention、silo.tagging、silo.versioningconfig 等公开辅助模块的兼容导出。以安装的上游公开模块清单为准，自动核对所有公开符号，避免只覆盖常用接口。
- 不重新实现 HTTP、S3 签名、分页、分片上传或重试。它们全部复用上游实现。
- SDK 接口完整不等于 Silo 服务端支持所有上游扩展；文档区分 API 兼容检查与真实服务端验证。

## 新增接口

- Silo.from_env()：从 SILO_ENDPOINT、SILO_ACCESS_KEY、SILO_SECRET_KEY、SILO_SECURE 读取配置；HTTPS 为默认；显式校验布尔配置。密钥不写入源码或日志。
- upload_bytes(bucket_name, object_name, data, content_type)：调用上游 put_object，返回上游结果。
- download_bytes(bucket_name, object_name)：读取上游 get_object 返回的响应，在 finally 中关闭并释放连接。
- 导出 S3Error 和 SDK 自身版本；不吞异常。

## 交付

src 布局 Python 包、pyproject.toml、中文 README、环境变量示例、运行示例、兼容测试及本机集成测试、wheel 和源码归档。依赖和临时虚拟环境放到工作目录，产物位于 outputs/silo-python-sdk。不发布 PyPI。

## 验证

1. 使用明确版本的 minio，检查 Silo 与 Minio 全部公开方法的存在性及签名一致性，核对辅助模块公开符号。
2. 单元测试环境变量配置、便捷方法以及响应资源释放，包括失败场景。
3. 针对已部署本机 Silo，使用随机独立桶执行创建、列举、文件和字节上传下载、元数据查询、复制、分页、分片上传、预签名下载、版本控制及版本读取，最后仅清理本次测试数据。
4. 额外验证生命周期、桶策略、标签等操作；未实测的服务端扩展明确列出，不声称全部端到端验证。
5. 构建 wheel 并在干净虚拟环境中安装，验证导入、依赖和实际上传下载。
