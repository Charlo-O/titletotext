import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import filedialog
import requests
import os
from threading import Thread
from tenacity import retry, stop_after_attempt, wait_exponential
import json
import hashlib
import sqlite3  # 导入 SQLite
from googleapiclient.discovery import build  # 导入 Google API

class DocumentSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文档搜索助手")
        self.root.geometry("1000x800")
        
        # 配置主窗口的网格权重，使其可以跟随拖拽调整大小
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 添加停止处理的标志
        self.processing = False
        
        # 粉色主题配色
        self.style = ttk.Style()
        self.style.configure("Custom.TFrame", background="#FFE6E6")  # 浅粉色背景
        self.style.configure("Custom.TLabel", 
                           foreground="#4A4A4A",  # 深灰文字
                           background="#FFE6E6")  # 浅粉色背景
        self.style.configure("Custom.TButton", 
                           background="#FF9999",  # 主粉色按钮
                           foreground="#FFFFFF",  # 白色文字
                           borderwidth=0,
                           padding=10)
        self.style.map("Custom.TButton",
                      background=[('active', '#FF7777')])  # 按钮悬停色
        
        # API配置
        self.api_base = ""
        self.openai_api_key = ""

        # Google Search API 配置
        self.google_api_key = ""  # 已替换为你的 Google API Key
        self.google_cse_id = ""  # 已替换为你的 Google Custom Search Engine ID
        
        # 存储提取的标题和内容
        self.titles = []
        self.processed_content = {}

        # 移除数据库连接的初始化
        self.db_path = 'search_cache.db'
        # 创建表
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_results (
                    hash TEXT PRIMARY KEY,
                    result TEXT
                )
            ''')

        self.setup_ui()

    def setup_ui(self):
       # 主框架
        self.root.configure(bg="#FFE6E6")  # 浅粉色背景
        main_frame = ttk.Frame(self.root, padding="20", style="Custom.TFrame")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置main_frame的网格权重
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 文档输入区域
        input_frame = ttk.Frame(main_frame, style="Custom.TFrame")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(input_frame, text="输入文档内容:", style="Custom.TLabel").pack(anchor=tk.W)
        # 更新文本框样式
        text_style = {
            "bg": "#FFF0F0",  # 更浅的粉色背景
            "fg": "#4A4A4A",  # 深灰文字
            "insertbackground": "#FF9999"  # 粉色光标
        }
        
        self.input_text = scrolledtext.ScrolledText(
            input_frame, 
            height=10,
            **text_style
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame, style="Custom.TFrame")
        button_frame.grid(row=1, column=0, pady=10)
        
        ttk.Button(button_frame, text="选择文件", command=self.load_file, style="Custom.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="提取标题", command=self.extract_and_show_titles, style="Custom.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="开始处理", command=self.process_document, style="Custom.TButton").pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(button_frame, text="停止处理", command=self.stop_processing, style="Custom.TButton", state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.download_btn = ttk.Button(button_frame, text="下载结果", command=self.save_results, style="Custom.TButton", state=tk.DISABLED)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        # 标题预览区域
        preview_frame = ttk.Frame(main_frame, style="Custom.TFrame")
        preview_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(preview_frame, text="提取的标题预览:", style="Custom.TLabel").pack(anchor=tk.W)
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            height=8,
            **text_style
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 结果显示区域
        result_frame = ttk.Frame(main_frame, style="Custom.TFrame")
        result_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(result_frame, text="处理结果:", style="Custom.TLabel").pack(anchor=tk.W)
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            height=20,
            **text_style
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            main_frame,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # 进度标签
        self.progress_label = ttk.Label(main_frame, text="", style="Custom.TLabel")
        self.progress_label.grid(row=5, column=0, sticky=(tk.W, tk.E))
        
        # 进度条样式
        self.style.configure("Horizontal.TProgressbar",
                           background="#FF9999",  # 进度条颜色
                           troughcolor="#FFF0F0")  # 进度条背景色

    def load_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.input_text.delete('1.0', tk.END)
                self.input_text.insert('1.0', file.read())

    def extract_and_show_titles(self):
        text = self.input_text.get('1.0', tk.END)
        self.titles = self.extract_titles(text)
        
        # 清空预览区域并显示提取的标题
        self.preview_text.delete('1.0', tk.END)
        if isinstance(self.titles, list):
            for title in self.titles:
                self.preview_text.insert(tk.END, f"• {title}\n")
            message = '标题提取完成，请检查预览区域的标题是否正确。确认无误后点击"开始处理"继续。'
            messagebox.showinfo('提示', message)
        else:
            self.preview_text.insert(tk.END, f"提取出错：{self.titles}")

    def process_document(self):
        if not hasattr(self, 'titles') or not self.titles:
            messagebox.showwarning("警告", "请先提取标题！")
            return

        def process():
            self.processing = True
            self.stop_btn.config(state=tk.NORMAL)  # 启用停止按钮
            self.progress_var.set(0)
            self.result_text.delete('1.0', tk.END)
            total_titles = len(self.titles)
            
            for i, title in enumerate(self.titles, 1):
                if not self.processing:  # 检查是否应该停止处理
                    break
                    
                if isinstance(title, str) and title.strip():
                    progress = (i / total_titles) * 100
                    self.progress_var.set(progress)
                    self.progress_label.config(text=f"处理进度: {i}/{total_titles} ({int(progress)}%)")
                    
                    self.result_text.insert(tk.END, f"\n=== 处理标题: {title} ===\n")
                    result = self.search_content(title)
                    self.processed_content[title] = result
                    self.result_text.insert(tk.END, f"{result}\n")
                    self.result_text.see(tk.END)
            
            if self.processing:  # 只有在正常完成时才显示完成消息
                self.progress_label.config(text="处理完成！")
                self.download_btn.config(state=tk.NORMAL)
                messagebox.showinfo("完成", "所有内容处理完成！可以下载结果。")
            
            self.processing = False
            self.stop_btn.config(state=tk.DISABLED)  # 禁用停止按钮
            
        Thread(target=process).start()

    def save_results(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.result_text.get('1.0', tk.END))
            messagebox.showinfo("成功", "结果已保存！")

    def extract_titles(self, text):
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",  # 使用支持的模型
                "messages": [
                    {"role": "system", "content": "请从以下文本中提取所有标题，每行一个标题："},
                    {"role": "user", "content": text}
                ]
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                verify=False  # 如果有SSL证书问题
            )
            
            print("Request URL:", f"{self.api_base}/chat/completions")  # 调试信息
            print("Request Headers:", headers)
            print("Response Status:", response.status_code)
            print("Response:", response.text)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0 and 'message' in result['choices'][0] and 'content' in result['choices'][0]['message']:
                    return result['choices'][0]['message']['content'].split('\n')
                else:
                   return f"错误：API 返回结构异常 - {response.text}" 
            else:
                return f"错误：{response.status_code} - {response.text}"
            
        except Exception as e:
            print("Error details:", str(e))
            return f"错误：{str(e)}"
    
    def _get_cached_result(self, title):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            title_hash = hashlib.md5(title.encode()).hexdigest()
            cursor.execute("SELECT result FROM search_results WHERE hash = ?", (title_hash,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return None
    
    def _cache_result(self, title, result):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            title_hash = hashlib.md5(title.encode()).hexdigest()
            cursor.execute("INSERT OR REPLACE INTO search_results (hash, result) VALUES (?, ?)", 
                         (title_hash, result))
            conn.commit()

    def search_web(self, query):
        if not self.processing:  # 检查是否应该停止处理
            return ""
        try:
            service = build("customsearch", "v1", developerKey=self.google_api_key)
            res = (
                service.cse()
                .list(q=query, cx=self.google_cse_id)
                .execute()
            )
            search_results = []
            if 'items' in res:
                for item in res['items']:
                    search_results.append(item['snippet'])
            return "\n".join(search_results[:3])
        except Exception as e:
            print(f"网络搜索错误：{e}")
            return ""

    def search_content(self, title):
        cached_result = self._get_cached_result(title)
        if cached_result:
            print(f"Found cached result for '{title}'")
            return cached_result
        
        web_results = self.search_web(title)
        print(f"Web search result for '{title}':\n{web_results}")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f'''# 你是一位顶级AI研究员，专注于深度学习模型和计算机视觉领域。
