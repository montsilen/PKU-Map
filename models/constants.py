# 预定义坐标偏置常量
DELTA_LAT = 39.99098
DELTA_LON = 116.30423
MULTY = 200000

# 预定义道路类型常量
ROAD_TYPE_PEDESTRIAN = 1
ROAD_TYPE_BICYCLE = 2
ROAD_TYPE_MOTOR_VEHICLE_LOW = 3
ROAD_TYPE_MOTOR_VEHICLE_MEDIUM = 4
ROAD_TYPE_MOTOR_VEHICLE_HIGH = 5

# 预定义区域类型常量
AREA_TYPE_POINT_BUILDING = 1
AREA_TYPE_BUILDING = 2
AREA_TYPE_GREENLAND = 3
AREA_TYPE_WATER = 4
AREA_TYPE_STADIUM = 5
AREA_TYPE_BACKGROUND = 6

# 预定义出行方式常量
METHOD_WALK = 1
METHOD_DRIVE = 2

# 预定义样式和显示字符串
TEXT = {
    "title" : "燕园导航",
    "searchbar" : "搜索燕园的那一个角落…",
    "searchway" : ["选择起点…", "选择终点…"],
    "start" : "设为起点",
    "end" : "设为终点"
}

STYLE = {
    "searchbar" : "QLineEdit { background-color: white; padding: 6px 15px;\
            border: 1px solid #cccccc; border-right: none ; border-top-left-radius: 8px;\
            border-bottom-left-radius: 8px; font-size: 16px;}",
    "searchway" : [
        "QLineEdit { background-color: white; padding: 6px 15px; \
            border: 1px solid #cccccc; border-right: none ; border-top-left-radius: 8px;\
            font-size: 16px;}",
        "QLineEdit { background-color: white; padding: 6px 15px; \
            border: 1px solid #cccccc; border-bottom-right-radius: 8px;\
            border-bottom-left-radius: 8px; font-size: 16px;}"
    ],
    "logo" : "border-radius: 21px",
    "selectbutton" : "QPushButton { border: 1px solid #cccccc; border-left: none;\
                border-right: none; background-color: #eeeeee }",
    "searchbutton" : "QPushButton { border: none; \
                border-top-right-radius: 8px; border-bottom-right-radius: 8px; \
                background-color: #40c5f1 }",
    "upbutton" : "QPushButton { border: 1px solid #cccccc; \
                border-top-right-radius: 8px; border-top-left-radius: 8px;\
                background-color: white }",
    "downbutton" : "QPushButton { border: 1px solid #cccccc; \
                border-bottom-right-radius: 8px; border-bottom-left-radius: 8px;\
                background-color: white }",
    "navbutton" : "QPushButton { border: 1px solid #cccccc; border-radius: 8px;\
                background-color: white }",
    "searchlist" : "QListWidget { border: 1px solid #cccccc; border-radius: 8px;\
                font-size: 16px; border-radius: 8px} \
                QListWidget::item { padding: 6px 15px; height: 32px}",
    "startbutton" : "QPushButton { border: 1px solid green; border-top-left-radius: 8px; \
                border-bottom-left-radius: 8px; border-right: 0.5px solid #cccccc; font-size: 16px; \
                background-color: white}",
    "endbutton" : "QPushButton { border: 1px solid red; border-top-right-radius: 8px; \
                border-bottom-right-radius: 8px; border-left: 0.5px solid #cccccc; font-size: 16px; \
                background-color: white}"
}

# 预定义颜色常量
AREA_COLOR = {
    AREA_TYPE_POINT_BUILDING :  ("#FFB6C1", "#FF6666", "#222222"),
    AREA_TYPE_BUILDING : ("#CCCCCC", "#999999", "#222222"),
    AREA_TYPE_GREENLAND : ("#CCFFCC", "#228822", "#006400"),
    AREA_TYPE_WATER : ("#99CCFF", "#225599", "#00008B"),
    AREA_TYPE_STADIUM : ("#FFE0B2", "#FF8C00", "#CC6600"),
    AREA_TYPE_BACKGROUND : ("#FFF8DC", "#999999", "#222222")
}

# 预定义搜索常量
SEARCHSPOT = 0
SEARCHWAY = 1

# 预定义缩放常量
MAXSCALING = 5