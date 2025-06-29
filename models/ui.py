from PySide6.QtCore import Qt, QPointF, QRectF, QEvent, Signal
from PySide6.QtWidgets import QMainWindow, QApplication, \
            QWidget, QPushButton, QLineEdit, QLabel, QListWidget, \
            QGraphicsView, QGraphicsScene, QGraphicsPolygonItem, QGraphicsPathItem, \
            QGraphicsItem, QGraphicsEllipseItem, QGraphicsPixmapItem, QGraphicsTextItem ,\
            QStyle, QListWidgetItem
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtGui import QIcon, QColor, QPainter, QPolygonF, QBrush, QPen, \
            QPainterPath, QPixmap, QCursor

from .constants import *

class wheelEvent(QEvent):
    Type = QEvent.Type(QEvent.registerEventType())

    def __init__(self, data):
        super().__init__(wheelEvent.Type)
        self.data = data

class mapView(QGraphicsView):
    """
    地图视图类
    """
    def __init__(self, window):
        """
        控件拖拽和缩放初始化设置
        """
        super().__init__()
        self.window = window
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.ScrollHandDrag) 
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse) 
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.scales = 0
        self.scale(1.25, 1.25)

    def changeScale(self, larger):
        if larger and self.scales < MAXSCALING:
            self.scales += 1
            self.scale(1.25, 1.25)
            self.window.selficon.changeScale(larger)
            self.window.updateAreas()
            selected = self.window.mapscene.selectedItems()
            self.window.startSelf(self.window.startpos)
            self.window.endSelf(self.window.endpos)
            if self.window.ids[0]:
                self.window.startText(self.window.areas[self.window.ids[0]][1])
            if self.window.ids[1]:
                self.window.endText(self.window.areas[self.window.ids[1]][1])
            for item in selected:
                if isinstance(item, textItem):
                    self.window.pinText(item)
        if not larger and self.scales > -MAXSCALING:
            self.scales -= 1
            self.scale(0.8, 0.8)
            self.window.selficon.changeScale(larger)
            self.window.updateAreas()
            selected = self.window.mapscene.selectedItems()
            self.window.startSelf(self.window.startpos)
            self.window.endSelf(self.window.endpos)
            if self.window.ids[0]:
                self.window.startText(self.window.areas[self.window.ids[0]][1])
            if self.window.ids[1]:
                self.window.endText(self.window.areas[self.window.ids[1]][1])
            for item in selected:
                if isinstance(item, textItem):
                    self.window.pinText(item)
    
    def setscale(self, scales):
        if -MAXSCALING <= scales <= MAXSCALING:
            for i in range(self.scales, scales, 1 if scales > self.scales else -1):
                self.changeScale(scales > self.scales)

    def wheelEvent(self, event):
        self.changeScale(event.angleDelta().y() > 0)

