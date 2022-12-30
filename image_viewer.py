import tkinter as tk
from tkinter import filedialog
import tkinterdnd2 as dnd
from PIL import Image, ImageTk
# import numpy as np
import re
import os


class ImageViewer(tk.Frame):
    IMAGE_FILE_TYPES = '.bmp .png .jpg .tif'

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
        self.canvas_conf = None

        self.show_grid = tk.BooleanVar()
        self.show_grid.set(False)

        self.image_pillow = None
        self.image_tk = None
        self.image_id = 0
        self.image_scale = 1.0
        self.drag_widget_id = 0

        self.mouse_left_down_pos = None

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

        # - No longer needed due to improvements, but will be commented out for posterity. -
        # # monitor held keys
        # master.bind("<Key>", self.key_down)
        # master.bind("<KeyRelease>", self.key_release)

    # ------------------------------
    # widget

    def create_widget(self):
        # canvas
        self.canvas = tk.Canvas(self.master, background=self.CANVAS_BG_COLOR)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # mouse events
        self.canvas.bind("<B1-Motion>", self.mouse_left_move)   # drag while holding down the mouse left button

        self.canvas.bind("<Button-1>", self.mouse_left_down)    # down the mouse left button
        self.canvas.bind("<ButtonRelease-1>", self.mouse_left_release)          # release the mouse left button
        self.canvas.bind("<Double-Button-1>", self.mouse_left_double_click)     # double click the mouse left button

        self.canvas.bind("<Button-3>", self.mouse_right_down)  # down the mouse right button
        self.canvas.bind("<ButtonRelease-3>", self.mouse_right_release)  # release the mouse right button

        self.canvas.bind("<B3-MouseWheel>", self.mouse_wheel)   # mouse wheel-up while holding down the mouse right button
        self.canvas.bind("<Control-MouseWheel>", self.mouse_wheel)  # mouse wheel-up while holding down the control button

        # - under consideration -
        # #  For mouse wheel support under Linux, use Button-4 (scroll up) and Button-5 (scroll down)
        # self.canvas.bind("<Button-4>", self.mouse_wheel)  # mouse wheel
        # self.canvas.bind("<Button-5>", self.mouse_wheel)  # mouse wheel

        self.canvas.bind("<Configure>", self.canvas_resize)

    # ------------------------------
    # menu

    def create_menu(self, event=None):
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

    def menu_open(self, event=None):
        filename = tk.filedialog.askopenfilename(
            filetypes=[("Image file", ImageViewer.IMAGE_FILE_TYPES),
                       ("Bitmap", ".bmp"),
                       ("PNG", ".png"),
                       ("JPEG", ".jpg"),
                       ("Tiff", ".tif")],
            initialdir=os.getcwd()
        )

        if filename == '': return  # for when click the cancel button

        self.image_pillow = self.image_read_for_pillow(filename)
        self.set_image()
        self.show_fit_image()

    def menu_quit(self, event=None):
        self.master.destroy()

    def menu_fit(self, event=None):
        self.show_fit_image()

    def menu_grid(self, event=None):
        self.draw_grid(self.show_grid.get())

    def menu_grid_shortcut(self, event=None):
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
                if ext in ImageViewer.IMAGE_FILE_TYPES:
                    self.image_pillow = self.image_read_for_pillow(f)
                    self.set_image()
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

    def mouse_left_move(self, event=None):
        if self.drag_widget_id <= 0: return

        dx = event.x - self.mouse_left_down_pos.x
        dy = event.y - self.mouse_left_down_pos.y
        self.canvas.move(self.drag_widget_id, dx, dy)

        self.mouse_left_down_pos = event

    def mouse_left_down(self, event=None):
        self.mouse_left_down_pos = event
        self.drag_widget_id = self.overlapped_frontmost_widget(event.x, event.y)

    def mouse_left_release(self, event=None):
        self.drag_widget_id = 0

    def mouse_left_double_click(self, event=None):
        if self.image_id <= 0: return
        if not self.is_mouse_overlap_image(event.x, event.y): return

        self.show_fit_image()

    def mouse_right_down(self, event=None):
        pass

    def mouse_right_release(self, event=None):
        pass

    def mouse_wheel(self, event=None):
        if not self.is_mouse_overlap_image(event.x, event.y): return

        if event.delta < 0: self.show_zoom_image(0.8, event.x, event.y)
        else:               self.show_zoom_image(1.25, event.x, event.y)

    def is_mouse_overlap_image(self, x, y):

        # - No longer needed due to improvements, but will be commented out for posterity. -
        #
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

    def overlapped_frontmost_widget(self, x, y):
        overlaped_ids = self.canvas.find_overlapping(x, y, x, y)
        for i in reversed(overlaped_ids):
            tag = self.canvas.itemcget(i, 'tags')
            if self.TAG_GRID not in tag: return i
        return 0

    # ------------------------------
    # key

    # - No longer needed due to improvements, but will be commented out for posterity. -
    #
    # def key_down(self, event=None):
    #     if event.keysym == 'Control_L' or event.keysym == 'Control_R':
    #         self.key_control_hold = True
    #
    # def key_release(self, event=None):
    #     if event.keysym == 'Control_L' or event.keysym == 'Control_R':
    #         self.key_control_hold = False

    # ------------------------------
    # canvas

    def canvas_resize(self, event=None):
        if self.canvas_conf is None:
            self.canvas_conf = event

        dx = (event.width - self.canvas_conf.width) // 2
        dy = (event.height - self.canvas_conf.height) // 2
        self.canvas.move(self.image_id, dx, dy)

        self.canvas_conf = event

        self.draw_grid(self.show_grid.get())

    # ------------------------------
    # image

    def draw_grid(self, draw):
        self.canvas.delete(self.TAG_GRID)
        if not draw: return     # hide only

        # draw grid
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        for i in range(0, w, self.GRID_INTERVAL):
            # v-line
            self.canvas.create_line(i, 0, i, h, fill='red', tags=self.TAG_GRID)
        for i in range(0, h, self.GRID_INTERVAL):
            # h-line
            self.canvas.create_line(0, i, w, i, fill='red', tags=self.TAG_GRID)

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

    def set_image(self):
        self.image_tk = self.image_pillow_to_tk(self.image_pillow)
        if self.image_id > 0:
            self.canvas.delete(self.image_id)
        self.image_id = self.canvas.create_image(
                                                    0,
                                                    0,
                                                    image=self.image_tk,
                                                    anchor='nw',
                                                    tags=self.TAG_IMAGE
                                                )

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
            # affine = np.array([
            #                     [self.image_scale, 0, 0],
            #                     [0, self.image_scale, 0],
            #                     [0, 0, 1]
            #                 ])
            # affine_inv = np.linalg.inv(affine)
            # affine_tuple = tuple(affine_inv.flatten())
            # image = self.image_pillow.transform(
            #                                         (zoom_width, zoom_height),
            #                                         Image.Transform.AFFINE,
            #                                         affine_tuple
            #                                     )

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

        # redraw grid for zoom
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
