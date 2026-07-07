# TTS 小工具 (TXT to Speech)

一个简单易用的本地 TXT 文本转语音工具，基于微软高音质的 `edge-tts` 接口。无需配置复杂的 API 密钥，开箱即用，支持图形化界面和命令行批量按章节转换！

## 🌟 功能特性

- **图形界面 (GUI)**：提供友好的桌面窗口，支持选择 TXT 文件、选择多种发音人。
- **批量按章节转换 (CLI)**：支持自动识别 TXT 文本中的“第一章”、“第二章”、“序言”等结构，批量分割并生成独立的 MP3 音频文件。
- **高音质**：调用微软 Edge 浏览器的真实发音人 API（支持晓晓、云希等多款经典音色）。

## 📦 环境依赖

使用前请确保你的系统已经安装了 Python 3 和 `pip`。

```bash
# 安装所需依赖
pip install -r requirements.txt
```

*(如果遇到网络问题，建议使用国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`)*

## 🚀 使用说明

### 1. 桌面图形界面版 (推荐)
如果你只是想简单地把一整个 TXT 文件转换成一个音频，直接运行界面程序即可：

```bash
python tts_app.py
```
在弹出的窗口中点击“浏览”选择文件，选择心仪的声音，点击转换即可。

### 2. 命令行批量分章节转换版
如果你下载了一本长篇小说（比如包含多个章节的 TXT 文件），希望按章节生成几十个独立的 MP3 文件，可以使用 `batch_tts.py` 脚本：

```bash
python batch_tts.py "你的小说路径.txt" -o "输出文件夹路径" -v zh-CN-XiaoxiaoNeural
```

**参数说明**：
- `input_file`: 必填，你需要转换的 TXT 文本路径。
- `-o / --output_dir`: 选填，保存生成的 mp3 文件夹路径，默认是当前目录下的 `audio_output`。
- `-v / --voice`: 选填，发音人名称（如 `zh-CN-XiaoxiaoNeural`、`zh-CN-YunxiNeural`），默认是晓晓。

## 🤝 贡献
欢迎提交 Issue 和 Pull Request 来完善这个小工具。
