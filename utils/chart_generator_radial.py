import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import warnings
from PIL import Image
from utils.remove_image_whitespace import remove_image_whitespace

# 忽略字形缺失的警告
warnings.filterwarnings("ignore", category=UserWarning, message=".*Glyph.*missing from font.*")

def create_radial_chart(name: str, values: list, categories: list, formatted_date: str) -> str:
    """
    生成徑向條形圖，並將主圖與圖例合併成一張圖片儲存下來。

    :param name: 主題名稱或編號，用於檔名標識
    :param values: 每個類別的數值列表（百分比數據，範圍 0~100）
    :param categories: 類別名稱列表，長度需與 values 相同
    :param formatted_date: 用於檔名的格式化日期字串
    :return: 合併後徑向圖的檔案路徑
    """
    # 驗證輸入參數：類別數量必須與數值數量相同
    assert len(categories) == len(values), "The number of categories must match the number of values."

    # 為每個類別加上索引，便於識別
    categories = [f"[{i}] {category}" for i, category in enumerate(categories)]

    # 根據類別數量設定圖表尺寸與建立極座標子圖
    fig, ax = plt.subplots(subplot_kw={'polar': True}, figsize=(10, 10))

    # 定義自訂顏色漸層
    custom_colors = ['#CB1090', '#EAB107', '#F2800B', '#0B6DD7']
    cmap = mcolors.LinearSegmentedColormap.from_list("custom_gradient", custom_colors)
    colors = cmap(np.linspace(0, 1, len(categories)))

    # 繪製每個類別的橫向極座標條形圖
    bars = []
    for i, (category, value, color) in enumerate(zip(categories, values, colors)):
        # 將百分比數值轉換成弧度（滿分 100 對應 np.pi）
        bar_height = value / 100 * np.pi
        bar = ax.barh(i, bar_height, color=color, alpha=0.8, label=category)
        bars.append(bar)

    # 設定 y 軸：顯示所有類別對應的刻度
    ax.set_yticks(range(len(values)))

    # 設定極座標圖屬性：
    ax.set_theta_zero_location('W')  # 起始角度設為西側
    ax.set_theta_direction(-1)       # 順時針方向

    # 設定 x 軸（徑向方向）範圍及刻度標籤，標示百分比
    ax.set_xlim(0, np.pi)
    ax.set_xticks([np.pi * i / 10 for i in range(11)])
    ax.set_xticklabels([f'{i}%' for i in range(0, 101, 10)], fontsize=20)

    # 儲存主圖：徑向條形圖
    main_chart_name = f"./images/{formatted_date}_radial_{name}_chart.png"
    plt.savefig(main_chart_name, dpi=300, bbox_inches='tight', transparent=True)
    plt.close(fig)
    remove_image_whitespace(main_chart_name)

    # 建立單獨的圖例圖形
    legend_fig, legend_ax = plt.subplots(figsize=(10, 10))
    # 提取每個條形圖的第一個 patch 作為圖例項目
    legend_handles = [bar[0] for bar in bars]
    legend_ax.legend(handles=legend_handles, labels=categories, loc='center', frameon=False, ncol=2, fontsize=20)
    legend_ax.axis('off')

    # 儲存圖例圖
    legend_chart_name = f"./images/{formatted_date}_radial_{name}_legend.png"
    legend_fig.savefig(legend_chart_name, dpi=300, bbox_inches='tight', transparent=True)
    plt.close(legend_fig)
    remove_image_whitespace(legend_chart_name)

    # 讀取主圖與圖例圖，並合併為一張圖片
    main_img = Image.open(main_chart_name)
    legend_img = Image.open(legend_chart_name)
    total_width = max(main_img.width, legend_img.width)
    total_height = main_img.height + legend_img.height + 20  # 20 像素間距
    combined_img = Image.new('RGBA', (total_width, total_height), (255, 255, 255, 0))
    
    # 將主圖置中貼上，然後將圖例貼在下方
    combined_img.paste(main_img, ((total_width - main_img.width) // 2, 0))
    combined_img.paste(legend_img, ((total_width - legend_img.width) // 2, main_img.height + 20))
    
    # 儲存合併後的圖片
    combined_chart_name = f"./images/{formatted_date}_radial_{name}.png"
    combined_img.save(combined_chart_name)
    print(f"\n  ❏ Topic {name} 徑向條形圖已儲存: {combined_chart_name}")
    
    return combined_chart_name
