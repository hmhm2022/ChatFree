"""
ChatFree - AI辅助工具
Copyright (c) 2024 hmhm2022
Licensed under the MIT License - see LICENSE file for details
"""

import json
import os
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import keyboard
import win32clipboard
from ai_api import ChatSession
import pystray
from PIL import Image
import threading
import ctypes

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ChatFree')

class DialogWindow:
    def __init__(self, parent, selected_text=None, config=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AI 助手")
        self.dialog.geometry("600x400")
        self.dialog.minsize(400, 300)
        self.dialog.attributes('-topmost', True)
        
        self.selected_text = selected_text
        self.config = config
        
        self.chat_session = ChatSession(
            api_key=config['api_key'],
            base_url=config['api_url'],
            model=config['model'],
            system_prompt={"role": "system", "content": "你是一个智能AI助手。"}
        )
        
        self.txt_history = scrolledtext.ScrolledText(self.dialog, height=12)
        self.txt_history.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.txt_history.tag_configure('system', 
            foreground='#FF4D82', 
            background='#FFE6EE', 
            spacing1=5, 
            spacing3=5, 
            font=('Microsoft YaHei', 10, 'bold') 
        )
        
        self.txt_history.tag_configure('ai',
            foreground='#003366', 
            background='#E6F3FF', 
            spacing1=5,
            spacing3=5,
            font=('Microsoft YaHei', 10, 'bold')
        )
        
        self.txt_history.tag_configure('user',
            foreground='#004D26', 
            background='#E6FFE6', 
            spacing1=5,
            spacing3=5,
            font=('Microsoft YaHei', 10, 'bold')
        )
        
        self.txt_history.tag_configure('text',
            foreground='#000000',  
            background='#F0F0F0',  
            spacing1=5,
            spacing3=5,
            lmargin1=20, 
            lmargin2=20,  
            relief='solid', 
            borderwidth=1, 
            font=('Microsoft YaHei', 10)
        )
        
        self.txt_history.configure(
            background='#FAFAFA', 
            font=('Microsoft YaHei', 10) 
        )
        
        self.txt_input = scrolledtext.ScrolledText(self.dialog, height=8)
        self.txt_input.pack(fill='x', padx=10, pady=5)
        
        self.txt_input.bind('<Return>', self.on_enter)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        self.btn_translate = ttk.Button(btn_frame, text="翻译", command=self.translate)
        self.btn_translate.pack(side='left', padx=5)
        
        self.btn_explain = ttk.Button(btn_frame, text="解释", command=self.explain) 
        self.btn_explain.pack(side='left', padx=5)
        
        self.btn_summarize = ttk.Button(btn_frame, text="总结", command=self.summarize)
        self.btn_summarize.pack(side='left', padx=5)
        
        self.btn_ask = ttk.Button(btn_frame, text="询问", command=self.ask)
        self.btn_ask.pack(side='left', padx=5)
        
        if selected_text:
            self.append_message("系统", "您选中的文本是:")
            self.append_message("文本", selected_text)
            self.append_message("系统", "您可以选择翻译解释或询问相关问题。")
        else:
            self.btn_translate['state'] = 'disabled'
            self.btn_explain['state'] = 'disabled'
            self.btn_summarize['state'] = 'disabled'
            self.append_message("系统", "您没有选中任何文本。")
            self.append_message("系统", "您可以直接在下方输入框中提问。")
            
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'+{x}+{y}')
        
    def on_enter(self, event):
        """回车发送消息"""
        if not event.state & 0x1:
            self.send_message()
            return 'break'
            
    def append_message(self, role, content, stream=False):
        """添加消息到历史记录"""
        tag = {
            "系统": "system",
            "AI": "ai", 
            "用户": "user",
            "文本": "text"
        }.get(role, None)
        
        if not stream:
            if tag and tag != "text":
                self.txt_history.insert('end', '\n')
                self.txt_history.insert('end', f"{role}: {content}\n", tag)
            else:
                self.txt_history.insert('end', '\n')
                self.txt_history.insert('end', f"{content}\n", "text")
            self.txt_history.see('end')
        else:
            if tag and tag != "text":
                self.txt_history.insert('end', '\n')
                self.txt_history.insert('end', f"{role}: ", tag)
                for char in content:
                    self.txt_history.insert('end', char, tag)
                    self.txt_history.see('end')
                    self.dialog.update()
                    time.sleep(0.01)
                self.txt_history.insert('end', '\n')
            else:
                self.txt_history.insert('end', '\n')
                for char in content:
                    self.txt_history.insert('end', char, "text")
                    self.txt_history.see('end')
                    self.dialog.update()
                    time.sleep(0.01)
                self.txt_history.insert('end', '\n')
            self.txt_history.see('end')
    
    def send_message(self):
        """发送消息"""
        user_input = self.txt_input.get('1.0', 'end-1c').strip()
        if not user_input:
            return
            
        self.append_message("用户", user_input)
        self.txt_input.delete('1.0', 'end')
        
        response = self.chat_session.chat(user_input, temperature=self.config['temperature'])
        if response:
            self.append_message("AI", response, stream=True)
    
    def translate(self):
        """翻译功能"""
        if not self.selected_text:
            return
        self.btn_translate['state'] = 'disabled'
        prompt = f"请将以下文本翻译成中文:\n{self.selected_text}"
        self.append_message("用户", "请求翻译:")
        self.append_message("文本", self.selected_text)
        
        response = self.chat_session.chat(prompt)
        if response:
            self.append_message("AI", response, stream=True)
    
    def explain(self):
        """解释功能"""
        if not self.selected_text:
            return
        self.btn_explain['state'] = 'disabled'
        prompt = f"请解释以下文本的含义:\n{self.selected_text}"
        self.append_message("用户", "请求解释:")
        self.append_message("文本", self.selected_text)
        
        response = self.chat_session.chat(prompt)
        if response:
            self.append_message("AI", response, stream=True)
    
    def summarize(self):
        """总结功能"""
        if not self.selected_text:
            return
        self.btn_summarize['state'] = 'disabled'
        prompt = f"请对以下文本进行概括总结:\n{self.selected_text}"
        self.append_message("用户", "请求总结:")
        self.append_message("文本", self.selected_text)
        
        response = self.chat_session.chat(prompt)
        if response:
            self.append_message("AI", response, stream=True)
    
    def ask(self):
        """询问功能"""
        user_input = self.txt_input.get('1.0', 'end-1c').strip()
        if not user_input:
            return
            
        prompt = f"关于文本: {self.selected_text}\n问题: {user_input}"
        self.append_message("用户", f"问题: {user_input}")
        
        response = self.chat_session.chat(prompt)
        if response:
            self.append_message("AI", response, stream=True)
        
        self.txt_input.delete('1.0', 'end')

