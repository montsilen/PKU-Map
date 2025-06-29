from .constants import *
import heapq
import math
from collections import defaultdict

similar_rate=0.5
list_num=10
from fuzzywuzzy import fuzz

def similar_check(str1,str2):
    """
    对于两个字符串计算相似度
    """
    return fuzz.token_sort_ratio(str1, str2)

def searchstr(name, lst):
    """
    模糊搜索
    按照相似度降序返回，lst中和name相似的字符串列表
    """
    ans = []
    sorted_list = sorted(lst,key=lambda x:similar_check(name, x.gettag("name")),reverse=True)
    pos=0
    num=0
    while pos < len(sorted_list):
        if similar_check(name,sorted_list[pos].gettag("name"))>similar_rate and num<list_num:
            if sorted_list[pos].gettag("name") !="":
                ans.append((sorted_list[pos].id, sorted_list[pos].gettag("name")))
                num+=1
            pos += 1
        else:
            break
    return ans

class graph:
    """
    拓扑类
    保存地图中的拓扑信息
    节点图和路径
    """

    def __init__(self, routes):
        """
        由总地图信息初始化生成
        包含节点的邻接表
        在保存时仅需包含路径及其节点信息
        """
        self.routes=routes
        self.nodes=self.all_nodes()
        self.nodes_id={node.id for node in self.nodes}
        self.near_map=defaultdict(list)
        self.buildgraph()

    def all_nodes(self):
        node_set = {}  # 使用字典确保节点唯一性 (id -> node)
        for route in self.routes:
            for node in route.nodes:
                if node.id not in node_set:
                    node_set[node.id] = node
        return list(node_set.values())

    def get_distance(self,lat1,lon1,lat2,lon2):
        d_lat=abs(lat1-lat2)
        d_lon=abs(lon1-lon2)
        dis=math.sqrt(d_lat*d_lat+d_lon*d_lon)
        return dis

    def buildgraph(self):
        for route in self.routes:
            nodes=route.nodes
            road_type=route.gettype()
            for i in range(len(nodes)-1):
                tmp_node1=nodes[i]
                tmp_node2=nodes[i+1]
                lat1,lon1=tmp_node1.getpos()
                lat2,lon2=tmp_node2.getpos()
                distance=self.get_distance(lat1,lon1,lat2,lon2)
                self.near_map[tmp_node1.id].append((tmp_node2.id,road_type,distance))
                self.near_map[tmp_node2.id].append((tmp_node1.id,road_type,distance))

    def remove_adjacency(self, node_id1, node_id2):
        """
        删除两个节点之间的邻接关系（双向）

        参数:
            node_id1: 第一个节点的ID
            node_id2: 第二个节点的ID
        """
        # 从node_id1的邻接列表中删除node_id2
        if node_id1 in self.near_map:
            self.near_map[node_id1] = [
                (neighbor_id, road_type, distance)
                for neighbor_id, road_type, distance in self.near_map[node_id1]
                if neighbor_id != node_id2
            ]
        # 从node_id2的邻接列表中删除node_id1
        if node_id2 in self.near_map:
            self.near_map[node_id2] = [
                (neighbor_id, road_type, distance)
                for neighbor_id, road_type, distance in self.near_map[node_id2]
                if neighbor_id != node_id1
            ]

    def find_nearest_node(self, pos):
        """
        接受输入的坐标元组
        返回最近的路口节点的经纬度以及临近的两个node，以及roadtype
        """
        def point_to_segment_distance(x0, y0, x1, y1, x2, y2):
            ab_x = x2 - x1
            ab_y = y2 - y1
            ap_x = x0 - x1
            ap_y = y0 - y1
            ab_length_squared = ab_x * ab_x + ab_y * ab_y
            t = (ap_x * ab_x + ap_y * ab_y) / ab_length_squared
            if t <= 0:
                closest_x, closest_y = x1, y1  # 最近点为线段起点
            elif t >= 1:
                closest_x, closest_y = x2, y2  # 最近点为线段终点
            else:
                closest_x = x1 + t * ab_x
                closest_y = y1 + t * ab_y
            dx = x0 - closest_x
            dy = y0 - closest_y
            distance = math.sqrt(dx * dx + dy * dy)
            return distance, closest_x, closest_y#point_to_segment_distance返回了从(x0,y0)到（x1,y1),(x2,y2)确定的线段的最小距离，以及取到最小距离时候对应的点
        eps=1#通过加eps来保证点不是边缘的点，方便后续加点
        roadtype=""
        n_node0=self.nodes[0]
        n_node1=self.nodes[1]
        n_lat=0
        n_lon=0
        min_len=float('inf')
        lat=pos[0]
        lon=pos[1]
        for route in self.routes:
            tmproadtype=route.gettype()
            nodes=route.nodes
            for i in range(len(nodes)-1):
                tmp_node1=nodes[i]
                tmp_node2=nodes[i+1]
                lat1,lon1=tmp_node1.getpos()
                lat2,lon2=tmp_node2.getpos()
                tmp_len,tmp_lat,tmp_lon=point_to_segment_distance(lat,lon,lat1,lon1,lat2,lon2)
                if tmp_len<min_len:
                    min_len=tmp_len
                    n_node0=tmp_node1
                    n_node1=tmp_node2
                    n_lat=tmp_lat+eps
                    n_lon=tmp_lon+eps
                    roadtype=tmproadtype
        return n_lat,n_lon,n_node0,n_node1,roadtype

    def _dijkstra(self, start, end):
        dist = {_node.id: float('inf') for _node in self.nodes}
        dist[start] = 0
        prev = {_node.id: None for _node in self.nodes}
        heap = [(0, start)]
        while heap:
            current_dist, current_node = heapq.heappop(heap)
            current_dist=current_dist/1e5
            if current_node == end:
                break
            if current_dist > dist[current_node]:
                continue
            for neighbor, road_type, distance in self.near_map[current_node]:
                weight = distance
                if dist[neighbor] > current_dist + weight:
                    dist[neighbor] = current_dist + weight
                    prev[neighbor] = current_node
                    heapq.heappush(heap, (int(dist[neighbor]*1e5), neighbor))
        if prev[end] is None:
            return [start,end]
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = prev[current]
        return path[::-1]


    def kshortestroute(self, start_pos, end_pos,Node):
        """
        最近路径算法
        接受起点和终点节点的唯一标识符
        返回列表，元素是最小路径的转向点node的唯一标识符的列表
        """
        start_lat,start_lon,s_node1,s_node2,road_type1=self.find_nearest_node(start_pos)
        #start_node=node(0,start_lat,start_lon)
        s1_lat,s1_lon=s_node1.getpos()
        s2_lat,s2_lon=s_node2.getpos()
        Node[0].lat, Node[0].lon=(start_lat,start_lon)
        self.nodes.append(Node[0])
        self.nodes_id.add(0)
        self.near_map[s_node1.id].append((0, road_type1,self.get_distance(start_lat,start_lon,s1_lat,s1_lon)))
        self.near_map[s_node2.id].append((0, road_type1,self.get_distance(start_lat,start_lon,s2_lat,s2_lon)))
        self.near_map[0].append((s_node1.id, road_type1,self.get_distance(start_lat,start_lon,s1_lat,s1_lon)))
        self.near_map[0].append((s_node2.id, road_type1,self.get_distance(start_lat,start_lon,s2_lat,s2_lon)))
        #添加临时的初始点，id为0
        end_lat,end_lon,e_node1,e_node2,road_type2=self.find_nearest_node(end_pos)
        #end_node=node(1,end_lat,end_lon)
        e1_lat,e1_lon=e_node1.getpos()
        e2_lat,e2_lon=e_node2.getpos()
        Node[1].lat, Node[1].lon=(end_lat,end_lon)
        self.nodes.append(Node[1])
        self.nodes_id.add(1)
        self.near_map[e_node1.id].append((1, road_type2,self.get_distance(end_lat,end_lon,e1_lat,e1_lon)))
        self.near_map[e_node2.id].append((1, road_type2,self.get_distance(end_lat,end_lon,e2_lat,e2_lon)))
        self.near_map[1].append((e_node1.id, road_type2,self.get_distance(end_lat,end_lon,e1_lat,e1_lon)))
        self.near_map[1].append((e_node2.id, road_type2,self.get_distance(end_lat,end_lon,e2_lat,e2_lon)))
        #添加临时的终点，id为1
        try:
            nearest_path=self._dijkstra(0, 1)
        finally:
            self.remove_adjacency(s_node1.id,0)
            self.remove_adjacency(s_node2.id,0)
            self.remove_adjacency(e_node1.id,1)
            self.remove_adjacency(e_node2.id,1)
            self.nodes = [n for n in self.nodes if n.id not in (0, 1)]
            self.nodes_id.discard(0)
            self.nodes_id.discard(1)
        # 从邻接表中移除临时节点
            if 0 in self.near_map:
                del self.near_map[0]
            if 1 in self.near_map:
                del self.near_map[1]
        return nearest_path
