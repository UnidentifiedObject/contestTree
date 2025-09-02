import tkinter as tk
from tkinter import simpledialog, colorchooser, filedialog, messagebox
from PIL import Image, ImageGrab
import json
import os

# -----------------------------
# Helper Classes
# -----------------------------
class CanvasElement:
    def __init__(self, element_type, x, y, size=50, color="black", content="", x2=None, y2=None):
        self.type = element_type
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.content = content
        self.id = None  # main canvas ID

        # For lines: x2, y2 endpoint
        if element_type == "line":
            self.x2 = x2 if x2 is not None else x + size
            self.y2 = y2 if y2 is not None else y + size
            self.handle1_id = None
            self.handle2_id = None
        elif element_type in ("square", "circle"):
            self.handles = []  # corner handles for resizing

# -----------------------------
# Main Application
# -----------------------------
class ContestTreeApp:
    HANDLE_SIZE = 6

    def __init__(self, root):
        self.root = root
        self.root.title("Contest Tree")

        # Frames
        self.sidebar = tk.Frame(root, width=150, bg="#ddd")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        # Canvas
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Sidebar buttons
        self.add_sidebar_buttons()

        # Elements
        self.elements = []
        self.selected_element = None
        self.drag_data = {"x":0, "y":0, "endpoint":None, "handle_index":None}

        # Canvas bindings
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Menu
        self.create_menu()

        # Grid snapping
        self.snap_to_grid = False
        self.grid_size = 20

        # Delete button
        self.delete_button = tk.Button(self.sidebar, text="Delete Element", command=self.delete_selected)
        self.delete_button.pack_forget()

    # -----------------------------
    # Sidebar
    # -----------------------------
    def add_sidebar_buttons(self):
        tk.Label(self.sidebar, text="Shapes", bg="#ddd", font=("Arial",12,"bold")).pack(pady=5)
        tk.Button(self.sidebar, text="Square", command=lambda: self.add_element("square")).pack(pady=2)
        tk.Button(self.sidebar, text="Circle", command=lambda: self.add_element("circle")).pack(pady=2)
        tk.Button(self.sidebar, text="Line", command=lambda: self.add_element("line")).pack(pady=2)

        tk.Label(self.sidebar, text="Text", bg="#ddd", font=("Arial",12,"bold")).pack(pady=10)
        tk.Button(self.sidebar, text="Text Block", command=lambda: self.add_element("text")).pack(pady=2)

        tk.Button(self.sidebar, text="Toggle Grid Snap", command=self.toggle_grid_snap).pack(pady=20)

    # -----------------------------
    # Add Element
    # -----------------------------
    def add_element(self, element_type):
        x, y = 100, 100
        if element_type == "text":
            content = simpledialog.askstring("Input Text", "Enter text:")
            if not content:
                return
        else:
            content = ""
        color = colorchooser.askcolor(title="Choose Color")[1] or "black"
        element = CanvasElement(element_type, x, y, color=color, content=content)
        self.draw_element(element)
        self.elements.append(element)

    def draw_element(self, element):
        s = element.size
        if element.type == "square":
            element.id = self.canvas.create_rectangle(element.x, element.y, element.x+s, element.y+s, fill=element.color, tags=("element",))
            self.create_resize_handles(element)
        elif element.type == "circle":
            element.id = self.canvas.create_oval(element.x, element.y, element.x+s, element.y+s, fill=element.color, tags=("element",))
            self.create_resize_handles(element)
        elif element.type == "line":
            element.id = self.canvas.create_line(element.x, element.y, element.x2, element.y2, fill=element.color, width=2, tags=("element",))
            element.handle1_id = self.canvas.create_oval(element.x-5, element.y-5, element.x+5, element.y+5, fill="red", tags=("handle",))
            element.handle2_id = self.canvas.create_oval(element.x2-5, element.y2-5, element.x2+5, element.y2+5, fill="red", tags=("handle",))
        elif element.type == "text":
            element.id = self.canvas.create_text(element.x, element.y, text=element.content, font=("Arial",16), fill=element.color, tags=("element",))

    # -----------------------------
    # Resize Handles
    # -----------------------------
    def create_resize_handles(self, element):
        element.handles.clear()
        x0, y0, x1, y1 = self.canvas.coords(element.id)
        corners = [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        for cx, cy in corners:
            hid = self.canvas.create_rectangle(cx-self.HANDLE_SIZE, cy-self.HANDLE_SIZE, cx+self.HANDLE_SIZE, cy+self.HANDLE_SIZE, fill="red", tags=("handle",))
            element.handles.append(hid)

    def update_resize_handles(self, element):
        if element.type not in ("square","circle"):
            return
        x0, y0, x1, y1 = self.canvas.coords(element.id)
        corners = [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        for i, (cx, cy) in enumerate(corners):
            self.canvas.coords(element.handles[i], cx-self.HANDLE_SIZE, cy-self.HANDLE_SIZE, cx+self.HANDLE_SIZE, cy+self.HANDLE_SIZE)

    # -----------------------------
    # Canvas Interaction
    # -----------------------------
    def on_canvas_click(self, event):
        clicked = self.canvas.find_closest(event.x, event.y)
        canvas_id = clicked[0]

        # Check for handles
        for e in self.elements:
            if e.type=="line":
                if canvas_id in (e.handle1_id, e.handle2_id):
                    self.selected_element = e
                    self.drag_data["endpoint"] = "handle1" if canvas_id==e.handle1_id else "handle2"
                    return
            elif e.type in ("square","circle"):
                if canvas_id in e.handles:
                    self.selected_element = e
                    self.drag_data["handle_index"] = e.handles.index(canvas_id)
                    return

        # Check normal elements
        for e in self.elements:
            if e.id == canvas_id:
                self.selected_element = e
                self.drag_data["x"] = event.x - e.x
                self.drag_data["y"] = event.y - e.y
                self.drag_data["endpoint"] = None
                self.drag_data["handle_index"] = None
                break
        else:
            self.selected_element = None

        if self.selected_element:
            self.delete_button.pack()
        else:
            self.delete_button.pack_forget()

    def on_drag(self, event):
        if not self.selected_element:
            return
        x, y = (event.x, event.y)
        if self.snap_to_grid:
            x = round(x/self.grid_size)*self.grid_size
            y = round(y/self.grid_size)*self.grid_size
        e = self.selected_element

        # Resize shape handles
        if e.type in ("square","circle") and self.drag_data.get("handle_index") is not None:
            idx = self.drag_data["handle_index"]
            x0, y0, x1, y1 = self.canvas.coords(e.id)
            if idx==0: x0,y0 = x,y
            elif idx==1: x1,y0 = x,y
            elif idx==2: x1,y1 = x,y
            elif idx==3: x0,y1 = x,y
            self.canvas.coords(e.id,x0,y0,x1,y1)
            self.update_resize_handles(e)
            return

        # Move line endpoints
        if e.type=="line" and self.drag_data.get("endpoint"):
            if self.drag_data["endpoint"]=="handle1":
                e.x, e.y = x, y
            else:
                e.x2, e.y2 = x, y
            self.canvas.coords(e.id,e.x,e.y,e.x2,e.y2)
            self.canvas.coords(e.handle1_id,e.x-5,e.y-5,e.x+5,e.y+5)
            self.canvas.coords(e.handle2_id,e.x2-5,e.y2-5,e.x2+5,e.y2+5)
            return

        # Move normal element
        dx = x - e.x
        dy = y - e.y
        self.canvas.move(e.id, dx, dy)
        e.x, e.y = x, y
        if e.type in ("square","circle"): self.update_resize_handles(e)
        if e.type=="line":
            self.canvas.move(e.handle1_id, dx, dy)
            self.canvas.move(e.handle2_id, dx, dy)

    def on_release(self, event):
        self.drag_data = {"x":0,"y":0,"endpoint":None,"handle_index":None}

    # -----------------------------
    # Delete
    # -----------------------------
    def delete_selected(self):
        if not self.selected_element: return
        e = self.selected_element
        self.canvas.delete(e.id)
        if e.type=="line":
            self.canvas.delete(e.handle1_id)
            self.canvas.delete(e.handle2_id)
        elif e.type in ("square","circle"):
            for h in e.handles:
                self.canvas.delete(h)
        self.elements.remove(e)
        self.selected_element = None
        self.delete_button.pack_forget()

    # -----------------------------
    # Menu: Save/Load/Export
    # -----------------------------
    def create_menu(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save", command=self.save_canvas)
        filemenu.add_command(label="Load", command=self.load_canvas)
        filemenu.add_command(label="Export as Image", command=self.export_image)
        menubar.add_cascade(label="File", menu=filemenu)
        self.root.config(menu=menubar)

    def save_canvas(self):
        data = []
        for e in self.elements:
            d = {"type":e.type,"x":e.x,"y":e.y,"size":e.size,"color":e.color,"content":e.content}
            if e.type=="line": d.update({"x2":e.x2,"y2":e.y2})
            data.append(d)
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if path:
            with open(path,"w") as f: json.dump(data,f)
            messagebox.showinfo("Saved","Canvas saved successfully!")

    def load_canvas(self):
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if path:
            with open(path,"r") as f: data=json.load(f)
            self.canvas.delete("all")
            self.elements=[]
            for d in data:
                e=CanvasElement(d["type"],d["x"],d["y"],size=d.get("size",50),color=d.get("color","black"),content=d.get("content",""),x2=d.get("x2"),y2=d.get("y2"))
                self.draw_element(e)
                self.elements.append(e)

    # -----------------------------
    # Export as Image
    # -----------------------------
    def export_image(self):
        # Save canvas as postscript
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")])
        if not file_path: return
        x=self.root.winfo_rootx()+self.canvas.winfo_x()
        y=self.root.winfo_rooty()+self.canvas.winfo_y()
        x1=x+self.canvas.winfo_width()
        y1=y+self.canvas.winfo_height()
        ImageGrab.grab().crop((x,y,x1,y1)).save(file_path)
        messagebox.showinfo("Exported","Canvas exported as image!")

    # -----------------------------
    # Grid Snap
    # -----------------------------
    def toggle_grid_snap(self):
        self.snap_to_grid = not self.snap_to_grid
        status = "ON" if self.snap_to_grid else "OFF"
        messagebox.showinfo("Grid Snap", f"Grid snapping is now {status}.")

# -----------------------------
# Run App
# -----------------------------
if __name__=="__main__":
    root=tk.Tk()
    app=ContestTreeApp(root)
    root.geometry("900x600")
    root.mainloop()
