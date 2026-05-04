# pip_mode.py — Jarvis M45 Picture-in-Picture window
"""
Minimal round Jarvis window:
- Circular, frameless, transparent background
- Draggable anywhere on screen
- Resizable with mouse wheel or corner drag
- Shows only Jarvis face (no logs, no system stats, no panels)
- Always on top (optional)
- Hover controls: mute button, close, resize handle
"""
from PyQt6.QtCore import (
    Qt, QPoint, QSize, QTimer, QRect, pyqtSignal,
)
from PyQt6.QtGui import (
    QPainter, QPainterPath, QPen, QBrush, QColor, QPixmap,
    QFont, QMouseEvent, QWheelEvent,
)
from PyQt6.QtWidgets import (
    QWidget, QApplication, QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
)

class PiPWindow(QWidget):
    """Round, transparent, frameless Picture-in-Picture Jarvis window."""
    
    closed       = pyqtSignal()
    muted_toggle = pyqtSignal()

    def __init__(self, face_path: str = "face.png", size: int = 200):
        super().__init__()
        self._size = size
        self._muted = False
        self._drag_pos = None
        self._resizing = False
        self._state = "idle"  # idle | listening | speaking | thinking
        self._animation_angle = 0
        self._state_color = QColor("#00d4ff")  # Jarvis blue
        
        # Load face image
        self._face = QPixmap(face_path)
        if self._face.isNull():
            self._face = None
        
        # Window setup — frameless, transparent, always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        
        self.resize(size, size)
        
        # Center on screen initially
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen.width() - size) // 2,
            (screen.height() - size) // 2,
        )
        
        # State pulse timer
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse)
        self._pulse_timer.start(50)
    
    def set_state(self, state: str):
        """Update Jarvis state for visual feedback."""
        self._state = state.lower()
        colors = {
            "idle":      QColor("#00d4ff"),
            "listening": QColor("#00ff88"),
            "speaking":  QColor("#ffcc00"),
            "thinking":  QColor("#ff6b00"),
        }
        self._state_color = colors.get(self._state, QColor("#00d4ff"))
        self.update()
    
    def set_muted(self, muted: bool):
        self._muted = muted
        self.update()
    
    def _pulse(self):
        """Animate the ring glow."""
        self._animation_angle = (self._animation_angle + 2) % 360
        if self._state in ("speaking", "thinking"):
            self.update()
    
    # ── painting ────────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        r = min(w, h) // 2
        cx, cy = w // 2, h // 2
        
        # Clip to circle
        path = QPainterPath()
        path.addEllipse(cx - r, cy - r, r * 2, r * 2)
        painter.setClipPath(path)
        
        # Background — dark semi-transparent
        painter.setBrush(QColor(0, 6, 10, 220))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        
        # Face image
        if self._face and not self._face.isNull():
            scaled = self._face.scaled(
                r * 2, r * 2,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            fx = cx - scaled.width() // 2
            fy = cy - scaled.height() // 2
            painter.drawPixmap(fx, fy, scaled)
            
            # Dark overlay for muted state
            if self._muted:
                painter.setBrush(QColor(255, 51, 85, 80))
                painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        
        # State ring glow
        ring_w = max(3, r // 25)
        pen = QPen(self._state_color, ring_w)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        if self._state in ("speaking", "thinking"):
            # Animated pulsing ring
            alpha = int(120 + 80 * abs((self._animation_angle % 180) / 180 - 0.5))
            c = QColor(self._state_color)
            c.setAlpha(alpha)
            pen.setColor(c)
            pen.setWidth(ring_w + 1)
        elif self._state == "listening":
            # Steady green glow
            pen.setWidth(ring_w + 1)
        else:
            # Subtle idle ring
            c = QColor(self._state_color)
            c.setAlpha(100)
            pen.setColor(c)
        
        painter.setPen(pen)
        painter.drawEllipse(cx - r + ring_w, cy - r + ring_w,
                           r * 2 - ring_w * 2, r * 2 - ring_w * 2)
        
        # Muted indicator
        if self._muted:
            painter.setPen(QColor("#ff3355"))
            painter.setFont(QFont("Arial", r // 5, QFont.Weight.Bold))
            painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "MUTED")
        
        painter.end()
    
    # ── dragging ────────────────────────────────────────────────────
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if near edge (resize zone)
            w, h = self.width(), self.height()
            mx, my = event.position().x(), event.position().y()
            edge = 20
            if (mx < edge or mx > w - edge or my < edge or my > h - edge):
                self._resizing = True
                self._drag_start = event.globalPosition().toPoint()
                self._drag_size = self.size()
            else:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._resizing and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_start
            new_size = max(100, min(600, max(
                self._drag_size.width() + delta.x(),
                self._drag_size.height() + delta.y()
            )))
            self.resize(new_size, new_size)
        elif self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        self._resizing = False
        super().mouseReleaseEvent(event)
    
    # ── resize with scroll wheel ────────────────────────────────────
    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        new_size = max(100, min(600, self.width() + (10 if delta > 0 else -10)))
        self.resize(new_size, new_size)
        event.accept()
    
    # ── keyboard shortcuts ──────────────────────────────────────────
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.closed.emit()
            self.close()
        elif event.key() == Qt.Key.Key_M:
            self.muted_toggle.emit()
        super().keyPressEvent(event)

