import tkinter as tk
from tkinter import ttk, messagebox
import math
import json
import os

# --- Multi-User Configuration ---
current_user = "DefaultUser" 

def get_data_file_path(username):
    return f"{username}_grades.json"

# --- Data Persistence Logic ---

def save_data_to_json():
    if not current_user:
        return
    file_path = get_data_file_path(current_user)
    try:
        with open(file_path, 'w') as f:
            json.dump(subjects_data, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save data: {e}")

def load_data_from_json():
    global subjects_data
    file_path = get_data_file_path(current_user)
    if not os.path.exists(file_path):
        subjects_data = []
        return
    try:
        with open(file_path, 'r') as f:
            subjects_data = json.load(f)
    except Exception as e:
        subjects_data = []

# --- Business Logic ---
subjects_data = []

def get_grade_point(score):
    if score >= 79.5: return "4.0"
    if score >= 75: return "3.5"
    if score >= 70: return "3.0"
    if score >= 65: return "2.5"
    if score >= 60: return "2.0"
    if score >= 55: return "1.5"
    if score >= 50: return "1.0"
    return "0.0"

def update_treeview():
    for item in grade_tree.get_children():
        grade_tree.delete(item)
    for subj in subjects_data:
        total_score = subj['pre_score'] + subj['final_score_40']
        grade_label = get_grade_point(total_score)
        final_display = f"{subj['final_score']}/{subj['final_total']} ({subj['final_score_40']:.2f})"
        
        if subj['final_total'] > 0:
            needed_40 = 79.5 - subj['pre_score']
            items_needed = math.ceil((needed_40 * subj['final_total']) / 40)
            note = f"Need {max(0, items_needed)} for 4.0" if items_needed <= subj['final_total'] else "4.0 Impossible"
        else:
            note = "Set total items"

        grade_tree.insert('', tk.END, values=(
            subj['name'], subj['credit'], f"{subj['pre_score']:.2f}",
            final_display, f"{total_score:.2f} ({grade_label})", note
        ))

# --- Integrated Editor (Pre-Score + Final Exam) ---

def open_unified_editor(subject_name):
    selected_subj = next((subj for subj in subjects_data if subj['name'] == subject_name), None)
    if not selected_subj: return

    editor = tk.Toplevel(root)
    editor.title(f"Manage Subject: {subject_name}")
    editor.geometry("450x550")
    editor.grab_set()

    main_frame = ttk.Frame(editor, padding="20")
    main_frame.pack(fill='both', expand=True)

    ttk.Label(main_frame, text=f"Editing: {subject_name}", font=('Arial', 12, 'bold')).pack(pady=5)
    
    # Pre-Score Entry
    ttk.Label(main_frame, text="Current Pre-Score (max 60):").pack(anchor='w', pady=(10,0))
    pre_var = tk.StringVar(value=str(selected_subj['pre_score']))
    ttk.Entry(main_frame, textvariable=pre_var).pack(fill='x')

    ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=15)

    # Final Exam Entries
    ttk.Label(main_frame, text="Exam Score Obtained:").pack(anchor='w')
    score_var = tk.StringVar(value=str(selected_subj['final_score']))
    ttk.Entry(main_frame, textvariable=score_var).pack(fill='x', pady=5)

    ttk.Label(main_frame, text="Total Exam Items:").pack(anchor='w')
    total_var = tk.StringVar(value=str(selected_subj['final_total']))
    ttk.Entry(main_frame, textvariable=total_var).pack(fill='x', pady=5)

    # Target Display
    target_frame = ttk.LabelFrame(main_frame, text="Live Target Calculator", padding="10")
    target_frame.pack(fill='x', pady=15)
    target_label = ttk.Label(target_frame, text="", justify="left")
    target_label.pack()

    def refresh_targets(*args):
        try:
            total_items = float(total_var.get())
            current_pre = float(pre_var.get())
            if total_items > 0:
                targets = [("4.0", 79.5), ("3.5", 75), ("3.0", 70), ("2.5", 65), ("2.0", 60)]
                txt = ""
                for label, val in targets:
                    needed = math.ceil(((val - current_pre) * total_items) / 40)
                    needed_text = f"{max(0, needed)} items" if needed <= total_items else "Impossible"
                    txt += f"Grade {label}: {needed_text}\n"
                target_label.config(text=txt)
        except: pass

    # Trace both Pre-score and Total Items for live target updates
    pre_var.trace_add("write", refresh_targets)
    total_var.trace_add("write", refresh_targets)
    refresh_targets()

    def save_all():
        try:
            ps = float(pre_var.get())
            s = float(score_var.get())
            t = float(total_var.get())
            
            if ps > 60 or s > t:
                messagebox.showerror("Error", "Check logic: Pre-score max 60, Score cannot exceed total.")
                return
            
            selected_subj['pre_score'] = ps
            selected_subj['final_score'] = s
            selected_subj['final_total'] = t
            selected_subj['final_score_40'] = round((s / t * 40), 2) if t > 0 else 0.0
            
            save_data_to_json() 
            update_treeview()
            editor.destroy()
        except ValueError: messagebox.showerror("Error", "Please enter valid numbers.")

    ttk.Button(main_frame, text="Save & Close", command=save_all).pack(side='bottom', pady=10)

