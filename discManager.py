import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from functools import partial
import hashlib
from collections import defaultdict
import shutil
from tkinter import simpledialog
import customtkinter as ctk
import magic

# -------Clear output for every next result------
def clear():
    for widgets in frame_result.winfo_children():
      widgets.destroy()


# -------Error if no choice of path made--------
def error_message(directory):
    if(directory==""):
        messagebox.showinfo(message="Please select a path to get details")


# ---------Complte disc size----------
def get_total_space(path):
    total, _, _ = shutil.disk_usage(path)
    print(path)
    return total

def get_free_space(path):
    if not os.path.isdir(path):
        raise OSError("Could not determine space")
    return shutil.disk_usage(path).free 

def get_file_type(file_path):
    mime = magic.Magic(mime=True)

    type = mime.from_file(file_path)

    file_type = type.split("/")[0]
    
    if(file_type =="image" or file_type == "video"):
        return file_type
    elif(file_type == "application" or type=="text/plain"):
        return "document"
    elif(file_type=="text"):
        var = type.split('-')
        if var[0] == type:
            return type.split('/')[1]
        else:
            return var[1]
    else:
        return type
    

# ---------Total directory breakdown---------
def get_size_of_directory(directory):
    
    clear()
    error_message(directory)
    dic={}
    
    total_size = 0
    stack = [directory]

    while stack:
        entry = stack.pop()
        if os.path.isdir(entry):
            with os.scandir(entry) as entries:
                for child in entries:
                    dic[child.name] = os.path.getsize(child.path)
                    stack.append(child.path)
        else:
            total_size += os.path.getsize(entry)
 
    total_size=total_size/(1024*1024)
    message = f"\nTotal Space: {total_size} MB \n\n"
    
    f_type=get_file_types(directory)

    for key,lis in f_type.items():
        value=0
        for file in lis:
            value += os.path.getsize(file)
        value = value/(1024*1024)
        if value > 0:
            message += str(key)+" : " + str(value)+" MB \n"
            message += "\n"

    frame_utilization = ctk.CTkFrame(frame_result,fg_color="transparent")
    frame_utilization.pack()
    
    label_message = ctk.CTkLabel(frame_utilization, text=message, fg_color="transparent")
    label_message.pack()

# ---------Utility function for size formatting----------
def format_bytes(bytes_value):
    sizes = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    while bytes_value >= 1024 and index < len(sizes) - 1:
        bytes_value /= 1024
        index += 1
    return f"{bytes_value:.2f} {sizes[index]}"


# ----------Disc usage display----------
def display_space_utilization_message(directory):
    clear()
    error_message(directory)
    total_space = get_total_space(directory)
    utilized_space = total_space - get_free_space(directory)
    utilization_percentage = (utilized_space / total_space) * 100

    total_space_formatted = format_bytes(total_space)
    utilized_space_formatted = format_bytes(utilized_space)
    free_space_formatted = format_bytes(get_free_space(directory))

    message = f"Total Space: {total_space_formatted}\nUtilized Space: {utilized_space_formatted}\nFree Space: {free_space_formatted}"

    # frame for the bar graph and the message
    frame_utilization = ctk.CTkFrame(frame_result,fg_color="transparent")
    frame_utilization.pack()

    #  bar graph to represent disk space utilization
    bar_width = 400
    bar_height = 20
    canvas = ctk.CTkCanvas(frame_utilization, width=bar_width, height=bar_height)
    canvas.pack()

    
    if(utilized_space>=total_space/2):
        canvas.create_rectangle(0, 0, utilization_percentage * bar_width / 100, bar_height, fill="red")    
    else:
        canvas.create_rectangle(0, 0, utilization_percentage * bar_width / 100, bar_height, fill="#0096FF")
    
    canvas.create_rectangle(utilization_percentage * bar_width / 100, 0, bar_width, bar_height, fill="white")

    label_message = ctk.CTkLabel(frame_utilization, text=message, fg_color="transparent")
    label_message.pack()



# --------Grouping file types based on extensions----------
def get_file_types(directory):

    
    # dictionary to store file names by extension
    file_groups = {
        "Images": ["jpg", "png", "gif", "tiff", "jpeg"],
        "Documents": ["doc", "docx", "ppt", "pptx", "pdf", "txt","xlsx","csv"],
        "Audios": ["mp3", "wav", "ogg", "flac"],
        "Videos": ["mp4", "avi", "mpeg", "mov"],
        "Compressed files": ["zip", "rar", "gz"],
        "Programs": ["c", "cpp", "java", "py", "kotlin", "php"],
        "Databases": ["db","mdb","sql"]
    }

    grouped_files = {file_type: [] for file_type in file_groups.keys()}
    grouped_files["other"] = []

    for root, _, files in os.walk(directory):
        for file in files:
            file_ext = file.split(".")[-1].lower()

            # Check the file extension and add file to the list in the dictionary
            added_to_group = False
            for file_type, ext_list in file_groups.items():
                if file_ext in ext_list:
                    grouped_files[file_type].append(os.path.join(root, file))
                    added_to_group = True
                    break

            if not added_to_group:
                grouped_files["other"].append(os.path.join(root, file))

    return grouped_files


