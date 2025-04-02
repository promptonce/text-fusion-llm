"""
LLM文本提示拼接器 v2.1
完整可运行版本，包含以下改进：
1. MVP架构分离
2. 输入验证与安全处理
3. 多标签筛选支持
4. 样式配置中心
5. 模板变量库
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from typing import List, Dict, Any, Optional
from jsonschema import validate, ValidationError

# === 数据验证 Schema ===
CONFIG_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "minLength": 1},
            "prompt": {"type": "string", "minLength": 1},
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "uniqueItems": True
            }
        },
        "required": ["text", "prompt"]
    }
}

# === 样式配置中心 ===
class AppStyle:
    COLOR_SCHEME = {
        "background": "#f5f5f7",
        "primary": "#007AFF",
        "warning": "#FF3B30",
        "text": "#1C1C1E",
        "placeholder": "#8E8E93",
        "success": "#34C759"
    }
    
    FONT_CONFIG = {
        "default": ("Helvetica", 12),
        "title": ("Helvetica Bold", 14),
        "code": ("Menlo", 11)
    }
    
    DIMENSIONS = {
        "main_window": "800x1200",
        "input_height": 6,
        "button_spacing": 5
    }

# === 数据模型 ===
class PromptModel:
    def __init__(self):
        self.buttons: List[Dict[str, Any]] = []
        self.tags: List[str] = []
        self.variables: List[str] = ["<用户下次输入>", "<当前日期>"]
        self.load_config()
    
    def load_config(self, path: str = "buttons_config.json"):
        if os.path.exists(path):
            try:
                data = SecurityUtils.safe_json_load(path)
                validate(data, CONFIG_SCHEMA)
                self.buttons = data
                self._update_tags()
            except (ValidationError, json.JSONDecodeError) as e:
                messagebox.showerror("配置错误", f"无效配置文件: {str(e)}")
    
    def save_config(self, path: str = "buttons_config.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.buttons, f, indent=2, ensure_ascii=False)
    
    def _update_tags(self):
        tags = set()
        for btn in self.buttons:
            tags.update(btn.get("tags", []))
        self.tags = sorted(tags)
    
    def add_button(self, button_data: Dict[str, Any]):
        self.buttons.append(button_data)
        self._update_tags()
    
    def remove_button(self, button_text: str):
        self.buttons = [b for b in self.buttons if b["text"] != button_text]
        self._update_tags()

# === 视图层 ===
class MainView(tk.Tk):
    def __init__(self, presenter):
        super().__init__()
        self.presenter = presenter
        self.app_style = AppStyle()
        self.style = ttk.Style()
        self.configure_styles()
        self.configure_ui()

    def configure_styles(self):
        """配置所有组件样式"""
        # 基础样式
        self.configure(bg=self.app_style.COLOR_SCHEME["background"])
        
        # ttk样式配置
        self.style.configure(
            'Placeholder.TEntry',
            foreground=self.app_style.COLOR_SCHEME["placeholder"],
            font=self.app_style.FONT_CONFIG["default"]
        )
        self.style.configure(
            'Normal.TEntry',
            foreground=self.app_style.COLOR_SCHEME["text"],
            font=self.app_style.FONT_CONFIG["default"]
        )
        self.style.configure(
            'danger.TButton',
            foreground='white',
            background=self.app_style.COLOR_SCHEME["warning"]
        )
        self.style.map(
            'Placeholder.TEntry',
            foreground=[
                ('!focus', self.app_style.COLOR_SCHEME["placeholder"]),
                ('focus', self.app_style.COLOR_SCHEME["text"])
            ]
        )

    def configure_ui(self):
        self.title("LLM提示拼接器")
        self.geometry(self.app_style.DIMENSIONS["main_window"])
        
        # 主布局
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 输入区域
        self.setup_input_section(main_frame)
        # 按钮配置
        self.setup_button_config(main_frame)
        # 标签筛选
        self.setup_tag_filter(main_frame)
        # 按钮列表
        self.setup_button_list(main_frame)
        # 输出区域
        self.setup_output_section(main_frame)

    def setup_input_section(self, parent):
        frame = ttk.LabelFrame(parent, text="用户输入", padding=10)
        frame.pack(fill="x", pady=10)
        
        self.user_input = tk.Text(
            frame, 
            wrap="word",
            height=4,
            font=self.app_style.FONT_CONFIG["default"]
        )
        self.user_input.pack(fill="x")
        self.add_placeholder(self.user_input, "请输入你的问题或请求...")

    def setup_button_config(self, parent):
        frame = ttk.LabelFrame(parent, text="按钮配置", padding=10)
        frame.pack(fill="x", pady=10)
        
        ttk.Label(frame, text="按钮名称:").grid(row=0, column=0, sticky="w")
        self.btn_text_entry = ttk.Entry(frame, style='Placeholder.TEntry')
        self.btn_text_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.add_placeholder(self.btn_text_entry, "示例: 翻译助手")
        
        ttk.Label(frame, text="提示模板:").grid(row=1, column=0, sticky="nw")
        self.prompt_content = tk.Text(frame, wrap="word", height=6)
        self.prompt_content.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.add_placeholder(self.prompt_content, "输入提示模板...")
        
        ttk.Label(frame, text="插入变量:").grid(row=2, column=0, sticky="w")
        self.var_combobox = ttk.Combobox(frame, values=self.presenter.model.variables)
        self.var_combobox.grid(row=2, column=1, sticky="ew", padx=5)
        self.var_combobox.bind("<<ComboboxSelected>>", self.insert_variable)
        
        ttk.Label(frame, text="标签 (逗号分隔):").grid(row=3, column=0, sticky="w")
        self.tag_entry = ttk.Entry(frame, style='Placeholder.TEntry')
        self.tag_entry.grid(row=3, column=1, sticky="ew", padx=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=1, sticky="e", pady=5)
        ttk.Button(btn_frame, text="添加按钮", command=self.add_button).pack(side="left", padx=5)
        
        frame.columnconfigure(1, weight=1)

    def setup_tag_filter(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=10)
        
        ttk.Label(frame, text="筛选标签:").pack(side="left")
        self.tag_filter = ttk.Combobox(
            frame, 
            values=["全部"] + self.presenter.model.tags,
            state="readonly"
        )
        self.tag_filter.pack(side="left", padx=5)
        self.tag_filter.set("全部")
        self.tag_filter.bind("<<ComboboxSelected>>", lambda e: self.presenter.filter_buttons())

    def setup_button_list(self, parent):
        frame = ttk.LabelFrame(parent, text="按钮列表", padding=10)
        frame.pack(fill="both", expand=True, pady=10)
        
        self.canvas = tk.Canvas(frame, bg=self.app_style.COLOR_SCHEME["background"])
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.button_frame = ttk.Frame(self.canvas)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas.create_window((0,0), window=self.button_frame, anchor="nw")
        self.button_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def setup_output_section(self, parent):
        frame = ttk.LabelFrame(parent, text="生成提示", padding=10)
        frame.pack(fill="x", pady=10)
        
        self.output_text = tk.Text(
            frame,
            wrap="word",
            height=6,
            state="disabled",
            font=self.app_style.FONT_CONFIG["code"]
        )
        self.output_text.pack(fill="x")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="复制", command=self.copy_output).pack(side="left")
        ttk.Button(btn_frame, text="导出配置", command=self.export_config).pack(side="right")
        ttk.Button(btn_frame, text="导入配置", command=self.import_config).pack(side="right", padx=5)

    def add_placeholder(self, widget, text):
        if isinstance(widget, ttk.Entry):
            widget.insert(0, text)
            widget.configure(style='Placeholder.TEntry')
            widget.bind("<FocusIn>", lambda e: self.clear_placeholder(widget, text))
            widget.bind("<FocusOut>", lambda e: self.check_placeholder(widget, text))
        elif isinstance(widget, tk.Text):
            widget.insert("1.0", text)
            widget.config(fg=self.app_style.COLOR_SCHEME["placeholder"])
            widget.bind("<FocusIn>", lambda e: self.clear_placeholder(widget, text))
            widget.bind("<FocusOut>", lambda e: self.check_placeholder(widget, text))

    def clear_placeholder(self, widget, text):
        current = widget.get("1.0", "end-1c") if isinstance(widget, tk.Text) else widget.get()
        if current.strip() == text:
            if isinstance(widget, ttk.Entry):
                widget.delete(0, "end")
                widget.configure(style='Normal.TEntry')
            else:
                widget.delete("1.0", "end")
                widget.config(fg=self.app_style.COLOR_SCHEME["text"])

    def check_placeholder(self, widget, text):
        current = widget.get("1.0", "end-1c") if isinstance(widget, tk.Text) else widget.get()
        if not current.strip():
            self.add_placeholder(widget, text)

    def insert_variable(self, event):
        var = self.var_combobox.get()
        self.prompt_content.insert(tk.INSERT, var)
        self.prompt_content.focus_set()

    def add_button(self):
        data = {
            "text": self.btn_text_entry.get(),
            "prompt": self.prompt_content.get("1.0", "end-1c"),
            "tags": [t.strip() for t in self.tag_entry.get().split(",") if t.strip()]
        }
        self.presenter.add_button(data)

    def copy_output(self):
        self.clipboard_clear()
        self.clipboard_append(self.output_text.get("1.0", "end-1c"))
        self.show_popup("复制成功", self.app_style.COLOR_SCHEME["success"])

    def export_config(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            self.presenter.model.save_config(path)
            self.show_popup("导出成功", self.app_style.COLOR_SCHEME["success"])

    def import_config(self):
        path = filedialog.askopenfilename(filetypes=[("JSON文件", "*.json")])
        if path:
            self.presenter.model.load_config(path)
            self.presenter.refresh_ui()
            self.show_popup("导入成功", self.app_style.COLOR_SCHEME["success"])

    def show_popup(self, message, color):
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.geometry(f"200x60+{self.winfo_rootx()+300}+{self.winfo_rooty()+500}")
        label = ttk.Label(popup, text=message, foreground=color)
        label.pack(expand=True, fill="both")
        popup.after(2000, popup.destroy)

# === 逻辑控制层 ===
class Presenter:
    def __init__(self):
        self.model = PromptModel()
        self.view = MainView(self)
        self.setup_initial_buttons()

    def setup_initial_buttons(self):
        self.model.load_config()
        self.refresh_ui()

    def add_button(self, data: Dict[str, Any]):
        if not self.validate_input(data):
            return
        self.model.add_button(data)
        self.model.save_config()
        self.refresh_ui()

    def validate_input(self, data: Dict) -> bool:
        if len(data["text"]) < 2:
            self.show_error("按钮名称至少需要2个字符")
            return False
        if "<用户下次输入>" not in data["prompt"]:
            self.show_error("提示中必须包含<用户下次输入>")
            return False
        return True

    def filter_buttons(self):
        selected = self.view.tag_filter.get()
        buttons = self.model.buttons if selected == "全部" else [
            b for b in self.model.buttons if selected in b.get("tags", [])
        ]
        self.refresh_button_list(buttons)

    def refresh_ui(self):
        self.refresh_tag_filter()
        self.refresh_button_list()

    def refresh_tag_filter(self):
        self.view.tag_filter["values"] = ["全部"] + self.model.tags

    def refresh_button_list(self, buttons: Optional[List] = None):
        for widget in self.view.button_frame.winfo_children():
            widget.destroy()
        
        buttons = buttons or self.model.buttons
        for btn in buttons:
            self.create_button_widget(btn)

    def create_button_widget(self, data: Dict):
        frame = ttk.Frame(self.view.button_frame)
        frame.pack(fill="x", pady=2)
        
        ttk.Button(
            frame,
            text=data["text"],
            command=lambda: self.generate_prompt(data["prompt"]),
            width=20
        ).pack(side="left", padx=5)
        
        ttk.Label(frame, text=f"标签: {', '.join(data.get('tags', []))}").pack(side="left", padx=10)
        
        ttk.Button(
            frame,
            text="×",
            command=lambda: self.remove_button(data["text"]),
            style="danger.TButton"
        ).pack(side="right")

    def generate_prompt(self, template: str):
        user_input = self.view.user_input.get("1.0", "end-1c").strip()
        final = template.replace("<用户下次输入>", user_input)
        self.view.output_text.config(state="normal")
        self.view.output_text.delete("1.0", "end")
        self.view.output_text.insert("1.0", final)
        self.view.output_text.config(state="disabled")

    def remove_button(self, text: str):
        self.model.remove_button(text)
        self.model.save_config()
        self.refresh_ui()

    def show_error(self, message: str):
        messagebox.showerror("输入错误", message)

# === 安全工具 ===
class SecurityUtils:
    @staticmethod
    def safe_json_load(path: str) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            sanitized = SecurityUtils.sanitize_input(content)
            return json.loads(sanitized)
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        replacements = {"<": "&lt;", ">": "&gt;"}
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

# === 运行入口 ===
if __name__ == "__main__":
    app = Presenter()
    app.view.mainloop()