class selfGraphicsItem(QGraphicsItem):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setZValue(10)
        self.R = 20
        self.r = 8

    def boundingRect(self):
        return QRectF(-self.R, -self.R, 2 * self.R, 2 * self.R)
    
    def paint(self, painter : QPainter, option, widget = None):
        painter.setBrush(QBrush(QColor("#9BC3FF")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-self.R, -self.R, 2*self.R, 2*self.R)

        painter.setBrush(QBrush(QColor("#3C8AFF")))
        painter.setPen(QPen(QColor("white"), 4))
        painter.drawEllipse(-self.r, -self.r, 2*self.r, 2*self.r)
    
    def changeScale(self, larger):
        self.prepareGeometryChange()
        self.R += 3 if larger else -3
        self.update()

class areaItem(QGraphicsPolygonItem):
    def __init__(self, area, parent=None):
        if area.gettype() == AREA_TYPE_POINT_BUILDING:
            posx, posy = area.getpos()[0]    
            points = [
                QPointF(posy - 5, - posx), 
                QPointF(posy, - posx - 5),
                QPointF(posy + 5, - posx),
                QPointF(posy, - posx + 5),
            ]
        else:
            points = [QPointF(y, -x) for x, y in area.getpos()]
        x = y = 0
        for point in points:
            x += point.x()
            y += point.y()
        self.centerpos = ( - y / len(points), x / len(points))
        polygon = QPolygonF(points)
        super().__init__(polygon, parent)
        fill_color, border_color = AREA_COLOR.get(area.gettype(), ("#DDDDDD", "#999999"))[0:2]
        if area.gettype() == AREA_TYPE_BACKGROUND and area.gettag("landuse") == "grass":
            fill_color = AREA_COLOR.get(AREA_TYPE_GREENLAND, ("#DDDDDD", "#999999"))[0]
            border_color = AREA_COLOR.get(AREA_TYPE_BUILDING, ("#DDDDDD", "#999999"))[1]
        self.setBrush(QBrush(QColor(fill_color)))
        self.setPen(QPen(QColor(border_color), 0.4))

class textItem(QGraphicsTextItem):
    def __init__(self, parent, area):
        super().__init__(parent)
        self.type = area.gettype()
        self.id = area.id
        self.setAcceptHoverEvents(True)
        self.setDefaultTextColor(QColor("black"))
        self.setZValue(100)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def hoverEnterEvent(self, event):
        QApplication.setOverrideCursor(QCursor(Qt.PointingHandCursor))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        QApplication.restoreOverrideCursor()
        super().hoverLeaveEvent(event)
    
    def paint(self, painter, option, widget):
        option.state &= ~QStyle.State_Selected
        super().paint(painter, option, widget)

class searchItem(QListWidgetItem):
    def __init__(self, text, id):
        super().__init__(text)
        self.id = id

class SearchLineEdit(QLineEdit):
    focused = Signal()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused.emit()

class window(QMainWindow):
    def __init__(self):
        """
        基本的UI初始化内容
        字体初始化设置
        为地图页面创建GraphicsView
        """
        super().__init__()

        self.ids = [None, None]
        self.startpos = None
        self.endpos = None

        self.setWindowTitle(TEXT["title"])
        self.setWindowIcon(QIcon("src/img/icon.png"))
        self.setMinimumSize(600, 400)
        self.resize(800, 600)

        self.initmap()
        self.initcontrol()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.upbutton.move(self.width() - 30 - 44, self.height() - 30 - 87)
        self.downbutton.move(self.width() - 30 - 44, self.height() - 30 - 44)
        self.navbutton.move(self.width() - 30 - 44, self.height() - 30 - 44 * 3 - 20)

    def initcontrol(self):
        self.logo = QLabel(self)
        self.logo.setPixmap(QPixmap("src/img/logo.png").scaledToHeight(42, Qt.SmoothTransformation))
        self.logo.move(30, 25)
        self.logo.setFixedSize(44, 44)
        self.logo.setStyleSheet(STYLE["logo"])
        self.logo.raise_()

        self.searchbar = SearchLineEdit(self)
        self.searchbar.setPlaceholderText(TEXT["searchbar"])
        self.searchbar.setFixedSize(300, 44)
        self.searchbar.move(80, 25)
        self.searchbar.setStyleSheet(STYLE["searchbar"])
        self.searchbar.raise_()

        self.waybar = SearchLineEdit(self)
        self.waybar.setPlaceholderText(TEXT["searchway"][1])
        self.waybar.setFixedSize(300, 44)
        self.waybar.move(80, 68)
        self.waybar.setStyleSheet(STYLE["searchway"][1])
        self.waybar.raise_()
        self.waybar.hide()
        
        self.selectbutton = QPushButton(self)
        self.selectbutton.setIcon(QIcon("src/img/spot.png"))
        self.selectbutton.setFixedSize(44, 44)
        self.selectbutton.move(380, 25)
        self.selectbutton.setStyleSheet(STYLE["selectbutton"])
        self.selectbutton.setCursor(Qt.PointingHandCursor)
        self.selectbutton.raise_()

        self.searchbutton = QPushButton(self)
        self.searchbutton.setIcon(QIcon("src/img/search.png"))
        self.searchbutton.setFixedSize(44, 44)
        self.searchbutton.move(424, 25)
        self.searchbutton.setStyleSheet(STYLE["searchbutton"])
        self.searchbutton.setCursor(Qt.PointingHandCursor)
        self.searchbutton.raise_()

        self.upbutton = QPushButton(self)
        self.upbutton.setIcon(QIcon("src/img/plus.png"))
        self.upbutton.setFixedSize(44, 44)
        self.upbutton.move(800 - 30 - 44, 600 - 30 - 87)
        self.upbutton.setStyleSheet(STYLE["upbutton"])
        self.upbutton.setCursor(Qt.PointingHandCursor)
        self.upbutton.raise_()

        self.downbutton = QPushButton(self)
        self.downbutton.setIcon(QIcon("src/img/minus.png"))
        self.downbutton.setFixedSize(44, 44)
        self.downbutton.move(800 - 30 - 44, 600 - 30 - 44)
        self.downbutton.setStyleSheet(STYLE["downbutton"])
        self.downbutton.setCursor(Qt.PointingHandCursor)
        self.downbutton.raise_()

        self.navbutton = QPushButton(self)
        self.navbutton.setIcon(QIcon("src/img/nav.png"))
        self.navbutton.setFixedSize(44, 44)
        self.navbutton.move(800 - 30 - 44, 600 - 30 - 44 * 3 - 20)
        self.navbutton.setStyleSheet(STYLE["navbutton"])
        self.navbutton.setCursor(Qt.PointingHandCursor)
        self.navbutton.raise_()

        self.startbutton = QPushButton(self)
        self.startbutton.setText(TEXT["start"])
        self.startbutton.setFixedSize(150, 44)
        self.startbutton.move(80, 112)
        self.startbutton.setStyleSheet(STYLE["startbutton"])
        self.startbutton.setCursor(Qt.PointingHandCursor)
        self.startbutton.hide()
        self.startbutton.raise_()

        self.endbutton = QPushButton(self)
        self.endbutton.setText(TEXT["end"])
        self.endbutton.setFixedSize(150, 44)
        self.endbutton.move(230, 112)
        self.endbutton.setStyleSheet(STYLE["endbutton"])
        self.endbutton.setCursor(Qt.PointingHandCursor)
        self.endbutton.hide()
        self.endbutton.raise_()

        self.searchlist = QListWidget(self)
        self.searchlist.setMouseTracking(True)
        self.searchlist.move(80, 68)
        self.searchlist.setStyleSheet(STYLE["searchlist"])
        self.searchlist.setCursor(Qt.PointingHandCursor)
        self.searchlist.raise_()
        self.searchlist.hide()

    def setSearchlist(self, l):
        self.searchlist.clear()
        if l:
            maxlength = 0
            for id, name in l:
                maxlength = max(maxlength, len(name))
                item = searchItem(name, id)
                self.searchlist.addItem(item)
            self.searchlist.setFixedHeight(min(45 * len(l), 45 * 8))
            self.searchlist.setFixedWidth(max(19 * maxlength, 300))
            self.startbutton.move(80, 112 + min(45 * len(l), 45 * 8))
            self.endbutton.move(230, 112 + min(45 * len(l), 45 * 8))
            self.searchlist.show()
        elif l is None:
            self.startbutton.move(80, 112)
            self.endbutton.move(230, 112)
            self.searchlist.hide()
        else:
            item = QListWidgetItem("没有搜索到结果")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.searchlist.addItem(item)
            self.searchlist.setFixedHeight(45)
            self.searchlist.setFixedWidth(300)
            self.startbutton.move(80, 112 + 45)
            self.endbutton.move(230, 112 + 45)
            self.searchlist.show()

    def centerArea(self, item):
        self.mapview.setscale(-1)
        self.mapview.centerOn(item)
    
    def changeselectbutton(self, to):
        if to == SEARCHSPOT:
            self.searchbar.setPlaceholderText(TEXT["searchbar"])
            self.searchbar.setStyleSheet(STYLE["searchbar"])
            self.waybar.hide()
            self.selectbutton.setIcon(QIcon("src/img/spot.png"))
        elif to == SEARCHWAY:
            self.searchbar.setPlaceholderText(TEXT["searchway"][0])
            self.searchbar.setStyleSheet(STYLE["searchway"][0])
            self.waybar.show()
            self.selectbutton.setIcon(QIcon("src/img/way.png"))

    def initmap(self):
        self.areas = {}

        self.path = None

        self.mapscene = QGraphicsScene()
        self.mapscene.setBackgroundBrush(QColor("#FFF8DC"))
        self.mapview = mapView(self)
        self.mapview.setScene(self.mapscene)
        self.setCentralWidget(self.mapview)

        self.selficon = selfGraphicsItem()
        self.selficon.hide()
        self.mapscene.addItem(self.selficon)
        self.selficon.setZValue(10)

        self.spotpin = QGraphicsSvgItem("src/img/pin.svg")
        self.spotpin.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.spotpin.hide()
        self.mapscene.addItem(self.spotpin)
        self.spotpin.setZValue(10)

        self.startpin = QGraphicsSvgItem("src/img/start.svg")
        self.startpin.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.startpin.hide()
        self.mapscene.addItem(self.startpin)
        self.startpin.setZValue(10)

        self.endpin = QGraphicsSvgItem("src/img/end.svg")
        self.endpin.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.endpin.hide()
        self.mapscene.addItem(self.endpin)
        self.endpin.setZValue(10)

    def drawMap(self, nav):
        """
        绘制地图
        """
        for area in nav.getarea({"type": [AREA_TYPE_GREENLAND]}):
            self.drawArea(area)
        for area in nav.getarea({"type": [AREA_TYPE_WATER]}):
            self.drawArea(area)
        for area in nav.getarea({"type": [AREA_TYPE_BUILDING, AREA_TYPE_STADIUM]}):
            self.drawArea(area)
        for area in nav.getarea({"type": [AREA_TYPE_BACKGROUND]}):
            self.drawArea(area)
        for area in nav.getarea({"type": [AREA_TYPE_POINT_BUILDING]}):
            self.drawArea(area)
        for route in nav.getroute():
            self.drawRoute(route)

    def drawRoute(self, route):
        """
        绘制地图中的道路
        """
        if route.gettype() in [1, 2]:
            points = route.getpos()
            path = QPainterPath()
            path.moveTo(QPointF(points[0][1], -points[0][0]))
            for x, y in points[1:]:
                path.lineTo(QPointF(y, -x))
            item = QGraphicsPathItem(path)
            pen = QPen(QColor("red"), route.gettype())
            pen.setStyle(Qt.DashLine)
            pen.setCosmetic(True)
            item.setPen(pen)
            self.mapscene.addItem(item)
        else:
            points = route.getpos()
            path = QPainterPath()
            path.moveTo(QPointF(points[0][1], -points[0][0]))
            for x, y in points[1:]:
                path.lineTo(QPointF(y, -x))
            outlineitem = QGraphicsPathItem(path)
            outlinepen = QPen(QColor("gray"), 2.5 * route.gettype())
            outlinepen.setJoinStyle(Qt.RoundJoin)
            outlinepen.setCosmetic(True)
            outlineitem.setPen(outlinepen)
            self.mapscene.addItem(outlineitem)
            lineitem = QGraphicsPathItem(path)
            linepen = QPen(QColor("white"), 2.5 * route.gettype() - 2)
            linepen.setJoinStyle(Qt.RoundJoin)
            linepen.setCosmetic(True)
            lineitem.setPen(linepen)
            self.mapscene.addItem(lineitem)

    def drawArea(self, area):
        """
        绘制地图中的区域
        """
        if area.gettype() == AREA_TYPE_POINT_BUILDING:
            item = areaItem(area)
            self.mapscene.addItem(item)
            textitem = None
            if area.gettag("name"):
                textitem = textItem(area.gettag("name"), area)
                textrect = textitem.boundingRect()
                textitem.setDefaultTextColor(QColor(AREA_COLOR.get(area.gettype(), ("", "", "black"))[2]))
                textitem.setPos(item.boundingRect().center() - QPointF(textrect.width() / 2, textrect.height() / 2 + 8))
                self.mapscene.addItem(textitem)
            self.areas[area.id] = [item, textitem]
        else:
            item = areaItem(area)
            self.mapscene.addItem(item)
            textitem = None
            if area.gettag("name"):
                textitem = textItem(str(area.gettag("name")), area)
                textrect = textitem.boundingRect()
                textitem.setDefaultTextColor(QColor(AREA_COLOR.get(area.gettype(), ("", "", "black"))[2]))
                textitem.setPos(item.boundingRect().center() - QPointF(textrect.width() / 2, textrect.height() / 2))
                self.mapscene.addItem(textitem)
            self.areas[area.id] = [item, textitem]

    def updateAreas(self):
        for items in self.areas.values():
            arearect = items[0].polygon().boundingRect()
            topleft = self.mapview.mapFromScene(arearect.topLeft())
            bottomright = self.mapview.mapFromScene(arearect.bottomRight())
            if items[1]:
                textrect = items[1].boundingRect()
                items[1].setPos(arearect.center() - QPointF(textrect.width() / 2 * 0.8 ** self.mapview.scales, textrect.height() / 2 * 0.8 ** self.mapview.scales + (8 if items[1].type == AREA_TYPE_POINT_BUILDING else 0)))
                width = abs(bottomright.x() - topleft.x())
                height = abs(bottomright.y() - topleft.y())
                if not items[1].isSelected():
                    items[1].setDefaultTextColor(QColor(AREA_COLOR.get(items[1].type, ("", "", "black"))[2]))
                if width * height > 2000 or items[1].isSelected() or self.mapview.scales >= 0 or items[1].id in self.ids:
                    items[1].show()
                else:
                    items[1].hide()

    def pinText(self, item):
        if item:
            item.setDefaultTextColor(QColor("red"))
            self.spotpin.show()
            spotpinrect = self.spotpin.boundingRect()
            self.spotpin.setPos(self.areas[item.id][0].boundingRect().center() - QPointF(spotpinrect.width() / 2 * 0.8 ** self.mapview.scales, spotpinrect.height() * 0.8 ** self.mapview.scales + (8 if item.type == AREA_TYPE_POINT_BUILDING else 0)))
        else:
            self.spotpin.hide()

    def startText(self, item):
        if item:
            self.startpin.show()
            startpinrect = self.startpin.boundingRect()
            self.startpin.setPos(self.areas[item.id][0].boundingRect().center() - QPointF(startpinrect.width() / 2 * 0.8 ** self.mapview.scales, startpinrect.height() * 0.8 ** self.mapview.scales + (8 if item.type == AREA_TYPE_POINT_BUILDING else 0)))
        else:
            if not self.startpos:
                self.startpin.hide()

    def endText(self, item):
        if item:
            self.endpin.show()
            endpinrect = self.endpin.boundingRect()
            self.endpin.setPos(self.areas[item.id][0].boundingRect().center() - QPointF(endpinrect.width() / 2 * 0.8 ** self.mapview.scales, endpinrect.height() * 0.8 ** self.mapview.scales + (8 if item.type == AREA_TYPE_POINT_BUILDING else 0)))
        else:
            if not self.endpos:
                self.endpin.hide()

    def startSelf(self, pos):
        if self.startpos:
            self.startpin.show()
            startpinrect = self.startpin.boundingRect()
            self.startpin.setPos(self.selficon.mapToScene(self.selficon.boundingRect().center()) - QPointF(startpinrect.width() / 2 * 0.8 ** self.mapview.scales, startpinrect.height() * 0.8 ** self.mapview.scales))
        else:
            self.startpin.hide()

    def endSelf(self, pos):
        if self.endpos:
            self.endpin.show()
            endpinrect = self.endpin.boundingRect()
            self.endpin.setPos(self.selficon.mapToScene(self.selficon.boundingRect().center()) - QPointF(endpinrect.width() / 2 * 0.8 ** self.mapview.scales, endpinrect.height() * 0.8 ** self.mapview.scales))
        else:
            self.endpin.hide()
    
    def setSelfPos(self, pos):
        if pos:
            self.selficon.show()
            self.navbutton.setIcon(QIcon("src/img/navself.png"))
            lat, lon = pos
            lat = (lat - DELTA_LAT) * MULTY
            lon = (lon - DELTA_LON) * MULTY
            self.selficon.setPos(QPointF(lon, -lat))
        else:
            self.navbutton.setIcon(QIcon("src/img/nav.png"))
            self.selficon.hide()

    def drawway(self, nodes, nav):
        points = [nav.nodes[node].getpos() for node in nodes]
        path = QPainterPath()
        path.moveTo(QPointF(points[0][1], -points[0][0]))
        for x, y in points[1:]:
            path.lineTo(QPointF(y, -x))
        outlineitem = QGraphicsPathItem(path)
        outlinepen = QPen(QColor("blue"), 5)
        outlinepen.setJoinStyle(Qt.RoundJoin)
        outlinepen.setCosmetic(True)
        outlineitem.setPen(outlinepen)
        self.mapscene.addItem(outlineitem)
        lineitem = QGraphicsPathItem(path)
        linepen = QPen(QColor("lightblue"), 5 - 2)
        linepen.setJoinStyle(Qt.RoundJoin)
        linepen.setCosmetic(True)
        lineitem.setPen(linepen)
        self.mapscene.addItem(lineitem)
        self.path = [lineitem, outlineitem]
        rect = outlineitem.boundingRect() 
        viewsize = self.mapview.viewport().rect().size() 
        scalex = rect.width() / viewsize.width() 
        scaley = rect.height() / viewsize.height()
        scales = max(4 - int(max(scalex, scaley) / 0.1), -5)
        self.mapview.setscale(scales)
        self.mapview.centerOn(lineitem)

    def clearway(self):
        if self.path:
            self.mapscene.removeItem(self.path[0])
            self.mapscene.removeItem(self.path[1])
            del self.path
            self.path = None