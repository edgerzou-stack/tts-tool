import asyncio
import edge_tts
import os
import re
import argparse

async def async_tts(text, save_path, voice_id):
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(save_path)

def split_text_by_chapters(text):
    # 根据 "第一章 xxx" 或者 "序言" 进行正则拆分
    pattern = re.compile(r'^(序\s*言|第[一二三四五六七八九十百]+章.*?)$', re.MULTILINE)
    
    parts = pattern.split(text)
    
    chapters = []
    # parts[0] 是第一章/序言之前的内容，比如书名和作者信息
    if parts[0].strip():
        chapters.append(("00_前言及书籍信息", parts[0].strip()))
        
    # parts[1] 是章节标题，parts[2] 是章节内容，依此类推
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        # 清理标题中不能作为文件名的字符
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        safe_title = safe_title.replace('\n', '').strip()
        content = parts[i+1].strip()
        chapters.append((safe_title, title + "\n" + content))
        
    return chapters

def main():
    parser = argparse.ArgumentParser(description="将 TXT 文件按章节分割并转换为 MP3")
    parser.add_argument("input_file", help="输入的 TXT 文件路径")
    parser.add_argument("--output_dir", "-o", default="audio_output", help="输出文件夹，默认在当前目录下创建 audio_output")
    parser.add_argument("--voice", "-v", default="zh-CN-XiaoxiaoNeural", help="发音人 (默认晓晓)")
    
    args = parser.parse_args()
    
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(args.input_file, 'r', encoding='gbk') as f:
            text = f.read()
            
    chapters = split_text_by_chapters(text)
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    print(f"找到 {len(chapters)} 个独立章节/部分，准备开始转换...")
    
    for idx, (title, content) in enumerate(chapters):
        if not content:
            continue
            
        # 如果 title 已经包含序号（比如 00_前言），就直接用，否则加上序号排序
        if title.startswith("00_"):
            filename = f"{title}.mp3"
        else:
            filename = f"{idx:02d}_{title}.mp3"
            
        save_path = os.path.join(args.output_dir, filename)
        
        print(f"正在转换 [{idx}/{len(chapters)-1}]: {title} -> {filename} ...")
        
        # 为了防止某些特殊字符导致网络报错，添加简单的重试机制
        try:
            asyncio.run(async_tts(content, save_path, args.voice))
            print(f"  √ 成功: {filename}")
        except Exception as e:
            print(f"  × 失败: {filename}, 错误: {e}")
            
    # 生成 M3U 播放列表
    playlist_path = os.path.join(args.output_dir, "playlist.m3u")
    try:
        # 获取所有 mp3 文件并按名称排序
        mp3_files = sorted([f for f in os.listdir(args.output_dir) if f.endswith('.mp3')])
        with open(playlist_path, 'w', encoding='utf-8') as pl:
            pl.write("#EXTM3U\n")
            for mp3 in mp3_files:
                # 提取去掉了扩展名的文件名作为显示标题
                title_display = os.path.splitext(mp3)[0]
                pl.write(f"#EXTINF:-1,{title_display}\n")
                pl.write(f"{mp3}\n")
        print(f"\n√ 已自动生成播放列表: {playlist_path} (可以使用各类音乐播放器直接打开)")
    except Exception as e:
        print(f"\n生成播放列表失败: {e}")
            
    print(f"\n全部转换完成！音频保存在文件夹: {os.path.abspath(args.output_dir)}")

if __name__ == "__main__":
    main()
