# 好玩的 SELPHY · fun-selphy

把 Doom 跑在 Canon SELPHY CP1500 照片打印机上。这里公开固件解码方法、离线分析工具、USB DBGmon 协议、RAM 程序加载方法，以及能够使用打印机实体按键操作的 Doom 移植源码。

**已在 CP1500、1.0.7.0 固件上实测运行。** 画面由打印机自己计算并显示；一次场景采样约 15 FPS，不是全游戏性能基准。运行于 RAM，没有刷写固件。当前无声音；电源重启后回到原厂程序，游戏需重新加载。

| 实体按键 | 游戏操作 |
| --- | --- |
| 上 / 下 | 前进 / 后退；菜单选择 |
| 左 / 右 | 转向 |
| OK | 菜单确认；游戏中开火 |
| 返回 | 打开菜单 / 返回 |
| 菜单 | 游戏中开门、使用；其他界面返回 |

## 目录

- [`docs/`](docs/)：完整路线、文件格式、协议、运行过程与已知限制。
- [`cp1500/unpack_cnn.py`](cp1500/unpack_cnn.py)：可复现的固件字节解码、区域解析、gzip 提取和完整性校验。
- [`cp1500/analysis/`](cp1500/analysis/)：各阶段的静态分析记录；历史记录以当时证据为限，后续实测结论见 docs。
- [`cp1500/usb/`](cp1500/usb/)：USB 枚举、调试握手、RAM 读写、临时符号调用、线程测试及加载器。
- [`cp1500/payload/`](cp1500/payload/)：ARM 小程序：返回 `OK`、内存分配、彩条、固件函数调用桥。
- [`cp1500/doom/port/`](cp1500/doom/port/)：显示、计时、按键、内存 WAD、最小系统接口和构建脚本。
- [`cp1500/doom/doomgeneric-master/`](cp1500/doom/doomgeneric-master/)：本项目实际使用的 Doomgeneric 源码快照及必要修改，保留上游许可和作者信息。

## 从源码开始

这是开发用工具集，不是一键安装器。推荐先阅读 [实机步骤](docs/DEVICE.md) 和 [固件解码](docs/FIRMWARE.md)。函数地址、结构尺寸和硬件寄存器配置针对已分析的 1.0.7.0，不应套用到其他型号或固件。

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

主机实测为 macOS Apple Silicon。USB 通过 libusb 的 ctypes 接口访问；例如安装 libusb 后，可按需设置 `LIBUSB_LIBRARY`。Doom 使用 `arm-none-eabi-gcc`、配套 binutils 和 newlib（Arm GNU Toolchain）；将工具链加入 `PATH`，或设置 `ARM_CC`。最小 `.S` 测试程序另使用支持 ARM 的 Clang。

1. 自行从佳能官方获得固件，把 `CP1500_1060.cnn` 与 `CP1500_1070.cnn` 放入 `cp1500/original/`。
2. 执行 `python3 cp1500/unpack_cnn.py`。解包器默认交叉验证这两个版本。
3. 自行取得 Doom 1.9 共享版 `doom1.wad`，放到 `cp1500/doom/doom1.wad`。原始文件 MD5 应为 `f0cefca49926d00903cf57551d901abe`，大小 4,196,020 字节。
4. 执行 `python3 cp1500/doom/port/repack_wad.py` 生成保留对齐的无音频测试数据。
5. 在 `PATH` / `ARM_CC` 配好工具链后，可离线构建：`python3 cp1500/doom/port/build.py`。默认链接地址只是构建占位值；实机加载器会按实际分配地址重建。

固件文件、解包后的代码、游戏数据、工具链、设备序列号、个人路径、实机 RAM 备份与原始会话日志均不随仓库发布。公开的是方法与源码；这些输入由运行者本地提供或生成。

## 主要发现

- 固件前 640 KiB 不是无法分析的密文：恢复了一个固定的 256 字节置换，并在固件自身解码函数中交叉确认。
- ARM9 / ThreadX；初始化时钟计算为 264 MHz。MMU 配置了 128 MiB RAM 地址范围，不能把映射大小当作芯片实测容量。
- ST7272A 显示路径，最终输出 320×240、24 位三通道；输入为 640×240，相邻横向像素平均。
- 普通打印数据流接受一个 12 字节调试启用命令；随后出现 DBGmon Bulk OUT `0x07` / IN `0x87`。
- 调试协议可读写 RAM，`C` 命令可通过 RAM 符号表调用类型 6 扩展；已验证加载、调用、返回和恢复。
- 按键缓存不持续更新时，可调用现有 GPIO/ADC 采样及按键解码函数取得真实输入。
- WAD 直接映射到 ARM 内存时必须保留 4 字节对齐；初版精简丢失 padding 导致渲染初始化黑屏，修复后游戏正常出帧。

关于签名：已检查的升级校验路径包含 XOR32 和 gzip CRC；未在该路径确认数字签名验证，**这不能证明完整启动链没有签名，也不代表自定义固件已可安全刷入**。本项目没有实现或验证刷机。

## 许可与来源

本项目原创代码以 **GPL-2.0-or-later** 发布，见 [LICENSE](LICENSE)。第三方代码维持各文件原许可与署名。Doomgeneric 来源为 [ozkl/doomgeneric](https://github.com/ozkl/doomgeneric)，基于 id Software Doom 和 Chocolate Doom 等项目。详见 [来源与许可](docs/PROVENANCE.md)。佳能名称与 SELPHY 商标属于其权利人，本项目为独立研究。
