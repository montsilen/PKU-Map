from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtPositioning import QGeoPositionInfoSource, QGeoCoordinate
import sys

from models.constants import *
from models import *

class app():
    """
    主程序控制类
    """
    def __init__(self):
        self.n = nav("src/map-4.osm")

        self.searchStatus = SEARCHSPOT
        self.initnavigation()

        main = QApplication(sys.argv)
        main.setWindowIcon(QIcon("src/img/icon.png"))
        self.w = window()
        self.w.selectbutton.clicked.connect(self.changeSearchStatus)
        self.w.searchbar.textChanged.connect(lambda: self.presearch(True))
        self.w.waybar.textChanged.connect(lambda: self.presearch(False))
        self.w.searchbar.focused.connect(lambda: self.focuspresearch(True))
        self.w.waybar.focused.connect(lambda: self.focuspresearch(False))
        self.w.searchbutton.clicked.connect(self.search)
        self.w.upbutton.clicked.connect(lambda: self.w.mapview.changeScale(True))
        self.w.downbutton.clicked.connect(lambda: self.w.mapview.changeScale(False))
        self.w.navbutton.clicked.connect(self.navigateSelf)
        self.w.searchlist.itemClicked.connect(self.searchClickSpot)
        self.w.startbutton.clicked.connect(lambda: self.setdest(True))
        self.w.endbutton.clicked.connect(lambda: self.setdest(False))
        self.w.mapscene.selectionChanged.connect(self.selectSpot)

        self.selfPos = None
        self.waystart = None
        self.wayend = None

        self.w.drawMap(self.n)
        self.w.show()

        sys.exit(main.exec())

    def changeSearchStatus(self):
        self.waystart = self.wayend = None
        self.searchStatus = 1 - self.searchStatus
        if self.searchStatus == SEARCHSPOT:
            self.w.startpos = self.w.endpos = None
            self.w.startSelf(None)
            self.w.endSelf(None)
            self.w.clearway()
            self.w.waybar.setText("")
            self.waystart = None
            self.wayend = None
            self.w.startText(None)
            self.w.endText(None)
            self.w.ids = [None, None]
            self.w.updateAreas()
            self.w.startbutton.hide()
            self.w.endbutton.hide()
            self.w.searchlist.move(80, 68)
            self.presearch(True)
        else:
            selected = self.w.mapscene.selectedItems()
            for item in selected:
                if isinstance(item, textItem):
                    self.w.startbutton.show()
                    self.w.endbutton.show()
            self.w.searchlist.move(80, 112)
        self.w.changeselectbutton(self.searchStatus)

    def setdest(self, target):
        self.w.clearway()
        selected = self.w.mapscene.selectedItems()
        item = None
        for item in selected:
            if isinstance(item, textItem):
                break
        if item:        
            selected = self.w.mapscene.selectedItems()
            for item in selected:
                item.setSelected(False)
            self.w.startbutton.hide()
            self.w.endbutton.hide()
            self.w.searchbar.clearFocus()
            self.w.waybar.clearFocus()
            if target:
                self.w.searchbar.setText(item.toPlainText())
                self.waystart = item.id
                self.w.ids[0] = item.id
                self.w.startText(item)
            else:
                self.w.waybar.setText(item.toPlainText())
                self.w.ids[1] = item.id
                self.wayend = item.id
                self.w.endText(item)
            self.w.setSearchlist(None)
            self.w.updateAreas()

    def initnavigation(self):
        source = QGeoPositionInfoSource.createDefaultSource(None)
        if source:
            def position_updated(position):
                coordinate = position.coordinate()
                self.selfPos = (coordinate.latitude(), coordinate.longitude())
                self.w.setSelfPos(self.selfPos)
            source.positionUpdated.connect(position_updated)
            source.startUpdates()
        else:
            self.w.setSelfPos(None)
            self.selfPos = None

    def navigateSelf(self):
        """
        定位到我的位置
        """
        if self.selfPos:
            self.w.mapview.setscale(0)
            self.w.mapview.centerOn(self.w.selficon)

    def selectSpot(self):
        """
        在屏幕中选中地点时
        """
        self.w.updateAreas()
        selected = self.w.mapscene.selectedItems()
        for item in selected:
            if isinstance(item, textItem):
                for i in range(self.w.searchlist.count()):
                    if item.id != self.w.searchlist.item(i).id:
                        self.w.searchlist.item(i).setSelected(False)
                    else:
                        self.w.searchlist.item(i).setSelected(True)
                if self.searchStatus == SEARCHWAY:
                    self.w.startbutton.show()
                    self.w.endbutton.show()
                self.w.centerArea(self.w.areas[item.id][0])
                self.w.pinText(item)
                return
        self.w.searchlist.clearSelection()
        self.w.startbutton.hide()
        self.w.endbutton.hide()
        self.w.pinText(None)

    def focuspresearch(self, target):
        if self.searchStatus == SEARCHSPOT:
            self.searchSpot()
            return 
        if target:
            if not self.waystart:
                self.searchSpot()
            else:
                self.w.setSearchlist(None)
        else:
            if not self.wayend:
                self.presearch(target)
            else:
                self.searchSpot(False)

    def presearch(self, target):
        """
        输入框内容变化时的行为
        """
        self.w.clearway()
        if self.searchStatus == SEARCHSPOT:
            self.searchSpot()
        else:
            if target:
                self.waystart = None
                self.w.ids[0] = None
                self.w.startText(None)
                self.w.startpos = None
                self.w.startSelf(None)
                self.searchSpot()
            else:
                self.wayend = None
                self.w.ids[1] = None
                self.w.endText(None)
                self.w.endpos = None
                self.w.endSelf(None)
                self.searchSpot(False)

    def search(self):
        """
        按下搜索按钮的行为
        """
        if self.searchStatus == SEARCHSPOT:
            self.searchSpot()
        else:
            if self.waystart and self.wayend and self.waystart == self.wayend:
                self.w.waybar.setFocus()
                return 
            if not self.waystart and self.wayend:
                if self.w.searchbar.text() or not self.selfPos:
                    self.w.searchbar.setFocus()
                    return
                else:
                    self.waystart = "-1"
            if not self.wayend and self.waystart:
                if self.w.waybar.text() or not self.selfPos:
                    self.w.waybar.setFocus()
                    return 
                else:
                    self.wayend = "-1"
            self.searchWay()

    def searchSpot(self, target = True):
        """
        地点搜索触发
        """
        if target:
            name = self.w.searchbar.text()
        else:
            name = self.w.waybar.text()
        if name:
            self.w.setSearchlist(self.n.searchspot(name))
        else:
            self.w.setSearchlist(None)

    def searchClickSpot(self, item):
        """
        从多选列表中选中地点时
        """
        selected = self.w.mapscene.selectedItems()
        for ite in selected:
            ite.setSelected(False)
        if isinstance(item, searchItem):
            self.w.centerArea(self.w.areas[item.id][0])
            self.w.areas[item.id][1].show()
            self.w.areas[item.id][1].setSelected(True)

    def searchWay(self):
        """
        路径搜索触发
        """
        if self.waystart and self.wayend:
            if self.waystart == "-1":
                self.w.searchbar.setText("我的位置")
                self.waystart = "-1"
                lat, lon = self.selfPos
                lat = (lat - DELTA_LAT) * MULTY
                lon = (lon - DELTA_LON) * MULTY
                startpos = (lat, lon)
                self.w.startpos = startpos
                self.w.startSelf(startpos)
            else:
                startpos = self.w.areas[self.waystart][0].polygon().boundingRect().center()
                startpos = (-startpos.y(), startpos.x())
            if self.wayend == "-1":
                self.w.waybar.setText("我的位置")
                self.wayend = "-1"
                lat, lon = self.selfPos
                lat = (lat - DELTA_LAT) * MULTY
                lon = (lon - DELTA_LON) * MULTY
                endpos = (lat, lon)
                self.w.endpos = endpos
                self.w.endSelf(endpos)
            else:
                endpos = self.w.areas[self.wayend][0].polygon().boundingRect().center()
                endpos = (-endpos.y(), endpos.x())
            self.w.drawway(self.n.calcroute(startpos, endpos, self.n.nodes), self.n)
            
if __name__ == "__main__":
    app()