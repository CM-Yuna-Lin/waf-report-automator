"""
Reference:
    This implementation is inspired by techniques described in the following article:
    "https://www.yisu.com/jc/693336.html"
"""
from PIL import Image
import numpy as np
from settings import *

def remove_image_whitespace(file_path: str) -> None:
    """
    移除圖片中多餘的空白邊界，並以裁剪後的圖像覆蓋原始檔案。

    此函式基於圖片的 alpha 通道資訊來判斷非透明區域，計算出圖片的
    最小裁剪範圍，並在該範圍外各留出 5 像素的邊距後進行裁切。

    :param file_path: 圖片檔案的路徑
    """

    image = Image.open(file_path)
    image_array = np.array(image)
    row = image_array.shape[0]
    col = image_array.shape[1]
    # print(row,col)
    # 先计算所有图片的裁剪范围，然后再统一裁剪并输出图片
    x_left = row
    x_top = col
    x_right = 0
    x_bottom = 0
    # 上下左右范围
    """
    Image.crop(left, up, right, below)
    left：与左边界的距离
    up：与上边界的距离
    right：还是与左边界的距离
    below：还是与上边界的距离
    简而言之就是，左上右下。
    """
    for r in range(row):
        for c in range(col):
            if image_array[r][c][3] > 0: #外框有个黑色边框，增加条件判断
                if x_top > r:
                    x_top = r  # 获取最小x_top
                if x_bottom < r:
                    x_bottom = r  # 获取最大x_bottom
                if x_left > c:
                    x_left = c  # 获取最小x_left
                if x_right < c:
                    x_right = c  # 获取最大x_right
    cropped = image.crop((x_left - 5, x_top - 5, x_right + 5, x_bottom + 5))  # (left, upper, right, lower)

    # 保存图片
    cropped.save(file_path)
    # print("\n    ▪ 圖片多餘空白裁剪成功")