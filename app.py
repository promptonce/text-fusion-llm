import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os

class Placeholder:
    def __init__(self, widget, placeholder, is_text_widget=False):
        self.widget = widget
        self.placeholder = placeholder
        self.is_text_widget = is_text_widget
        self.placeholder_color = 'grey'
        self.text_color = 'black'
        self.placeholder_visible = False

        self.add_placeholder()

        if self.is_text_widget:
            self.widget.bind("<FocusIn>", self.focus_in_text)
            self.widget.bind("<FocusOut>", self.focus_out_text)
            self.widget.bind("<Key>", self.key_pressed_text)
        else:
            self.widget.bind("<FocusIn>", self.focus_in_entry)
            self.widget.bind("<FocusOut>", self.focus_out_entry)

    def add_placeholder(self):
        if self.is_text_widget:
            current_text = self.widget.get("1.0", tk.END).strip()
            if not current_text:
                self.widget.insert("1.0", self.placeholder)
                self.widget.config(fg=self.placeholder_color)
                self.placeholder_visible = True
        else:
            current_text = self.widget.get()
            if not current_text:
                self.widget.insert(0, self.placeholder)
                self.widget.config(fg=self.placeholder_color)
                self.placeholder_visible = True

    def focus_in_entry(self, event):
        if self.placeholder_visible:
            self.widget.delete(0, tk.END)
            self.widget.config(fg=self.text_color)
            self.placeholder_visible = False

    def focus_out_entry(self, event):
        if not self.widget.get():
            self.widget.insert(0, self.placeholder)
            self.widget.config(fg=self.placeholder_color)
            self.placeholder_visible = True

    def focus_in_text(self, event):
        if self.placeholder_visible:
            self.widget.delete("1.0", tk.END)
            self.widget.config(fg=self.text_color)
            self.placeholder_visible = False

    def focus_out_text(self, event):
        current_text = self.widget.get("1.0", tk.END).strip()
        if not current_text:
            self.widget.insert("1.0", self.placeholder)
            self.widget.config(fg=self.placeholder_color)
            self.placeholder_visible = True

    def key_pressed_text(self, event):
        if self.placeholder_visible:
            self.widget.delete("1.0", tk.END)
            self.widget.config(fg=self.text_color)
            self.placeholder_visible = False

class LLMTextPromptApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM文本提示拼接器 v1.4")
        self.root.geometry("600x1000")
        self.root.configure(bg="#f5f5f7")

        # 保存按钮配置，所有按钮数据存储在此
        self.buttons = []

        # 上区域: 用户输入框
        top_frame = tk.Frame(root, bg="#f5f5f7", padx=10, pady=10)
        top_frame.grid(row=0, column=0, sticky="ew")

        tk.Label(top_frame, text="输入你的问题或请求:", bg="#f5f5f7").pack(anchor="w")
        self.user_input = tk.Text(top_frame, wrap="word", height=4)
        self.user_input.pack(fill="x", pady=5)
        # 添加占位符
        sample_placeholder = "请输入你的问题或请求..."
        Placeholder(self.user_input, sample_placeholder, is_text_widget=True)

        # 中区域: 按钮管理
        mid_frame = tk.Frame(root, bg="#f5f5f7", padx=10, pady=5)
        mid_frame.grid(row=1, column=0, sticky="ew")

        tk.Label(mid_frame, text="按钮文本", bg="#f5f5f7").grid(row=0, column=0, sticky="w")
        self.button_text = tk.Entry(mid_frame)
        self.button_text.grid(row=0, column=1, sticky="ew")
        # 添加占位符
        Placeholder(self.button_text, "请输入按钮文本...")

        tk.Label(mid_frame, text="提示内容", bg="#f5f5f7").grid(row=1, column=0, sticky="w")
        self.prompt_content = tk.Text(mid_frame, wrap="word", height=6)
        self.prompt_content.grid(row=1, column=1, sticky="ew")
        # 添加占位符
        sample_prompt_placeholder = (
            "示例\n"
            "下面我让你来充当翻译家，你的目标是把任何语言翻译成中文，请翻译时不要带翻译腔，而是要翻译得自然、流畅和地道，使用优美和高雅的表达方式。请翻译下面这句话：\n"
            "<用户下次输入>\n"
            "生成的回答："
        )
        Placeholder(self.prompt_content, sample_prompt_placeholder, is_text_widget=True)

        tk.Label(mid_frame, text="标签（可选）", bg="#f5f5f7").grid(row=2, column=0, sticky="w")
        self.tag_input = tk.Entry(mid_frame)
        self.tag_input.grid(row=2, column=1, sticky="ew")
        # 添加占位符
        Placeholder(self.tag_input, "请输入标签（可选）...")

        # 添加说明标签，解释占位符的作用
        explanation_label = tk.Label(
            mid_frame,
            text="使用 <用户下次输入> 作为用户输入的占位符，它将在生成的提示中被替换为用户的实际输入。",
            bg="#f5f5f7",
            fg="blue",
            wraplength=400,
            justify="left",
            font=("Arial", 10, "italic")
        )
        explanation_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(5, 0))

        # 按钮操作
        tk.Button(mid_frame, text="插入<用户下次输入>", command=self.insert_flag).grid(row=3, column=0, sticky="ew", pady=5)
        tk.Button(mid_frame, text="添加按钮到提示列表", command=self.add_prompt_button).grid(row=3, column=1, sticky="ew", pady=5)

        mid_frame.grid_columnconfigure(1, weight=1)

        # 下区域: 按钮展示和操作
        bottom_frame = tk.Frame(root, bg="#f5f5f7", padx=10, pady=5)
        bottom_frame.grid(row=2, column=0, sticky="nsew")

        # 标签筛选器
        filter_frame = tk.Frame(bottom_frame, bg="#f5f5f7")
        filter_frame.pack(fill="x")

        tk.Label(filter_frame, text="筛选标签:", bg="#f5f5f7").pack(side="left")
        self.tag_filter_var = tk.StringVar(value="全部")
        self.tag_filter = tk.OptionMenu(filter_frame, self.tag_filter_var, "全部")
        self.tag_filter.pack(side="left")
        tk.Button(filter_frame, text="筛选", command=self.filter_buttons).pack(side="left", padx=5)

        # 按钮展示区域
        self.buttons_canvas = tk.Canvas(bottom_frame, bg="#f5f5f7")
        self.buttons_frame = tk.Frame(self.buttons_canvas, bg="#f5f5f7")
        self.buttons_scroll = tk.Scrollbar(bottom_frame, orient="vertical", command=self.buttons_canvas.yview)
        self.buttons_canvas.configure(yscrollcommand=self.buttons_scroll.set)

        self.buttons_scroll.pack(side="right", fill="y")
        self.buttons_canvas.pack(fill="both", expand=True)
        self.buttons_canvas.create_window((0, 0), window=self.buttons_frame, anchor="nw")
        self.buttons_frame.bind("<Configure>", lambda e: self.buttons_canvas.configure(scrollregion=self.buttons_canvas.bbox("all")))

        # 最终生成的提示区域
        tk.Label(root, text="生成的提示:", bg="#f5f5f7").grid(row=3, column=0, sticky="w", padx=10)
        self.final_prompt = tk.Text(root, wrap="word", height=6, state="disabled")
        self.final_prompt.grid(row=4, column=0, sticky="ew", padx=10, pady=5)

        # 一键复制和导入导出
        action_frame = tk.Frame(root, bg="#f5f5f7", pady=5)
        action_frame.grid(row=5, column=0, sticky="ew")

        tk.Button(action_frame, text="复制到剪贴板", command=self.copy_to_clipboard).pack(side="left", padx=5)
        tk.Button(action_frame, text="导出按钮配置", command=self.export_config).pack(side="right", padx=5)
        tk.Button(action_frame, text="导入按钮配置", command=self.import_config).pack(side="right", padx=5)

        # 启动时加载已保存的配置
        self.import_config()

        # Configure grid weights for responsive design
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        root.grid_rowconfigure(2, weight=10)  # 增加权重以更好地分配空间
        root.grid_rowconfigure(3, weight=1)
        root.grid_rowconfigure(4, weight=1)
        root.grid_rowconfigure(5, weight=1)
        root.grid_columnconfigure(0, weight=1)

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        copied_text = self.final_prompt.get("1.0", tk.END).strip()
        self.root.clipboard_append(copied_text)
        # 使用弹出提示提示复制成功
        self.show_temporary_popup("已复制到剪贴板", duration=2000)

    def show_temporary_popup(self, message, duration=2000):
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)  # 去掉窗口装饰
        popup.configure(bg="#f5f5f7")
        popup.attributes("-topmost", True)  # 确保提示窗口在最前

        # 设置窗口大小
        popup_width = 300
        popup_height = 100

        # 确保主窗口已经完全渲染
        self.root.update_idletasks()

        # 获取主窗口的位置和大小
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        # 计算弹出窗口的位置，使其居中
        x = root_x + (root_width // 2) - (popup_width // 2)
        y = root_y + (root_height // 2) - (popup_height // 2)

        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        # 添加提示内容
        label = tk.Label(popup, text=message, bg="#f5f5f7", fg="green", font=("Arial", 14))
        label.pack(expand=True, fill="both")

        # 设定duration后关闭窗口
        popup.after(duration, popup.destroy)

    def insert_flag(self):
        if "<用户下次输入>" not in self.prompt_content.get("1.0", tk.END):
            cursor_position = self.prompt_content.index("insert")
            self.prompt_content.insert(cursor_position, "<用户下次输入>")
        else:
            messagebox.showinfo("信息", "占位符已存在")

    def add_prompt_button(self):
        btn_text = self.button_text.get().strip()
        prompt = self.prompt_content.get("1.0", tk.END).strip()
        tag = self.tag_input.get().strip()

        # 检查是否是占位符内容
        if btn_text == "请输入按钮文本...":
            btn_text = ""
        if prompt.startswith("请输入提示内容...") or prompt.startswith("示例:"):
            prompt = ""
        if tag == "请输入标签（可选）...":
            tag = ""

        if not btn_text or not prompt:
            messagebox.showwarning("警告", "请输入按钮文本和提示内容")
            return

        self.buttons.append({"text": btn_text, "prompt": prompt, "tag": tag})
        self.create_button(btn_text, prompt, tag)

        self.button_text.delete(0, tk.END)
        Placeholder(self.button_text, "请输入按钮文本...")
        self.prompt_content.delete("1.0", tk.END)
        sample_prompt_placeholder = (
            "示例\n"
            "下面我让你来充当翻译家，你的目标是把任何语言翻译成中文，请翻译时不要带翻译腔，而是要翻译得自然、流畅和地道，使用优美和高雅的表达方式。请翻译下面这句话：\n"
            "<用户下次输入>\n"
            "生成的回答："
        )
        Placeholder(self.prompt_content, sample_prompt_placeholder, is_text_widget=True)
        self.tag_input.delete(0, tk.END)
        Placeholder(self.tag_input, "请输入标签（可选）...", is_text_widget=True)

        if tag and tag not in [self.tag_filter["menu"].entrycget(i, "label") for i in range(self.tag_filter["menu"].index("end") + 1)]:
            self.tag_filter["menu"].add_command(label=tag, command=tk._setit(self.tag_filter_var, tag))

        # 自动导出按钮配置
        self.export_config(show_message=False)

    def create_button(self, text, prompt, tag):
        def append_prompt():
            user_value = self.user_input.get("1.0", tk.END).strip()
            # 检查是否为占位符文本
            if user_value.startswith("请输入你的问题或请求..."):
                user_value = ""
            generated_prompt = prompt.replace("<用户下次输入>", user_value)
            self.final_prompt.configure(state="normal")
            self.final_prompt.delete("1.0", tk.END)
            self.final_prompt.insert(tk.END, generated_prompt)
            self.final_prompt.configure(state="disabled")

        button_frame = tk.Frame(self.buttons_frame, bg="#f5f5f7")
        button_frame.pack(fill="x", pady=2)

        button = tk.Button(button_frame, text=text, command=append_prompt, width=25)
        button.pack(side="left", padx=5)

        delete_button = tk.Button(button_frame, text="删除", command=lambda: self.remove_button(button_frame, text))
        delete_button.pack(side="right")

    def remove_button(self, button_frame, text):
        button_frame.destroy()
        self.buttons = [b for b in self.buttons if b["text"] != text]
        # 自动导出按钮配置
        self.export_config(show_message=False)

    def filter_buttons(self):
        selected_tag = self.tag_filter_var.get()
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()

        for button in self.buttons:
            if selected_tag == "全部" or button["tag"] == selected_tag:
                self.create_button(button["text"], button["prompt"], button["tag"])

    def export_config(self, show_message=True):
        config_json = json.dumps(self.buttons, indent=4, ensure_ascii=False)
        with open("buttons_config.json", "w", encoding="utf-8") as file:
            file.write(config_json)
        if show_message:
            # 使用弹出提示提示导出成功
            self.show_temporary_popup("按钮配置已导出为 buttons_config.json", duration=2000)

    def import_config(self):
        if os.path.exists("buttons_config.json"):
            with open("buttons_config.json", "r", encoding="utf-8") as file:
                loaded_buttons = json.load(file)

            self.buttons.clear()
            for widget in self.buttons_frame.winfo_children():
                widget.destroy()

            for button in loaded_buttons:
                # 仅添加非空的按钮配置
                if button["text"] and button["prompt"]:
                    self.buttons.append(button)
                    self.create_button(button["text"], button["prompt"], button["tag"])

                    if button["tag"] and button["tag"] not in [self.tag_filter["menu"].entrycget(i, "label") for i in range(self.tag_filter["menu"].index("end") + 1)]:
                        self.tag_filter["menu"].add_command(label=button["tag"], command=tk._setit(self.tag_filter_var, button["tag"]))

        # 可以选择在导入配置后显示提示
        self.show_temporary_popup("按钮配置已导入", duration=2000)

if __name__ == "__main__":
    root = tk.Tk()
    app = LLMTextPromptApp(root)
    root.mainloop()