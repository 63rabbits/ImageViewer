# ImageViewer
Image viewer made with python.


| Features                    |                                              |
| :-------------------------- | :------------------------------------------- |
| handling image              | .bmp .png .jpg .tif                          |
| open image                  | dialog box / drag and drop                   |
| drag image                  | mouse left button + drag                     |
| zoom-up/out image           | mouse right button + wheel / control + wheel |
| fit the image to the window | double click with mouse left button          |
| show grid                   |                                              |

---

## Problem
- Poor zoom performance.
  - When using Pillow's `Image.resize(...)`, performance deteriorates as the image zoom rate increases. This is because the entire image is enlarged and the displayed portion is cropped. The processing time for the parts that are not displayed is wasted.  
To improve the performance, the image size should be the same as that of the Canvas and ***affine transformation*** should be performed using `Image.transform(...)`. My guess is that only the part of the image to be displayed is processed, so the processing time is reduced. However, it is necessary to modify the program to include ***dragging (translation)***.  
Since this is a major revision, we will release the revised version as a separate version. When the work is completed, we will post the link here.  
For those in a hurry, please refer [here](https://gist.github.com/ImagingSolution/bf7d9b348a2cc31c300ebb080171150b#file-imageviewer-py).

- Grid does not support window resizing.
