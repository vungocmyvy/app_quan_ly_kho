

import sys
import sqlite3
from datetime import datetime

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidgetItem,
    QMessageBox, QComboBox, QDialog,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCompleter, QMenu, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, QDate, QPoint
from PyQt6.QtGui import QAction, QColor, QCursor
from PyQt6.QtWidgets import QScrollArea, QVBoxLayout, QSizePolicy

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.ticker as mticker
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from Giaodien    import Ui_Content
from ThemKH      import Ui_Dialog as ThemKH_Ui
from ThemNCC     import Ui_Dialog as ThemNCC_Ui
from ThemSP      import Ui_Dialog as ThemSP_Ui
from Taohoadon   import Ui_Dialog as TaoHD_Ui
from Dondathang  import Ui_Dialog as DonDH_Ui

from logic_xu_ly import (
    dashboard_db, product_db, supplier_db,
    Invoices_db, check_login_db, customer_db,
    purchase_orders_db,
)


# =============================================================================
#  2. BIỂU ĐỒ ĐƯỜNG
# =============================================================================
class LineChartCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(4, 2.6), dpi=90)
        self.fig.patch.set_facecolor("#1B3A4B")
        self.ax    = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self._months = []; self._sales = []; self._purch = []
        self._annot  = None
        self.mpl_connect("motion_notify_event", self._on_hover)

    def plot(self, months, sales, purchases):
        self._months, self._sales, self._purch = months, sales, purchases
        ax = self.ax
        ax.clear()
        ax.set_facecolor("#1B3A4B")
        x = range(len(months))
        ax.plot(x, sales,     color="#8B5CF6", lw=3, marker="o",
                markersize=6, label="Doanh thu")
        ax.plot(x, purchases, color="#22D3EE", lw=3, marker="o",
                markersize=6, label="Nhập kho")
        ax.fill_between(x, sales,     alpha=0.15, color="#7C3AED")
        ax.fill_between(x, purchases, alpha=0.15, color="#06B6D4")
        ax.set_xticks(list(x))
        ax.set_xticklabels(months, color="#AED6F1", fontsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda v, _: f"{v/1_000_000:.1f}M" if v >= 1_000_000
            else f"{v/1000:.0f}k" if v >= 1000 else str(int(v))))
        ax.tick_params(colors="#AED6F1", labelsize=8)
        for sp in ax.spines.values():
            sp.set_edgecolor("#2E5C6E")
        ax.grid(axis="y", linestyle="--", alpha=0.3, color="#2E5C6E")
        ax.legend(facecolor="#0F1E25", edgecolor="#2E5C6E",
                  labelcolor="white", fontsize=8, loc="upper left")
        self._annot = ax.annotate(
            "", xy=(0, 0), xytext=(10, 10), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.4", fc="#0F1E25",
                      ec="#3B82F6", lw=1.2),
            color="white", fontsize=8, visible=False)
        self.fig.tight_layout(pad=0.8)
        self.draw()

    def _on_hover(self, event):
        if not self._annot or event.inaxes != self.ax or not self._months:
            if self._annot:
                self._annot.set_visible(False)
                self.draw_idle()
            return
        xi = round(event.xdata) if event.xdata is not None else -1
        if 0 <= xi < len(self._months):
            self._annot.set_text(
                f"{self._months[xi]}\n"
                f"📈 {self._sales[xi]:,.0f} ₫\n"
                f"📦 {self._purch[xi]:,.0f} ₫")
            self._annot.xy = (xi, max(self._sales[xi], self._purch[xi]))
            self._annot.set_visible(True)
        else:
            self._annot.set_visible(False)
        self.draw_idle()


# =============================================================================
#  3. BIỂU ĐỒ TRÒN
# =============================================================================
class PieChartCanvas(FigureCanvas):
    COLORS = ["#7C3AED","#06B6D4","#F59E0B","#10B981","#EF4444",
              "#8B5CF6","#3B82F6","#EC4899","#14B8A6","#F97316"]

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(4, 2.6), dpi=90)
        self.fig.patch.set_facecolor("#1B3A4B")
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self._wedges = []; self._labels = []; self._values = []
        self._hover_idx = None
        self.mpl_connect("motion_notify_event", self._on_hover)
        self.mpl_connect("button_press_event",  self._on_click)

    def plot(self, data):
        self.ax.clear(); self.ax.set_facecolor("#1B3A4B")
        if not data:
            self.ax.text(0.5, 0.5, "Chưa có dữ liệu",
                         ha="center", va="center", color="#AED6F1",
                         transform=self.ax.transAxes, fontsize=10)
            self.draw(); return
        self._labels = [d[0] for d in data]
        self._values = [d[1] for d in data]
        total = sum(self._values)
        wedges, _, autotexts = self.ax.pie(
            self._values, colors=self.COLORS[:len(data)], labels=None,
            autopct=lambda p: f"{p:.0f}%" if p > 5 else "",
            startangle=140,
            wedgeprops=dict(linewidth=1.5, edgecolor="#1B3A4B"),
            pctdistance=0.78)
        for t in autotexts:
            t.set_color("white"); t.set_fontsize(8); t.set_fontweight("bold")
        self.ax.legend(wedges,
            [f"{l}  {v/total*100:.0f}%" for l, v in zip(self._labels, self._values)],
            loc="center left", bbox_to_anchor=(1.0, 0.5),
            facecolor="#0F1E25", edgecolor="#2E5C6E",
            labelcolor="white", fontsize=7.5)
        self._wedges = wedges
        self.fig.tight_layout(pad=0.5); self.draw()

    def _get_idx(self, event):
        if event.inaxes != self.ax: return -1
        for i, w in enumerate(self._wedges):
            if w.contains(event)[0]: return i
        return -1

    def _on_hover(self, event):
        idx = self._get_idx(event)
        if idx == self._hover_idx: return
        self._hover_idx = idx
        for i, w in enumerate(self._wedges):
            if i == idx: w.set_linewidth(3); w.set_edgecolor("#FFD700")
            else:        w.set_linewidth(1.5); w.set_edgecolor("#1B3A4B")
        if idx >= 0 and self._values:
            total = sum(self._values)
            self.ax.set_title(
                f"{self._labels[idx]}: {self._values[idx]}"
                f"  ({self._values[idx]/total*100:.1f}%)",
                color="#FFD700", fontsize=9, pad=6)
        else:
            self.ax.set_title("Danh mục sản phẩm",
                              color="white", fontsize=9, pad=6)
        self.draw_idle()

    def _on_click(self, event):
        idx = self._get_idx(event)
        if idx < 0 or not self._wedges: return
        explode = [0.12 if i == idx else 0 for i in range(len(self._wedges))]
        self.ax.clear(); self.ax.set_facecolor("#1B3A4B")
        total = sum(self._values)
        wedges, _, autotexts = self.ax.pie(
            self._values, colors=self.COLORS[:len(self._values)], labels=None,
            autopct=lambda p: f"{p:.0f}%" if p > 5 else "",
            startangle=140, explode=explode,
            wedgeprops=dict(linewidth=1.5, edgecolor="#1B3A4B"),
            pctdistance=0.78)
        for t in autotexts:
            t.set_color("white"); t.set_fontsize(8); t.set_fontweight("bold")
        self.ax.legend(wedges,
            [f"{l}  {v/total*100:.0f}%" for l, v in zip(self._labels, self._values)],
            loc="center left", bbox_to_anchor=(1.0, 0.5),
            facecolor="#0F1E25", edgecolor="#2E5C6E",
            labelcolor="white", fontsize=7.5)
        self.ax.set_title(f"▶ {self._labels[idx]}: {self._values[idx]}",
                          color="#FFD700", fontsize=9, pad=6, fontweight="bold")
        self._wedges = wedges
        self.fig.tight_layout(pad=0.5); self.draw()


# =============================================================================
#  STYLE CHUNG CHO CÁC DIALOG
# =============================================================================
_DIALOG_INPUT = """
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
        background-color: #A6C8D8;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 4px 8px;
        color: #1e293b;
        font-size: 13px;
    }
    QLineEdit:focus, QComboBox:focus,
    QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
        border: 1px solid #3b82f6;
    }
    QComboBox::drop-down { border: none; }
    QComboBox::down-arrow { image: none; }
    QDateEdit::drop-down  { border: none; }
    QDateEdit::down-arrow { image: none; }
    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { border: none; }
"""

_MENU_STYLE = """
    QMenu {
        background: #1B3A4B; color: white;
        border: 1px solid #2E5C6E; border-radius: 8px; padding: 4px;
        font-size: 13px;
    }
    QMenu::item { padding: 8px 20px 8px 12px; border-radius: 4px; }
    QMenu::item:selected { background: #3B82F6; }
    QMenu::separator { height: 1px; background: #2E5C6E; margin: 4px 8px; }
"""


# =============================================================================
#  4. DIALOG THÊM KHÁCH HÀNG
# =============================================================================
class ThemKHDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui =ThemKH_Ui()
        self.ui.setupUi(self)
        self.setWindowTitle("Thêm Khách Hàng")

        # Kiểm tra xem customer_db có tồn tại không để tránh crash
        try:
            next_id = customer_db.get_next_stt()
            self.ui.lne_stt.setText(str(next_id))
        except Exception as e:
            print(f"Lỗi database: {e}")
            self.ui.lne_stt.setText("1")
        self.ui.lne_stt.setReadOnly(True)

        self.ui.cb_tt.clear()
        self.ui.cb_tt.addItems(["Active", "Inactive", "VIP"])

        self.ui.pb_hb.clicked.connect(self.reject)
        self.ui.pb_thd.clicked.connect(self._submit)

    def _submit(self):
        if not self.ui.lne_tkh.text().strip():
            QMessageBox.warning(self, "Thiếu thông tin",
                                "Vui lòng nhập Tên khách hàng!")
            return
        self.accept()

    def get_data(self):
        return {
            "name":    self.ui.lne_tkh.text().strip(),
            "email":   self.ui.lne_email.text().strip(),
            "phone":   self.ui.lne_sdt.text().strip(),
            "orders":  self.ui.spb_tdh.value(),
            "balance": 0.0,
            "status":  self.ui.cb_tt.currentText(),
        }


# =============================================================================
#  5. DIALOG THÊM NHÀ CUNG CẤP
# =============================================================================
class ThemNCCDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = ThemNCC_Ui(); self.ui.setupUi(self)
        self.setWindowTitle("Thêm Nhà Cung Cấp")

        # FIX #1: ID thực sẽ được cấp tiếp theo
        self.ui.lne_stt.setText(str(supplier_db.get_next_stt()))
        self.ui.lne_stt.setReadOnly(True)

        self.ui.cb_tt.clear()
        self.ui.cb_tt.addItems(["Đã xác minh", "Chưa giải quyết"])

        self.ui.pb_hb.clicked.connect(self.reject)
        self.ui.pb_thd.clicked.connect(self._submit)

    def _submit(self):
        if not self.ui.lne_tncc.text().strip():
            QMessageBox.warning(self, "Thiếu thông tin",
                                "Vui lòng nhập Tên nhà cung cấp!")
            return
        self.accept()

    def get_data(self):
     return {
        "name": self.ui.lne_tncc.text().strip(),
        "email": self.ui.lne_email.text().strip(),
        "phone": self.ui.lne_sdt.text().strip(),
        "total_orders": self.ui.spb_tdh.value(), 
        "status": self.ui.cb_tt.currentText()
     }