## 任务：详细分析 `comfyui/models/models` 文件夹中的模型权重文件。联网查询后，请提供以下信息：
### 1. 模型类别：
    - 请识别并分类每个模型权重文件所属的类别（例如：Stable Diffusion 模型、LoRA、VAE、ControlNet 模型、AnimateDiff 模型、其他）。
    - 如果有不属于已知类别的模型，请尝试根据其文件名称或用途推断其类别。
### 2. 模型全称：
    - 给出每个模型权重文件的完整名称（包括文件扩展名）。
### 3. 功能详解：
    - 针对每个模型类别，提供详细的功能描述，包括：
        - 模型的用途和目标。
        - 模型的训练数据和方法（如果已知）。
        - 模型在图像生成或处理流程中的作用。
        - 模型的主要特性和优势。
        - 模型的限制和潜在问题。
        - 是否有相关的研究论文或文档可以参考。
    - 如果是特定类型的模型（例如，LoRA 或 ControlNet），请解释它们如何与其他模型协同工作。
### 4. 具体示例：
    -  提供一些实际的应用示例，展示每个模型类别在 ComfyUI 中可以实现的效果。
### 5. 注意事项：
    - 请确保所有信息的准确性，专业性，并避免模棱两可的描述。
    -  如果某个模型的信息不明确，请指出无法获取详细信息，并尽可能根据现有信息给出合理的推测。