# --- App Handlers ---

def add_subject():
    try:
        name = subject_entry.get().strip()
        credit = float(credit_entry.get())
        pre = float(pre_score_entry.get())
        if not name: raise ValueError
        subjects_data.append({
            'name': name, 'credit': credit, 'pre_score': pre,
            'final_score': 0, 'final_total': 0, 'final_score_40': 0.0
        })
        save_data_to_json(); update_treeview()
        subject_entry.delete(0, tk.END); credit_entry.delete(0, tk.END); pre_score_entry.delete(0, tk.END)
    except: messagebox.showwarning("Input Error", "Enter valid Name, Credit, and Pre-score.")

# --- UI Setup ---

root = tk.Tk()
root.title(f"Grade 4.0 Planner - {current_user}")
root.geometry("1280x650")

input_frame = ttk.LabelFrame(root, text="Subject Management", padding="10")
input_frame.pack(fill="x", padx=20, pady=10)

ttk.Label(input_frame, text="Name:").grid(row=0, column=0)
subject_entry = ttk.Entry(input_frame); subject_entry.grid(row=0, column=1,padx=5)
ttk.Label(input_frame, text="Credit:").grid(row=0, column=5)
credit_entry = ttk.Entry(input_frame, width=10); credit_entry.grid(row=0, column=6, padx=5)
ttk.Label(input_frame, text="Pre (60):").grid(row=0, column=7)
pre_score_entry = ttk.Entry(input_frame, width=10); pre_score_entry.grid(row=0, column=8, padx=5)

btn_container = ttk.Frame(input_frame)
btn_container.grid(row=1, column=0, columnspan=6, pady=10)
ttk.Button(btn_container, text="Add Subject", command=add_subject).pack(side="left", padx=5)
ttk.Button(btn_container, text="Edit Subject Details", command=lambda: open_unified_editor(grade_tree.item(grade_tree.focus(), 'values')[0]) if grade_tree.focus() else None).pack(side="left", padx=5)
ttk.Button(btn_container, text="Remove", command=lambda: [subjects_data.pop(next(i for i, s in enumerate(subjects_data) if s['name'] == grade_tree.item(grade_tree.focus(), 'values')[0])), save_data_to_json(), update_treeview()] if grade_tree.focus() else None).pack(side="left", padx=5)

columns = ("Subject", "Credit", "Pre (60%)", "Final (40%)", "Total (Grade)", "Notes")
grade_tree = ttk.Treeview(root, columns=columns, show="headings")
for c in columns: grade_tree.heading(c, text=c)
grade_tree.pack(fill="both", expand=True, padx=20, pady=10)
grade_tree.bind('<Double-1>', lambda e: open_unified_editor(grade_tree.item(grade_tree.focus(), 'values')[0]) if grade_tree.focus() else None)

load_data_from_json(); update_treeview()
root.mainloop()
