# MinIO 功能一致性核验

本 SDK 复用安装的 `minio==7.2.20`，`Silo` 是 `Minio` 的子类。原有方法没有经过包装或重写，新增方法只使用上游公开 API。

| 核验 | 结果 |
| --- | --- |
| 原版公开方法 | 63 个，函数对象、签名相同 |
| 全部 Python 实现函数 | 82 个，含构造函数、私有传输/缓存助手，无覆盖 |
| 辅助模块 | 25 个，Python 3.13 为 707 个、Python 3.9 为 706 个公开符号，均与同版本上游身份相同，含导入顺序检查 |
| 构造配置 | 匿名/静态凭据/session token/secure/region/cert_check/custom HTTP/Provider 对齐 |
| 预签名请求 | 固定时间、版本和 Unicode 路径下 GET/PUT/HEAD/DELETE URL 逐字节相同 |
| 原版与 Silo 本机调用 | 上传下载、元数据、列举和错误代码结果一致 |
| 官方单元测试 | 原版与 Silo 各 116 项；114 通过，2 项波兰语 locale 缺失而跳过 |
| 官方功能测试 | 原版与 Silo 各 49 项实际执行通过；1 项 AWS 区域用例不适用 |

## 上游测试来源与执行方式

上游仓库：https://github.com/minio/minio-py

固定 tag `7.2.20`，commit `f671ca948b35978c39a3100e4ae0e9b93416b911`。上游测试源码不修改；仅在测试导入时选择 `Minio` 或 `Silo` 类。测试加载器额外确认上游客户端测试确实使用选定类，不能把原版自身通过当成 Silo 通过。

复现：安装本 SDK，将上游仓库检出到该 tag，运行：

```bash
python tools/run_upstream_tests.py /path/to/minio-py --client minio --result baseline.json
python tools/run_upstream_tests.py /path/to/minio-py --client silo --result silo.json
# 设置 SILO_* 环境变量，在 scratch 目录运行，绝对路径指向本 SDK 的工具：
python /path/to/sdk/tools/run_upstream_functional.py /path/to/minio-py --client minio --result baseline-functional.json
python /path/to/sdk/tools/run_upstream_functional.py /path/to/minio-py --client silo --result silo-functional.json
```

功能测试对同一个本机 Silo 服务执行，生成独立随机桶；包含实际条件复制、分片与文件读写、范围读取、版本读取/删除、策略、分页、预签名过期和响应头、线程读写、Select 和 Snowball。上游 presigned POST 用例仅生成策略，未真正 POST 上传；通知用例只查询空配置。AWS 区域用例直接返回，已明确计入不适用，未当作实测。

## 保证边界

保证原 `minio 7.2.20` 客户端公开 API 的执行实现、参数、返回类型、异常类型和辅助类型保留；额外方法不会覆盖上游方法。测试统计和运行时证据见 ../verification.json 及本目录 upstream-*.json。

这不等于声明所有服务端功能和外部设施都已验证。TLS/SSE-C、KMS、外部身份源、真实通知投递、复制、对象锁/保留/法律保留、管理员调用等需要相应环境；未实测项保留原 SDK 实现，不能把 Silo 服务端支持情况替换成客户端保证。未来上游版本也不在当前固定版本保证内。

## Python 版本兼容

最低版本对齐原版 `>=3.9`。在本机 ARM64 Python 3.9.25 与 Python 3.13.3 上，各运行 67 项 SDK 测试全部通过；Python 3.9 也完成官方 114 项单元测试（另 2 项 locale 跳过）。`datetime.UTC` 在新版 Python 才存在，导出按上游运行时条件保持一致。

最终 wheel 在 Python 3.9 和 3.13 安装后均从 site-packages 导入，并完成真实上传下载；3.13 安装使用全新环境，依赖检查通过。
