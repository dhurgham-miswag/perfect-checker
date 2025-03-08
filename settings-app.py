import tkinter as tk
from tkinter import messagebox
import json


class SettingsManager:
    def __init__(self, root, settings_file):
        self.root = root
        self.root.title("Settings Manager")
        self.settings_file = settings_file
        self.load_settings()
        self.create_widgets()

    def load_settings(self):
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f" ابه نيو: {e}")
            self.settings = {
                "allowed_comments": [],
                "allowed_keywords": [],
                "off_days": []
            }

    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Success", "الك | تم بكلبي ضميتهن")
        except Exception as e:
            messagebox.showerror("Error", f" ابه نيو :  {e}")

    def update_listbox(self, listbox, data):
        listbox.delete(0, tk.END)
        for item in data:
            listbox.insert(tk.END, item)

    def add_item(self, listbox, category, entry):
        new_item = entry.get().strip()
        if new_item:
            items = new_item.split('\n')
            for item in items:
                item = item.strip()
                if item and item not in self.settings[category]:
                    self.settings[category].append(item)
            self.update_listbox(listbox, self.settings[category])
            entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Input Error", "ضع قيمه صحيحه حبيبي >_")

    def delete_item(self, listbox, category):
        selected = listbox.curselection()
        if selected:
            item_to_delete = listbox.get(selected[0])
            if messagebox.askyesno("Confirm Deletion", f" متاكد تريد تحذف؟ ' {item_to_delete}'?"):
                self.settings[category].remove(item_to_delete)
                self.update_listbox(listbox, self.settings[category])
        else:
            messagebox.showwarning("Selection Error", "اختر اولا للحذف.")

    def create_widgets(self):
        tk.Button(self.root, text="حجي وكلام", command=self.show_info).grid(row=0, column=0, padx=10, pady=10)
        tk.Label(self.root, text="تعليقات ثابته", font=("Arial", 14)).grid(row=1, column=0, padx=10, pady=10)
        self.allowed_comments_listbox = tk.Listbox(self.root, width=40, height=10)
        self.update_listbox(self.allowed_comments_listbox, self.settings["allowed_comments"])
        self.allowed_comments_listbox.grid(row=2, column=0, padx=10, pady=10)
        allowed_comments_entry = tk.Entry(self.root, width=40)
        allowed_comments_entry.grid(row=3, column=0, padx=10, pady=5)
        tk.Button(self.root, text="اضافه",
                  command=lambda: self.add_item(self.allowed_comments_listbox, "allowed_comments",
                                                allowed_comments_entry)).grid(row=4, column=0, padx=10, pady=5)
        tk.Button(self.root, text="حذف",
                  command=lambda: self.delete_item(self.allowed_comments_listbox, "allowed_comments")).grid(row=5,
                                                                                                            column=0,
                                                                                                            padx=10,
                                                                                                            pady=5)

        tk.Label(self.root, text="كلمات مفتاحيه", font=("Arial", 14)).grid(row=1, column=1, padx=10, pady=10)

        self.allowed_keywords_listbox = tk.Listbox(self.root, width=40, height=10)
        self.update_listbox(self.allowed_keywords_listbox, self.settings["allowed_keywords"])
        self.allowed_keywords_listbox.grid(row=2, column=1, padx=10, pady=10)

        allowed_keywords_entry = tk.Entry(self.root, width=40)
        allowed_keywords_entry.grid(row=3, column=1, padx=10, pady=5)

        tk.Button(self.root, text="اضافه",
                  command=lambda: self.add_item(self.allowed_keywords_listbox, "allowed_keywords",
                                                allowed_keywords_entry)).grid(row=4, column=1, padx=10, pady=5)
        tk.Button(self.root, text="حذف",
                  command=lambda: self.delete_item(self.allowed_keywords_listbox, "allowed_keywords")).grid(row=5,
                                                                                                            column=1,
                                                                                                            padx=10,
                                                                                                            pady=5)

        tk.Label(self.root, text="ايام العطل (عدا الجمعه) (dd/mm/yyyy)", font=("Arial", 14)).grid(row=1, column=2, padx=10, pady=10)

        self.off_days_listbox = tk.Listbox(self.root, width=40, height=10)
        self.update_listbox(self.off_days_listbox, self.settings["off_days"])
        self.off_days_listbox.grid(row=2, column=2, padx=10, pady=10)

        off_days_entry = tk.Entry(self.root, width=40)
        off_days_entry.grid(row=3, column=2, padx=10, pady=5)

        tk.Button(self.root, text="اضافه",
                  command=lambda: self.add_item(self.off_days_listbox, "off_days", off_days_entry)).grid(row=4,
                                                                                                         column=2,
                                                                                                         padx=10,
                                                                                                         pady=5)
        tk.Button(self.root, text="حذف", command=lambda: self.delete_item(self.off_days_listbox, "off_days")).grid(
            row=5, column=2, padx=10, pady=5)

        # Save Settings Button
        tk.Button(self.root, text="حفظ التعديلات", command=self.save_settings).grid(row=6, column=0, columnspan=3,
                                                                                    padx=10, pady=10)

    def show_info(self):
        info_message = (
            "الإعدادات\n\n"
            "يتيح لك هذا التطبيق إدارة الإعدادات التالية:\n"
            "1. التعليقات الثابتة\n"
            "2. الكلمات المفتاحية\n"
            "3. أيام العطل\n\n"
            "يمكنك إضافة أو حذف العناصر من هذه الفئات. سيتم حفظ التغييرات في ملف الإعدادات.\n\n"
            "هذا التطبيق هو تحفة فنية من ضرغام إلى حسين رعد."
        )
        messagebox.showinfo("صبغ ولبخ", info_message)


if __name__ == "__main__":
    settings_file = "settings.json"
    root = tk.Tk()
    app = SettingsManager(root, settings_file)
    root.mainloop()
