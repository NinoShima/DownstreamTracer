# DownstreamTracer - Simple downstream selection tool for QGIS
# How to work: Click a line, start from the clicked position, and select all reachable and interested points following downstream.

from qgis.core import (
    QgsProject, QgsGeometry, QgsPointXY, QgsSpatialIndex, QgsWkbTypes
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog, QComboBox, QLabel, QPushButton, QFormLayout, QHBoxLayout, QMessageBox
from qgis.gui import QgsMapTool

# Select layers
def get_layers_by_geom(geom_type):
    return [lyr for lyr in QgsProject.instance().mapLayers().values()
            if lyr.type() == lyr.VectorLayer and QgsWkbTypes.geometryType(lyr.wkbType()) == geom_type]

class TracerDialog(QDialog):
    def __init__(self):
        super().__init__(None)
        self.setWindowTitle("DownstreamTracer - Select Layers")
        self.setMinimumWidth(300)
        self.lineCombo = QComboBox()
        self.pointCombo = QComboBox()
        self.line_layers = get_layers_by_geom(QgsWkbTypes.LineGeometry)
        self.point_layers = get_layers_by_geom(QgsWkbTypes.PointGeometry)

        for lyr in self.line_layers:
            self.lineCombo.addItem(lyr.name())
        for lyr in self.point_layers:
            self.pointCombo.addItem(lyr.name())

        form = QFormLayout()
        form.addRow(QLabel("Line layer:"), self.lineCombo)
        form.addRow(QLabel("Point layer:"), self.pointCombo)

        btnStart = QPushButton("Start")
        btnCancel = QPushButton("Cancel")
        btns = QHBoxLayout()
        btns.addWidget(btnStart)
        btns.addWidget(btnCancel)
        form.addRow(btns)

        self.setLayout(form)
        btnStart.clicked.connect(self.accept)
        btnCancel.clicked.connect(self.reject)

    def selected_layers(self):
        if not self.line_layers or not self.point_layers:
            return None, None
        return self.line_layers[self.lineCombo.currentIndex()], self.point_layers[self.pointCombo.currentIndex()]

# Helper
def get_line_points(geom):
    if geom.isMultipart():
        lines = geom.asMultiPolyline()
        return lines[0] if lines else []
    return geom.asPolyline() or []

def nearest_segment_index(points, pt):
    qgeom = QgsGeometry.fromPointXY(pt)
    best_i, best_d = None, float("inf")
    for i in range(len(points) - 1):
        seg = QgsGeometry.fromPolylineXY([points[i], points[i+1]])
        d = qgeom.distance(seg)
        if d < best_d:
            best_d, best_i = d, i
    return best_i

# Tracing tool
class DownstreamTracer(QgsMapTool):
    def __init__(self, canvas, line_layer, point_layer):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)
        self.line_layer = line_layer
        self.point_layer = point_layer

        self.line_points = {}
        self.line_geoms = {}
        for f in self.line_layer.getFeatures():
            g = f.geometry()
            if not g or g.isEmpty():
                continue
            pts = get_line_points(g)
            if pts:
                self.line_points[f.id()] = pts
                self.line_geoms[f.id()] = g

        self.index = QgsSpatialIndex(self.line_layer.getFeatures())
        self.point_lookup = {}
        for a in self.point_layer.getFeatures():
            g = a.geometry()
            if g and not g.isEmpty():
                p = g.asPoint()
                self.point_lookup.setdefault((p.x(), p.y()), []).append(a.id())

    def canvasReleaseEvent(self, e):
        click_pt = self.toMapCoordinates(e.pos())
        near = self.index.nearestNeighbor(click_pt, 1)
        if not near:
            QMessageBox.information(None, "DownstreamTracer", "No line found here.")
            return
        fid = near[0]
        if fid not in self.line_points:
            return

        pts = self.line_points[fid]
        seg_idx = nearest_segment_index(pts, click_pt)
        if seg_idx is None:
            return

        start_idx = min(seg_idx + 1, len(pts) - 1)
        start_pt = pts[start_idx]
        start_geom = QgsGeometry.fromPointXY(start_pt)

        stack = [(fid, start_idx)]
        visited = set()
        selected_points = set()

        while stack:
            cfid, idx = stack.pop()
            if (cfid, idx) in visited:
                continue
            visited.add((cfid, idx))

            cpts = self.line_points.get(cfid)
            if not cpts:
                continue

            for i in range(idx, len(cpts)):
                vpt = cpts[i]
                key = (vpt.x(), vpt.y())
                if key in self.point_lookup:
                    selected_points.update(self.point_lookup[key])

                vgeom = QgsGeometry.fromPointXY(vpt)
                cand_fids = self.index.intersects(vgeom.boundingBox())
                for ofid in cand_fids:
                    if ofid == cfid:
                        continue
                    oline = self.line_points.get(ofid)
                    if not oline:
                        continue
                    v0 = oline[0]
                    if v0.x() == vpt.x() and v0.y() == vpt.y():
                        stack.append((ofid, 0))

        self.point_layer.selectByIds(list(selected_points))
        QMessageBox.information(None, "DownstreamTracer",
                                f"Clicked line fid={fid}\nSelected points: {len(selected_points)}")

#Run
dlg = TracerDialog()
if dlg.exec_() == QDialog.Accepted:
    line_layer, point_layer = dlg.selected_layers()
    if line_layer and point_layer:
        tool = DownstreamTracer(iface.mapCanvas(), line_layer, point_layer)
        iface.mapCanvas().setMapTool(tool)
        print(f"DownstreamTracer ready - Line: {line_layer.name()}, Point: {point_layer.name()}")
    else:
        QMessageBox.information(None, "DownstreamTracer", "Please select valid layers.")
else:
    print("DownstreamTracer canceled.")
