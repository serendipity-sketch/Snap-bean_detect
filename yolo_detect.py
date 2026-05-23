import sys
import os
import warnings

os.environ["NUMPY_EXPERIMENTAL_ARRAY_API"] = "0"
os.environ["PYTHONWARNINGS"] = "ignore::UserWarning"
warnings.filterwarnings('ignore')

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMainWindow, QMessageBox,
    QStackedWidget, QDialog, QFormLayout, QFrame,
    QTextEdit, QFileDialog, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap, QImage, QColor, QIcon, QDesktopServices, QPainter
from PyQt5.QtCore import Qt, QTimer, QSize, QUrl

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView

    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    print("提示: 未检测到 PyQtWebEngine，百科将仅支持外部跳转。建议安装: pip install PyQtWebEngine")

try:
    import cv2
    from ultralytics import YOLO

    if not hasattr(cv2, 'imshow'):
        cv2.imshow = lambda *args, **kwargs: None
    cv2.imwrite = cv2.imwrite
except ImportError:
    print("错误: 缺少 cv2 或 ultralytics 库，请安装：pip install opencv-python ultralytics")
    sys.exit(1)

STYLESHEET = """
QWidget {
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
    font-size: 14px;
    color: #333333;
    background-color: #F0F2F5;
}
/* 侧边栏背景 */
QFrame#Sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #E0E0E0;
}
/* 标题样式 */
QLabel#Title {
    font-size: 26px;
    font-weight: 900;
    color: #2E7D32;
    margin-bottom: 10px;
}
QLabel#SubTitle {
    font-size: 14px;
    color: #666666;
}
QLabel#SectionTitle {
    font-size: 16px;
    font-weight: bold;
    color: #333;
    padding-left: 5px;
    border-left: 4px solid #2E7D32;
}
/* 输入框 */
QLineEdit {
    border: 1px solid #CCCCCC;
    border-radius: 6px;
    padding: 10px 12px;
    background-color: #FFFFFF;
    font-size: 14px;
}
QLineEdit:focus {
    border: 1px solid #2E7D32;
    background-color: #FAFFFA;
}
/* 按钮通用 */
QPushButton {
    background-color: #2E7D32;
    color: white;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
    border: none;
}
QPushButton:hover {
    background-color: #388E3C;
}
QPushButton:pressed {
    background-color: #1B5E20;
    padding-top: 12px;
    padding-bottom: 8px;
}
QPushButton:disabled {
    background-color: #BDBDBD;
    color: #F0F0F0;
}
/* 次要按钮 */
QPushButton#SecondaryBtn {
    background-color: #FFFFFF;
    color: #555555;
    border: 1px solid #CCCCCC;
}
QPushButton#SecondaryBtn:hover {
    background-color: #F5F5F5;
    border-color: #999999;
}
/* 危险按钮 */
QPushButton#DangerBtn {
    background-color: #D32F2F;
}
QPushButton#DangerBtn:hover {
    background-color: #E53935;
}
/* 卡片 */
QFrame#Card {
    background-color: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E0E0E0;
}
/* 文本框 */
QTextEdit {
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    background-color: #FAFAFA;
    font-family: "Consolas", monospace;
    font-size: 12px;
    line-height: 150%;
}
"""


#用户数据管理
class UserManager:
    def __init__(self):
        self.users = {"admin": "123456"}  # 默认账号

    def register(self, username, password):
        if username in self.users: return False, "用户已存在"
        if len(username) < 4 or len(password) < 6: return False, "账号至少4位，密码至少6位"
        self.users[username] = password
        return True, "注册成功"

    def login(self, username, password):
        if username in self.users and self.users[username] == password: return True, "登录成功"
        return False, "账号或密码错误"


USER_DB = UserManager()

def add_shadow(widget, blur=15):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, 50))
    shadow.setOffset(0, 4)
    widget.setGraphicsEffect(shadow)



class RegisterDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("注册新用户")
        self.setFixedSize(380, 360)  # 修正尺寸
        self.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        title = QLabel("创建账号")
        title.setObjectName("SectionTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("margin-bottom: 10px;")

        self.user_in = QLineEdit()
        self.user_in.setPlaceholderText("设置账号 (至少4位)")
        self.user_in.setMinimumHeight(40)

        self.pwd_in = QLineEdit()
        self.pwd_in.setPlaceholderText("设置密码 (至少6位)")
        self.pwd_in.setEchoMode(QLineEdit.Password)
        self.pwd_in.setMinimumHeight(40)

        self.pwd_confirm = QLineEdit()
        self.pwd_confirm.setPlaceholderText("确认密码")
        self.pwd_confirm.setEchoMode(QLineEdit.Password)
        self.pwd_confirm.setMinimumHeight(40)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(15)

        btn_reg = QPushButton("确认注册")
        btn_reg.setCursor(Qt.PointingHandCursor)
        btn_reg.setMinimumHeight(40)
        btn_reg.clicked.connect(self.do_register)

        btn_cancel = QPushButton("取消")
        btn_cancel.setObjectName("SecondaryBtn")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setMinimumHeight(40)
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(btn_reg)
        btn_box.addWidget(btn_cancel)

        layout.addWidget(title)
        layout.addWidget(self.user_in)
        layout.addWidget(self.pwd_in)
        layout.addWidget(self.pwd_confirm)
        layout.addStretch()
        layout.addLayout(btn_box)
        self.setLayout(layout)

    def do_register(self):
        u = self.user_in.text()
        p = self.pwd_in.text()
        pc = self.pwd_confirm.text()
        if p != pc:
            QMessageBox.warning(self, "错误", "两次输入的密码不一致")
            return
        success, msg = USER_DB.register(u, p)
        if success:
            QMessageBox.information(self, "成功", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "失败", msg)


class LoginWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.bg_image_path = "油豆角背景.png"
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedSize(450, 500)
        add_shadow(card)

        layout = QVBoxLayout()
        layout.setContentsMargins(50, 60, 50, 60)
        layout.setSpacing(20)

        title = QLabel("智慧农业监测系统")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("油豆角叶片病害智能识别终端")
        subtitle.setObjectName("SubTitle")
        subtitle.setAlignment(Qt.AlignCenter)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("请输入账号")
        self.user_input.setMinimumHeight(45)

        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("请输入密码")
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setMinimumHeight(45)

        btn_login = QPushButton("立即登录")
        btn_login.setMinimumHeight(50)
        btn_login.setStyleSheet("font-size: 16px;")
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.clicked.connect(self.handle_login)

        btn_reg = QPushButton("注册新账号")
        btn_reg.setObjectName("SecondaryBtn")
        btn_reg.setMinimumHeight(50)
        btn_reg.setCursor(Qt.PointingHandCursor)
        btn_reg.clicked.connect(self.handle_register)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(30)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pwd_input)
        layout.addSpacing(10)
        layout.addWidget(btn_login)
        layout.addWidget(btn_reg)
        layout.addStretch()

        card.setLayout(layout)
        main_layout.addWidget(card)
        self.setLayout(main_layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        if os.path.exists(self.bg_image_path):
            pixmap = QPixmap(self.bg_image_path)
            painter.drawPixmap(0, 0, self.width(), self.height(), pixmap)
        else:
            # 默认背景色
            painter.fillRect(self.rect(), QColor("#F0F2F5"))

    def handle_login(self):
        u = self.user_input.text()
        p = self.pwd_input.text()
        success, msg = USER_DB.login(u, p)
        if success:
            self.stacked_widget.setCurrentIndex(1)
            self.pwd_input.clear()
        else:
            QMessageBox.warning(self, "登录失败", msg)

    def handle_register(self):
        RegisterDialog(self).exec_()


class BaikeWindow(QWidget):
    """百科窗口"""

    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.url_str = "https://baike.baidu.com/item/油豆角"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #DDD;")
        toolbar.setFixedHeight(60)
        add_shadow(toolbar, blur=5)

        tb_layout = QHBoxLayout()
        tb_layout.setContentsMargins(20, 0, 20, 0)

        btn_back = QPushButton("⬅ 返回菜单")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.setFixedWidth(120)
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        lbl_title = QLabel("📚 油豆角 - 百度百科")
        lbl_title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        lbl_title.setAlignment(Qt.AlignCenter)

        btn_external = QPushButton("在浏览器打开 🌏")
        btn_external.setFixedWidth(140)
        btn_external.clicked.connect(self.open_external)

        tb_layout.addWidget(btn_back)
        tb_layout.addStretch()
        tb_layout.addWidget(lbl_title)
        tb_layout.addStretch()
        tb_layout.addWidget(btn_external)
        toolbar.setLayout(tb_layout)

        layout.addWidget(toolbar)

        # 浏览器部分
        if HAS_WEBENGINE:
            self.browser = QWebEngineView()
            self.browser.setUrl(QUrl(self.url_str))
            layout.addWidget(self.browser)
        else:
            no_web = QLabel("提示: 未检测到 PyQtWebEngine。\n请点击右上角按钮跳转外部浏览器查看。")
            no_web.setAlignment(Qt.AlignCenter)
            no_web.setStyleSheet("font-size: 16px; color: #666;")
            layout.addWidget(no_web)

        self.setLayout(layout)

    def open_external(self):
        QDesktopServices.openUrl(QUrl(self.url_str))


class FunctionChoiceWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(40)

        header = QLabel("请选择工作模式")
        header.setObjectName("Title")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)

        def create_card(title, desc, icon_text, target_index):
            btn = QPushButton()
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setMaximumSize(350, 400)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #E0E0E0;
                    border-radius: 15px;
                    text-align: center;
                }
                QPushButton:hover {
                    border: 2px solid #2E7D32;
                    background-color: #F6FBF6;
                    margin-top: -5px;
                }
            """)
            add_shadow(btn, blur=10)
            inner_layout = QVBoxLayout(btn)
            inner_layout.setContentsMargins(20, 20, 20, 20)

            lbl_icon = QLabel(icon_text)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet("font-size: 60px; background: transparent;")

            lbl_title = QLabel(title)
            lbl_title.setAlignment(Qt.AlignCenter)
            lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333; background: transparent;")

            lbl_desc = QLabel(desc)
            lbl_desc.setAlignment(Qt.AlignCenter)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("font-size: 14px; color: #777; background: transparent;")

            inner_layout.addStretch()
            inner_layout.addWidget(lbl_icon)
            inner_layout.addSpacing(15)
            inner_layout.addWidget(lbl_title)
            inner_layout.addSpacing(10)
            inner_layout.addWidget(lbl_desc)
            inner_layout.addStretch()

            btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(target_index))
            return btn

        cards_layout.addStretch()
        cards_layout.addWidget(create_card("实时检测", "连接摄像头\n实时识别叶片病害", "📹", 2))
        cards_layout.addWidget(create_card("本地检测", "导入本地图片\n进行精确分析", "🖼️", 3))
        cards_layout.addWidget(create_card("百科知识", "查看油豆角\n生长特性与简介", "📚", 4))
        cards_layout.addStretch()

        layout.addLayout(cards_layout)

        btn_logout = QPushButton("退出登录")
        btn_logout.setObjectName("SecondaryBtn")
        btn_logout.setFixedWidth(120)
        btn_logout.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(btn_logout, 0, Qt.AlignCenter)
        self.setLayout(layout)


class RealTimeWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.model = None
        self.timer = QTimer()
        self.cap = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(300)

        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(20, 30, 20, 30)
        side_layout.setSpacing(15)

        title = QLabel("🎥 实时监测")
        title.setObjectName("SectionTitle")
        side_layout.addWidget(title)
        side_layout.addSpacing(10)

        self.btn_load = QPushButton("加载模型权重")
        self.btn_load.clicked.connect(self.load_model)

        self.btn_start = QPushButton("开启摄像头")
        self.btn_start.clicked.connect(self.start_camera)

        self.btn_stop = QPushButton("停止检测")
        self.btn_stop.setObjectName("DangerBtn")
        self.btn_stop.clicked.connect(self.stop_camera)

        self.btn_snap = QPushButton("截图保存")
        self.btn_snap.setObjectName("SecondaryBtn")
        self.btn_snap.clicked.connect(self.save_frame)

        side_layout.addSpacing(20)
        side_layout.addWidget(QLabel("系统日志:"))
        self.log_box = QTextEdit()

        btn_back = QPushButton("返回主页")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.clicked.connect(self.back)

        side_layout.addWidget(self.btn_load)
        side_layout.addWidget(self.btn_start)
        side_layout.addWidget(self.btn_stop)
        side_layout.addWidget(self.btn_snap)
        side_layout.addWidget(self.log_box)
        side_layout.addStretch()
        side_layout.addWidget(btn_back)

        sidebar.setLayout(side_layout)

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.video_label = QLabel("摄像头未开启")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000; color: #FFF; border-radius: 8px;")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        content_layout.addWidget(self.video_label)
        content.setLayout(content_layout)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)
        self.setLayout(main_layout)

    def back(self):
        self.stop_camera()
        self.stacked_widget.setCurrentIndex(1)

    def load_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择YOLO模型", filter="*.pt")
        if path:
            try:
                self.model = YOLO(path)
                self.log_box.append(f"成功加载模型: {os.path.basename(path)}")
            except Exception as e:
                self.log_box.append(f"加载失败: {str(e)}")

    def start_camera(self):
        if not self.model:
            QMessageBox.warning(self, "提示", "请先加载模型权重！")
            return
        self.cap = cv2.VideoCapture(0)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        self.btn_start.setEnabled(False)
        self.log_box.append("摄像头已启动...")

    def stop_camera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.video_label.clear()
        self.video_label.setText("摄像头已关闭")
        self.btn_start.setEnabled(True)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.frame = frame
            results = self.model(frame)
            annotated = results[0].plot()
            rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            h, w, c = rgb.shape
            qimg = QImage(rgb.data, w, h, c * w, QImage.Format_RGB888)
            if self.video_label.width() > 10:
                pix = QPixmap.fromImage(qimg).scaled(self.video_label.size(), Qt.KeepAspectRatio,
                                                     Qt.SmoothTransformation)
                self.video_label.setPixmap(pix)
            if len(results[0].boxes) > 0:
                text = f"检测到 {len(results[0].boxes)} 个目标"
                cursor = self.log_box.textCursor()
                cursor.movePosition(cursor.End)
                cursor.insertText(text + "\n")
                self.log_box.setTextCursor(cursor)

    def save_frame(self):
        if hasattr(self, 'frame') and self.frame is not None:
            cv2.imwrite("snapshot.jpg", self.frame)
            QMessageBox.information(self, "成功", "已保存 snapshot.jpg")


class LocalWindow(QWidget):
    """本地检测"""

    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.img_list = []
        self.cur_idx = -1
        self.model = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(300)

        sl = QVBoxLayout()
        sl.setContentsMargins(20, 30, 20, 30)
        sl.setSpacing(12)

        sl.addWidget(QLabel("🖼️ 本地分析", objectName="SectionTitle"))

        self.btn_model = QPushButton("1. 加载模型")
        self.btn_model.clicked.connect(self.load_model)

        self.btn_imgs = QPushButton("2. 导入图片")
        self.btn_imgs.clicked.connect(self.load_images)

        self.btn_detect = QPushButton("3. 开始检测")
        self.btn_detect.clicked.connect(self.detect)

        self.btn_del = QPushButton("删除当前图")
        self.btn_del.setObjectName("DangerBtn")
        self.btn_del.clicked.connect(self.delete_img)

        nav_box = QHBoxLayout()
        self.btn_prev = QPushButton("上一张")
        self.btn_prev.setObjectName("SecondaryBtn")
        self.btn_prev.clicked.connect(self.prev_img)

        self.btn_next = QPushButton("下一张")
        self.btn_next.setObjectName("SecondaryBtn")
        self.btn_next.clicked.connect(self.next_img)
        nav_box.addWidget(self.btn_prev)
        nav_box.addWidget(self.btn_next)

        self.file_label = QLabel("未加载文件")
        self.file_label.setWordWrap(True)
        self.file_label.setAlignment(Qt.AlignCenter)

        btn_back = QPushButton("返回")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        sl.addWidget(self.btn_model)
        sl.addWidget(self.btn_imgs)
        sl.addWidget(self.btn_detect)
        sl.addWidget(self.btn_del)
        sl.addLayout(nav_box)
        sl.addWidget(self.file_label)
        sl.addWidget(QLabel("检测结果:"))

        self.res_box = QTextEdit()
        sl.addWidget(self.res_box)
        sl.addStretch()
        sl.addWidget(btn_back)
        sidebar.setLayout(sl)

        content = QWidget()
        cl = QVBoxLayout()
        cl.setContentsMargins(20, 20, 20, 20)

        self.img_display = QLabel("请导入图片")
        self.img_display.setAlignment(Qt.AlignCenter)
        self.img_display.setStyleSheet("background-color: #E0E0E0; border-radius: 8px; border: 2px dashed #AAA;")
        # 核心：防止图片撑大窗口
        self.img_display.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.img_display.setScaledContents(False)

        cl.addWidget(self.img_display)
        content.setLayout(cl)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)
        self.setLayout(main_layout)

    def load_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择模型", filter="*.pt")
        if path:
            self.model = YOLO(path)
            QMessageBox.information(self, "成功", "模型加载完成")

    def load_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择图片", filter="*.jpg *.png *.jpeg")
        if paths:
            self.img_list = paths
            self.cur_idx = 0
            self.show_img()

    def delete_img(self):
        if not self.img_list:
            QMessageBox.warning(self, "提示", "列表为空，无需删除")
            return
        del self.img_list[self.cur_idx]
        if not self.img_list:
            self.cur_idx = -1
            self.img_display.clear()
            self.img_display.setText("请导入图片")
            self.file_label.setText("未加载文件")
            self.res_box.clear()
        else:
            if self.cur_idx >= len(self.img_list):
                self.cur_idx = len(self.img_list) - 1
            self.show_img()
            self.res_box.clear()

    def show_img(self, img=None):
        if not self.img_list: return
        path = self.img_list[self.cur_idx]
        self.file_label.setText(f"[{self.cur_idx + 1}/{len(self.img_list)}]\n{os.path.basename(path)}")
        if img is None:
            if not os.path.exists(path):
                self.img_display.setText("文件丢失")
                return
            img = cv2.imread(path)
        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, c = img.shape
            qimg = QImage(img.data, w, h, c * w, QImage.Format_RGB888)
            target_size = self.img_display.size()
            if target_size.width() < 10 or target_size.height() < 10: return
            pix = QPixmap.fromImage(qimg).scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_display.setPixmap(pix)

    def detect(self):
        if not self.model:
            QMessageBox.warning(self, "提示", "请先加载模型")
            return
        if not self.img_list:
            QMessageBox.warning(self, "提示", "请先导入图片")
            return
        img = cv2.imread(self.img_list[self.cur_idx])
        results = self.model(img)
        annotated = results[0].plot()
        text = ""
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            name = results[0].names[cls_id]
            text += f"{name}: {conf:.2f}\n"
        self.res_box.setText(text if text else "未检测到目标")
        self.show_img(annotated)

    def prev_img(self):
        if self.cur_idx > 0:
            self.cur_idx -= 1
            self.res_box.clear()
            self.show_img()

    def next_img(self):
        if self.cur_idx < len(self.img_list) - 1:
            self.cur_idx += 1
            self.res_box.clear()
            self.show_img()

    def resizeEvent(self, event):
        if self.cur_idx >= 0 and self.img_list:
            self.show_img()
        super().resizeEvent(event)


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("油豆角叶片病害识别检测系统")
        self.resize(1280, 800)
        self.setStyleSheet(STYLESHEET)

        self.stacked_widget = QStackedWidget()

        self.page_login = LoginWindow(self.stacked_widget)
        self.page_choice = FunctionChoiceWindow(self.stacked_widget)
        self.page_realtime = RealTimeWindow(self.stacked_widget)
        self.page_local = LocalWindow(self.stacked_widget)
        self.page_baike = BaikeWindow(self.stacked_widget)

        self.stacked_widget.addWidget(self.page_login)  # 0
        self.stacked_widget.addWidget(self.page_choice)  # 1
        self.stacked_widget.addWidget(self.page_realtime)  # 2
        self.stacked_widget.addWidget(self.page_local)  # 3
        self.stacked_widget.addWidget(self.page_baike)  # 4

        self.setCentralWidget(self.stacked_widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())