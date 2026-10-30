# 固件格式与“解密”方法

该 `.cnn` 文件使用固定的单字节置换。以下 `TABLE` 的第 n 项就是输入字节 n 解码后的值：

```python
TABLE = bytes(
    [0] + list(range(255, 0, -17))
    + [x for x in range(255, 0, -1) if x % 17]
)
decoded = raw.translate(TABLE)
```

它是可逆的编码/混淆，不是需要秘钥的现代加密。逆表可以通过 `bytes(TABLE.index(x) for x in range(256))` 构造。固件 main 文件偏移 `0xaa38` 的解码函数与 `0x4b243d` 的表支持这一结论。

完整视图仍需保留原始未编码字段：`[0xa0000,0xa0004)`、`[0xa0024,0xa0028)` 和最后 12 字节。不要把全文件 translate 的结果当作刷机镜像。

前缀开头是记录数量及其按位取反值；两个版本均为 374 条 5 字节记录，布局 `<IB`，用于初始化寄存器。之后保存 boot 加载地址、长度及取反校验，boot 数据从原文件 `0x762` 开始。

原文件 `0xa0000` 的 `OART` 区域包含 98 个 `<III` 表项。存储地址减 `0x80000000` 得文件偏移。flag=1 项为经过同一置换编码的 gzip 主程序；解包器检查 gzip CRC、长度及解码可逆性。两个版本主程序均为 7,724,800 字节。

| 输入文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| CP1500_1060.cnn | 6,216,468 | `37b7d60f9769814365a4d9ea27f409c9fe923dced5567bf0d05e628242968a76` |
| CP1500_1070.cnn | 6,217,080 | `6d87a06fa84644922682bd16e77886fcc7bf19fa7ba2789b0833be96f050e36e` |

## 地址与复现

main 初始载入后按 scatter 表搬移。文件 `0x980` 起的主代码段搬到运行地址 `0x900`，所以该段内 runtime = file offset − `0x80`。初始化数据段有另一套映射，不能全文件统一减 `0x80`。`inspect_main.py` 输出主要是文件偏移；boot 工具的 `0x500000` 标签是反汇编坐标，不能直接当全部最终运行地址。

```sh
python3 cp1500/unpack_cnn.py
python3 cp1500/audit_contents.py
python3 cp1500/audit_hardware.py
python3 cp1500/inspect_main.py 0xaa38 0xab54
```

详细边界、时钟和 MMU 证据见 `cp1500/analysis/`。没有发布固件或完整解包结果，使用者从官方取得输入后可自行复现。
