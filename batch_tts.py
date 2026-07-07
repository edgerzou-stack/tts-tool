import asyncio
import edge_tts
import os
from tqdm.asyncio import tqdm

async def async_tts(text, save_path, voice_id, sem, title):
    async with sem:
        communicate = edge_tts.Communicate(text, voice_id)
        total_chars = len(text)
        processed_chars = 0
        
        # 设置 leave=False，这样转换完后进度条会自动消失，保持终端整洁
        pbar = tqdm(total=total_chars, desc=f"转换中: {title[:15]}...", unit="字", leave=False, bar_format="{desc} {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}")
        
        with open(save_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "SentenceBoundary":
                    # 获取当前句子长度
                    chunk_len = len(chunk["text"])
                    processed_chars += chunk_len
                    # 避免超过总长度
                    if processed_chars > total_chars:
                        chunk_len -= (processed_chars - total_chars)
                        processed_chars = total_chars
                    pbar.update(chunk_len)
        
        # 补全最后一点进度
        if processed_chars < total_chars:
            pbar.update(total_chars - processed_chars)
        
        pbar.close()

def split_text_by_chapters(text):
    # 支持匹配 "第一章 xxx"、"1、 xxx"、"1、xxx" 以及 "序言"
    # 添加一个简单的断言过滤掉文本内刚好以 "1、" 开头的普通句子(比如特定的印第安人名言引用)
    pattern = re.compile(r'^(序\s*言|第[一二三四五六七八九十百]+章.*?|\d{1,2}、\s*(?!凡有辖内).*?)$', re.MULTILINE)
    
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

async def process_all_chapters(chapters, output_dir, voice):
    # 使用 Semaphore 控制并发数，避免被微软服务器限制或封禁 (最大同时转换 3 个章节)
    sem = asyncio.Semaphore(3)
    tasks = []
    
    for idx, (title, content) in enumerate(chapters):
        if not content:
            continue
            
        if title.startswith("00_"):
            filename = f"{title}.mp3"
        else:
            filename = f"{idx:02d}_{title}.mp3"
            
        save_path = os.path.join(output_dir, filename)
        
        # 包装任务，传递 title 以供进度条显示
        task = asyncio.create_task(convert_and_log(idx, len(chapters)-1, title, filename, content, save_path, voice, sem))
        tasks.append(task)
        
    await asyncio.gather(*tasks)

async def convert_and_log(idx, total, title, filename, content, save_path, voice, sem):
    try:
        await async_tts(content, save_path, voice, sem, title)
        print(f"  √ 成功: {filename}")
    except Exception as e:
        print(f"  × 失败: {filename}, 错误: {e}")

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
        
    print(f"找到 {len(chapters)} 个独立章节/部分，准备开始并发转换...")
    
    # 启动并发转换
    asyncio.run(process_all_chapters(chapters, args.output_dir, args.voice))
            
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