# =============================================================================
#  6. DIALOG THÊM SẢN PHẨM
# =============================================================================
class ThemSPDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = ThemSP_Ui(); self.ui.setupUi(self)
        self.setWindowTitle("Thêm Sản Phẩm")

        # Danh mục từ DB + mặc định
        dm = set(r[2] for r in product_db.fetch_all_products() if r[2])
        for c in ["Electronics","Clothing","Food","Furniture","Office","Khác"]:
            dm.add(c)
        self.ui.cb_pl.clear()
        self.ui.cb_pl.addItems(sorted(dm))

        # Trạng thái
        self.ui.cb_tt.clear()
        self.ui.cb_tt.addItems(["Còn hàng", "Sắp hết", "Hết hàng"])

        # FIX #2: set range hợp lý, không restrict
        self.ui.spb_sl.setMinimum(0)
        self.ui.spb_sl.setMaximum(999_999)
        # Tự động trạng thái theo số lượng
        self.ui.spb_sl.valueChanged.connect(self._auto_trang_thai)
        self._auto_trang_thai(0)

        # FIX #5: ô Giá bán – dùng QDoubleSpinBox thay QLineEdit
        geo = self.ui.lne_gb.geometry()
        par = self.ui.lne_gb.parent()
        self.ui.lne_gb.setVisible(False)
        self._dsb_gia = QDoubleSpinBox(par)
        self._dsb_gia.setGeometry(geo)
        self._dsb_gia.setMinimum(0.0)
        self._dsb_gia.setMaximum(999_999_999_999.0)
        self._dsb_gia.setDecimals(0)
        self._dsb_gia.setSingleStep(10_000)
        self._dsb_gia.setGroupSeparatorShown(True)
        self._dsb_gia.setStyleSheet(_DIALOG_INPUT)
        self._dsb_gia.show()

        self.ui.pb_hb.clicked.connect(self.reject)
        self.ui.pb_tsp.clicked.connect(self._submit)

    def _auto_trang_thai(self, sl):
        if sl == 0:    self.ui.cb_tt.setCurrentText("Hết hàng")
        elif sl < 10:  self.ui.cb_tt.setCurrentText("Sắp hết")
        else:          self.ui.cb_tt.setCurrentText("Còn hàng")

    def _submit(self):
        if not self.ui.lne_msp.text().strip() or not self.ui.lne_tsp.text().strip():
            QMessageBox.warning(self, "Thiếu thông tin",
                                "Vui lòng nhập Mã và Tên sản phẩm!")
            return
        self.accept()

    def get_data(self):
        gia = self._dsb_gia.value()
        return {
            "sku":      self.ui.lne_msp.text().strip(),
            "name":     self.ui.lne_tsp.text().strip(),
            "category": self.ui.cb_pl.currentText(),
            "stock":    self.ui.spb_sl.value(),
            "price":    gia,
            "cost":     round(gia * 0.7, 0),
            "status":   self.ui.cb_tt.currentText(),
        }


