import xml.etree.ElementTree as ET
from .algorithm import graph, searchstr
from .constants import *

class node:
    """
    位置节点类
    包含点的唯一标识符，经纬度
    需学习参考osm xml的node标签数据格式
    """

    def __init__(self, id, lat, lon):
        self.id = id
        self.lat = (lat - DELTA_LAT) * MULTY
        self.lon = (lon - DELTA_LON) * MULTY

    def getpos(self):
        """
        获取坐标(lat,lon)二元组
        """
        return (self.lat, self.lon)

class route:
    """
    路径类
    仅包含道路路径
    包含路径的唯一标识符，类型和标签信息
    """
    def __init__(self, id, nodes, road_type, tags):
        self.id = id
        self.nodes = nodes
        self.road_type = road_type
        self.tags = tags

    def getpos(self):
        """
        获取坐标列表，返回(lat,lon)的二元组列表
        """
        return [node.getpos() for node in self.nodes]

    def gettype(self):
        """
        获取道路的级别信息以供渲染
        返回预定义的类常量
        包含步道，自行车道和各级机动车道
        """
        return self.road_type

    def gettag(self, key):
        """
        获取路径的标签信息，返回字符串
        若不存在返回空
        """
        return self.tags.get(key, "")

class area:
    """
    区域类
    各类闭合区域
    包含建筑，绿地，水域等类型
    包含路径的唯一标识符，类型和标签信息
    """

    def __init__(self, id, nodes, area_type, tags):
        self.id = id
        self.nodes = nodes
        self.area_type = area_type
        self.tags = tags

    def getpos(self):
        """
        获取坐标列表，返回(lat,lon)的二元组列表
        """
        return [node.getpos() for node in self.nodes]

    def gettype(self):
        """
        获取区域的类型信息以供渲染
        返回预定义的类常量
        包含点状建筑，建筑，绿地，水域，运动场类型
        """
        return self.area_type

    def gettag(self, key):
        """
        获取路径的标签信息，返回字符串
        若不存在返回空
        """
        return self.tags.get(key, "")

