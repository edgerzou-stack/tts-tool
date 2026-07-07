import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import asyncio
import edge_tts
import os

VOICES = {
    "晓晓 (温柔女声)": "zh-CN-XiaoxiaoNeural",
    "云希 (阳光男声)": "zh-CN-YunxiNeural",
    "云健 (成熟男声)": "zh-CN-YunjianNeural",
    "晓伊 (可爱童声)": "zh-CN-XiaoyiNeural",
    "辽宁晓北 (东北口音)": "zh-CN-liaoning-XiaobeiNeural",
    "陕西晓妮 (陕西方言)": "zh-CN-shaanxi-XiaoniNeural",
}

class TTSTool:
    def __init__(self, root):
        self.root = root
        self.root.title("TXT 转语音小工具 (Edge-TTS)")
        # 居中显示窗口
        window_width = 480
        window_height = 280
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)
        
        # 文件选择
        self.file_path = tk.StringVar()
        
        tk.Label(root, text="1. 选择 TXT 文件:", font=("Arial", 11, "bold")).pack(pady=(20, 5), anchor="w", padx=30)
        
        file_frame = tk.Frame(root)
        file_frame.pack(fill="x", padx=30)
        
        self.file_entry = tk.Entry(file_frame, textvariable=self.file_path, state='readonly', font=("Arial", 10))
        self.file_entry.pack(side=tk.LEFT, fill="x", expand=True, ipady=3)
        
        tk.Button(file_frame, text="浏览...", command=self.browse_file, width=8).pack(side=tk.RIGHT, padx=(10, 0))
        
        # 声音选择
        tk.Label(root, text="2. 选择发音人:", font=("Arial", 11, "bold")).pack(pady=(15, 5), anchor="w", padx=30)
        self.voice_var = tk.StringVar()
        self.voice_cb = ttk.Combobox(root, textvariable=self.voice_var, values=list(VOICES.keys()), state='readonly', font=("Arial", 10))
        self.voice_cb.current(0)
        self.voice_cb.pack(fill="x", padx=30, ipady=3)
        
        # 转换按钮
        self.convert_btn = tk.Button(root, text="▶ 开始转换", command=self.start_conversion, 
                                     bg="#4CAF50", fg="black", font=("Arial", 12, "bold"), pady=5)
        self.convert_btn.pack(pady=20, fill="x", padx=30)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪。注意：转换过程需要连接网络。")
        tk.Label(root, textvariable=self.status_var, fg="#666666", font=("Arial", 9)).pack()
        
    def browse_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filepath:
            self.file_path.set(filepath)
            
    def start_conversion(self):
        txt_file = self.file_path.get()
        if not txt_file or not os.path.exists(txt_file):
            messagebox.showerror("错误", "请先选择一个有效的 TXT 文件！")
            return
            
        # 自动生成默认保存路径 (和 txt 同目录，同名)
        default_save = os.path.splitext(txt_file)[0] + ".mp3"
        save_path = filedialog.asksaveasfilename(
            title="保存音频文件",
            defaultextension=".mp3",
            filetypes=[("MP3 Audio", "*.mp3")],
            initialfile=os.path.basename(default_save),
            initialdir=os.path.dirname(default_save)
        )
        
        if not save_path:
            return
            
        voice_key = self.voice_var.get()
        voice_id = VOICES.get(voice_key, "zh-CN-XiaoxiaoNeural")
        
        # 禁用按钮，更新状态
        self.convert_btn.config(state=tk.DISABLED, text="⏳ 正在转换中...")
        self.status_var.set("正在调用微软语音接口生成音频，这可能需要一点时间...")
        
        # 在独立线程中运行，避免阻塞主界面卡死
        threading.Thread(target=self.run_tts, args=(txt_file, save_path, voice_id), daemon=True).start()

    def run_tts(self, txt_file, save_path, voice_id):
        try:
            # 尝试使用 utf-8 读取，如果失败尝试 GBK (兼容 Windows 默认编码)
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    text = f.read().strip()
            except UnicodeDecodeError:
                with open(txt_file, 'r', encoding='gbk') as f:
                    text = f.read().strip()
                
            if not text:
                self.root.after(0, self.conversion_done, False, "TXT 文件内容为空！")
                return
                
            asyncio.run(self.async_tts(text, save_path, voice_id))
            self.root.after(0, self.conversion_done, True, "转换成功！音频已保存。")
        except Exception as e:
            self.root.after(0, self.conversion_done, False, f"转换失败:\n{str(e)}")
            
    async def async_tts(self, text, save_path, voice_id):
        communicate = edge_tts.Communicate(text, voice_id)
        await communicate.save(save_path)
        
    def conversion_done(self, success, message):
        self.status_var.set(message)
        self.convert_btn.config(state=tk.NORMAL, text="▶ 开始转换")
        if success:
            messagebox.showinfo("成功", message)
        else:
            messagebox.showerror("错误", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = TTSTool(root)
    # macOS 上需要调用这个方法来确保窗口显示在最上层
    root.eval('tk::PlaceWindow . center')
    root.lift()
    root.attributes('-topmost',True)
    root.after_idle(root.attributes,'-topmost',False)
    root.mainloop()
