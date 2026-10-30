# 实机路线与协议

本页记录 CP1500 1.0.7.0 上已经完成的实验。以下地址均为该版本运行时地址，不能跨固件复用。工具不会自动识别所有固件差异。先完成 README 的离线准备，再连接 USB；一次只连接一台 CP1500，关闭占用打印接口的程序。

## 复现顺序

```sh
python3 cp1500/usb/inspect_usb.py
python3 cp1500/usb/enable_dbgmon.py
python3 cp1500/usb/handshake.py
python3 cp1500/usb/read_ram_sample.py
python3 cp1500/usb/test_return_ok.py
```

RAM 读回和 `OK` 小程序确认后，可进一步运行分配器、线程和彩条测试。目录中的 `probe_*`、`recover_page_probe.py`、`capture_*` 和 `reload_stage.py` 是研究期间的实验工具，部分包含特定会话的地址或状态假设，不是顺序执行的安装步骤。尤其不要运行历史恢复脚本去释放一个新会话的 RAM。

完成离线构建与 WAD 重打包后，从新开机的空闲打印机启动完整游戏：

```sh
CP_STAGE=10 python3 cp1500/usb/run_doom.py
python3 cp1500/usb/check_doom.py
python3 cp1500/usb/stop_doom.py
```

默认 `CP_STAGE=1` 只运行最小线程诊断。`2` 测试内存；`10` 运行游戏循环。上传器直接写入代码和 WAD，不做完整回读。运行状态保存在本地 `cp1500/usb/doom-runtime.json`；不能跨电源重启复用。停止脚本设置游戏自己的退出标志并等待线程返回；不释放其全部分配，不会自动恢复原厂 UI。需要回到原厂界面时正常关机、开机即可。不要在仍运行的游戏上重复执行初始加载器。

## USB 与 DBGmon

设备 VID:PID `04a9:3302`。普通打印接口 0、alt 0、OUT `0x01` 收到 `2b0100000000000000000000` 后启用调试接口 2，Bulk OUT `0x07` / IN `0x87`。

调试重置为控制传输 `bmRequestType=0x41, bRequest=0, wValue=0x81, wIndex=2, length=0`。发送 credit 头 `04000000000000fb`，实测回复 `14000000000000eb`。接着发送通道打开数据 `00000f0001000101010e040e040000`。打开回调异步执行，需要短暂等待后继续发送 credit 取回复；仅发一次并立即等待可能看起来卡住。

外层头 8 字节：byte 0 为 credit，byte 1 为子包数，+2 为小端 u16 长度；头部字节和模 256 为 255。头与 payload 分开发送。通道子头 6 字节：byte 1 通道号、+2 小端 u16 长度、byte 4 credit。`dbgmon_link.py` 和 `bulk_transfer_helpers.py` 为实际封装。

命令以 ESC + `D` / `d` 开始。`R/W` 逐字节访问，地址在 +3，写值在 +7；`Aw` 的 +4 设置写指针，`o` 的 +3 为 u16 长度并跟随数据；`Mr` 设置读指针，`r` 读取指定长度。`C` 按名称查找 RAM 符号表的类型 6 记录并调用指针。函数收到 `r0=请求缓冲区, r1=请求长度, r2=请求缓冲区+0x400`（回复长度字位置），输出放回请求缓冲区。

## RAM、缓存和调用约定

MMU 映射低地址 `0x00000000..0x07ffffff`，`0x40000000..0x47ffffff` 为另一段不缓存映射；有限样本已确认对应 RAM 内容一致。映射 128 MiB 不等于物理容量测量。低地址首 MiB 为 write-through，其余使用 write-back。

符号表 `0x7d7e6c`、记录大小 28 字节；名称 +8、长度 12，类型 +0x14、函数指针 +0x18。元数据从 `0x70c71c` 起。本工具借用未使用的表尾和临时 `cp_*` 记录，退出时恢复；不会把替换写进固件。加载通过已有调试功能和 RAM 扩展表完成。

ARM 模式、软浮点、AAPCS：前四个参数在 r0-r3，其余在栈上；桥保存被调用者保存寄存器并维护栈对齐。调用桥源码为最终依据。代码写入后调用 D-cache 清理 `0x3211e4` 和 I-cache 失效 `0x10d84`，参数采用本固件的 `[start,end]` 约定。

| 功能 | 地址与参数 |
| --- | --- |
| malloc | `0x32d524(size)`，0 表示失败 |
| free | `0x31db84(0x70bae0, ptr)` |
| DMB 分配 | `0x324c0c(out_handle, previous=0, flags=0, 0)`，32 KiB 页 |
| DMB 地址 / 释放 | `0x324b84(handle)` / `0x324eac(0, handle)` |
| ThreadX 创建 | `0x2c2d74(tcb,name,entry,input,stack,size,priority,threshold,slice,autostart,0x220)` |
| resume / terminate / delete | `0x2c3138` / `0x2c3188` / `0x2c2fbc` |
| sleep / tick | `0x2c0f0c` / `0x2c1720`，约 1000 tick/s |

普通堆申请 16 MiB 失败，游戏改用 DMB 连续 221 页（约 6.9 MiB），前 116 页容纳代码、BSS 和内部堆，其后是精简 WAD。线程另有 256 KiB 栈。加载器按实际分配基址重新链接，不能假定历史地址仍可用。

## 显示和实体按键

显示函数 `0x673dc` 接受 640×240×3 输入，横向相邻像素平均得到 320×240 输出。Doom 原始画面 320×200，移植层负责转换和留边。实机确认了彩条、游戏画面和实体键操作。

键位：上 `08`、下 `10`、左 `02`、右 `04`、OK `40`、返回 `80`、菜单 `20`，电源 `01` 不映射。仅调用 `0x127014` 会取得停滞的缓存；平台层调用 `0x126c8c` 采样，再调用 `0x126f9c` 解码。按下与松开分别维护状态，避免切换菜单时卡键。暂无侧移、换武器与声音。

最初黑屏来自精简 WAD 时删掉了 lump 间的 padding，导致 ARM 非对齐访问。`repack_wad.py` 保留 4 字节边界；不要换回简单拼接版本。