class ChatFreeApp:
    def __init__(self, master):
        self.master = master
        self.master.title("ChatFree")
        
        self.master.withdraw()
        
        try:
            self.master.iconbitmap(default="linuxdo.ico")
        except:
            print("图标加载失败")
            
        self.master.resizable(width=False, height=False)
        self.master.state('normal')
        
        self.master.deiconify()
        
        self.master.minsize(400, 400)
        
        self.master.attributes('-alpha', 1.0)
        self.master.wm_attributes('-toolwindow', 0)
        
        self.setup_tray()
        
        self.config_file = "config.json"
        self.load_config()
        self.chat_session = None
        self.master.minsize(400, 600)
        
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)
    
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text='说明')
        
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', padx=20, pady=(20,10))
        ttk.Label(title_frame, text="ChatFree", font=("Arial", 24, "bold")).pack(side='left')
        ttk.Label(title_frame, text="v0.2.8", font=("Arial", 12)).pack(side='left', padx=(10,0), pady=8)
        
        intro_frame = ttk.LabelFrame(main_frame, text="功能介绍")
        intro_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(intro_frame, text="ChatFree一个AI辅助工具，集成了智能文本补全和AI对话助手功能，让AI摆脱浏览器的束缚。", 
                 wraplength=360, justify='left').pack(padx=10, pady=5)
        
        usage_frame = ttk.LabelFrame(main_frame, text="使用方法")
        usage_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(usage_frame, text="1. 文本补全:", font=("Arial", 10, "bold")).pack(anchor='w', padx=10, pady=(5,0))
        completion_text = f"""• 选择文本: 在任意编辑器中选中需要续写的文本
• 快捷键: 按下 {self.hotkey} 开始智能补全长按Ctrl键终止补全
• 补全过程: 支持自定义Prompt，自由定义风格、字数等
• 历史记录: 可在设置中选择是否记住补全历史"""
        ttk.Label(usage_frame, text=completion_text, justify='left').pack(anchor='w', padx=30, pady=(0,10))

        ttk.Label(usage_frame, text="2. AI助手:", font=("Arial", 10, "bold")).pack(anchor='w', padx=10, pady=(5,0))
        assistant_text = f"""• 快捷键: 按下 {self.assistant_hotkey} 呼出AI助手窗口
• 助理模式:
  - 选中文本后呼出助手
  - 可使用翻译、解释和总结功能
• 对话模式:
  - 直接呼出助手进行自由对话
  - 支持连续对话，保持上下文
  - 询问或者输入框回车发送消息"""
        ttk.Label(usage_frame, text=assistant_text, justify='left').pack(anchor='w', padx=30, pady=(0,10))
        
        info_frame = ttk.LabelFrame(main_frame, text="项目信息")
        info_frame.pack(fill='x', padx=20, pady=10)
        
        info_text = """项目地址: https://github.com/hmhm2022/ChatFree
作      者: ♥ linux.do 论坛♥  user705
"""
        
        ttk.Label(info_frame, text=info_text, justify='left').pack(padx=10, pady=5)
        
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(side='bottom', fill='x', padx=20, pady=10)
        
        ttk.Label(footer_frame, 
                 text="© 2024 ChatFree | MIT License", 
                 font=("Arial", 8),
                 foreground='#666666',
                 anchor='center').pack(fill='x')
        
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text='设置')
        
        api_frame = ttk.LabelFrame(settings_frame, text="API设置")
        api_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(api_frame, text="API Key:").pack(anchor='w')
        self.ent_apikey = ttk.Entry(api_frame, width=52)
        self.ent_apikey.insert(0, self.apikey)
        self.ent_apikey.pack(pady=(0,5))
        
        ttk.Label(api_frame, text="API URL:").pack(anchor='w')
        self.ent_base_url = ttk.Entry(api_frame, width=52)
        self.ent_base_url.insert(0, self.base_url)
        self.ent_base_url.pack(pady=(0,5))
        
        ttk.Label(api_frame, text="Temperature:").pack(anchor='w')
        self.ent_temperature = ttk.Entry(api_frame, width=52)
        self.ent_temperature.insert(0, str(self.temperature))
        self.ent_temperature.pack(pady=(0,5))
        
        ttk.Label(api_frame, text="Model:").pack(anchor='w')
        model_frame = ttk.Frame(api_frame)
        model_frame.pack(fill='x', pady=(0,5))
        self.model_var = tk.StringVar(value=self.model)
        self.cmb_model = ttk.Combobox(model_frame, textvariable=self.model_var, width=40)
        self.cmb_model.pack(side='left', padx=(15,5))
        refresh_btn = ttk.Button(model_frame, text="获取模型", width=8, command=self.update_models)
        refresh_btn.pack(side='left')
        self.update_models()
        
        hotkey_frame = ttk.LabelFrame(settings_frame, text="快捷键设置")
        hotkey_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(hotkey_frame, text="补全快捷键:").pack(anchor='w')
        self.ent_hotkey = ttk.Entry(hotkey_frame, width=52)
        self.ent_hotkey.insert(0, self.hotkey)
        self.ent_hotkey.pack(pady=(0,5))
        
        ttk.Label(hotkey_frame, text="AI助手快捷键:").pack(anchor='w')
        self.ent_assistant_hotkey = ttk.Entry(hotkey_frame, width=52)
        self.ent_assistant_hotkey.insert(0, self.assistant_hotkey)
        self.ent_assistant_hotkey.pack(pady=(0,5))
        
        completion_frame = ttk.LabelFrame(settings_frame, text="补全设置")
        completion_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.keep_history_var = tk.BooleanVar(value=self.keep_history)
        ttk.Checkbutton(completion_frame, text="记住历史对话", variable=self.keep_history_var).pack(anchor='w', padx=5, pady=5)
        
        ttk.Label(completion_frame, text="自定义Prompt:").pack(anchor='w', padx=5)
        self.txt_prompt = scrolledtext.ScrolledText(completion_frame, width=50, height=10)
        self.txt_prompt.insert('1.0', self.custom_prompt)
        self.txt_prompt.pack(pady=5, padx=5, fill='both', expand=True)
        
        self.btn_submit = ttk.Button(settings_frame, text="保存设置", command=self.submit)
        self.btn_submit.pack(pady=10)
        
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.bind_hotkey()
        keyboard.add_hotkey(self.assistant_hotkey, self.show_dialog)
        
    def setup_tray(self):
        """设置系统托盘"""
        image = Image.open("linuxdo.ico")
        menu = (
            pystray.MenuItem('显示', self.show_window),
            pystray.MenuItem('退出', self.quit_app)
        )
        self.icon = pystray.Icon("ChatFree", image, "ChatFree", menu)
        self.icon_thread = None
        
    def show_window(self, icon=None):
        """显示窗口"""
        if self.icon_thread and self.icon_thread.is_alive():
            self.icon.visible = False
        self.master.after(0, self.master.deiconify)
        
    def hide_window(self):
        """隐藏窗口到托盘"""
        self.master.withdraw()
        if not self.icon_thread or not self.icon_thread.is_alive():
            self.icon_thread = threading.Thread(target=self.icon.run, daemon=True)
            self.icon_thread.start()
        else:
            self.icon.visible = True
        
    def quit_app(self, icon=None):
        """退出应用"""
        try:
            keyboard.unhook_all_hotkeys()
            
            if self.icon_thread and self.icon_thread.is_alive():
                self.icon.stop()
            
            self.master.destroy()
            os._exit(0)
        except Exception as e:
            print(f"退出时发错误: {str(e)}")
            os._exit(1)
        
    def on_closing(self):
        """窗口关闭事件处理"""
        if self.master.winfo_exists():
            result = messagebox.askyesnocancel(
                "退出",
                "请选择操作:\n'是' - 退出程序\n'否' - 最小化到系统托盘\n'取消' - 取消关闭",
                icon='question',
                default='no'
            )
            if result is True:
                self.quit_app()
            elif result is False:
                self.hide_window()
    
    def update_models(self):
        """更新模型列表"""
        def fetch_models():
            try:
                print("开始获取模型列表...") 
                
                current_config = {
                    'api_key': self.ent_apikey.get(), 
                    'base_url': self.ent_base_url.get(),
                    'model': self.model_var.get(),
                    'system_prompt': {"role": "system", "content": self.txt_prompt.get('1.0', 'end-1c')}
                }
                
                print(f"当前API URL: {current_config['base_url']}")
                chat_session = ChatSession(
                    api_key=current_config['api_key'],
                    base_url=current_config['base_url'],
                    model=current_config['model'],
                    system_prompt=current_config['system_prompt']
                )
                
                models = chat_session.get_models()
                print(f"获取到的模型列表: {models}")
                
                if models:
                    def update_ui():
                        current_model = self.model_var.get()
                        self.cmb_model.configure(values=models)
                        
                        if current_model and current_model not in models:
                            self.model_var.set("")
                            messagebox.showinfo("成功", 
                                f"成功获取到{len(models)}个可用模型\n当前选择的模型不可用,请重新选择")
                        else:
                            messagebox.showinfo("成功", 
                                f"成功获取到{len(models)}个可用模型")
                        
                    self.master.after(0, update_ui)
                else:
                    self.master.after(0, lambda: messagebox.showwarning(
                        "警告",
                        "未能获取到可用模型列表\n请检查网络连接或API配置，修改保存后手动获取模型。"
                    ))
            except Exception as e:
                error_msg = f"获取模型列表时发生错误:\n{str(e)}\n\n请检查网络连接和API配置后重试。"
                print(f"错误: {error_msg}")
                self.master.after(0, lambda: messagebox.showerror("错误", error_msg))
        
        threading.Thread(target=fetch_models, daemon=True).start()
    
    def bind_hotkey(self):
        """绑定快捷键"""
        try:
            keyboard.remove_hotkey(self.hotkey)
        except:
            pass
        keyboard.add_hotkey(self.hotkey, self.complete)

    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.apikey = config.get('api_key')
                    self.base_url = config.get('api_url')
                    self.model = config.get('model')
                    self.temperature = config.get('temperature', 0.9)
                    self.keep_history = config.get('keep_history', False)
                    self.custom_prompt = config.get('custom_prompt', "你是一个专业的文本续写助手...")
                    self.hotkey = config.get('hotkey', 'ctrl+alt+\\')
                    self.assistant_hotkey = config.get('assistant_hotkey', 'alt+r')
            else:
                pass
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")

    def save_config(self):
        """保存配置"""
        config = {
            'api_key': self.apikey,
            'api_url': self.base_url,
            'model': self.model,
            'temperature': self.temperature,
            'keep_history': self.keep_history,
            'custom_prompt': self.custom_prompt,
            'hotkey': self.hotkey,
            'assistant_hotkey': self.assistant_hotkey
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print("配置已保存")
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")

    def submit(self):
        """保存设置"""
        self.apikey = self.ent_apikey.get()
        self.base_url = self.ent_base_url.get()
        self.model = self.model_var.get()
        self.temperature = float(self.ent_temperature.get())
        self.keep_history = self.keep_history_var.get()
        self.custom_prompt = self.txt_prompt.get('1.0', 'end-1c')
        
        new_hotkey = self.ent_hotkey.get()
        new_assistant_hotkey = self.ent_assistant_hotkey.get()
        
        if new_hotkey != self.hotkey:
            self.hotkey = new_hotkey
            self.bind_hotkey()
        
        if new_assistant_hotkey != self.assistant_hotkey:
            keyboard.remove_hotkey(self.assistant_hotkey)
            self.assistant_hotkey = new_assistant_hotkey
            keyboard.add_hotkey(self.assistant_hotkey, self.show_dialog)
        
        self.save_config()
        
        self.btn_submit["text"] = "保存成功"
        self.master.after(700, lambda: self.btn_submit.configure(text="保存设置"))

    def get_selected_text(self):
        """获取选中的文本"""
        win32clipboard.OpenClipboard()
        try:
            old_clipboard = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        except:
            old_clipboard = ''
        win32clipboard.CloseClipboard()

        hotkey_parts = self.hotkey.lower().split('+')

        while any(keyboard.is_pressed(key) for key in hotkey_parts):
            time.sleep(0.1)

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()

        time.sleep(0.3)
        keyboard.press_and_release('ctrl+c')
        time.sleep(0.5)

        max_attempts = 3
        selected_text = None
        for _ in range(max_attempts):
            try:
                win32clipboard.OpenClipboard()
                selected_text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                if not selected_text.strip():
                    selected_text = None
                break
            except:
                win32clipboard.CloseClipboard()
                time.sleep(0.3)

        if old_clipboard:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(old_clipboard)
            win32clipboard.CloseClipboard()

        return selected_text

    def complete(self):
        """文本补全功能"""
        try:
            selected_text = self.get_selected_text()
            if not selected_text:
                print("未能获取到选中的文本，请重试")
                return

            print("您选择补全的文本:\t", selected_text)
            keyboard.press_and_release('right')
            msg = "【请稍等，等待补全】"
            keyboard.write(msg)

            if self.chat_session is None:
                self.chat_session = ChatSession(
                    api_key=self.apikey,
                    base_url=self.base_url,
                    model=self.model,
                    system_prompt={
                        "role": "system", 
                        "content": self.custom_prompt
                    }                    
                )

            for i in range(len(msg)):
                keyboard.press_and_release('backspace')
            msg = " << 请勿其它操作，长按ctrl键终止】"
            keyboard.write("【" + msg)
            for i in range(len(msg)):
                keyboard.press_and_release('left')

            if not self.keep_history:
                self.chat_session.clear_history()
            
            response = self.chat_session.chat(selected_text, temperature=self.temperature)

            if response.startswith(("\n发生错误", "request error", "API请求错误")):
                print(f"\n{response}")
                keyboard.write(f" >> {response}")
                return

            for char in response:
                if keyboard.is_pressed('ctrl'):
                    print("\n--用户终止")
                    keyboard.write(" >> 用户终止")
                    return
                print(char, end="", flush=True)
                keyboard.write(char)
                time.sleep(0.01)

            print()
            keyboard.write("】")
            for i in range(len(msg)):
                keyboard.press_and_release('delete')

        except Exception as e:
            print(f"发生错误: {str(e)}")
            return

    def show_dialog(self):
        """显示对话窗口"""
        try:
            selected_text = None
            try:
                selected_text = self.get_selected_text()
                print(f"获取到选中文本: {selected_text}")
            except Exception as e:
                print(f"获取选中文本时错: {e}")
                pass
            
            config = {
                'api_key': self.apikey,
                'api_url': self.base_url,
                'model': self.model,
                'temperature': self.temperature
            }
            
            if self.master.winfo_exists():
                dialog = DialogWindow(self.master, selected_text, config)
                dialog.dialog.lift()
                dialog.dialog.focus_force()
                
        except Exception as e:
            print(f"显示对话窗口时发生错误: {str(e)}")

if __name__ == '__main__':
    root = tk.Tk()
    app = ChatFreeApp(root)
    root.mainloop()
    keyboard.unhook_all_hotkeys()