# ----------Hashing file content to check duplicates later----------
def generate_md5(fname):
    chunk_size=1024
    hash = hashlib.md5()
    with open(fname, "rb") as f:
        # Read file in blocks (less expensive)
        chunk = f.read(chunk_size)
        # Keep reading the file until the end and update hash
        while chunk:
            hash.update(chunk)
            chunk = f.read(chunk_size)

    return hash.hexdigest()

# ---------Find duplicate files based oon content (empty files considered non-duplicate)----------
def find_duplicate_files(directory):

    md5_dict = defaultdict(list)
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if os.path.getsize(file_path) == 0 :
                continue 
            md5_dict[generate_md5(file_path)].append(file_path)
    return {hash_key: files for hash_key, files in md5_dict.items() if len(files) > 1}




# --------Deletion of duplicated files as per user choice----------
files_to_delete = set()

def delete_selected_files():
    # delete the selected files
    if files_to_delete:
        confirmation = messagebox.askokcancel("Confirmation", "Are you sure you want to delete the selected files?")
        if confirmation:
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    print(f"File '{file_path}' deleted successfully.")
                except Exception as e:
                    print(f"Error occurred while deleting '{file_path}': {e}")
            # Clear the set after deletion
            files_to_delete.clear()
            clear()
            label_message = ctk.CTkLabel(frame_result, text="File Deleted Successfully", fg_color="transparent")
            label_message.pack()
            
    else:
        messagebox.showinfo("No Files Selected", "No files selected for deletion.")

def checkbox_handler(file_path, check_var, checkbox_vars):
    # update the checkbox_vars dictionary with the new checkbox state
    checkbox_vars[file_path] = check_var
    update_files_to_delete(checkbox_vars)

def update_files_to_delete(checkbox_vars):
    # update the files_to_delete set based on checkbox states
    files_to_delete.clear()
    for file_path, check_var in checkbox_vars.items():
        if check_var.get() == "on":
            files_to_delete.add(file_path)

def display_duplicate_files_message(directory):
    clear()
    duplicate_files = find_duplicate_files(directory)
    scrollable_frame = ctk.CTkScrollableFrame(frame_result, width=800, height=200)
    scrollable_frame.pack()
    a = 1
    message = ""
    checkbox_vars = {}  # Dictionary to store checkbox variables for each file
    flag = False
    if duplicate_files:
        label_message = ctk.CTkLabel(scrollable_frame, text="Uncheck the boxes to prevent deletion", fg_color="transparent")
        label_message.pack()
            
        flag = True
        for files in duplicate_files.values():
            message = "Duplicate Files " + str(a) + ":\n"
            a += 1
            label_message = ctk.CTkLabel(scrollable_frame, text=message, fg_color="transparent")
            label_message.pack()
            for file_path in files:
                check_var = tk.StringVar()
                check_var.set("on")  # default value set to "on"
                checkbox_vars[file_path] = check_var  

                checkbox = ctk.CTkCheckBox(scrollable_frame, text=file_path,
                                           command=partial(checkbox_handler, file_path, check_var, checkbox_vars),
                                           variable=check_var, onvalue="on", offvalue="off")
                checkbox.pack(padx=20, pady=10)

    else:
        label_message = ctk.CTkLabel(scrollable_frame, text="No Duplicate File is found", fg_color="transparent")
        label_message.pack()
        
    if flag == True:
        delete_button = tk.Button(scrollable_frame, text="Delete Selected Files", command=delete_selected_files)
        delete_button.pack(pady=10)



# ---------Delete specific file types of user choice-----------
def delete_file(directory,specific_type):
    clear()
    file_found = False
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if(get_file_type(file_path)==specific_type):
                file_found = True
                os.remove(file_path)
    if (file_found):
        messagebox.showinfo(message="Deletion Successful")
    else:
        messagebox.showinfo(message="No such file found!")



# Threshold for large files taken user input
def get_threshold_from_user():
    root = tk.Tk()
    root.withdraw()  
    # Ask the user to input the threshold value
    threshold = simpledialog.askinteger("Threshold", "Enter the size threshold (in MB):", minvalue=1)

    return threshold

# Find large files acc to given size
def find_large_files(directory, size_threshold):
    large_files = []
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if os.path.getsize(file_path)/(1024*1024) > size_threshold:
               yield file_path

