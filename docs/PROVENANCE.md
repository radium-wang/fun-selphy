# 来源、许可与发布边界

- 原创解包器、分析工具、USB 实现、ARM 载荷与 CP1500 平台移植：GPL-2.0-or-later，版权署名 SELPHY contributors。
- `cp1500/doom/doomgeneric-master/` 是实际构建使用的源码快照，上游为 https://github.com/ozkl/doomgeneric 。保留源码中的作者、版权、许可和历史说明；包含 id Software、Chocolate Doom、Doomgeneric 贡献者代码，适用各文件原有许可。本地改动随该源码快照一并提供，没有只发布二进制。
- 固件输入来自 Canon CP1500 官方更新，研究了 1.0.6.0 与 1.0.7.0。仓库提供解码方法、格式与地址研究，不分发佳能固件或解包出的固件代码。
- 测试游戏数据为 Doom 1.9 shareware `doom1.wad`，不是本项目原创，不随仓库分发。校验值和精简脚本用于复现；使用者自行取得合法副本。
- Arm GNU Toolchain、Python 依赖、libusb 不随仓库打包。各自保留原许可。

未固定上游提交号的快照不推断为任何特定版本。研究报告记录静态推断和实验过程；README 与 DEVICE 中明确标记的实测结果优先于早期猜测。时钟来自寄存器配置推导，物理 RAM 容量没有通过拆机确认；性能数据来自单一场景。未实现固件刷写与持久安装。
