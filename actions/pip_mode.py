# pip_mode.py — Jarvis M45 Picture-in-Picture window
"""
iPhone Dynamic Island-style notch PiP with dual reactive particle clusters:
- Left cluster: Jarvis (always green, pulses when speaking)
- Right cluster: user (always blue, pulses when listening)
- Compact pill at screen top below panel, always-on-top
- Mute toggle, Escape to close, double-click to restore main window
"""
import math, random
from PyQt6.QtCore import (
    Qt, QPoint, QTimer, QRectF, QPointF, pyqtSignal,
)
from PyQt6.QtGui import (
    QPainter, QPainterPath, QPen, QBrush, QColor, QFont,
    QMouseEvent, QCursor,
)
from PyQt6.QtWidgets import QWidget, QApplication

NOTCH_W = 244
NOTCH_H = 44

BLUE   = QColor("#3B82F6")
GREEN  = QColor("#10B981")
PURPLE = QColor("#6366F1")
ROSE   = QColor("#FB7185")


class _ReactiveCluster:
    """8 orbiting particles around a mini core, pulses on activation."""

    def __init__(self, cx: float, cy: float, base_color: QColor):
        self.cx = cx
        self.cy = cy
        self.base_color   = QColor(base_color)
        self.core_color   = QColor(base_color)
        self.pulse        = 0.0
        self._active      = False
        self._tick        = 0

        self.particles = []
        for i in range(8):
            a = (i / 8) * 2 * math.pi + random.uniform(-0.15, 0.15)
            self.particles.append({
                "angle": a, "base_r": 9 + random.uniform(-2, 3),
                "r": 9 + random.uniform(-2, 3),
                "size": random.uniform(1.5, 2.8),
                "speed": random.uniform(0.8, 1.6),
                "color": QColor(base_color),
            })

    def set_active(self, active: bool):
        self._active = active

    def step(self, dt: float):
        self._tick += 1
        tgt_pulse = 1.0 if self._active else 0.0
        self.pulse += (tgt_pulse - self.pulse) * 0.09

        cr, cg, cb = self.core_color.red(), self.core_color.green(), self.core_color.blue()
        br, bg, bb = self.base_color.red(), self.base_color.green(), self.base_color.blue()
        sp = 0.12
        self.core_color = QColor(int(cr+(br-cr)*sp), int(cg+(bg-cg)*sp), int(cb+(bb-cb)*sp))

        for p in self.particles:
            spd = p["speed"] * (1.0 + self.pulse * 2.5)
            p["angle"] += spd * dt
            tgt_r = p["base_r"] * (1.0 + self.pulse * 0.5)
            p["r"] += (tgt_r - p["r"]) * 0.1

    def paint(self, p: QPainter):
        core_r = 4.5 + self.pulse * 2.5

        for i in range(3, 0, -1):
            r = core_r * (1.2 + i * 0.4 + self.pulse * 0.25)
            a = int((12 + self.pulse * 20) / i)
            col = QColor(self.core_color); col.setAlpha(a)
            p.setBrush(QBrush(col))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(self.cx - r, self.cy - r, r * 2, r * 2))

        for pt in self.particles:
            px = self.cx + math.cos(pt["angle"]) * pt["r"]
            py = self.cy + math.sin(pt["angle"]) * pt["r"]
            sz = pt["size"] * (1.0 + self.pulse * 0.3)
            gl = QColor(pt["color"]); gl.setAlpha(50 + int(self.pulse * 35))
            p.setBrush(QBrush(gl))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(px - sz*1.3, py - sz*1.3, sz*2.6, sz*2.6))
            p.setBrush(QBrush(pt["color"]))
            p.drawEllipse(QRectF(px - sz/2, py - sz/2, sz, sz))

        p.setBrush(QBrush(self.core_color.lighter(140 + int(self.pulse * 20))))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(self.cx - core_r, self.cy - core_r, core_r * 2, core_r * 2))
        p.setBrush(QBrush(QColor(255, 255, 255, 120 + int(self.pulse * 40))))
        p.drawEllipse(QRectF(self.cx - core_r*0.4, self.cy - core_r*0.45, core_r*0.8, core_r*0.8))


