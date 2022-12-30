import image_viewer as iv
from tkinterdnd2 import *

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = iv.ImageViewer(master=root)
    app.mainloop()
