# 硬件接线说明

- 整理日期：2026-09-28
- 主机：Raspberry Pi 5
- 系统：Bookworm，Python 3.11.2，使用 SSH 操作
- 引脚图：[figures/pinouts.png](../figures/pinouts.png)
- 已验证：I²S 声卡的录音与扬声器回放测试通过；当前 ALSA 声卡编号为 `card 0`、设备编号为 `device 0`。
- OLED 的具体型号、控制器及供电规格尚未确认；本文中的 OLED 接线适用于支持 3.3V 供电和 3.3V I²C 电平的四针模块。

## 1. 引脚编号与连接原则

本文的“物理针脚”是 Pi 的 40 针排针位置编号，与引脚图中间的 1–40 对应。“GPIO”是信号编号，两者不能混用，例如物理 12 脚对应 GPIO18。

接线或改线前，关机并拔掉 Pi 电源。模块如果之前连接 ESP32，应先断开那些连接，再按本文改接 Pi。

- Pi 和模块均为公排针时，可使用母对母杜邦线。
- 面包板不是必需品；共用信号可用一分二杜邦线、分线端子或焊接分线。
- 3.3V 和 5V 电源线分开；各模块的 GND 共地。
- 麦克风的 `SD` 是音频数据输出，功放的 `SD` 是启停控制，不能连接在一起。

## 2. I²S 麦克风

六个引脚：`LR / WS / SCK / SD / VDD / GND`。照片可以确认其为 I²S 接口，尚未确认麦克风芯片的具体型号。

| 麦克风引脚 | Pi 物理针脚 | Pi 信号 | 说明 |
| --- | ---: | --- | --- |
| `LR` / `L/R` | 9 | GND | 选择左声道 |
| `WS` | 35 | GPIO19 | 左右声道时钟 |
| `SCK` | 12 | GPIO18 | 音频位时钟 |
| `SD` | 38 | GPIO20 | 麦克风数据进入 Pi |
| `VDD` | 17 | 3.3V | 麦克风供电 |
| `GND` | 9 | GND | 接地 |

`LR` 和 `GND` 共用地线；麦克风 `VDD` 接 3.3V。

## 3. MAX98357A I²S 功放与扬声器

七个引脚：`LRC / BCLK / DIN / GAIN / SD / GND / VIN`。

| 功放引脚 | Pi 物理针脚 | Pi 信号 | 说明 |
| --- | ---: | --- | --- |
| `LRC` | 35 | GPIO19 | 左右声道时钟 |
| `BCLK` | 12 | GPIO18 | 音频位时钟 |
| `DIN` | 40 | GPIO21 | 接收 Pi 输出的音频数据 |
| `GAIN` | 不连接 | — | 使用载板默认增益 |
| `SD` | 36 | GPIO16 | 由音频驱动控制功放启停 |
| `GND` | 14 | GND | 接地 |
| `VIN` | 2 | 5V | 功放供电 |

功放 `SD` 接物理 36 脚，与本文的 `googlevoicehat-soundcard` 配置配套；这是当前采用的接法，替代早期讨论中的“SD 留空”。该 overlay 会占用 GPIO16。

扬声器两根线分别接功放绿色螺丝端子的 `+` 和 `−`。这是桥接输出，两根扬声器线都不能接 Pi GND。扬声器阻抗应至少为 4Ω，额定功率需与功放输出匹配。

### 共用时钟线

```text
Pi 物理12脚（GPIO18）──┬── 麦克风 SCK
                       └── 功放 BCLK

Pi 物理35脚（GPIO19）──┬── 麦克风 WS
                       └── 功放 LRC

麦克风 SD ───────────────> Pi 物理38脚（GPIO20）
Pi 物理40脚（GPIO21）────> 功放 DIN
Pi 物理36脚（GPIO16）────> 功放 SD
```

## 4. MAX30102 心率传感器

MH-ET LIVE 载板的八个引脚：`GND / RD / IRD / INT / VIN / SDA / SCL / GND`。基础读取使用四根线。