class nav:
    """
    地图类
    整合的地图信息
    实现与algorithm.py的耦合
    """

    def __init__(self, dir):
        """
        读取dir路径的osm文件并解析
        初始化地图的节点列表
        初始化地图的各类路径列表
        """
        self.nodes = {}
        self.nodes[0] = node(0,0,0)
        self.nodes[1] = node(1,0,0)
        self.routes = []
        self.areas = []

        tree = ET.parse(dir)
        root = tree.getroot()

        for element in root:
            if element.tag == 'node':
                id = element.get('id')
                lat = float(element.get('lat'))
                lon = float(element.get('lon'))
                self.nodes[id] = node(id, lat, lon)
                # 检查node是否带有name属性，如果有则转换为area
                
                tags = {}
                for child in element:
                    if child.tag == 'tag':
                        k = child.get('k')
                        v = child.get('v')
                        tags[k] = v
                if 'name' in tags:
                    area_id = id
                    area_nodes = [self.nodes[id]]
                    area_type = AREA_TYPE_POINT_BUILDING  
                    self.areas.append(area(area_id, area_nodes, area_type, tags))
                    
            elif element.tag == 'way':
                id = element.get('id')
                nodes = []
                tags = {}
                is_area = False
                road_type = None
                area_type = None

                for child in element:
                    if child.tag == 'nd':
                        node_id = child.get('ref')
                        if node_id in self.nodes:
                            nodes.append(self.nodes[node_id])
                    elif child.tag == 'tag':
                        k = child.get('k')
                        v = child.get('v')
                        tags[k] = v
                        if k == 'area' and v == 'yes':
                            is_area = True
                            area_type = AREA_TYPE_BUILDING
                        elif k == 'highway':
                            if v == 'footway':
                                road_type = ROAD_TYPE_PEDESTRIAN
                            elif v == 'cycleway':
                                road_type = ROAD_TYPE_BICYCLE
                            elif v in ['residential', 'living_street', 'service']:
                                road_type = ROAD_TYPE_MOTOR_VEHICLE_LOW
                            elif v in ['primary', 'secondary', 'tertiary']:
                                road_type = ROAD_TYPE_MOTOR_VEHICLE_MEDIUM
                            elif v in ['motorway', 'trunk']:
                                road_type = ROAD_TYPE_MOTOR_VEHICLE_HIGH
                            else:
                                road_type = ROAD_TYPE_PEDESTRIAN
                        elif k == 'building':
                            is_area = True
                            area_type = AREA_TYPE_BUILDING
                        elif k == 'natural' and v == 'water':
                            is_area = True
                            area_type = AREA_TYPE_WATER
                        elif k == 'landuse' and v in ['grass', 'commercial']:
                            is_area = True
                            area_type = AREA_TYPE_GREENLAND
                        elif k == 'leisure' and v in ['garden', 'park']:
                            is_area = True
                            area_type = AREA_TYPE_GREENLAND
                        elif k == 'leisure' and v in ['stadium', 'track', 'pitch', 'sports_centre']:
                            is_area = True
                            area_type = AREA_TYPE_STADIUM

                if is_area and area_type:
                    self.areas.append(area(id, nodes, area_type, tags))
                elif road_type:
                    self.routes.append(route(id, nodes, road_type, tags))
                    
            elif element.tag == 'relation':
                # 处理relation标签
                relation_id = element.get('id')
                relation_tags = {}
                member_ways = []

                for child in element:
                    if child.tag == 'tag':
                        k = child.get('k')
                        v = child.get('v')
                        relation_tags[k] = v
                    elif child.tag == 'member' and child.get('type') == 'way':
                        member_ways.append((child.get('ref'), child.get('role')))

                if 'building' in relation_tags:
                    first_area=None
                    for way_id, way_role in member_ways:
                        # 查找对应的way
                        for way_element in root.findall('.//way[@id="{}"]'.format(way_id)):
                            way_nodes = []
                            way_tags = {}
                            for way_child in way_element:
                                if way_child.tag == 'nd':
                                    node_id = way_child.get('ref')
                                    if node_id in self.nodes:
                                        way_nodes.append(self.nodes[node_id])
                                elif way_child.tag == 'tag':
                                    k = way_child.get('k')
                                    v = way_child.get('v')
                                    way_tags[k] = v
                            new_area = area(way_id, way_nodes, AREA_TYPE_BUILDING if way_role == "outer" else AREA_TYPE_BACKGROUND, way_tags)
                            self.areas.append(new_area)
                            if first_area is None and way_role == "outer":
                                first_area=new_area
                            break
                    if first_area:
                        first_area.tags.update(relation_tags)
        self.g = graph(self.routes)


    def getroute(self, condition = None):
        """
        获取满足condition条件的道路路径的列表
        condition条件是一个字典
        可能包含道路级别信息的限制条件 用condition["type"]的列表限定
        可能包含道路tag的限制条件 用condition[key]=value限定
        """
        if condition is None:
            return self.routes

        result = []
        for route in self.routes:
            match = True
            if "type" in condition:
                if route.gettype() not in condition["type"]:
                    match = False
            for key, value in condition.items():
                if key != "type" and route.gettag(key) != value:
                    match = False
            if match:
                result.append(route)
        return result

    def getarea(self, condition = None):
        """
        获取满足condition条件的区域路径的列表
        condition条件是一个字典
        可能包含区域类型信息的限制条件 用condition["type"]的列表限定
        可能包含区域tag的限制条件 用condition[key]=value限定
        """
        if condition is None:
            return self.areas

        result = []
        for area in self.areas:
            match = True
            if "type" in condition:
                if area.gettype() not in condition["type"]:
                    match = False
            for key, value in condition.items():
                if key != "type" and area.gettag(key) != value:
                    match = False
            if match:
                result.append(area)
        return result

    def findpos(self, pos):
        """
        返回距离pos最近的路径上的node
        使用algorithm中的类graph
        """
        return self.g.find_nearest_node(pos)

    def searchspot(self, name):
        """
        模糊搜索地点，按照匹配度降低顺序，返回包含area和route的列表
        使用algorithm中的函数searchstr
        """
        return searchstr(name, self.areas)

    def calcroute(self, start, end, nodes):
        """
        路径搜索
        接受起点和终点的唯一标识符
        并提供步行和驾车两种方式，method需要预定义常量，并默认赋值为步行
        返回route的列表
        """
        return self.g.kshortestroute(start, end, nodes)