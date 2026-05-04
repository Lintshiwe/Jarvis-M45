# pip_mode.py — Jarvis M45 Picture-in-Picture window
"""
iPhone Dynamic Island-style notch PiP window:
- Horizontal pill shape positioned at screen top centre
- Animated particle core with orbiting micro-particles
- State-aware colour transitions
- Draggable, always-on-top, frameless
- Escape to close | M to toggle mute | Click to restore main window
"""
import math, random, time
from PyQt6.QtCore import (
    Qt, QPoint, QSize, QTimer, QRect, QRectF, QPointF, pyqtSignal,
)
from PyQt6.QtGui import (
    QPainter, QPainterPath, QPen, QBrush, QColor, QFont,
    QMouseEvent, QWheelEvent, QLinearGradient,
)
from PyQt6.QtWidgets import QWidget, QApplication

NOTCH_W = 380
NOTCH_H = 72

class _NotchParticles:
    """Mini particle system for the PiP notch."""
    def __init__(self):
        self.num = 10
        self.particles = []
        self.core_color = QColor("#3B82F6")
        self.tgt_core = QColor("#3B82F6")
        self._tick = 0
        for i in range(self.num):
            a = (i / self.num) * 2 * math.pi + random.uniform(-0.2, 0.2)
            self.particles.append({
                "angle": a,
                "radius": 16 + random.uniform(-3, 5),
                "size": random.uniform(2.0, 3.5),
                "speed": random.uniform(0.6, 1.3),
                "color": QColor("#3B82F6"),
                "tgt_color": QColor("#3B82F6"),
            })

    def set_state(self, state: str, muted: bool):
        if muted:
            c = QColor("#FB7185")
        elif state == "speaking":
            c = QColor("#10B981")
        elif state == "listening":
            c = QColor("#3B82F6")
        elif state in ("thinking", "processing"):
            c = QColor("#6366F1")
        else:
            c = QColor("#3B82F6")
        self.tgt_core = c
        for p in self.particles:
            p["tgt_color"] = c

    def step(self, dt: float):
        self._tick += 1
        cr = self.core_color.red();    cg = self.core_color.green();    cb = self.core_color.blue()
        tr = self.tgt_core.red();       tg = self.tgt_core.green();       tb = self.tgt_core.blue()
        sp = 0.09
        self.core_color = QColor(int(cr+(tr-cr)*sp), int(cg+(tg-cg)*sp), int(cb+(tb-cb)*sp))

        for p in self.particles:
            p["angle"] += p["speed"] * dt
            pr, pg, pb = p["color"].red(), p["color"].green(), p["color"].blue()
            ptr, ptg, ptb = p["tgt_color"].red(), p["tgt_color"].green(), p["tgt_color"].blue()
            p["color"] = QColor(int(pr+(ptr-pr)*0.06), int(pg+(ptg-pg)*0.06), int(pb+(ptb-pb)*0.06))

    def paint(self, painter: QPainter, cx: float, cy: float):
        core_r = 8.0
        # outer glow
        for i in range(3, 0, -1):
            r = core_r * (1.0 + i * 0.4)
            a = int(30 / i)
            col = QColor(self.core_color); col.setAlpha(a)
            painter.setBrush(QBrush(col))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
        # orbiting particles
        for p in self.particles:
            px = cx + math.cos(p["angle"]) * p["radius"]
            py = cy + math.sin(p["angle"]) * p["radius"]
            sz = p["size"]
            gl = QColor(p["color"]); gl.setAlpha(50)
            painter.setBrush(QBrush(gl))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(px - sz, py - sz, sz * 2, sz * 2))
            painter.setBrush(QBrush(p["color"]))
            painter.drawEllipse(QRectF(px - sz/2, py - sz/2, sz, sz))
        # core
        painter.setBrush(QBrush(self.core_color.lighter(140)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - core_r, cy - core_r, core_r * 2, core_r * 2))
        # bright spot
        painter.setBrush(QBrush(QColor(255, 255, 255, 130)))
        painter.drawEllipse(QRectF(cx - core_r*0.45, cy - core_r*0.5, core_r*0.9, core_r*0.9))


