"""
Reference:
    This implementation is inspired by techniques described in the following article:
    "https://blog.csdn.net/weixin_42152811/article/details/115899467"
"""
import os
from pyecharts import options as opts
from pyecharts.charts import Gauge
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot
import warnings

# 忽略字形缺失的警告
warnings.filterwarnings("ignore", category=UserWarning, message=".*Glyph.*missing from font.*")

def create_gauge_chart(name: str, maturity: float, formatted_date: str) -> str:
    """
    建立一個基本的儀表圖並將其儲存為 PNG 檔案

    :param name: 主題名稱或編號
    :param maturity: 成熟度數值（介於 0 到 100）
    :param formatted_date: 格式化的日期字串，用於檔名生成
    :return: 產生的 PNG 圖片檔案路徑
    """
    # 建立儀表圖
    gauge = (
        Gauge()
        .add(
            series_name='',  # 系列名稱（此處不顯示名稱）
            data_pair=[('Maturity', maturity)],  # 圖表數據：標籤 'Maturity' 與其對應數值
            min_=0,         # 儀表圖最小值
            max_=100,       # 儀表圖最大值
            split_number=10,  # 儀表圖刻度分段數量
            radius="75%",   # 儀表圖半徑（相對於容器大小）
            start_angle=225,  # 儀表圖起始角度（以度為單位）
            end_angle=-45,    # 儀表圖結束角度（以度為單位）
            is_clock_wise=True,  # 刻度增長方向是否為順時針
            detail_label_opts=opts.GaugeDetailOpts(
                formatter="{value}%",  # 自定義細節標籤格式（顯示百分比）
                font_size=30
            ),
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(
                    color=[  # 定義軸線的顏色漸變區間
                        (0.3, '#cb1090'),  # 0% ~ 30% 使用 '#cb1090'
                        (0.7, '#eab107'),  # 30% ~ 70% 使用 '#eab107'
                        (1, '#0b6dd7')     # 70% ~ 100% 使用 '#0b6dd7'
                    ],
                    width=-20  # 軸線寬度（負值表示內縮效果）
                )
            ),
            pointer=opts.GaugePointerOpts(
                width=10  # 指針寬度
            ),
            title_label_opts=opts.LabelOpts(
                font_size=30  # 增加 "Maturity" 的字體大小
            ),
            axislabel_opts=opts.LabelOpts(
                font_size=20  # 增加刻度標籤的字體大小
            )
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(is_show=True)  # 顯示圖例
        )
    )

    # 定義中間暫存的 HTML 檔案與最終輸出的 PNG 路徑
    html_file = "./images/gauge_chart.html"
    output_png = f"./images/{formatted_date}_gauge_{name}.png"

    # 將儀表圖渲染至 HTML 檔案，接著轉成 PNG
    gauge.render(html_file)
    make_snapshot(snapshot, html_file, output_png)

    # 清理暫存的 HTML 檔案
    if os.path.exists(html_file):
        os.remove(html_file)
    
    print(f"\n  ❏ Topic {name} 儀表圖已儲存: {output_png}")
    return output_png