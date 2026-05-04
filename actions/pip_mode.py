# pip_mode.py — Jarvis M45 Picture-in-Picture window
"""
iPhone Dynamic Island-style notch PiP with dual reactive particle clusters:
- Left cluster: reacts when Jarvis SPEAKS (green pulse, particle burst)
- Right cluster: reacts when user is LISTENING (blue pulse, faster orbit)
- Compact pill at screen top, always-on-top, draggable
"""
import math, random
from PyQt6.QtCore import (
    Qt, QPoint, QTimer, QRectF, QPointF, pyqtSignal,
)
from PyQt6.QtGui import (
    QPainter, QPainterPath, QPen, QBrush, QColor, QFont,
    QMouseEvent,
)
from PyQt6.QtWidgets import QWidget, QApplication

NOTCH_W = 280
NOTCH_H = 52

# ── colour palette ──────────────────────────────────────────────
BLUE   = QColor("#3B82F6")
GREEN  = QColor("#10B981")
PURPLE = QColor("#6366F1")
ROSE   = QColor("#FB7185")
WHITE  = QColor(255, 255, 255)
SLATE  = QColor(148, 163, 184)


class _ReactiveCluster:
    """A cluster of 8 particles orbiting a mini core that pulses on activation."""

    def __init__(self, cx: float, cy: float, base_color: QColor, active_color: QColor):
        self.cx = cx
        self.cy = cy
        self.base_color   = QColor(base_color)
        self.active_color = QColor(active_color)
        self.core_color   = QColor(base_color)
        self.tgt_core     = QColor(base_color)
        self.pulse        = 0.0          # 0–1, driven by activation
        self._active      = False
        self._tick        = 0

        self.particles = []
        for i in range(8):
            a = (i / 8) * 2 * math.pi + random.uniform(-0.15, 0.15)
            self.particles.append({
                "angle":      a,
                "base_r":     11 + random.uniform(-2, 4),
                "r":          11 + random.uniform(-2, 4),
                "size":       random.uniform(1.8, 3.2),
                "speed":      random.uniform(0.8, 1.6),
                "color":      QColor(base_color),
                "tgt_color":  QColor(base_color),
            })

    def set_active(self, active: bool):
        self._active = active

    def step(self, dt: float):
        self._tick += 1
        tgt_pulse = 1.0 if self._active else 0.0
        self.pulse += (tgt_pulse - self.pulse) * 0.09

        self.tgt_core = self.active_color if self._active else self.base_color
        cr, cg, cb = self.core_color.red(), self.core_color.green(), self.core_color.blue()
        tr, tg, tb = self.tgt_core.red(), self.tgt_core.green(), self.tgt_core.blue()
        sp = 0.12
        self.core_color = QColor(int(cr+(tr-cr)*sp), int(cg+(tg-cg)*sp), int(cb+(tb-cb)*sp))

        for p in self.particles:
            p["tgt_color"] = self.active_color if self._active else self.base_color
            # orbit speed scales with pulse
            spd = p["speed"] * (1.0 + self.pulse * 2.5)
            p["angle"] += spd * dt
            # radius expands when active
            tgt_r = p["base_r"] * (1.0 + self.pulse * 0.5)
            p["r"] += (tgt_r - p["r"]) * 0.1

            pr, pg, pb = p["color"].red(), p["color"].green(), p["color"].blue()
            ptr, ptg, ptb = p["tgt_color"].red(), p["tgt_color"].green(), p["tgt_color"].blue()
            p["color"] = QColor(int(pr+(ptr-pr)*0.08), int(pg+(ptg-pg)*0.08), int(pb+(ptb-pb)*0.08))

    def paint(self, p: QPainter):
        core_r = 5.5 + self.pulse * 3.0

        # outer glow (pulses with activation)
        for i in range(3, 0, -1):
            r = core_r * (1.2 + i * 0.45 + self.pulse * 0.3)
            a = int((15 + self.pulse * 25) / i)
            col = QColor(self.core_color); col.setAlpha(a)
            p.setBrush(QBrush(col))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(self.cx - r, self.cy - r, r * 2, r * 2))

        # particles
        for pt in self.particles:
            px = self.cx + math.cos(pt["angle"]) * pt["r"]
            py = self.cy + math.sin(pt["angle"]) * pt["r"]
            sz = pt["size"] * (1.0 + self.pulse * 0.3)
            # glow
            gl = QColor(pt["color"]); gl.setAlpha(60 + int(self.pulse * 40))
            p.setBrush(QBrush(gl))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(px - sz*1.5, py - sz*1.5, sz*3, sz*3))
            # dot
            p.setBrush(QBrush(pt["color"]))
            p.drawEllipse(QRectF(px - sz/2, py - sz/2, sz, sz))

        # core
        p.setBrush(QBrush(self.core_color.lighter(140 + int(self.pulse * 20))))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(self.cx - core_r, self.cy - core_r, core_r * 2, core_r * 2))

        # bright highlight
        p.setBrush(QBrush(QColor(255, 255, 255, 120 + int(self.pulse * 40))))
        p.drawEllipse(QRectF(self.cx - core_r*0.4, self.cy - core_r*0.5, core_r*0.8, core_r*0.8))


class PiPWindow(QWidget):
    """Compact iPhone-Dynamic-Island notch with dual reactive particle clusters."""

    closed       = pyqtSignal()
    muted_toggle = pyqtSignal()

    def __init__(self, face_path: str = "face.png", size: int = 200):
        super().__init__()
        self._muted  = False
        self._state  = "idle"
        self._drag_pos: QPoint | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setFixedSize(NOTCH_W, NOTCH_H)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - NOTCH_W) // 2, 5)

        # left cluster — Jarvis (always green)
        self._speak_cluster = _ReactiveCluster(28, NOTCH_H / 2, GREEN, GREEN)
        # right cluster — user (always blue)
        self._listen_cluster = _ReactiveCluster(NOTCH_W - 28, NOTCH_H / 2, BLUE, BLUE)

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
        # left cluster active when Jarvis is SPEAKING
        self._speak_cluster.set_active(not self._muted and self._state == "speaking")
        # right cluster active when LISTENING or user is talking
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

        # clip to pill
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, W, H), r, r)
        p.setClipPath(path)

        # glass background
        bg_alpha = 235 if self._muted else 225
        p.setBrush(QBrush(QColor(15, 23, 42, bg_alpha)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0, 0, W, H), r, r)

        # subtle border
        p.setPen(QPen(QColor(255, 255, 255, 25), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, W - 1, H - 1), r, r)

        # ── particle clusters ──
        self._speak_cluster.paint(p)
        self._listen_cluster.paint(p)

        # ── centre text ──
        label_x  = 54
        label_w  = W - 108
        tick     = self._speak_cluster._tick

        # JARVIS title
        p.setPen(QColor(255, 255, 255, 200))
        p.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        p.drawText(QRectF(label_x, 5, label_w, 18),
                   Qt.AlignmentFlag.AlignCenter, "JARVIS")

        # state line
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
        p.drawText(QRectF(label_x, 24, label_w, 14),
                   Qt.AlignmentFlag.AlignCenter, state_txt)

        # M45 subtitle
        p.setPen(QColor(148, 163, 184, 150))
        p.setFont(QFont("Courier New", 6))
        p.drawText(QRectF(label_x, 37, label_w, 11),
                   Qt.AlignmentFlag.AlignCenter, "M45")

        p.end()

    # ── dragging ──────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

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