# =============================================================================
#  7. DIALOG TẠO / SỬA HÓA ĐƠN
# =============================================================================
class TaoHoaDonDialog(QDialog):
    """
    Dialog Tạo / Sửa Hóa Đơn – dùng Taohoadon.py làm khung,
    thêm chọn sản phẩm và tự động tính tổng tiền.

    edit_data = tuple 7 phần tử:
        (row_id, inv_no, customer, date, due_date, amount, status)
    """

    def __init__(self, parent=None, edit_data=None):
        super().__init__(parent)
        self.ui = TaoHD_Ui(); self.ui.setupUi(self)
        self.setWindowTitle("Tạo Hóa Đơn" if edit_data is None else "Sửa Hóa Đơn")

        # Mở rộng dialog để có chỗ cho dòng sản phẩm
        self.resize(522, 580)
        self._row_id = None  # id thực trong DB (dùng cho update/delete)

        # ── Lấy dữ liệu từ DB ──────────────────────────────────────────────
        self._khach_hang = Invoices_db.fetch_customer_names()  # [(id,name,phone,email)]
        self._san_pham   = Invoices_db.fetch_available_products()  # [(sku,name,price,stock)]

        par = self.ui.lne_tkh.parent()  # Dialog chính là parent

        # ── 1. Trạng thái ──────────────────────────────────────────────────
        self.ui.cb_tt.clear()
        self.ui.cb_tt.addItems(["pending","paid","overdue","draft"])
        # Di chuyển cb_tt xuống dưới để nhường chỗ
        self.ui.cb_tt.setGeometry(160, 480, 311, 31)
        # Di chuyển label tương ứng
        self.ui.lb_tt.setGeometry(30, 480, 121, 31)
        # Di chuyển các nút xuống
        self.ui.pb_hb.setGeometry(164, 530, 81, 31)
        self.ui.pb_thd.setGeometry(270, 530, 141, 31)

        # ── 2. Ngày tháng – bật calendar picker ────────────────────────────
        self.ui.de_ndathang.setDate(QDate.currentDate())
        self.ui.de_ndathang.setCalendarPopup(True)
        self.ui.de_ndathang.setDisplayFormat("dd/MM/yyyy")

        self.ui.de_ndenhan.setDate(QDate.currentDate())
        self.ui.de_ndenhan.setCalendarPopup(True)
        self.ui.de_ndenhan.setDisplayFormat("dd/MM/yyyy")
        self.ui.de_ndenhan.setMinimumDate(QDate.currentDate())
        self.ui.de_ndathang.dateChanged.connect(self._on_start_date_changed)

        # ── 3. Khách hàng: thay lne_tkh bằng ComboBox ─────────────────────
        self.ui.lne_tkh.setVisible(False)

        self._cb_kh = QComboBox(par)
        self._cb_kh.setGeometry(160, 110, 311, 31)
        self._cb_kh.setEditable(True)
        self._cb_kh.lineEdit().setPlaceholderText("Chọn hoặc nhập tên KH...")
        self._cb_kh.setStyleSheet(_DIALOG_INPUT)
        self._cb_kh.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        for r in self._khach_hang:           # r = (id, name, phone, email)
            self._cb_kh.addItem(r[1], userData=r)

        completer = QCompleter(
            [self._cb_kh.itemText(i) for i in range(self._cb_kh.count())], self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._cb_kh.setCompleter(completer)
        self._cb_kh.setCurrentIndex(-1)
        self._cb_kh.show()

        # Label hiển thị info KH (phone / email)
        self._lbl_kh_info = QLabel("", par)
        self._lbl_kh_info.setGeometry(160, 143, 311, 18)
        self._lbl_kh_info.setStyleSheet(
            "color: #AED6F1; font-size: 11px; padding-left: 4px;")
        self._lbl_kh_info.show()
        self._cb_kh.currentIndexChanged.connect(self._on_kh_changed)

        # Dịch chuyển ngày xuống 20px vì thêm info label
        self.ui.lb_ndathang.setGeometry(30, 173, 211, 31)
        self.ui.de_ndathang.setGeometry(160, 173, 311, 31)
        self.ui.lb_ndenhan.setGeometry(30, 220, 121, 31)
        self.ui.de_ndenhan.setGeometry(160, 220, 311, 31)

        # ── 4. Sản phẩm: ComboBox mới (y=265) ─────────────────────────────
        from PyQt6.QtWidgets import QSpinBox

        lbl_sp = QLabel("Sản phẩm:", par)
        lbl_sp.setGeometry(30, 265, 121, 31)
        lbl_sp.setStyleSheet("color: white; font-size: 10pt; font-weight: 600;")
        lbl_sp.show()

        self._cb_sp = QComboBox(par)
        self._cb_sp.setGeometry(160, 265, 311, 31)
        self._cb_sp.setStyleSheet(_DIALOG_INPUT)
        self._cb_sp.addItem("-- Không chọn SP (nhập tay) --", userData=None)
        for r in self._san_pham:            # r = (sku, name, price, stock)
            label = f"{r[1]}  [{r[0]}]  –  {r[2]:,.0f} ₫  (tồn: {r[3]})"
            self._cb_sp.addItem(label, userData=r)
        self._cb_sp.show()

        # Số lượng
        lbl_sl = QLabel("Số lượng:", par)
        lbl_sl.setGeometry(30, 308, 121, 31)
        lbl_sl.setStyleSheet("color: white; font-size: 10pt; font-weight: 600;")
        lbl_sl.show()

        self._spb_sl = QSpinBox(par)
        self._spb_sl.setGeometry(160, 308, 100, 31)
        self._spb_sl.setMinimum(1); self._spb_sl.setMaximum(999_999)
        self._spb_sl.setValue(1)
        self._spb_sl.setStyleSheet(_DIALOG_INPUT)
        self._spb_sl.show()

        # Label đơn giá (readonly, hiển thị bên cạnh số lượng)
        self._lbl_don_gia = QLabel("Đơn giá: –", par)
        self._lbl_don_gia.setGeometry(275, 308, 196, 31)
        self._lbl_don_gia.setStyleSheet(
            "color: #AED6F1; font-size: 11px; background: #1B3A4B;"
            "border-radius:8px; padding: 4px 8px;")
        self._lbl_don_gia.show()

        # ── 5. Tổng tiền: dịch lne_st xuống y=355 ─────────────────────────
        self.ui.lne_st.setVisible(False)
        self.ui.lb_st.setGeometry(30, 355, 121, 31)

        self._dsb_amount = QDoubleSpinBox(par)
        self._dsb_amount.setGeometry(160, 355, 311, 31)
        self._dsb_amount.setMinimum(0.0)
        self._dsb_amount.setMaximum(999_999_999_999.0)
        self._dsb_amount.setDecimals(0)
        self._dsb_amount.setSingleStep(100_000)
        self._dsb_amount.setGroupSeparatorShown(True)
        self._dsb_amount.setStyleSheet(_DIALOG_INPUT)
        self._dsb_amount.show()

        # Kết nối tự tính tiền
        self._cb_sp.currentIndexChanged.connect(self._tinh_tien)
        self._spb_sl.valueChanged.connect(self._tinh_tien)

        # ── Nút OK / Hủy ──────────────────────────────────────────────────
        self.ui.pb_hb.clicked.connect(self.reject)
        self.ui.pb_thd.clicked.connect(self._submit)

        # ── Chế độ SỬA ────────────────────────────────────────────────────
        if edit_data:
            # edit_data = (row_id, inv_no, customer, date, due_date, amount, status)
            self._row_id = edit_data[0]
            self.ui.lne_shd.setText(str(edit_data[1]))
            self.ui.lne_shd.setReadOnly(True)

            kh_name = str(edit_data[2])
            idx = self._cb_kh.findText(kh_name, Qt.MatchFlag.MatchFixedString)
            self._cb_kh.setCurrentIndex(idx) if idx >= 0 \
                else self._cb_kh.setCurrentText(kh_name)

            d1 = QDate.fromString(str(edit_data[3]), "yyyy-MM-dd")
            if d1.isValid(): self.ui.de_ndathang.setDate(d1)
            d2 = QDate.fromString(str(edit_data[4]), "yyyy-MM-dd")
            if d2.isValid(): self.ui.de_ndenhan.setDate(d2)

            try:
                amt = float(str(edit_data[5]).replace("₫","").replace(",","").strip())
                self._dsb_amount.setValue(amt)
            except Exception:
                pass

            self.ui.cb_tt.setCurrentText(str(edit_data[6]))

    # ── Xử lý sự kiện ──────────────────────────────────────────────────────
    def _on_start_date_changed(self, date):
        self.ui.de_ndenhan.setMinimumDate(date)
        if self.ui.de_ndenhan.date() < date:
            self.ui.de_ndenhan.setDate(date)

    def _on_kh_changed(self, idx):
        """Hiển thị phone/email khi chọn khách hàng."""
        data = self._cb_kh.itemData(idx)
        if data and isinstance(data, tuple):
            _, name, phone, email = data
            parts = [p for p in [phone, email] if p and str(p).strip()]
            self._lbl_kh_info.setText("  |  ".join(parts) if parts else "")
        else:
            self._lbl_kh_info.setText("")

    def _tinh_tien(self):
        """Tự tính tổng = đơn giá × số lượng khi chọn SP."""
        sp_data = self._cb_sp.currentData()
        if sp_data and isinstance(sp_data, tuple):
            sku, name, don_gia, ton_kho = sp_data
            qty   = self._spb_sl.value()
            tong  = don_gia * qty
            self._lbl_don_gia.setText(f"Đơn giá: {don_gia:,.0f} ₫")
            self._dsb_amount.setValue(tong)
        else:
            self._lbl_don_gia.setText("Đơn giá: –")
            # Không reset amount khi không chọn SP → user có thể nhập tay

    def _submit(self):
        if not self.ui.lne_shd.text().strip():
            QMessageBox.warning(self, "Thiếu thông tin",
                                "Vui lòng nhập Số hóa đơn!")
            return
        if not self._cb_kh.currentText().strip():
            QMessageBox.warning(self, "Thiếu thông tin",
                                "Vui lòng chọn Khách hàng!")
            return
        self.accept()

    def get_data(self):
        return {
            "row_id":   self._row_id,
            "inv_no":   self.ui.lne_shd.text().strip(),
            "customer": self._cb_kh.currentText().strip(),
            "date":     self.ui.de_ndathang.date().toString("yyyy-MM-dd"),
            "due_date": self.ui.de_ndenhan.date().toString("yyyy-MM-dd"),
            "amount":   self._dsb_amount.value(),
            "status":   self.ui.cb_tt.currentText(),
        }


# =============================================================================
#  8. DIALOG TẠO ĐƠN ĐẶT HÀNG
# =============================================================================
class DonDatHangDialog(QDialog):
    """
    Dialog Tạo Đơn Đặt Hàng – dùng đúng UI từ Dondathang.py.

    Widget map (Dondathang.py):
      cb_ncc      → Nhà cung cấp
      de_ndh      → Ngày đặt hàng     de_tgghdk → Ngày giao dự kiến
      cb_ncc_2    → ComboBox sản phẩm (tên nhầm trong Designer)
      label       → hiển thị số lượng  (replace → QSpinBox)
      label_2     → hiển thị đơn giá   (readonly label, auto từ SP)
      cb_ddgh     → Địa điểm giao (Kho 1/2/3)
      cb_ddgh_2   → Phương thức vận chuyển
      label_3     → trọng lượng (kg)   (replace → QDoubleSpinBox)
      label_4     → ưu tiên            (replace → QComboBox)
      label_5     → ghi chú            (replace → QLineEdit)
      fr_tddh / lb_ddgh_6/7/8/9 → hiển thị tiền hàng/phí VC/phụ phí/tổng
      pb_hb → Hủy    pb_td → Tạo đơn

    Logic chi phí vận chuyển:
      Tiền hàng   = đơn giá × số lượng
      Phí VC gốc  = (phí_kho + phí_kg × trọng_lượng) × hệ_số_ptvc
      Phụ phí UT  = phí VC gốc × tỷ_lệ_ưu_tiên
      Tổng cộng   = tiền hàng + phí VC gốc + phụ phí UT
    """

    # Phí cơ bản + giá/kg theo kho
    PHI_KHO = {
        "Kho 1": {"co_ban": 15_000, "kg": 3_500, "ten": "Kho Hà Nội"},
        "Kho 2": {"co_ban": 15_000, "kg": 3_500, "ten": "Kho TP.HCM"},
        "Kho 3": {"co_ban": 35_000, "kg": 5_000, "ten": "Kho Đà Nẵng"},
    }
    # Hệ số phương thức vận chuyển
    HE_SO_PT = {
        "Tiêu chuẩn (3-5 ngày)": 1.0,
        "Nhanh (1-2 ngày)":       1.8,
        "Hỏa tốc (trong ngày)":   3.0,
        "Tự giao (miễn phí)":     0.0,
    }
    # Phụ phí theo mức ưu tiên (% trên phí VC)
    PHU_PHI_UT = {
        "Bình thường": 0.00,
        "Cao":          0.15,
        "Khẩn cấp":     0.35,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = DonDH_Ui()
        self.ui.setupUi(self)
        self.setWindowTitle("Tạo Đơn Đặt Hàng")

        # Lưu cache tính toán
        self._tien_hang = 0.0
        self._phi_vc    = 0.0
        self._tong      = 0.0

        # ── 1. NCC từ DB ─────────────────────────────────────────────────
        self.ui.cb_ncc.clear()
        for r in supplier_db.fetch_all_suppliers():
            self.ui.cb_ncc.addItem(r[1], userData=r[0])
        if self.ui.cb_ncc.count() == 0:
            self.ui.cb_ncc.addItem("(Chưa có NCC)")

        # ── 2. Sản phẩm từ DB (cb_ncc_2 = ComboBox sản phẩm) ─────────────
        self.ui.cb_ncc_2.clear()
        for r in product_db.fetch_all_products():
            # r = (sku, name, category, stock, price, cost, status)
            # FIX #2: đơn giá nhập = cost (r[5]); nếu cost=0 thì dùng price*0.8
            cost_val = r[5] if (r[5] and r[5] > 0) else round(r[4] * 0.8, 0)
            label = (f"{r[1]}  [{r[0]}]  –  "
                     f"Giá nhập: {cost_val:,.0f} ₫  |  "
                     f"Giá bán: {r[4]:,.0f} ₫  (tồn: {r[3]})")
            # userData: (sku, name, cost_val, stock, gia_ban)
            self.ui.cb_ncc_2.addItem(label, userData=(r[0], r[1], cost_val, r[3], r[4]))
        if self.ui.cb_ncc_2.count() == 0:
            self.ui.cb_ncc_2.addItem("(Chưa có sản phẩm)")

        # ── 3. Ngày tháng ────────────────────────────────────────────────
        self.ui.de_ndh.setDate(QDate.currentDate())
        self.ui.de_ndh.setCalendarPopup(True)
        self.ui.de_ndh.setDisplayFormat("dd/MM/yyyy")

        self.ui.de_tgghdk.setDate(QDate.currentDate())
        self.ui.de_tgghdk.setCalendarPopup(True)
        self.ui.de_tgghdk.setDisplayFormat("dd/MM/yyyy")
        self.ui.de_tgghdk.setMinimumDate(QDate.currentDate())
        self.ui.de_ndh.dateChanged.connect(self._on_ngay_dat_changed)

        # ── 4. Thay label → widget nhập liệu (cùng geometry) ─────────────
        par = self.ui.label.parent()

        # label → QSpinBox số lượng
        geo_sl = self.ui.label.geometry()
        self.ui.label.setVisible(False)
        self._spb_sl = QtWidgets.QSpinBox(par)
        self._spb_sl.setGeometry(geo_sl)
        self._spb_sl.setMinimum(1)
        self._spb_sl.setMaximum(999_999)
        self._spb_sl.setValue(1)
        self._spb_sl.setStyleSheet(
            "background-color:#A6C8D8;border:1px solid #bfdbfe;"
            "border-radius:8px;padding:4px 8px;color:#1e293b;")
        self._spb_sl.show()

        # label_2 → QLabel readonly đơn giá (giữ nguyên là label, chỉ cập nhật text)
        self.ui.label_2.setText("0 ₫")

        # Kho giao – đã có cb_ddgh với 3 kho, thêm item đầy đủ
        self.ui.cb_ddgh.clear()
        for k in self.PHI_KHO:
            info = self.PHI_KHO[k]
            self.ui.cb_ddgh.addItem(f"{k} – {info['ten']}", userData=k)

        # Phương thức – cb_ddgh_2 đang có 1 item → thêm đủ
        self.ui.cb_ddgh_2.clear()
        self.ui.cb_ddgh_2.addItems(list(self.HE_SO_PT.keys()))

        # label_3 → QDoubleSpinBox trọng lượng
        geo_tl = self.ui.label_3.geometry()
        self.ui.label_3.setVisible(False)
        self._dsb_tl = QtWidgets.QDoubleSpinBox(par)
        self._dsb_tl.setGeometry(geo_tl)
        self._dsb_tl.setDecimals(1)
        self._dsb_tl.setMinimum(0.1)
        self._dsb_tl.setMaximum(99_999.0)
        self._dsb_tl.setSingleStep(0.5)
        self._dsb_tl.setValue(1.0)
        self._dsb_tl.setStyleSheet(
            "background-color:#A6C8D8;border:1px solid #bfdbfe;"
            "border-radius:8px;padding:4px 8px;color:#1e293b;")
        self._dsb_tl.show()

        # label_4 → QComboBox ưu tiên
        geo_ut = self.ui.label_4.geometry()
        self.ui.label_4.setVisible(False)
        self._cb_ut = QtWidgets.QComboBox(par)
        self._cb_ut.setGeometry(geo_ut)
        self._cb_ut.addItems(list(self.PHU_PHI_UT.keys()))
        self._cb_ut.setStyleSheet(
            "QComboBox{background-color:#A6C8D8;border:1px solid #bfdbfe;"
            "border-radius:8px;padding:4px 8px;color:#1e293b;}"
            "QComboBox::drop-down{border:none;}")
        self._cb_ut.show()

        # label_5 → QLineEdit ghi chú
        geo_gc = self.ui.label_5.geometry()
        self.ui.label_5.setVisible(False)
        self._lne_gc = QtWidgets.QLineEdit(par)
        self._lne_gc.setGeometry(geo_gc)
        self._lne_gc.setPlaceholderText("Ghi chú giao hàng (tùy chọn)...")
        self._lne_gc.setStyleSheet(
            "background-color:#A6C8D8;border:1px solid #bfdbfe;"
            "border-radius:8px;padding:4px 8px;color:#1e293b;")
        self._lne_gc.show()

        # ── 5. Kết nối signals → tính chi phí ────────────────────────────
        self.ui.cb_ncc_2.currentIndexChanged.connect(self._on_sp_changed)
        self._spb_sl.valueChanged.connect(self._tinh_chi_phi)
        self._dsb_tl.valueChanged.connect(self._tinh_chi_phi)
        self.ui.cb_ddgh.currentIndexChanged.connect(self._tinh_chi_phi)
        self.ui.cb_ddgh_2.currentIndexChanged.connect(self._tinh_chi_phi)
        self._cb_ut.currentIndexChanged.connect(self._tinh_chi_phi)
        self.ui.pb_add.clicked.connect(self._tinh_chi_phi)

        self._tinh_chi_phi()  # tính lần đầu

        # ── Nút ──────────────────────────────────────────────────────────
        self.ui.pb_hb.clicked.connect(self.reject)
        self.ui.pb_td.clicked.connect(self._submit)

    # ── Sự kiện ──────────────────────────────────────────────────────────
    def _on_ngay_dat_changed(self, date):
        self.ui.de_tgghdk.setMinimumDate(date)
        if self.ui.de_tgghdk.date() < date:
            self.ui.de_tgghdk.setDate(date)

    def _on_sp_changed(self):
        """Khi đổi SP → cập nhật đơn giá (giá nhập/cost) + ước tính trọng lượng."""
        data = self.ui.cb_ncc_2.currentData()
        if data and isinstance(data, tuple):
            # userData = (sku, name, cost_val, stock, gia_ban)
            sku      = data[0]
            ten      = data[1]
            don_gia  = data[2]   # giá nhập (cost)
            ton_kho  = data[3]
            gia_ban  = data[4] if len(data) > 4 else don_gia
            self.ui.label_2.setText(
                f"{don_gia:,.0f} ₫  (giá bán: {gia_ban:,.0f} ₫)")
            sl = self._spb_sl.value()
            self._dsb_tl.setValue(max(0.5, sl * 0.5))
        else:
            self.ui.label_2.setText("0 ₫")
        self._tinh_chi_phi()

    def _tinh_chi_phi(self):
        """
        Tính đầy đủ và cập nhật frame tóm tắt.

        Công thức:
          Tiền hàng   = đơn giá × số lượng
          Phí VC gốc  = (phi_kho + phi_kg × kg) × he_so_pt
          Phụ phí UT  = phí VC gốc × tỷ lệ UT
          Tổng cộng   = tiền hàng + phí VC gốc + phụ phí UT
        """
        sp_data     = self.ui.cb_ncc_2.currentData()
        don_gia     = sp_data[2] if (sp_data and isinstance(sp_data, tuple)) else 0.0
        qty         = self._spb_sl.value()
        trong_luong = self._dsb_tl.value()

        # Kho (userData = "Kho 1" / "Kho 2" / "Kho 3")
        kho_key = self.ui.cb_ddgh.currentData() or "Kho 1"
        kho_inf = self.PHI_KHO.get(kho_key, {"co_ban": 15_000, "kg": 3_500})

        pt_key  = self.ui.cb_ddgh_2.currentText()
        ut_key  = self._cb_ut.currentText()

        # Tính
        tien_hang  = don_gia * qty
        phi_vc_goc = (kho_inf["co_ban"] + kho_inf["kg"] * trong_luong) \
                     * self.HE_SO_PT.get(pt_key, 1.0)
        ty_le_ut   = self.PHU_PHI_UT.get(ut_key, 0.0)
        phu_phi_ut = phi_vc_goc * ty_le_ut
        phi_vc     = phi_vc_goc + phu_phi_ut
        tong_cong  = tien_hang + phi_vc

        # Cập nhật frame tóm tắt (lb_ddgh_6/7/8/9)
        self.ui.lb_ddgh_6.setText(f"{tien_hang:,.0f} ₫")
        self.ui.lb_ddgh_7.setText(f"{phi_vc:,.0f} ₫")

        if phu_phi_ut > 0:
            self.ui.lb_ddgh_8.setText(
                f"{phu_phi_ut:,.0f} ₫  (+{ty_le_ut*100:.0f}%)")
        else:
            self.ui.lb_ddgh_8.setText("0 ₫")

        self.ui.lb_ddgh_9.setText(f"{tong_cong:,.0f} ₫")

        # Màu lb_ddgh_7 theo mức phí
        if phi_vc == 0:      mau = "lightgreen"
        elif phi_vc < 50_000: mau = "lightyellow"
        elif phi_vc < 200_000:mau = "orange"
        else:                mau = "#FF6B6B"
        self.ui.lb_ddgh_7.setStyleSheet(
            f"color:{mau};font-weight:bold;background:transparent;border:none;")

        # Cache
        self._tien_hang = tien_hang
        self._phi_vc    = phi_vc
        self._tong      = tong_cong

    def _submit(self):
        if "(Chưa có NCC)" in (self.ui.cb_ncc.currentText() or ""):
            QMessageBox.warning(self, "Lỗi", "Vui lòng thêm Nhà cung cấp trước!")
            return
        if not self.ui.cb_ncc_2.currentData():
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn Sản phẩm!")
            return
        self.accept()

    def get_data(self):
        pd  = self.ui.cb_ncc_2.currentData()
        dg  = pd[2] if pd else 0.0
        sl  = self._spb_sl.value()
        return {
            "supplier_name":     self.ui.cb_ncc.currentText(),
            "order_date":        self.ui.de_ndh.date().toString("yyyy-MM-dd"),
            "expected_delivery": self.ui.de_tgghdk.date().toString("yyyy-MM-dd"),
            "delivery_location": self.ui.cb_ddgh.currentText(),
            "shipping_method":   self.ui.cb_ddgh_2.currentText(),
            "priority":          self._cb_ut.currentText(),
            "weight_kg":         self._dsb_tl.value(),
            "notes":             self._lne_gc.text().strip(),
            "product_sku":       pd[0] if pd else "",
            "product_name":      pd[1] if pd else "",
            "quantity":          sl,
            "unit_price":        dg,
            "subtotal":          self._tien_hang,
            "shipping_cost":     self._phi_vc,
            "total_amount":      self._tong,
        }


# =============================================================================
#  9. POPUP THÔNG BÁO
# =============================================================================
class NotificationPopup(QDialog):
    def __init__(self, notifications, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thông Báo")
        self.setMinimumWidth(400); self.setMaximumHeight(520)
        self.setStyleSheet("""
            QDialog     { background: #0F1E25; }
            QLabel      { color: white; font-size: 13px; font-weight: bold;
                          padding: 4px; }
            QListWidget { background: #1B3A4B; color: white; border: none;
                          border-radius: 8px; font-size: 12px; }
            QListWidget::item       { padding: 10px 8px;
                                      border-bottom: 1px solid #2E5C6E; }
            QListWidget::item:hover { background: #2F5D75; }
            QPushButton { background: #3B82F6; color: white;
                          border-radius: 6px; padding: 6px 18px;
                          font-weight: bold; }
        """)
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"🔔  {len(notifications)} thông báo"))
        lst = QListWidget()
        for text, level in notifications:
            item = QListWidgetItem(text)
            item.setForeground(QtGui.QColor(
                "#FF6B6B" if level == "critical" else
                "#FFD93D" if level == "warning"  else "#6BCB77"))
            lst.addItem(item)
        layout.addWidget(lst)
        btn = QPushButton("Đóng"); btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)