### 6. 格式要求：
    -  使用清晰的标题和子标题组织你的输出。
    -  对于模型列表，可以使用编号或列表格式。
    -  使用清晰的 Markdown 语法，方便阅读和理解。

## 示例（仅供参考，请勿局限于此）：
用户输入：animatediff_models
输出：
**1.  AnimateDiff 模型 (Motion Modules)**
    - **模型类别:** 运动模块（Motion Modules）
    - **模型全称示例:**
        - `mm_sd15_v1.ckpt`
        - `mm_sd15_v2.ckpt`
        - `mm_sdxl_v10_beta.safetensors`
    - **功能详解:** 
        - **用途:**  为 Stable Diffusion 生成的图像引入运动和时间一致性，用于创建动画。
        - **训练方法:**  AnimateDiff 模型通过在大量视频数据集上训练神经网络来学习运动模式。
        - **作用:** 它们与基础 Stable Diffusion 模型一起工作，作为"运动附加组件"，在扩散过程中添加运动变化。
        - **主要特性:** 能够产生平滑且视觉上连贯的动画，可以通过调整"强度"和帧率来控制运动。
        - **限制:**  并非独立的图像生成器，必须与 Stable Diffusion 模型结合使用。
    - **实际示例:**  可以用于生成具有人物动作、场景变化或特效的动画视频。
**2. 其他 AnimateDiff 模型**
    - **模型类别:** 检查点特定模型、LoRA/LyCORIS 模型
    - **模型全称示例:** （请在此处列出示例，并进行功能解释）
        - （例如：`mm_sd15_v1_anime_specific.ckpt`, `motion_lora.safetensors`）
    - **功能详解:** （请在此处详细解释这些模型的功能）
'''
            
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": title}
                ]
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                verify=False  # 如果有SSL证书问题
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0 and 'message' in result['choices'][0] and 'content' in result['choices'][0]['message']:
                     content = result['choices'][0]['message']['content']
                     self._cache_result(title, content)
                     return content
                else:
                    return f"搜索错误：API 返回结构异常 - {response.text}"
            else:
                return f"搜索错误：{response.status_code} - {response.text}"
            
        except Exception as e:
            return f"搜索错误：{str(e)}"

    def stop_processing(self):
        """停止处理"""
        self.processing = False
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="处理已停止")
        messagebox.showinfo("提示", "处理已停止")

def main():
    root = tk.Tk()
    app = DocumentSearchApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