class PiPWindow(QWidget):
    """Compact always-on-top notch with dual particle clusters + mute button."""

    closed       = pyqtSignal()
    muted_toggle = pyqtSignal()

    def __init__(self, face_path: str = "face.png", size: int = 200):
        super().__init__()
        self._muted  = False
        self._state  = "idle"
        self._drag_pos: QPoint | None = None
        self._hover_mute = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        self.setFixedSize(NOTCH_W, NOTCH_H)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - NOTCH_W) // 2, 32)

        self._speak_cluster = _ReactiveCluster(26, NOTCH_H / 2, GREEN)
        self._listen_cluster = _ReactiveCluster(NOTCH_W - 58, NOTCH_H / 2, BLUE)

        self.setMouseTracking(True)
        self._tmr = QTimer(self)
        self._tmr.timeout.connect(self._step)
        self._tmr.start(16)

    # ── public API ─────────────────────────────────────────────────

    def set_state(self, state: str):
        self._state = state.lower()
        self.update()

    def set_muted(self, muted: bool):
        self._muted = muted
        self.update()

    # ── animation ──────────────────────────────────────────────────

    def _step(self):
        dt = 0.016
        self._speak_cluster.set_active(not self._muted and self._state == "speaking")
        self._listen_cluster.set_active(not self._muted and self._state == "listening")
        self._speak_cluster.step(dt)
        self._listen_cluster.step(dt)
        self.update()

    # ── painting ───────────────────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        r = H / 2

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, W, H), r, r)
        p.setClipPath(path)

        # glass background
        bg_alpha = 240 if self._muted else 228
        p.setBrush(QBrush(QColor(15, 23, 42, bg_alpha)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0, 0, W, H), r, r)

        # border
        p.setPen(QPen(QColor(255, 255, 255, 28), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, W - 1, H - 1), r, r)

        # particle clusters
        self._speak_cluster.paint(p)
        self._listen_cluster.paint(p)

        # centre text
        label_x = 52
        label_w = W - 104
        tick = self._speak_cluster._tick

        p.setPen(QColor(255, 255, 255, 210))
        p.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        p.drawText(QRectF(label_x, 2, label_w, 15),
                   Qt.AlignmentFlag.AlignCenter, "JARVIS")

        if self._muted:
            state_txt, st_col = "MUTED", ROSE
        elif self._state == "speaking":
            state_txt, st_col = "SPEAKING", GREEN
        elif self._state == "listening":
            dot = "●" if (tick % 50 < 25) else "○"
            state_txt, st_col = f"{dot} LISTENING", BLUE
        elif self._state in ("thinking", "processing"):
            sym = "◈" if (tick % 50 < 25) else "◇"
            state_txt, st_col = f"{sym} THINKING", PURPLE
        else:
            state_txt, st_col = self._state.upper(), BLUE

        p.setPen(st_col)
        p.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        p.drawText(QRectF(label_x, 17, label_w, 12),
                   Qt.AlignmentFlag.AlignCenter, state_txt)

        # M45 + mute mic on same row, centred
        mute_icon = "🔇" if self._muted else "🎤"
        mute_col  = ROSE if self._muted else QColor(255, 255, 255, 150 if not self._hover_mute else 220)
        p.setPen(QColor(148, 163, 184, 140))
        p.setFont(QFont("Courier New", 6))
        p.drawText(QRectF(label_x, 29, label_w, 13),
                   Qt.AlignmentFlag.AlignCenter, f"M45  {mute_icon}")
        # highlight mic when hovered
        if self._hover_mute:
            p.setPen(mute_col)
            p.drawText(QRectF(label_x, 29, label_w, 13),
                       Qt.AlignmentFlag.AlignCenter, f"M45  {mute_icon}")

        # Store mute click zone (right half of bottom row)
        self._mute_zone = QRectF(label_x + label_w * 0.5, 28, label_w * 0.5, 14)
        p.end()

    # ── mouse ──────────────────────────────────────────────────────

    def _mute_rect(self):
        if hasattr(self, '_mute_zone'):
            return self._mute_zone
        # fallback
        return QRectF(self.width() * 0.5, 28, self.width() * 0.35, 14)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            if self._mute_rect().contains(pos):
                self.muted_toggle.emit()
                return
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            return
        pos = event.position()
        over = self._mute_rect().contains(pos)
        if over != self._hover_mute:
            self._hover_mute = over
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor if over else Qt.CursorShape.ArrowCursor))
            self.update()

    def mouseReleaseEvent(self, _):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, _):
        self.closed.emit()
        self.close()

    # ── keyboard ──────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.closed.emit()
            self.close()
        elif event.key() == Qt.Key.Key_M:
            self.muted_toggle.emit()
        super().keyPressEvent(event)