# Display large files 
def display_large_files_message(directory):
    clear()
    scrollable_frame = ctk.CTkScrollableFrame(frame_result, width=800, height=200)
    scrollable_frame.pack()

    size_threshold = get_threshold_from_user()
    large_files = find_large_files(directory, size_threshold)

    try:
        first_large_file = next(large_files)
        print(first_large_file)
    except StopIteration:
        label_message = ctk.CTkLabel(scrollable_frame, text="No Large File Detected", fg_color="transparent")
    else:
        # If there was at least one large file, continue iterating
        message = "Large Files:\n"
        for file_path in large_files:
            message += f"{file_path} - {os.path.getsize(file_path)} MB\n"
        label_message = ctk.CTkLabel(scrollable_frame, text=message, fg_color="transparent")
    label_message.pack()
       


# --------Deletion of specific file types--------
value=""
def display_specific_file_type(directory,specific_type):
    clear()
    error_message(directory)
    message=""
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if(get_file_type(file_path)==specific_type):
              message+=file_path+'\n'  

    frame_utilization = ctk.CTkFrame(frame_result,fg_color="transparent")
    frame_utilization.pack()

    
    if(len(message)==0):
        message="No such file is present"
    label_message = ctk.CTkLabel(frame_utilization, text=message, fg_color="transparent")
    label_message.pack()



# UI (REF: CustomTkinter)
root = ctk.CTk()
root.title("Disk Management Application")
root.geometry("700x400")
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

frame_heading = ctk.CTkFrame(root)
frame_heading.pack()

heading_label = ctk.CTkLabel(frame_heading, text="Disk Management Application",font=("Helvetica", 30))
heading_label.pack()

frame_target = ctk.CTkFrame(root,fg_color="transparent")
frame_target.pack()

ctk.CTkLabel(frame_target, text="Target Directory:",font=("Helvetica",20)).pack(side=tk.LEFT, padx=10)
entry_target_directory = ctk.CTkEntry(frame_target, width=170, fg_color="transparent")
entry_target_directory.pack(side=tk.LEFT, padx=5,pady=10)



def browse_target_directory():
    target_dir = filedialog.askdirectory()
    if target_dir:
        entry_target_directory.delete(0, tk.END)
        entry_target_directory.insert(0, target_dir)


btn_browse = ctk.CTkButton(frame_target, text="Browse",width=20, command=browse_target_directory, corner_radius=10)
btn_browse.pack(side=tk.LEFT)

def checkbox_event():
    print("checkbox toggled, current value:", check_var.get())

check_var = ctk.StringVar(value="on")
checkbox = ctk.CTkCheckBox(root, text="CTkCheckBox", command=checkbox_event,variable=check_var, onvalue="on", offvalue="off")


frame_ac = ctk.CTkFrame(root, fg_color="transparent")
frame_ac.pack()

ctk.CTkLabel(frame_ac, text="File Type to Scan", font=("Helvetica", 20)).pack(side=tk.LEFT, padx=10)


options=["image","video","document","python","c",'c++',"java", "html"]


combobox = ctk.CTkComboBox(frame_ac, values=options)
combobox.pack(side=tk.LEFT)



frame_result = ctk.CTkFrame(root,fg_color="transparent")
button = ctk.CTkButton(frame_ac, text="Scan", command=lambda:display_specific_file_type(entry_target_directory.get(),combobox.get()))
button.pack(side=tk.LEFT,padx=10)

button = ctk.CTkButton(frame_ac, text="Delete", command=lambda:delete_file(entry_target_directory.get(),combobox.get()))
button.pack(side=tk.LEFT,padx=10)



frame_actions = ctk.CTkFrame(root,fg_color="transparent")
frame_actions.pack()
frame_result.pack()


btn_show_space = ctk.CTkButton(frame_actions,corner_radius=10, text="Show Disk Space", command=lambda: display_space_utilization_message(entry_target_directory.get()))
btn_show_space.pack(pady=10, padx=10, side=tk.LEFT)

btn_find_large = ctk.CTkButton(frame_actions,corner_radius=10, text="Show Directory Size", command=lambda: get_size_of_directory(entry_target_directory.get()))
btn_find_large.pack(pady=10, padx=10, side=tk.LEFT)

btn_find_duplicate = ctk.CTkButton(frame_actions, corner_radius=10,text="Find Duplicate Files", command=lambda: display_duplicate_files_message(entry_target_directory.get()))
btn_find_duplicate.pack(pady=10, padx=10, side=tk.LEFT)

btn_find_large = ctk.CTkButton(frame_actions, corner_radius=10,text="Find Large Files", command=lambda: display_large_files_message(entry_target_directory.get()))
btn_find_large.pack(pady=10, padx=10, side=tk.LEFT)



root.mainloop()