class PiPWindow(QWidget):
    """iPhone Dynamic Island-style notch PiP with animated particles."""

    closed       = pyqtSignal()
    muted_toggle = pyqtSignal()

    def __init__(self, face_path: str = "face.png", size: int = 200):
        super().__init__()
        self._muted  = False
        self._state  = "idle"
        self._drag_pos: QPoint | None = None

        # window — frameless pill, always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setFixedSize(NOTCH_W, NOTCH_H)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - NOTCH_W) // 2, 6)

        self._particles = _NotchParticles()

        self._tmr = QTimer(self)
        self._tmr.timeout.connect(self._step)
        self._tmr.start(16)

    # ── public API (compatible with old PiPWindow) ──────────────────

    def set_state(self, state: str):
        self._state = state.lower()
        self._particles.set_state(self._state, self._muted)
        self.update()

    def set_muted(self, muted: bool):
        self._muted = muted
        self._particles.set_state(self._state, self._muted)
        self.update()

    # ── animation ───────────────────────────────────────────────────

    def _step(self):
        self._particles.step(0.016)
        if self._state in ("speaking", "thinking"):
            self.update()

    # ── painting ────────────────────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        r = H / 2  # corner radius for pill

        # clip to pill
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, W, H), r, r)
        p.setClipPath(path)

        # background — glass effect
        bg = QColor(15, 23, 42, 225) if self._muted else QColor(15, 23, 42, 215)
        p.setBrush(QBrush(bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0, 0, W, H), r, r)

        # subtle border
        border_col = QColor(255, 255, 255, 30)
        pen = QPen(border_col, 1)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, W - 1, H - 1), r, r)

        # ── left: particle core ──
        core_cx = 22 + 20   # offset from left
        core_cy = H / 2
        self._particles.paint(p, core_cx, core_cy)

        # ── centre: label + state ──
        text_x = 65
        text_w = W - text_x - 65

        p.setPen(QColor(255, 255, 255, 220))
        p.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        p.drawText(QRectF(text_x, 8, text_w, 22),
                   Qt.AlignmentFlag.AlignCenter, "JARVIS")

        # state label
        if self._muted:
            state_txt, st_col = "MUTED", QColor("#FB7185")
        elif self._state == "speaking":
            state_txt, st_col = "SPEAKING", QColor("#10B981")
        elif self._state == "listening":
            dot = "●" if (self._particles._tick % 50 < 25) else "○"
            state_txt, st_col = f"{dot} LISTENING", QColor("#3B82F6")
        elif self._state in ("thinking", "processing"):
            sym = "◈" if (self._particles._tick % 50 < 25) else "◇"
            state_txt, st_col = f"{sym} THINKING", QColor("#6366F1")
        else:
            state_txt, st_col = self._state.upper(), QColor("#3B82F6")

        p.setPen(st_col)
        p.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        p.drawText(QRectF(text_x, 32, text_w, 18),
                   Qt.AlignmentFlag.AlignCenter, state_txt)

        # subtitle
        p.setPen(QColor(148, 163, 184, 180))
        p.setFont(QFont("Courier New", 7))
        p.drawText(QRectF(text_x, 50, text_w, 14),
                   Qt.AlignmentFlag.AlignCenter, "M45")

        # ── right: mini waveform ──
        if not self._muted and self._state == "speaking":
            wx0 = W - 55
            wy0 = 22
            for i in range(8):
                hgt = random.randint(3, 18)
                clr = QColor("#10B981") if hgt > 10 else QColor("#34D399")
                p.fillRect(QRectF(wx0 + i * 5, wy0 + 20 - hgt, 3, hgt), clr)

        p.end()

    # ── dragging ────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, _):
        """Double-click restores main window."""
        self.closed.emit()
        self.close()

    # ── keyboard ────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.closed.emit()
            self.close()
        elif event.key() == Qt.Key.Key_M:
            self.muted_toggle.emit()
        super().keyPressEvent(event)