# =============================================================================
#  10. APP CHÍNH
# =============================================================================
class StockFlowApp(QMainWindow):
    """
    Chỉ số trang stackedWidget:
        0=Quên MK  1=Đăng nhập  2=Đăng ký
        3=Tổng quan  4=Hóa đơn  5=NCC
        6=Sản phẩm   7=Đơn hàng  8=KH
    """

    MAU_HOA_DON = {"paid":"#6BCB77","pending":"#FFD93D",
                   "overdue":"#FF6B6B","draft":"#AED6F1"}
    MAU_DON_DAT = {"pending":"#FFD93D","received":"#6BCB77",
                   "cancelled":"#FF6B6B","partial":"#AED6F1"}

    TRANG_QMK=0; TRANG_DN=1; TRANG_DK=2; TRANG_TQ=3
    TRANG_HD=4;  TRANG_NCC=5; TRANG_SP=6; TRANG_DH=7; TRANG_KH=8

    _LOGO_HTML = ('<html><body>'
                  '<p style="font-size:36pt;">QUẢN LÝ</p>'
                  '<p style="font-size:36pt;">KHO 📦</p>'
                  '</body></html>')

    # --------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.ui = Ui_Content(); self.ui.setupUi(self)
        # Danh sách các bảng cần giãn đều
        cac_bang = [self.ui.tbwg_ncc, self.ui.tbwg_kh, self.ui.tbwg_sp, self.ui.tbwg_hd, self.ui.tbwg_dh]
        
        for bang in cac_bang:
            # Giãn ngang
            bang.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
            # Giãn dọc
            bang.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
            # Ẩn header dọc mặc định
            bang.verticalHeader().setVisible(False)
            # bang.setShowGrid(False)
        # Danh sách các ô tìm kiếm cần đổi màu chữ sang đen
        cac_o_tim_kiem = [
            self.ui.lne_search,        # Thanh trên cùng
            self.ui.lne_search_kh,     # Trang Khách hàng
            self.ui.lne_search_ncc,    # Trang Nhà cung cấp
            self.ui.lne_search_sp,     # Trang Sản phẩm
            self.ui.lne_search_hd,     # Trang Hóa đơn
            self.ui.lne_search_dh      # Trang Đơn hàng
        ]

        for o in cac_o_tim_kiem:
            o.setStyleSheet("""
            QLineEdit {
             color: black; 
             background-color: #A6C8D8; 
             border-radius: 10px; 
             padding-left: 10px;
            }
        """)

        for index in [3, 4, 5, 6, 7, 8]:
            trang_goc = self.ui.stackedWidget.widget(index)
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("border: none; background-color: transparent;")
            
            trang_goc.setMaximumHeight(16777215) 
            
            trang_goc.setMinimumHeight(1250) 
            
            scroll.setWidget(trang_goc)
            self.ui.stackedWidget.removeWidget(trang_goc)
            self.ui.stackedWidget.insertWidget(index, scroll)
 
        self.is_logged_in   = False
        self._notifications = []
        self._ten_dang_nhap = ""

        # ── FIX #1: đặt logo về đúng giá trị gốc (lb_name = logo, không phải username)
        self.ui.lb_name.setText(self._LOGO_HTML)

        # ── FIX #1: thêm label tên người dùng nhỏ ở phía dưới logo trong sidebar
        #   lb_name: y=20, h=181 → các nav button từ y=210
        #   → đặt username label tại y=192
        self._lbl_user = QLabel("", self.ui.sidebar)
        self._lbl_user.setGeometry(10, 192, 290, 18)
        self._lbl_user.setStyleSheet(
            "color: #AED6F1; font-size: 11px; font-weight: bold;")
        self._lbl_user.setAlignment(
            Qt.AlignmentFlag.AlignCenter)
        self._lbl_user.setVisible(False)

        # ComboBox bộ lọc
        self._khoi_tao_bo_loc()

        # FIX #1: sidebar tắt trước khi đăng nhập
        self.ui.sidebar.setEnabled(False)
        self.ui.stackedWidget.setCurrentIndex(self.TRANG_DN)

        # FIX #1 (màu chữ đen cho ô đăng nhập)
        _s = "QLineEdit { color: black; background-color: white; }"
        for w in [self.ui.lne_tdn_dn,  self.ui.lnex_mk_dn,
                  self.ui.lne_tdn_dk,  self.ui.lne_mk_dk,  self.ui.lne_dlmk_dk,
                  self.ui.lne_tdn_dlmk,self.ui.lne_mkm_dlmk,self.ui.lne_nlmk_dlmk]:
            w.setStyleSheet(_s)

        self._khoi_tao_bieu_do()
        self._ket_noi_tin_hieu()
        self._ket_noi_bo_loc()


    # --------------------------------------------------------------------------
    #  KHỞI TẠO
    # --------------------------------------------------------------------------
    def _khoi_tao_bo_loc(self):
        for cb, items in [
            (self.ui.cb_f_kh,  ["Tất cả","Active","Inactive","VIP"]),
            (self.ui.cb_f_sp,  ["Tất cả","Còn hàng","Sắp hết","Hết hàng"]),
            (self.ui.cb_f_ncc, ["Tất cả","Đã xác minh","Chưa giải quyết"]),
            (self.ui.cb_f_hd,  ["Tất cả","paid","pending","overdue","draft"]),
            (self.ui.cb_f_dh,  ["Tất cả","pending","received","cancelled","partial"]),
        ]:
            cb.clear(); cb.addItems(items)

    def _khoi_tao_bieu_do(self):
        vl1 = QHBoxLayout(self.ui.wg_xhgdt)
        vl1.setContentsMargins(0, 30, 0, 0)
        self.bieu_do_duong = LineChartCanvas(self.ui.wg_xhgdt)
        vl1.addWidget(self.bieu_do_duong)

        vl2 = QHBoxLayout(self.ui.wg_dmsp)
        vl2.setContentsMargins(0, 30, 0, 0)
        self.bieu_do_tron = PieChartCanvas(self.ui.wg_dmsp)
        vl2.addWidget(self.bieu_do_tron)

    def _lam_moi_bieu_do(self):
        """FIX #6: lấy dữ liệu thực từ DB."""
        try:
            thang, dt, nk = dashboard_db.get_monthly_trend()
            self.bieu_do_duong.plot(thang, dt, nk)
            self.bieu_do_tron.plot(dashboard_db.get_category_distribution())
        except Exception as e:
            print(f"[Lỗi biểu đồ]: {e}")

    # --------------------------------------------------------------------------
    #  KẾT NỐI TÍN HIỆU
    # --------------------------------------------------------------------------
    def _ket_noi_tin_hieu(self):
        # Sidebar
        self.ui.pb_tq.clicked.connect(
            lambda: self._chuyen_trang(self.TRANG_TQ, self.ui.pb_tq))
        self.ui.pb_kh.clicked.connect(
            lambda: self._chuyen_trang(self.TRANG_KH, self.ui.pb_kh))
        self.ui.pb_ncc.clicked.connect(
            lambda: self._chuyen_trang(self.TRANG_NCC,self.ui.pb_ncc))
        self.ui.pb_sp.clicked.connect(
            lambda: self._chuyen_trang(self.TRANG_SP, self.ui.pb_sp))
        self.ui.pb_hd.clicked.connect(
            lambda: self._chuyen_trang(self.TRANG_HD, self.ui.pb_hd))
        self.ui.pb_dh.clicked.connect(
            lambda: self._chuyen_trang(self.TRANG_DH, self.ui.pb_dh))

        # Auth
        self.ui.pb_dn.clicked.connect(self._dang_nhap)
        self.ui.pb_qmk_dn.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentIndex(self.TRANG_QMK))
        self.ui.pb_dk_dn.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentIndex(self.TRANG_DK))
        self.ui.pb_dk.clicked.connect(self._dang_ky)
        self.ui.pb_dn_dk.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentIndex(self.TRANG_DN))
        self.ui.pb_qmk_dk.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentIndex(self.TRANG_QMK))
        self.ui.pb_dl.clicked.connect(self._doi_mat_khau)
        self.ui.pb_dn_dlmk.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentIndex(self.TRANG_DN))
        self.ui.pb_dk_dlmk.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentIndex(self.TRANG_DK))

        # Thêm mới
        self.ui.pb_add_kh.clicked.connect(self._them_khach_hang)
        self.ui.pb_add_ncc.clicked.connect(self._them_nha_cung_cap)
        self.ui.pb_add_sp.clicked.connect(self._them_san_pham)
        self.ui.pb_add_hd.clicked.connect(self._them_hoa_don)
        self.ui.pb_add_dh.clicked.connect(self._them_don_dat_hang)

        # Tìm kiếm
        for pb, le, fn in [
            (self.ui.pb_search_kh,  self.ui.lne_search_kh,  self._tim_khach_hang),
            (self.ui.pb_search_ncc, self.ui.lne_search_ncc, self._tim_nha_cung_cap),
            (self.ui.pb_search_sp,  self.ui.lne_search_sp,  self._tim_san_pham),
            (self.ui.pb_search_hd,  self.ui.lne_search_hd,  self._tim_hoa_don),
            (self.ui.pb_search_dh,  self.ui.lne_search_dh,  self._tim_don_dat_hang),
            (self.ui.pb_search,     self.ui.lne_search,     self._tim_toan_cuc),
        ]:
            pb.clicked.connect(fn)
            le.returnPressed.connect(fn)

        # Chuông + tài khoản
        self.ui.tb_noti.clicked.connect(self._hien_thong_bao)
        self.ui.tb_account.clicked.connect(self._hien_menu_tai_khoan)

        # Context menu (click phải + double-click)
        for bang, loai in [
            (self.ui.tbwg_kh,  "khách hàng"),
            (self.ui.tbwg_ncc, "nhà cung cấp"),
            (self.ui.tbwg_sp,  "sản phẩm"),
            (self.ui.tbwg_dh,  "đơn đặt hàng"),
        ]:
            bang.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            bang.customContextMenuRequested.connect(
                lambda pos, b=bang, l=loai: self._context_menu(pos, b, l))
            bang.itemDoubleClicked.connect(
                lambda _, b=bang, l=loai: self._context_menu(
                    b.viewport().mapFromGlobal(QtGui.QCursor.pos()), b, l))

        self.ui.tbwg_hd.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.tbwg_hd.customContextMenuRequested.connect(
            lambda pos: self._context_menu_hoa_don(pos))
        self.ui.tbwg_hd.itemDoubleClicked.connect(
            lambda _: self._context_menu_hoa_don(
                self.ui.tbwg_hd.viewport().mapFromGlobal(
                    QtGui.QCursor.pos())))

    def _ket_noi_bo_loc(self):
        self.ui.cb_f_kh.currentTextChanged.connect(self._tai_bang_khach_hang)
        self.ui.cb_f_ncc.currentTextChanged.connect(self._tai_bang_nha_cung_cap)
        self.ui.cb_f_sp.currentTextChanged.connect(self._tai_bang_san_pham)
        self.ui.cb_f_hd.currentTextChanged.connect(self._tai_bang_hoa_don)
        self.ui.cb_f_dh.currentTextChanged.connect(self._tai_bang_don_dat_hang)

    # --------------------------------------------------------------------------
    #  TIỆN ÍCH
    # --------------------------------------------------------------------------
    def _tao_o(self, nd, mau="white"):
        o = QTableWidgetItem(str(nd)); o.setForeground(QtGui.QColor(mau)); return o

    def _cap_nhat_gio(self, label):
        try:
            label.setText(
                f"Lần cập nhật cuối: "
                f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        except Exception: pass

    def _chuyen_trang(self, chi_so, nut=None):
        if not self.is_logged_in: return
        self.ui.stackedWidget.setCurrentIndex(chi_so)
        self._highlight_sidebar(nut)
        ham = {
            self.TRANG_TQ:  self._lam_moi_tong_quan,
            self.TRANG_KH:  self._tai_bang_khach_hang,
            self.TRANG_NCC: self._tai_bang_nha_cung_cap,
            self.TRANG_SP:  self._tai_bang_san_pham,
            self.TRANG_HD:  self._tai_bang_hoa_don,
            self.TRANG_DH:  self._tai_bang_don_dat_hang,
        }
        try:
            if chi_so in ham: ham[chi_so]()
        except Exception as e:
            print(f"[Lỗi tải trang {chi_so}]: {e}")

    def _highlight_sidebar(self, active):
        for btn in [self.ui.pb_tq, self.ui.pb_kh, self.ui.pb_ncc,
                    self.ui.pb_sp, self.ui.pb_hd, self.ui.pb_dh]:
            btn.setStyleSheet(
                "background:#3b82f6;color:white;border-radius:5px;"
                "text-align:left;padding:10px;" if btn == active else
                "background:transparent;color:white;border:none;"
                "text-align:left;padding:10px;")

    # --------------------------------------------------------------------------
    #  FIX #2: MENU TÀI KHOẢN
    # --------------------------------------------------------------------------
    def _hien_menu_tai_khoan(self):
        menu = QMenu(self); menu.setStyleSheet(_MENU_STYLE)
        act_info = QAction(f"👤  {self._ten_dang_nhap}", self)
        act_info.setEnabled(False)
        menu.addAction(act_info)
        menu.addSeparator()
        act_out = QAction("🚪  Đăng xuất", self)
        act_out.triggered.connect(self._dang_xuat)
        menu.addAction(act_out)
        pos = self.ui.tb_account.mapToGlobal(
            self.ui.tb_account.rect().bottomLeft())
        menu.exec(pos)

    def _dang_xuat(self):
        if QMessageBox.question(
                self, "Đăng xuất", "Bạn có chắc muốn đăng xuất?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        self.is_logged_in   = False
        self._ten_dang_nhap = ""
        self._notifications = []
        self.ui.sidebar.setEnabled(False)
        # FIX #1: khôi phục logo
        self.ui.lb_name.setText(self._LOGO_HTML)
        self._lbl_user.setVisible(False)
        self.ui.lnex_mk_dn.clear()
        self.ui.stackedWidget.setCurrentIndex(self.TRANG_DN)

    # --------------------------------------------------------------------------
    #  AUTH
    # --------------------------------------------------------------------------
    def _dang_nhap(self):
        ten = self.ui.lne_tdn_dn.text().strip()
        mk  = self.ui.lnex_mk_dn.text()
        if check_login_db.check_login(ten, mk):
            self.is_logged_in   = True
            self._ten_dang_nhap = ten
            self.ui.sidebar.setEnabled(True)
            # FIX #1: hiện username nhỏ bên dưới logo, không đè logo
            self._lbl_user.setText(f"👤  {ten}")
            self._lbl_user.setVisible(True)
            self._chuyen_trang(self.TRANG_TQ, self.ui.pb_tq)
        else:
            QMessageBox.warning(self, "Lỗi đăng nhập",
                                "Sai tài khoản hoặc mật khẩu!")

    def _dang_ky(self):
        ten = self.ui.lne_tdn_dk.text().strip()
        mk  = self.ui.lne_mk_dk.text()
        mk2 = self.ui.lne_dlmk_dk.text()
        if not ten or not mk:
            QMessageBox.warning(self,"Lỗi","Vui lòng nhập đầy đủ!"); return
        if mk != mk2:
            QMessageBox.warning(self,"Lỗi","Mật khẩu không khớp!"); return
        if check_login_db.register_user(ten, mk):
            QMessageBox.information(self,"Thành công","Đã đăng ký tài khoản!")
            self.ui.stackedWidget.setCurrentIndex(self.TRANG_DN)
        else:
            QMessageBox.warning(self,"Lỗi","Tên đăng nhập đã tồn tại!")

    def _doi_mat_khau(self):
        ten = self.ui.lne_tdn_dlmk.text().strip()
        mk  = self.ui.lne_mkm_dlmk.text()
        mk2 = self.ui.lne_nlmk_dlmk.text()
        if not ten or not mk:
            QMessageBox.warning(self,"Lỗi","Vui lòng nhập đầy đủ!"); return
        if mk != mk2:
            QMessageBox.warning(self,"Lỗi","Mật khẩu không khớp!"); return
        if check_login_db.update_password(ten, mk):
            QMessageBox.information(self,"Thành công","Đã cập nhật mật khẩu!")
            self.ui.stackedWidget.setCurrentIndex(self.TRANG_DN)
        else:
            QMessageBox.warning(self,"Lỗi","Không tìm thấy tài khoản!")

    # --------------------------------------------------------------------------
    #  TỔNG QUAN
    # --------------------------------------------------------------------------
    def _lam_moi_tong_quan(self):
        tk  = dashboard_db.get_dashboard_stats()
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.ui.lb_updatetime_tq.setText(f"Lần cập nhật cuối: {now}")
        self.ui.lb_tdt_1.setText(tk["total_value"])
        self.ui.lb_hh_1.setText(str(tk["out_of_stock"]))
        self.ui.lb_tkt_1.setText(str(tk["low_stock"]))
        self.ui.lb_lkh_1.setText(str(tk["total_customers"]))

        # Cảnh báo tồn kho thấp
        sp_cb = [r for r in product_db.fetch_all_products()
                 if str(r[-1]) in ("Hết hàng","Sắp hết") or r[3] < 10][:3]
        slots_cb = [
            (self.ui.lb_cbtkt_1,self.ui.lb_cbtkt_1_1,
             self.ui.lb_cbtkt_1_2,self.ui.lb_cbtkt_1_3),
            (self.ui.lb_cbtkt_2,self.ui.lb_cbtkt_2_1,
             self.ui.lb_cbtkt_2_2,self.ui.lb_cbtkt_2_3),
            (self.ui.lb_cbtkt_3,self.ui.lb_cbtkt_3_1,
             self.ui.lb_cbtkt_3_2,self.ui.lb_cbtkt_3_3),
        ]
        for i, (ln, lm, lv, lb) in enumerate(slots_cb):
            if i < len(sp_cb):
                r = sp_cb[i]
                ln.setText(r[1]); lm.setText(f"Mã: {r[0]}")
                lv.setText(f"Tồn: {r[3]}")
                badge = "Khẩn Cấp" if r[3] == 0 else "Cảnh Báo"
                mau   = "#FF6B6B"  if r[3] == 0 else "#FFD93D"
                lb.setText(badge); lb.setStyleSheet(
                    f"color:{mau};font-weight:bold;")
            else:
                for l in (ln, lm, lv, lb): l.setText("")

        # Hoạt động gần đây
        acts = dashboard_db.get_recent_activities()
        slots_hd = [
            (self.ui.lb_hdgd_1,self.ui.lb_hdgd_1_1,self.ui.lb_hdgd_1_2),
            (self.ui.lb_hdgd_2,self.ui.lb_hdgd_2_1,self.ui.lb_hdgd_2_2),
            (self.ui.lb_hdgd_3,self.ui.lb_hdgd_3_1,self.ui.lb_hdgd_3_2),
        ]
        for i, (lt, la, ld) in enumerate(slots_hd):
            if i < len(acts):
                inv, kh, ngay, tien, _ = acts[i]
                lt.setText(f"Hóa đơn #{inv} — {kh}")
                la.setText(f"+{float(tien):,.0f} ₫" if tien else "0 ₫")
                ld.setText(str(ngay) if ngay else "")
            else:
                for l in (lt, la, ld): l.setText("")

        self._lam_moi_bieu_do()
        self._lam_moi_thong_bao()

    # --------------------------------------------------------------------------
    #  THÔNG BÁO
    # --------------------------------------------------------------------------
    def _lam_moi_thong_bao(self):
        self._notifications = []
        for r in product_db.fetch_all_products():
            ten, ton, tt = r[1], r[3], str(r[-1])
            if tt == "Hết hàng" or ton == 0:
                self._notifications.append(
                    (f"🔴 HẾT HÀNG: {ten} (SL: {ton})", "critical"))
            elif tt == "Sắp hết" or ton < 10:
                self._notifications.append(
                    (f"🟡 Sắp hết: {ten} (SL: {ton})", "warning"))
        n = len(self._notifications)
        self.ui.lb_noti.setText(str(n) if n > 0 else "")
        self.ui.lb_noti.setVisible(n > 0)
        self.ui.tb_noti.setStyleSheet(
            "QToolButton{background:#F59E0B;border:none;border-radius:15px;padding:4px;}"
            "QToolButton:hover{background:#D97706;}" if n > 0 else
            "QToolButton{background:#3F6F88;border:none;border-radius:15px;padding:4px;}"
            "QToolButton:hover{background:#2F5D75;}")

    def _hien_thong_bao(self):
        if not self._notifications: self._lam_moi_thong_bao()
        if not self._notifications:
            QMessageBox.information(self,"Thông Báo","✅ Không có cảnh báo!")
            return
        NotificationPopup(self._notifications, self).exec()

    # --------------------------------------------------------------------------
    #  CONTEXT MENU BẢNG (FIX #4 double-click)
    # --------------------------------------------------------------------------
    def _context_menu(self, pos, bang, loai):
        dong = bang.currentRow()
        if dong < 0: return
        bang.selectRow(dong)                # Highlight toàn hàng

        ten = bang.item(dong, 1).text() if bang.item(dong, 1) else "?"
        menu = QMenu(self); menu.setStyleSheet(_MENU_STYLE)

        act_title = QAction(f"  {ten}", self); act_title.setEnabled(False)
        menu.addAction(act_title); menu.addSeparator()

        act_xoa = QAction("🗑  Xóa", self)
        act_xoa.triggered.connect(
            lambda: self._xac_nhan_xoa(bang, dong, loai))
        menu.addAction(act_xoa)

        global_pos = bang.viewport().mapToGlobal(pos) \
            if isinstance(pos, QPoint) else bang.mapToGlobal(pos)
        menu.exec(global_pos)

    def _context_menu_hoa_don(self, pos):
        bang = self.ui.tbwg_hd
        dong = bang.currentRow()
        if dong < 0: return
        bang.selectRow(dong)

        # Số HĐ ở cột 0, row_id lưu trong UserRole
        item0 = bang.item(dong, 0)
        so_hd = item0.text() if item0 else "?"

        menu = QMenu(self); menu.setStyleSheet(_MENU_STYLE)
        act_title = QAction(f"  HĐ #{so_hd}", self)
        act_title.setEnabled(False)
        menu.addAction(act_title); menu.addSeparator()

        act_sua = QAction("✏  Sửa hóa đơn", self)
        act_sua.triggered.connect(self._sua_hoa_don)
        menu.addAction(act_sua)

        act_xoa = QAction("🗑  Xóa hóa đơn", self)
        act_xoa.triggered.connect(lambda: self._xoa_hoa_don(dong))
        menu.addAction(act_xoa)

        global_pos = bang.viewport().mapToGlobal(pos) \
            if isinstance(pos, QPoint) else bang.mapToGlobal(pos)
        menu.exec(global_pos)

    # --------------------------------------------------------------------------
    #  XÓA (FIX #5 cập nhật liên kết)
    # --------------------------------------------------------------------------
    def _xac_nhan_xoa(self, bang, dong, loai):
        ten = bang.item(dong, 1).text() if bang.item(dong, 1) else "?"
        if QMessageBox.question(
                self, f"Xác nhận xóa {loai}",
                f"Bạn có chắc muốn xóa:\n\n  {ten}\n\nHành động không thể hoàn tác!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            o_id = bang.item(dong, 0)
            if o_id:
                id_str = o_id.text()
                if loai == "khách hàng":
                    customer_db.delete_customer(int(id_str))
                elif loai == "sản phẩm":
                    product_db.delete_product(id_str)
                elif loai == "đơn đặt hàng":
                    purchase_orders_db.delete_purchase_order(int(id_str))
                elif loai == "nhà cung cấp":
                    # Xóa đơn đặt hàng liên quan + reset AUTOINCREMENT
                    ncc_ten = ten
                    ds_dh   = purchase_orders_db.fetch_all_purchase_orders()
                    dem_xoa = 0
                    for dh in ds_dh:
                        if str(dh[1]).strip().lower() == ncc_ten.lower():
                            purchase_orders_db.delete_purchase_order(dh[0])
                            dem_xoa += 1
                    supplier_db.delete_supplier(int(id_str))  # reset AUTOINCREMENT

                    msg = f"✅ Đã xóa nhà cung cấp: {ncc_ten}"
                    if dem_xoa:
                        msg += f"\n📦 Đã xóa {dem_xoa} đơn đặt hàng liên quan."
                    QMessageBox.information(self, "Thành công", msg)
                    bang.removeRow(dong)
                    return
        except Exception as e:
            QMessageBox.critical(self, "Lỗi xóa", str(e)); return
        bang.removeRow(dong)
        QMessageBox.information(self, "Thành công", f"Đã xóa {loai}: {ten}")

    def _xoa_hoa_don(self, dong):
        bang  = self.ui.tbwg_hd
        item0 = bang.item(dong, 0)
        if not item0: return

        # row_id lưu trong UserRole, text hiển thị là số HĐ
        row_id = item0.data(Qt.ItemDataRole.UserRole)
        so_hd  = item0.text()

        if row_id is None:
            QMessageBox.warning(self, "Lỗi", "Không tìm được ID hóa đơn!")
            return

        if QMessageBox.question(
                self, "Xác nhận xóa",
                f"Bạn có chắc muốn xóa hóa đơn #{so_hd}?\n"
                f"Hành động này không thể hoàn tác!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            Invoices_db.delete_invoice(int(row_id))
            bang.removeRow(dong)
            QMessageBox.information(self, "Thành công",
                                    f"✅ Đã xóa hóa đơn #{so_hd}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi xóa", str(e))

    # --------------------------------------------------------------------------
    #  KHÁCH HÀNG
    # --------------------------------------------------------------------------
    def _tai_bang_khach_hang(self, du_lieu=None):
        bo_loc = self.ui.cb_f_kh.currentText()
        # Lấy dữ liệu từ file customer_db
        hang = du_lieu if du_lieu is not None else customer_db.fetch_all_customers()
        bang = self.ui.tbwg_kh
        
        bang.blockSignals(True)
        bang.setRowCount(0)
        
        
        stt_ao = 1 # Biến đếm để STT luôn tự động lùi khi xóa
        
        for r in hang:
            # Cấu trúc r giả định: (0:id, 1:name, 2:email, 3:phone, 4:address, 5:status)
            dong = bang.rowCount()
            bang.insertRow(dong)
            
            # Cột 0: STT ảo + Lưu ID thật (r[0]) ẩn vào ô này
            item_stt = self._tao_o(stt_ao)
            item_stt.setData(Qt.ItemDataRole.UserRole, r[0]) # Giấu ID database vào đây
            bang.setItem(dong, 0, item_stt)
            
            bang.setItem(dong, 1, self._tao_o(r[1])) # Tên KH
            bang.setItem(dong, 2, self._tao_o(r[2])) # Email
            bang.setItem(dong, 3, self._tao_o(r[3])) # SĐT
            bang.setItem(dong, 4, self._tao_o(r[4])) # Địa chỉ
            
            # Cột 5: Trạng thái (ComboBox)
            cb = QComboBox()
            cb.addItems(["Active", "Inactive", "VIP"])
            cb.setCurrentText(str(r[5]) if r[5] else "Active")
            cb.setStyleSheet("color: black; background: #A6C8D8; border: none;")
            
            # Cập nhật trạng thái
            cb.currentTextChanged.connect(
                lambda txt, cid=r[0]: customer_db.update_customer_status(cid, txt))
            bang.setCellWidget(dong, 5, cb)
            
            stt_ao += 1 # Tăng STT hiển thị

        # --- TÍCH HỢP CHỨC NĂNG XÓA (Context Menu) ---
        try: bang.customContextMenuRequested.disconnect() # Tránh lặp sự kiện
        except: pass
        
        bang.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        def show_delete_menu(pos):
            idx = bang.indexAt(pos)
            if not idx.isValid(): return
            
            # Lấy ID và Tên từ dòng vừa nhấn chuột
            row_idx = idx.row()
            customer_id = bang.item(row_idx, 0).data(Qt.ItemDataRole.UserRole)
            customer_name = bang.item(row_idx, 1).text()
            
            from PyQt6.QtGui import QAction, QCursor
            menu = QMenu(self)
            menu.setStyleSheet("background: #1a2634; color: white; border: 1px solid gray;")
            act_xoa = menu.addAction(" 🗑️ Xóa Khách Hàng")
            
            # Khi bấm vào chữ Xóa
            act_xoa.triggered.connect(lambda: (
                QMessageBox.question(self, "Xác nhận", f"Xóa vĩnh viễn: {customer_name}?") == QMessageBox.StandardButton.Yes and (
                    customer_db.delete_customer(customer_id), # 1. Xóa trong DB
                    self._tai_bang_khach_hang()               # 2. Nạp lại bảng (STT tự lùi)
                )
            ))
            menu.exec(QCursor.pos()) # Hiện menu tại vị trí chuột

        bang.customContextMenuRequested.connect(show_delete_menu)
        bang.blockSignals(False)

    def _tao_o(self, van_ban):
        """Hàm phụ trợ tạo ô bảng với chữ màu đen và căn giữa"""
        item = QTableWidgetItem(str(van_ban))
        item.setForeground(QColor("white"))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Căn giữa
        return item
    
    def _tim_khach_hang(self):
        kw = self.ui.lne_search_kh.text().strip()
        if kw:
            kw_lo = kw.lower()
            kq = [r for r in customer_db.fetch_all_customers()
                  if kw_lo in str(r[1]).lower()
                  or kw_lo in str(r[2]).lower()
                  or kw_lo in str(r[3]).lower()]
            self._tai_bang_khach_hang(du_lieu=kq)
        else:
            self._tai_bang_khach_hang()

    def _them_khach_hang(self):
        dlg = ThemKHDialog(self)
        
        # Lấy số gợi ý (Tổng người đang có + 1)
        try:
            next_num = customer_db.get_next_stt()
            dlg.ui.lne_stt.setText(str(next_num))
        except Exception as e:
            print(f"Lỗi: {e}")

        if dlg.exec() != QDialog.DialogCode.Accepted: 
            return
            
        d = dlg.get_data()
        try:
            customer_db.add_customer(d["name"], d["email"], d["phone"],
                                     d["orders"], d["balance"], d["status"])
            # Load lại bảng: stt_hien_thi sẽ tự chạy lại từ 1, 2, 3...
            self._tai_bang_khach_hang()
            QMessageBox.information(self, "Thành công", f"✅ Đã thêm: {d['name']}")
        except Exception as e: 
            QMessageBox.critical(self, "Lỗi", str(e))

    # --------------------------------------------------------------------------
    #  SẢN PHẨM
    # --------------------------------------------------------------------------
    def _tai_bang_san_pham(self, du_lieu=None):
        bo_loc = self.ui.cb_f_sp.currentText()
        hang   = du_lieu if du_lieu is not None else product_db.fetch_all_products()
        bang   = self.ui.tbwg_sp
        bang.blockSignals(True); bang.setRowCount(0)
        for r in hang:
            tt  = str(r[-1]).strip() if r[-1] else "Còn hàng"
            sku = r[0]
            if bo_loc != "Tất cả" and tt.lower() != bo_loc.lower():
                continue
            dong = bang.rowCount(); bang.insertRow(dong)
            for cot, v in enumerate([r[0],r[1],r[2],r[3],f"{r[4]:,.0f}"]):
                bang.setItem(dong, cot, self._tao_o(v))
            cb = QComboBox(); cb.addItems(["Còn hàng","Sắp hết","Hết hàng"])
            cb.setCurrentText(tt)
            cb.setStyleSheet("color:white;background:#1e293b;border:none;")
            cb.currentTextChanged.connect(
                lambda txt, sk=sku: product_db.update_product_status(sk, txt))
            bang.setCellWidget(dong, 5, cb)
        bang.blockSignals(False)
        self._cap_nhat_gio(self.ui.lb_updatetime_sp)

    def _tim_san_pham(self):
        kw = self.ui.lne_search_sp.text().strip()
        if kw:
            kw_lo = kw.lower()
            kq = [r for r in product_db.fetch_all_products()
                  if kw_lo in str(r[0]).lower()
                  or kw_lo in str(r[1]).lower()
                  or kw_lo in str(r[2]).lower()]
            self._tai_bang_san_pham(du_lieu=kq)
        else:
            self._tai_bang_san_pham()

    def _them_san_pham(self):
        dlg = ThemSPDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted: return
        d = dlg.get_data()
        try:
            product_db.add_product(d["sku"],d["name"],d["category"],
                                   d["stock"],d["price"],d["cost"],d["status"])
            self._tai_bang_san_pham()
            self._lam_moi_thong_bao()
            QMessageBox.information(self,"Thành công",
                                    f"✅ Đã thêm sản phẩm: {d['name']}")
        except Exception as e: QMessageBox.critical(self,"Lỗi",str(e))

    # --------------------------------------------------------------------------
    #  NHÀ CUNG CẤP
    # --------------------------------------------------------------------------

    def _tai_bang_nha_cung_cap(self, du_lieu=None):
        bo_loc = self.ui.cb_f_ncc.currentText()
        # 1. Lấy dữ liệu từ file supplier_db
        hang = du_lieu if du_lieu is not None else supplier_db.fetch_all_suppliers()
        bang = self.ui.tbwg_ncc
        
        bang.blockSignals(True)
        bang.setRowCount(0)
        
        # Bản đồ trạng thái để lọc
        TT_MAP = {
            "verified": "Đã xác minh", "da xac minh": "Đã xác minh", "đã xác minh": "Đã xác minh",
            "unverified": "Chưa giải quyết", "chua giai quyet": "Chưa giải quyết", "chưa giải quyết": "Chưa giải quyết"
        }

        stt_ao = 1 # Biến đếm để STT luôn tự động lùi khi xóa

        for r in hang:
            # r giả định: (0:id, 1:name, 2:category, 3:email, 4:phone, 5:address, 6:contact, 7:total_orders)
            raw_stt = str(r[2]).strip().lower() if r[2] else ""
            tt_hien_thi = TT_MAP.get(raw_stt, "Chưa giải quyết")

            # Bộ lọc ComboBox
            if bo_loc != "Tất cả" and tt_hien_thi != bo_loc:
                continue

            dong = bang.rowCount()
            bang.insertRow(dong)

            # --- ĐỔ DỮ LIỆU VÀO 6 CỘT ---
            
            # Cột 0: STT ảo + Lưu ID thật (r[0]) ẩn vào ô này
            item_stt = self._tao_o(stt_ao)
            item_stt.setData(Qt.ItemDataRole.UserRole, r[0]) # Giấu ID database vào đây
            bang.setItem(dong, 0, item_stt)

            # Cột 1: Tên NCC (r[1])
            bang.setItem(dong, 1, self._tao_o(r[1]))
            
            # Cột 2: Email (r[3])
            bang.setItem(dong, 2, self._tao_o(r[3]))
            
            # Cột 3: SĐT (r[4])
            bang.setItem(dong, 3, self._tao_o(r[4]))
            
            # Cột 4: Tổng đơn hàng (r[7])
            tong_don = str(r[7]) if len(r) > 7 and r[7] is not None else "0"
            bang.setItem(dong, 4, self._tao_o(tong_don))

            # Cột 5: Trạng thái (ComboBox)
            cb = QComboBox()
            cb.addItems(["Đã xác minh", "Chưa giải quyết"])
            cb.setCurrentText(tt_hien_thi)
            cb.setStyleSheet("color: white; background: #1e293b; border: none;")
            
            # Cập nhật trạng thái vào DB
            cb.currentTextChanged.connect(
                lambda txt, sid=r[0]: supplier_db.update_supplier_status(sid, txt))
            bang.setCellWidget(dong, 5, cb)

            stt_ao += 1 # Tăng STT hiển thị cho dòng tiếp theo

        # --- TÍCH HỢP CHỨC NĂNG XÓA (Context Menu) ---
        try: bang.customContextMenuRequested.disconnect()
        except: pass
        
        bang.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        def show_delete_menu_ncc(pos):
            idx = bang.indexAt(pos)
            if not idx.isValid(): return
            
            row_idx = idx.row()
            # Lấy ID ẩn từ cột 0
            supplier_id = bang.item(row_idx, 0).data(Qt.ItemDataRole.UserRole)
            supplier_name = bang.item(row_idx, 1).text()
            
            from PyQt6.QtGui import QAction, QCursor
            menu = QMenu(self)
            menu.setStyleSheet("background: #1a2634; color: white; border: 1px solid gray;")
            act_xoa = menu.addAction(" 🗑️ Xóa Nhà Cung Cấp")
            
            act_xoa.triggered.connect(lambda: (
                QMessageBox.question(self, "Xác nhận", f"Xóa vĩnh viễn NCC: {supplier_name}?") == QMessageBox.StandardButton.Yes and (
                    supplier_db.delete_supplier(supplier_id), # 1. Xóa trong DB
                    self._tai_bang_nha_cung_cap()             # 2. Nạp lại bảng (STT tự lùi)
                )
            ))
            menu.exec(QCursor.pos())

        bang.customContextMenuRequested.connect(show_delete_menu_ncc)
        bang.blockSignals(False)
        
        if hasattr(self.ui, 'lb_updatetime_ncc'):
            self._cap_nhat_gio(self.ui.lb_updatetime_ncc)

    def _tim_nha_cung_cap(self):
        kw = self.ui.lne_search_ncc.text().strip()
        if kw:
            kw_lo = kw.lower()
            kq = [r for r in supplier_db.fetch_all_suppliers()
                  if kw_lo in str(r[1]).lower()
                  or kw_lo in str(r[2]).lower()
                  or kw_lo in str(r[4]).lower()]
            self._tai_bang_nha_cung_cap(du_lieu=kq)
        else:
            self._tai_bang_nha_cung_cap()

    def _them_nha_cung_cap(self):
     dlg = ThemNCCDialog(self)
     if dlg.exec() != QDialog.DialogCode.Accepted: return
     d = dlg.get_data() # Giả sử trong d đã có key "total_orders" từ Dialog
    
     try:
        # Truyền thêm dữ liệu tổng đơn hàng vào đây
        supplier_db.add_supplier(
            d.get("name"),           # 1. Tên
            d.get("status"),         # 2. Trạng thái (category)
            d.get("email"),          # 3. Email
            d.get("phone"),          # 4. SĐT
            "",                      # 5. address (Truyền trống vì UI không có)
            "",                      # 6. contact_person (Truyền trống vì UI không có)
            d.get("total_orders") # 7. Tổng đơn hàng
        )
        self._tai_bang_nha_cung_cap()
        QMessageBox.information(self, "Thành công", f"✅ Đã thêm NCC: {d['name']}")
     except Exception as e: 
        QMessageBox.critical(self, "Lỗi", str(e))

    # --------------------------------------------------------------------------
    #  HÓA ĐƠN
    # --------------------------------------------------------------------------
    def _tai_bang_hoa_don(self, du_lieu=None):
        """
        Giữ đúng 6 cột của Giaodien.py:
            Cột 0 = Số HĐ  | 1 = Tên KH | 2 = Ngày tạo
            Cột 3 = Ngày hạn | 4 = Tổng tiền | 5 = Trạng thái (ComboBox)

        row_id (id DB) được lưu trong Qt.ItemDataRole.UserRole của ô cột 0
        để dùng cho sửa / xóa mà không cần thêm cột ẩn.
        """
        bo_loc = self.ui.cb_f_hd.currentText()
        # fetch_all_invoices trả về 7 phần tử:
        #   (id, hd_no, customer, date, due_date, amount, status)
        hang = du_lieu if du_lieu is not None else Invoices_db.fetch_all_invoices()
        bang = self.ui.tbwg_hd

        bang.blockSignals(True)
        bang.setRowCount(0)

        for r in hang:
            row_id = r[0]                                        # id thực trong DB
            tt     = str(r[6]).strip().lower() if r[6] else "pending"

            if bo_loc != "Tất cả" and tt != bo_loc.lower():
                continue

            dong = bang.rowCount()
            bang.insertRow(dong)

            # Cột 0: Số HĐ – lưu row_id vào UserRole để dùng khi sửa/xóa
            o0 = QTableWidgetItem(str(r[1]))
            o0.setForeground(QtGui.QColor("white"))
            o0.setData(Qt.ItemDataRole.UserRole, row_id)   # ← lưu id ẩn
            bang.setItem(dong, 0, o0)

            # Cột 1-4: dữ liệu hiển thị
            tien = f"{float(r[5]):,.0f} ₫" if r[5] else "0 ₫"
            for cot, v in enumerate([r[2], r[3], r[4], tien], start=1):
                bang.setItem(dong, cot, self._tao_o(v))

            # Cột 5: ComboBox trạng thái
            cb = QComboBox()
            cb.addItems(["pending", "paid", "overdue", "draft"])
            cb.setCurrentText(tt)
            mau = self.MAU_HOA_DON.get(tt, "white")
            cb.setStyleSheet(
                f"color:{mau};background:#1e293b;border:none;font-weight:bold;")
            cb.currentTextChanged.connect(
                lambda txt, rid=row_id: Invoices_db.update_invoice_status(rid, txt))
            bang.setCellWidget(dong, 5, cb)

        bang.blockSignals(False)
        self._cap_nhat_gio(self.ui.lb_updatetime_hd)

    def _tim_hoa_don(self):
        kw = self.ui.lne_search_hd.text().strip()
        if kw:
            kw_lo = kw.lower()
            kq = [r for r in Invoices_db.fetch_all_invoices()
                  if kw_lo in str(r[0]).lower()
                  or kw_lo in str(r[1]).lower()]
            self._tai_bang_hoa_don(du_lieu=kq)
        else:
            self._tai_bang_hoa_don()

    def _them_hoa_don(self):
        dlg = TaoHoaDonDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted: return
        d = dlg.get_data()
        try:
            Invoices_db.add_invoice(d["inv_no"],d["customer"],d["date"],
                                    d["due_date"],d["amount"],d["status"])
            self._tai_bang_hoa_don()
            QMessageBox.information(self,"Thành công",
                f"✅ HĐ {d['inv_no']} — {d['customer']}\n"
                f"Tổng: {d['amount']:,.0f} ₫")
        except Exception as e: QMessageBox.critical(self,"Lỗi",str(e))

    def _sua_hoa_don(self):
        """
        Đọc dữ liệu từ 6 cột hiển thị:
            Cột 0: Số HĐ (UserRole = row_id)
            Cột 1: Tên KH | 2: Ngày tạo | 3: Ngày hạn
            Cột 4: Tổng tiền | 5: Trạng thái (ComboBox)
        """
        bang = self.ui.tbwg_hd
        dong = bang.currentRow()
        if dong < 0: return

        item0 = bang.item(dong, 0)
        if not item0: return

        row_id = item0.data(Qt.ItemDataRole.UserRole)
        if row_id is None:
            QMessageBox.warning(self, "Lỗi", "Không tìm được ID hóa đơn!")
            return

        def _cell(c):
            w = bang.cellWidget(dong, c)
            if isinstance(w, QComboBox): return w.currentText()
            it = bang.item(dong, c)
            return it.text() if it else ""

        inv_no   = _cell(0)
        customer = _cell(1)
        date     = _cell(2)
        due_date = _cell(3)
        amount   = _cell(4).replace("₫","").replace(",","").strip()
        status   = _cell(5)

        # edit_data = (row_id, inv_no, customer, date, due_date, amount, status)
        edit_data = (row_id, inv_no, customer, date, due_date, amount, status)

        dlg = TaoHoaDonDialog(self, edit_data=edit_data)
        if dlg.exec() != QDialog.DialogCode.Accepted: return

        d = dlg.get_data()
        try:
            Invoices_db.update_invoice(
                int(d["row_id"]), d["inv_no"], d["customer"],
                d["date"], d["due_date"], d["amount"], d["status"])
            self._tai_bang_hoa_don()
            QMessageBox.information(self, "Thành công",
                                    f"✅ Đã cập nhật hóa đơn #{d['inv_no']}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi cập nhật", str(e))

    # --------------------------------------------------------------------------
    #  ĐƠN ĐẶT HÀNG
    # --------------------------------------------------------------------------
    def _tai_bang_don_dat_hang(self, du_lieu=None):
        bo_loc = self.ui.cb_f_dh.currentText()
        hang   = du_lieu if du_lieu is not None else \
                 purchase_orders_db.fetch_all_purchase_orders()
        bang   = self.ui.tbwg_dh
        bang.blockSignals(True); bang.setRowCount(0)
        for r in hang:
            tt = str(r[7]).strip().lower() if r[7] else "pending"
            if bo_loc != "Tất cả" and tt != bo_loc.lower():
                continue
            dong = bang.rowCount(); bang.insertRow(dong)
            tien = f"{float(r[6]):,.0f} ₫" if r[6] else "0 ₫"
            for cot, v in enumerate([r[0],r[1],r[2],r[4],r[5],tien]):
                bang.setItem(dong, cot, self._tao_o(v))
            cb = QComboBox()
            cb.addItems(["pending","received","cancelled","partial"])
            cb.setCurrentText(tt)
            mau = self.MAU_DON_DAT.get(tt, "white")
            cb.setStyleSheet(
                f"color:{mau};background:#1e293b;border:none;font-weight:bold;")
            cb.currentTextChanged.connect(
                lambda txt, oid=r[0]:
                    purchase_orders_db.update_purchase_order_status(oid, txt))
            bang.setCellWidget(dong, 5, cb)
        bang.blockSignals(False)
        self._cap_nhat_gio(self.ui.lb_updatetime_dh)

    def _tim_don_dat_hang(self):
        kw = self.ui.lne_search_dh.text().strip()
        if kw:
            kw_lo = kw.lower()
            kq = [r for r in purchase_orders_db.fetch_all_purchase_orders()
                  if kw_lo in str(r[1]).lower()
                  or kw_lo in str(r[4]).lower()]
            self._tai_bang_don_dat_hang(du_lieu=kq)
        else:
            self._tai_bang_don_dat_hang()

    def _them_don_dat_hang(self):
        dlg = DonDatHangDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted: return
        d = dlg.get_data()
        try:
            purchase_orders_db.add_purchase_order(
                d["supplier_name"], d["order_date"], d["expected_delivery"],
                d["delivery_location"], d["product_sku"], d["product_name"],
                d["quantity"], d["unit_price"],
                d["subtotal"], d["shipping_cost"], d["total_amount"],
                d["shipping_method"], d["priority"],
                d["weight_kg"], d["notes"])
            self._tai_bang_don_dat_hang()
            QMessageBox.information(self, "Thành công",
                f"✅ Đã tạo đơn đặt hàng\n\n"
                f"NCC       : {d['supplier_name']}\n"
                f"SP        : {d['product_name']}  ×  {d['quantity']}\n"
                f"─────────────────────────\n"
                f"Tiền hàng : {d['subtotal']:,.0f} ₫\n"
                f"Phí VC    : {d['shipping_cost']:,.0f} ₫"
                f"  [{d['shipping_method']}]\n"
                f"Kho giao  : {d['delivery_location']}\n"
                f"Ưu tiên   : {d['priority']}\n"
                f"─────────────────────────\n"
                f"TỔNG CỘNG : {d['total_amount']:,.0f} ₫")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi tạo đơn hàng", str(e))

    # --------------------------------------------------------------------------
    #  TÌM KIẾM TOÀN CỤC (tự nhảy sang trang có kết quả)
    # --------------------------------------------------------------------------
    def _tim_toan_cuc(self):
        kw = self.ui.lne_search.text().strip()
        if not kw: return
        kw_lo = kw.lower()

        kq_hd  = [r for r in Invoices_db.fetch_all_invoices()
                  if kw_lo in str(r[0]).lower() or kw_lo in str(r[1]).lower()]
        kq_kh  = [r for r in customer_db.fetch_all_customers()
                  if kw_lo in str(r[1]).lower() or kw_lo in str(r[2]).lower()]
        kq_sp  = [r for r in product_db.fetch_all_products()
                  if kw_lo in str(r[0]).lower() or kw_lo in str(r[1]).lower()]
        kq_ncc = [r for r in supplier_db.fetch_all_suppliers()
                  if kw_lo in str(r[1]).lower() or kw_lo in str(r[2]).lower()]

        if kq_hd:
            self.ui.lne_search_hd.setText(kw)
            self._chuyen_trang(self.TRANG_HD, self.ui.pb_hd)
            self._tai_bang_hoa_don(du_lieu=kq_hd)
        elif kq_kh:
            self.ui.lne_search_kh.setText(kw)
            self._chuyen_trang(self.TRANG_KH, self.ui.pb_kh)
            self._tai_bang_khach_hang(du_lieu=kq_kh)
        elif kq_sp:
            self.ui.lne_search_sp.setText(kw)
            self._chuyen_trang(self.TRANG_SP, self.ui.pb_sp)
            self._tai_bang_san_pham(du_lieu=kq_sp)
        elif kq_ncc:
            self.ui.lne_search_ncc.setText(kw)
            self._chuyen_trang(self.TRANG_NCC, self.ui.pb_ncc)
            self._tai_bang_nha_cung_cap(du_lieu=kq_ncc)
        else:
            QMessageBox.information(self,"Không tìm thấy",
                                    f"Không có kết quả cho: \"{kw}\"")

# =============================================================================
if __name__ == "__main__":
    app    = QApplication(sys.argv)
    window = StockFlowApp()
    window.show()
    sys.exit(app.exec())

