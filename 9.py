import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import json
import os
import zipfile
import shutil
from datetime import datetime


class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ACG主题单词卡")
        self.cards = []
        self.current_card = 0
        self.is_front = True
        self.current_images = []  # 新增图片引用保持

        self.load_data()
        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        # 风格配置
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#B9F5FE")
        style.configure("Title.TLabel", font=('Helvetica', 14, 'bold'), foreground="#FF69B4")

        # 控制面板
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.grid(row=0, column=0, sticky="nw")

        ttk.Label(control_frame, text="开始位置:", style="Title.TLabel").grid(row=0, column=0)
        self.start_entry = ttk.Entry(control_frame, width=5)
        self.start_entry.grid(row=0, column=1, padx=5)

        ttk.Button(control_frame, text="跳转", command=self.jump_to_card).grid(row=0, column=2)
        ttk.Button(control_frame, text="添加卡片", command=self.add_card_dialog).grid(row=0, column=3, padx=5)
        ttk.Button(control_frame, text="导出卡片", command=self.export_cards).grid(row=0, column=4, padx=5)
        ttk.Button(control_frame, text="导入卡片", command=self.import_cards).grid(row=0, column=5, padx=5)
        ttk.Button(control_frame, text="修改卡片", command=self.modify_card_dialog).grid(row=0, column=6, padx=5)
        ttk.Button(control_frame, text="删除卡片", command=self.delete_card).grid(row=0, column=7, padx=5)

        # 卡片显示区
        self.canvas = tk.Canvas(self.root, width=600, height=400, bg="#FFE4F3")
        self.canvas.grid(row=1, column=0, padx=10, pady=10)

        # 创建卡片内容容器
        self.card_width = 400
        self.card_height = 300
        self.card_x = 100
        self.card_y = 50
        self.card_center_x = self.card_x + self.card_width // 2
        self.card_center_y = self.card_y + self.card_height // 2

        self.card_bg = self.canvas.create_rectangle(self.card_x, self.card_y,
                                                    self.card_x + self.card_width,
                                                    self.card_y + self.card_height,
                                                    fill="white", outline="black")
        self.image_item = self.canvas.create_image(self.card_center_x, self.card_center_y)
        self.text_item = self.canvas.create_text(self.card_center_x, self.card_center_y,
                                                 text="", font=("Helvetica", 16), width=self.card_width - 40)

        # 导航面板
        nav_frame = ttk.Frame(self.root)
        nav_frame.grid(row=2, column=0, pady=10)

        ttk.Button(nav_frame, text="← 上一个", command=self.prev_card).grid(row=0, column=0, padx=5)
        ttk.Button(nav_frame, text="翻卡", command=self.flip_card).grid(row=0, column=1, padx=5)
        ttk.Button(nav_frame, text="下一个 →", command=self.next_card).grid(row=0, column=2, padx=5)
        self.position_label = ttk.Label(nav_frame, text="0/0")
        self.position_label.grid(row=0, column=3, padx=10)

        # 当没有卡片时禁用按钮
        self.toggle_nav_buttons()

    def update_display(self):
        """更新卡片显示内容"""
        if self.cards:
            card = self.cards[self.current_card]
            try:
                if self.is_front:
                    self.show_image(card["image"])
                else:
                    self.show_text(f"{card['word']}\n\n{card['meaning']}")
                self.position_label.config(text=f"{self.current_card + 1}/{len(self.cards)}")
            except Exception as e:
                messagebox.showerror("显示错误", f"图片加载失败：{str(e)}")
                self.cards.pop(self.current_card)
                self.auto_save()  # 自动保存数据
                self.update_display()
        else:
            self.canvas.itemconfig(self.image_item, image='')
            self.canvas.itemconfig(self.text_item, text="暂无卡片")
            self.position_label.config(text="0/0")

    def show_image(self, path):
        """显示图片"""
        try:
            # 使用PIL加载各种格式图片
            if not os.path.exists(path):
                raise FileNotFoundError(f"图片路径不存在：{path}")

            pil_image = Image.open(path)
            ratio = min(self.card_width / pil_image.width, self.card_height / pil_image.height)
            resized_image = pil_image.resize((int(pil_image.width * ratio),
                                             int(pil_image.height * ratio)),
                                            Image.Resampling.LANCZOS)

            tk_image = ImageTk.PhotoImage(resized_image)

            # 保持图像引用
            self.current_images.append(tk_image)
            self.canvas.itemconfig(self.image_item, image=tk_image)
            self.canvas.itemconfig(self.text_item, text="")
        except Exception as e:
            raise Exception(f"图片加载失败：{str(e)}")

    def show_text(self, text):
        """显示文本"""
        self.canvas.itemconfig(self.image_item, image='')
        self.canvas.itemconfig(self.text_item, text=text)

    def flip_card(self):
        """翻转卡片"""
        self.is_front = not self.is_front
        self.update_display()

    def next_card(self):
        """显示下一张卡片"""
        if self.current_card < len(self.cards) - 1:
            self.current_card += 1
            self.is_front = True
            self.update_display()
            self.auto_save()  # 自动保存数据

    def prev_card(self):
        """显示上一张卡片"""
        if self.current_card > 0:
            self.current_card -= 1
            self.is_front = True
            self.update_display()
            self.auto_save()  # 自动保存数据

    def jump_to_card(self):
        """跳转到指定卡片"""
        try:
            index = int(self.start_entry.get()) - 1
            if 0 <= index < len(self.cards):
                self.current_card = index
                self.is_front = True
                self.update_display()
                self.auto_save()  # 自动保存数据
            else:
                messagebox.showwarning("提示", "序号超出范围")
        except ValueError:
            messagebox.showerror("错误", "请输入有效数字")

    def add_card_dialog(self):
        """打开添加卡片对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加新卡片")

        ttk.Label(dialog, text="选择图片:").grid(row=0, column=0)
        img_path = tk.StringVar()
        ttk.Entry(dialog, textvariable=img_path, width=30).grid(row=0, column=1)
        ttk.Button(dialog, text="选择文件",
                   command=lambda: img_path.set(filedialog.askopenfilename())).grid(row=0, column=2)

        ttk.Label(dialog, text="单词:").grid(row=1, column=0)
        word_entry = ttk.Entry(dialog)
        word_entry.grid(row=1, column=1)

        ttk.Label(dialog, text="释义:").grid(row=2, column=0)
        meaning_entry = ttk.Entry(dialog)
        meaning_entry.grid(row=2, column=1)

        ttk.Button(dialog, text="添加",
                   command=lambda: self.add_card(
                       img_path.get(),
                       word_entry.get(),
                       meaning_entry.get(),
                       dialog
                   )).grid(row=3, column=1)

    def add_card(self, image_path, word, meaning, dialog):
        """添加新卡片"""
        if not all([image_path, word, meaning]):
            messagebox.showerror("错误", "请填写所有字段")
            return

        try:
            # 验证是否为有效图片
            test_image = Image.open(image_path)
            test_image.verify()
        except Exception as e:
            messagebox.showerror("错误", f"无效图片文件：{str(e)}")
            return

        # 将图片路径转换为绝对路径
        abs_path = os.path.abspath(image_path)

        self.cards.append({
            "image": abs_path,
            "word": word,
            "meaning": meaning
        })
        self.toggle_nav_buttons()
        dialog.destroy()
        self.current_card = len(self.cards) - 1
        self.is_front = True
        self.update_display()
        self.auto_save()  # 自动保存数据

    def modify_card_dialog(self):
        """打开修改卡片对话框"""
        if not self.cards:
            messagebox.showinfo("提示", "没有卡片可以修改")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("修改卡片内容")

        card = self.cards[self.current_card]

        ttk.Label(dialog, text="选择图片:").grid(row=0, column=0)
        img_path = tk.StringVar(value=card["image"])
        ttk.Entry(dialog, textvariable=img_path, width=30).grid(row=0, column=1)
        ttk.Button(dialog, text="选择文件",
                   command=lambda: img_path.set(filedialog.askopenfilename())).grid(row=0, column=2)

        ttk.Label(dialog, text="单词:").grid(row=1, column=0)
        word_entry = ttk.Entry(dialog)
        word_entry.insert(0, card["word"])
        word_entry.grid(row=1, column=1)

        ttk.Label(dialog, text="释义:").grid(row=2, column=0)
        meaning_entry = ttk.Entry(dialog)
        meaning_entry.insert(0, card["meaning"])
        meaning_entry.grid(row=2, column=1)

        ttk.Button(dialog, text="保存",
                   command=lambda: self.modify_card(
                       img_path.get(),
                       word_entry.get(),
                       meaning_entry.get(),
                       dialog
                   )).grid(row=3, column=1)

    def modify_card(self, image_path, word, meaning, dialog):
        """修改当前卡片内容"""
        if not all([image_path, word, meaning]):
            messagebox.showerror("错误", "请填写所有字段")
            return

        try:
            # 验证是否为有效图片
            test_image = Image.open(image_path)
            test_image.verify()
        except Exception as e:
            messagebox.showerror("错误", f"无效图片文件：{str(e)}")
            return

        # 更新卡片内容
        self.cards[self.current_card] = {
            "image": os.path.abspath(image_path),
            "word": word,
            "meaning": meaning
        }
        dialog.destroy()
        self.update_display()
        self.auto_save()  # 自动保存数据

    def delete_card(self):
        """删除当前卡片"""
        if not self.cards:
            messagebox.showinfo("提示", "没有卡片可以删除")
            return

        confirm = messagebox.askyesno("确认删除", "确定要删除当前卡片吗？")
        if confirm:
            self.cards.pop(self.current_card)
            if self.current_card >= len(self.cards):  # 如果删除后越界
                self.current_card = max(0, len(self.cards) - 1)
            self.update_display()
            self.auto_save()  # 自动保存数据

    def toggle_nav_buttons(self):
        """根据卡片数量启用或禁用导航按钮"""
        state = "normal" if len(self.cards) > 0 else "disabled"
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button) and widget["text"] in ("← 上一个", "下一个 →", "翻卡"):
                widget["state"] = state

    def auto_save(self):
        """自动保存数据"""
        with open("cards.json", "w") as f:
            json.dump(self.cards, f)

    def load_data(self):
        """加载数据"""
        try:
            with open("cards.json") as f:
                self.cards = json.load(f)
        except FileNotFoundError:
            self.cards = []
        except json.JSONDecodeError:
            messagebox.showerror("错误", "数据文件损坏")

    def export_cards(self):
        """导出卡片为压缩文件"""
        if not self.cards:
            messagebox.showinfo("提示", "没有卡片可以导出。")
            return

        # 创建临时目录
        export_dir = "exported_cards"
        os.makedirs(export_dir, exist_ok=True)

        # 保存卡片数据
        data_path = os.path.join(export_dir, "cards.json")
        with open(data_path, "w") as f:
            json.dump(self.cards, f)

        # 复制图片文件
        for card in self.cards:
            image_path = card["image"]
            if os.path.exists(image_path):
                dest_path = os.path.join(export_dir, os.path.basename(image_path))
                if not os.path.exists(dest_path):
                    shutil.copy(image_path, dest_path)

        # 打包为 ZIP 文件
        zip_filename = f"flashcards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, _, files in os.walk(export_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)

        # 清理临时目录
        shutil.rmtree(export_dir)

        messagebox.showinfo("导出成功", f"卡片已导出为 {zip_filename}。")

    def import_cards(self):
        """从 ZIP 文件中导入卡片"""
        zip_path = filedialog.askopenfilename(
            title="选择卡片压缩文件",
            filetypes=[("ZIP 文件", "*.zip")]
        )
        if not zip_path:
            return

        # 创建临时目录
        import_dir = "imported_cards"
        os.makedirs(import_dir, exist_ok=True)

        # 解压 ZIP 文件
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(import_dir)

        # 加载卡片数据
        data_path = os.path.join(import_dir, "cards.json")
        if not os.path.exists(data_path):
            messagebox.showerror("导入失败", "缺少 cards.json 文件。")
            shutil.rmtree(import_dir)
            return

        with open(data_path, "r") as f:
            try:
                imported_cards = json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror("导入失败", "cards.json 文件格式错误。")
                shutil.rmtree(import_dir)
                return

        # 检查图片文件是否存在
        missing_images = []
        for card in imported_cards:
            image_path = os.path.join(import_dir, os.path.basename(card["image"]))
            if not os.path.exists(image_path):
                missing_images.append(os.path.basename(card["image"]))
            else:
                card["image"] = image_path

        if missing_images:
            messagebox.showwarning("部分图片缺失", f"以下图片文件未找到：\n{', '.join(missing_images)}")

        # 合并卡片
        self.cards.extend(imported_cards)
        self.current_card = 0
        self.is_front = True
        self.update_display()
        self.auto_save()

        messagebox.showinfo("导入成功", "卡片已成功导入！")


if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()