| MAX30102 引脚 | Pi 物理针脚 | Pi 信号 | 说明 |
| --- | ---: | --- | --- |
| `VIN` | 1 | 3.3V | 载板供电 |
| `SDA` | 3 | GPIO2 / SDA | I²C 数据 |
| `SCL` | 5 | GPIO3 / SCL | I²C 时钟 |
| 一个 `GND` | 6 | GND | 两个 GND 任选一个 |
| 另一个 `GND` | 不连接 | — | 基础接线无需重复连接 |
| `RD` | 不连接 | — | 基础读取不使用 |
| `IRD` | 不连接 | — | 基础读取不使用 |
| `INT` | 不连接 | — | 基础读取采用轮询 |

上电前确认载板的 `1V8 / 3V3` 总线上拉电平选择焊盘已选择 `3V3`，不能把三个焊盘全部短接。此前照片不足以确认焊桥状态。

MAX30102 的七位 I²C 地址为 `0x57`。模块提供红光和红外光的原始脉搏采样数据，软件需要计算 BPM，再将结果显示到 OLED。

## 5. 四针 I²C OLED

以下接法的前提是模块支持 3.3V 供电和 3.3V I²C 电平。接线认模块上的引脚文字，不能只按排针顺序判断；具体屏幕仍需确认是 SSD1306、SH1106 或其他控制器。

| OLED 引脚 | Pi 物理针脚 | Pi 信号 |
| --- | ---: | --- |
| `VCC` | 1 或 17 | 3.3V |
| `GND` | 20 | GND |
| `SDA` | 3 | GPIO2 / SDA |
| `SCL` | 5 | GPIO3 / SCL |

OLED 和 MAX30102 共用 I²C 数据、时钟线，地址必须不同。OLED 常见地址为 `0x3C` 或 `0x3D`，以实际扫描结果为准。

```text
Pi 物理3脚（GPIO2）────┬── MAX30102 SDA
                       └── OLED SDA

Pi 物理5脚（GPIO3）────┬── MAX30102 SCL
                       └── OLED SCL
```

## 6. Camera Module 3

Camera Module 3 保持连接 Pi 5 的相机排线接口，不连接到本文的 40 针排针。

## 7. Pi 上的接口配置与基础测试

以下命令均在 SSH 登录 Pi 后执行。

### 7.1 I²S 音频配置

`/boot/firmware/config.txt` 中使用：

```ini
[all]
dtoverlay=googlevoicehat-soundcard
```

不要同时加载其他占用同一组 I²S 引脚的音频 overlay。修改后重启生效。

列出录音、播放设备：

```bash
arecord -l
aplay -l
```

当前实测录音和播放设备均为 `card 0`、`device 0`，名字包含 `googlevoicehat`。HDMI 播放设备分别为 card 1 和 card 2。交接或修改配置后，以设备列表中的实际编号为准。

录音 8 秒，期间对麦克风说话：

```bash
arecord -D hw:0,0 -c 2 -r 48000 -f S32_LE -d 8 -t wav -V stereo ~/mic-test.wav
```

通过功放播放录音：

```bash
aplay -D plughw:0,0 ~/mic-test.wav
```

验收：录音电平随说话变化，扬声器能回放清晰的人声。`LR` 接地选择左声道，因此双声道录音主要由左声道承载信号。

### 7.2 I²C 配置

执行 `sudo raspi-config`，选择 `Interface Options → I2C → Yes`。

安装工具并扫描总线：

```bash
sudo apt install i2c-tools
i2cdetect -y 1
```

预期 MAX30102 显示 `57`；OLED 地址以扫描结果为准。扫描通过只证明设备响应，还需分别验证传感器采样和屏幕显示。

## 8. 参考资料

- [树莓派 GPIO 与供电说明](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
- [I²S 麦克风接线与测试](https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/raspberry-pi-wiring-test)
- [MAX98357A 功放引脚与扬声器输出](https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp/pinouts)
- [Google voiceHAT overlay：GPIO16 启停控制](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/arch/arm/boot/dts/overlays/googlevoicehat-soundcard-overlay.dts)
- [MH-ET LIVE MAX30102 厂家示例](https://github.com/MHEtLive/MH-ET-LIVE-max30102)
- [MAX30102 数据手册](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX30102.pdf)
