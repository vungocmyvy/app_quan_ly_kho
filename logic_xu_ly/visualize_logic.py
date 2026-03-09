import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def draw_stock_alerts_chart(parent_frame):
    # 1. Kết nối và lấy dữ liệu từ database
    conn = sqlite3.connect('logic_xu_ly/inventory.db')
    cursor = conn.cursor()

    # Lấy 5 sản phẩm có lượng tồn kho thấp nhất hoặc cần chú ý
    query = "SELECT name, stock, min_threshold FROM products LIMIT 5"
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    if not data:
        print("Chưa có dữ liệu sản phẩm để vẽ biểu đồ.")
        return

    # 2. Chuẩn bị dữ liệu cho biểu đồ
    names = [row[0] for row in data]
    current_stock = [row[1] for row in data]
    min_thresholds = [row[2] for row in data]

    x = range(len(names))  # Vị trí các cột trên trục X
    width = 0.35  # Độ rộng của cột

    # 3. Tạo biểu đồ
    fig, ax = plt.subplots(figsize=(6, 4))

    # Vẽ cột Tồn kho hiện tại (Màu xanh dương)
    rects1 = ax.bar([i - width / 2 for i in x], current_stock, width, label='Current Stock', color='#3B82F6')

    # Vẽ cột Ngưỡng tối thiểu (Màu cam)
    rects2 = ax.bar([i + width / 2 for i in x], min_thresholds, width, label='Min Threshold', color='#F59E0B')

    # 4. Trang trí biểu đồ (Tiếng Việt)
    ax.set_ylabel('Số lượng')
    ax.set_title('Cảnh báo mức tồn kho')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.legend()


    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    # 5. Nhúng biểu đồ vào giao diện Tkinter
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill='both', expand=True)
    canvas.draw()