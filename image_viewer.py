import tkinter as tk
from tkinter import filedialog
import tkinterdnd2 as dnd
from PIL import Image, ImageTk
import re
import os


class ImageViewer(tk.Frame):
    image_file_types = '.bmp .png .jpg .tif'

    def __init__(self, master=None):
        super().__init__(master)
        self.pack()

        # instance variables
        self.APP_TITLE = "Image Viewer"
        self.CANVAS_BG_COLOR = 'gray32'
        self.TAG_IMAGE = 'tag_image'
        self.TAG_GRID = 'tag_grid'
        self.MAX_SCALE = 100.0
        self.GRID_INTERVAL = 50

        self.canvas = None

        self.show_grid = tk.BooleanVar(False)

        self.image_pillow = None
        self.image_tk = None
        self.image_id = 0
        self.image_scale = 1.0
        self.image_allow_drag = False
        self.image_allow_zoom = False

        self.mouse_left_down_pos = None
        self.mouse_right_down_pos = None
        self.mouse_left_hold = False
        self.mouse_right_hold = False

        self.key_control_hold = False

        # color reference :
        # https://memopy.hatenadiary.jp/entry/2017/06/11/092554
        # https://qiita.com/kuchida1981/items/ae04ded652bfc92a5e7e

        # root window setup
        master.title(self.APP_TITLE)
        master.geometry(
            self.get_pos_string_on_screen(
                int(master.winfo_screenwidth() * 0.5),
                int(master.winfo_screenheight() * 0.7),
                'n', 0, 50
            )[0]
        )

        # menu
        self.menu_bar = None
        self.menu_file = None
        self.menu_view = None
        self.create_menu()

        # for drag and drop
        master.drop_target_register(dnd.DND_FILES)
        master.dnd_bind('<<Drop>>', self.dnd_handler)

        # widget
        self.create_widget()

        # monitor held keys
        master.bind("<Key>", self.key_down)
        master.bind("<KeyRelease>", self.key_release)

    # ------------------------------
    # widget

    def create_widget(self):
        # canvas
        self.canvas = tk.Canvas(self.master, background=self.CANVAS_BG_COLOR)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # mouse events
        self.canvas.bind("<Motion>", self.mouse_move)  # mouse move
        self.canvas.bind("<B1-Motion>", self.mouse_left_move)  # drag mouse while holding down the left button
        self.canvas.bind("<Button-1>", self.mouse_left_down)  # down the left button
        self.canvas.bind("<ButtonRelease-1>", self.mouse_left_release)  # release the left button
        self.canvas.bind("<Double-Button-1>", self.mouse_left_double_click)  # double click the left button

        self.canvas.bind("<Button-3>", self.mouse_right_down)  # down the right button
        self.canvas.bind("<ButtonRelease-3>", self.mouse_right_release)  # release the right button
        self.canvas.bind("<Double-Button-3>", self.mouse_right_double_click)  # double click the right button

        self.canvas.bind("<MouseWheel>", self.mouse_wheel)  # mouse wheel

    # ------------------------------
    # menu

    def create_menu(self):
        self.menu_bar = tk.Menu(self)

        # File
        self.menu_file = tk.Menu(self.menu_bar, tearoff=tk.OFF)
        self.menu_bar.add_cascade(label="File", menu=self.menu_file)

        self.menu_file.add_command(label="Open", command=self.menu_open, accelerator="Ctrl+O")
        self.menu_bar.bind_all("<Control-o>", self.menu_open)
        self.menu_file.add_separator()
        self.menu_file.add_command(label="Quit", command=self.menu_quit, accelerator="Ctrl+Q")
        self.menu_bar.bind_all("<Control-q>", self.menu_quit)

        # View
        self.menu_view = tk.Menu(self.menu_bar, tearoff=tk.OFF)
        self.menu_bar.add_cascade(label="View", menu=self.menu_view)

        self.menu_view.add_command(label="Fit", command=self.menu_fit, accelerator="Ctrl+F")
        self.menu_bar.bind_all("<Control-f>", self.menu_fit)

        self.menu_view.add_checkbutton(label="Grid", command=self.menu_grid, variable=self.show_grid, accelerator="Ctrl+G")
        self.menu_bar.bind_all("<Control-g>", self.menu_grid_shortcut)

        # -----
        self.master.config(menu=self.menu_bar)

    def menu_open(self):
        filename = tk.filedialog.askopenfilename(
            filetypes=[("Image file", ImageViewer.image_file_types),
                       ("Bitmap", ".bmp"),
                       ("PNG", ".png"),
                       ("JPEG", ".jpg"),
                       ("Tiff", ".tif")],
            initialdir=os.getcwd()
        )

        if filename == '': return  # for when click the cancel button

        self.image_pillow = self.image_read_for_pillow(filename)
        self.show_fit_image()

    def menu_quit(self):
        self.master.destroy()

    def menu_fit(self):
        self.show_fit_image()

    def menu_grid(self):
        # print(f'menu grid = {self.show_grid.get()}')
        self.draw_grid(self.show_grid.get())

    def menu_grid_shortcut(self):
        self.show_grid.set(not self.show_grid.get())
        self.menu_grid()

    # ------------------------------
    # drag and drop

    def dnd_handler(self, event=None):
        file_list = self.make_file_list(event.data)
        for f in file_list:
            if os.path.isfile(f):
                fsplit = os.path.splitext(f)
                ext = fsplit[len(fsplit) - 1].lower()
                if ext in ImageViewer.image_file_types:
                    self.image_pillow = self.image_read_for_pillow(f)
                    self.show_fit_image()
                    return
            # elif os.path.isdir(f):
            #     pass
            # else:
            #     pass

    @staticmethod
    def make_file_list(dnd_files_string):
        rawfs = dnd_files_string
        bfs = re.findall('{.+?}', rawfs)
        fs = []
        for f in bfs:
            rawfs = rawfs.replace(f, '')
            fs.append(f.replace('{', '').replace('}', ''))
        fs = sorted(fs + rawfs.split())
        return fs

    # ------------------------------
    # mouse

    def mouse_move(self, event=None):
        pass

    def mouse_left_move(self, event=None):
        if self.image_id <= 0: return
        if not self.image_allow_drag: return

        dx = event.x - self.mouse_left_down_pos.x
        dy = event.y - self.mouse_left_down_pos.y
        ul_x, ul_y, _, _ = self.canvas.bbox(self.image_id)
        self.show_image(self.image_scale, ul_x + dx, ul_y + dy)

        self.mouse_left_down_pos = event

    def mouse_left_down(self, event=None):
        self.mouse_left_down_pos = event
        self.mouse_left_hold = True
        if self.is_mouse_overlap_image(event.x, event.y):
            self.image_allow_drag = True

    def mouse_left_release(self, event=None):
        self.mouse_left_hold = False
        self.image_allow_drag = False

    def mouse_left_double_click(self, event=None):
        if self.image_id <= 0: return
        if not self.is_mouse_overlap_image(event.x, event.y):
            return

        self.show_fit_image()

    def mouse_right_down(self, event=None):
        self.mouse_right_down_pos = event
        self.mouse_right_hold = True
        # if self.is_mouse_overlap_image(event.x, event.y):
        #     self.image_allow_zoom = True

    def mouse_right_release(self, event=None):
        self.mouse_right_hold = False
        self.image_allow_zoom = False

    def mouse_right_double_click(self, event=None):
        pass

    def mouse_wheel(self, event=None):
        if not self.image_allow_zoom:
            if not self.mouse_right_hold and not self.key_control_hold: return
            if not self.is_mouse_overlap_image(event.x, event.y): return
            self.image_allow_zoom = True

        if event.delta < 0:
            self.show_zoom_image(0.8, event.x, event.y)
        else:
            self.show_zoom_image(1.25, event.x, event.y)

    def is_mouse_overlap_image(self, x, y):
        # self.update()

        # # the frontmost object has tag "current" after calling find_overlapping().
        # overlaped_ids = self.canvas.find_overlapping(x, y, x, y)
        # frontmost_id = self.canvas.find_withtag("current")
        # if (len(frontmost_id) > 0) and (self.image_id == frontmost_id[0]):
        #     return True
        # return False

        # for ignore grid lines
        overlaped_ids = self.canvas.find_overlapping(x, y, x, y)
        for i in overlaped_ids:
            if self.image_id == i: return True
        return False

    # ------------------------------
    # key

    def key_down(self, event=None):
        if event.keysym == 'Control_L' or event.keysym == 'Control_R':
            self.key_control_hold = True
            # if self.is_mouse_overlap_image(event.x, event.y):
            #     self.image_allow_zoom = True

    def key_release(self, event=None):
        if event.keysym == 'Control_L' or event.keysym == 'Control_R':
            self.key_control_hold = False
            self.image_allow_zoom = False

    # ------------------------------
    # image

    def draw_grid(self, draw):
        self.canvas.delete(self.TAG_GRID)
        if not draw: return     # hide only

        # draw grid
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        # dash_pattern = (1, 1)
        for i in range(0, w, self.GRID_INTERVAL):
            # v-line
            self.canvas.create_line(i, 0, i, h, fill='red', tags=self.TAG_GRID)     # dash=dash_pattern
        for i in range(0, h, self.GRID_INTERVAL):
            # h-line
            self.canvas.create_line(0, i, w, i, fill='red', tags=self.TAG_GRID)     # dash=dash_pattern

    @staticmethod
    def get_image_fit_param(canvas, image_pillow):
        # calculate the fit scale
        scale = float(canvas.winfo_width() / image_pillow.width)
        scale_h = float(canvas.winfo_height() / image_pillow.height)
        if scale > scale_h: scale = scale_h

        delta_x: int = (canvas.winfo_width() - image_pillow.width * scale) // 2
        delta_y: int = (canvas.winfo_height() - image_pillow.height * scale) // 2

        return scale, delta_x, delta_y

    def show_fit_image(self):
        if self.image_pillow is None: return

        scale, offset_x, offset_y = self.get_image_fit_param(self.canvas, self.image_pillow)
        self.show_image(scale, offset_x, offset_y)

    def show_zoom_image(self, scale, zoom_x=0, zoom_y=0):
        if self.image_pillow is None: return

        ul_x, ul_y, _, _ = self.canvas.bbox(self.image_id)
        rescale = scale * self.image_scale
        offset_x = zoom_x - int((zoom_x - ul_x) * scale)
        offset_y = zoom_y - int((zoom_y - ul_y) * scale)

        self.show_image(rescale, offset_x, offset_y)

    def show_image(self, scale=1.0, offset_x=0, offset_y=0):
        if self.image_pillow is None: return
        if scale > self.MAX_SCALE: scale = self.MAX_SCALE

        zoom_width = int(self.image_pillow.width * scale)
        zoom_height = int(self.image_pillow.height * scale)
        if (zoom_width <= 0) or (zoom_height <= 0): return

        # resize image
        self.image_scale = scale
        image = self.image_pillow
        if self.image_scale != 1.0:
            image = self.image_pillow.resize((zoom_width, zoom_height))

        # show image
        self.image_tk = self.image_pillow_to_tk(image)
        if self.image_id > 0:
            self.canvas.delete(self.image_id)
        self.image_id = self.canvas.create_image(
            offset_x,
            offset_y,
            image=self.image_tk,
            anchor='nw',
            tags=self.TAG_IMAGE
        )

        # grid
        self.draw_grid(self.show_grid.get())

    # ------------------------------
    # utility

    def get_pos_string_on_screen(self, width, height, position='C', x_offset=0, y_offset=0):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        xy = ((sw - width) // 2, (sh - height) // 2)
        p = position.upper()
        if p == 'NW':
            xy = (0, 0)
        elif p == 'N':
            xy = ((sw - width) // 2, 0)
        elif p == 'NE':
            xy = (sw - width, 0)
        elif p == 'W':
            xy = (0, (sh - height) // 2)
        elif p == 'C':
            pass
        elif p == 'E':
            xy = (sw - width, (sh - height) // 2)
        elif p == 'SW':
            xy = (0, sh - height)
        elif p == 'S':
            xy = ((sw - width) // 2, sh - height)
        elif p == 'SE':
            xy = (sw - width, sh - height)

        xy = (xy[0] + x_offset, xy[1] + y_offset)
        r = (f'{width}x{height}+{xy[0]}+{xy[1]}', width, height, xy[0], xy[1])
        return r

    @staticmethod
    def image_read_for_pillow(file_path):
        return Image.open(file_path)

    @staticmethod
    def image_pillow_to_tk(img):
        return ImageTk.PhotoImage(img)
