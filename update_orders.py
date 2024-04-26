import datetime
import re
import pymysql
import os
import requests
import json
import time


class update_jd_orders:
    def __init__(self):
        self.path = os.getcwd()
        self.conn = None  # 初始化数据库连接对象
        self.db_info = None
        self.shop_name = None
        self.cookie = None
        self.day = None
        self.searchId =None
        self.jd_token = None
        self.stat_timestamp = None
        self.end_timestamp = None
        self.stat_time = None
    def update_session(self):
        self.read_txt()
        self.session = requests.session()
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'Cookie': self.cookie}
        print(headers)
        self.session.headers.update(headers)
        return self.session

            
    def get_times(self):
        self.read_txt()
        self.stat_time = datetime.date.today()-datetime.timedelta(days=self.day)
        self.stat_timestamp = int(datetime.datetime(self.stat_time.year,self.stat_time.month,self.stat_time.day).timestamp())
        self.end_timestamp = int(time.time())
        return self.stat_timestamp,self.end_timestamp
    
    def read_txt(self):
        # 读取txt文件
        with open(self.path + '/set_data.txt', 'r', encoding='utf-8', errors='ignore') as file:
            data = file.read()
        # 提取数据
        self.db_info = int(data.split('environment = ')[1].split('\n')[0])
        self.day = int(data.split('day = ')[1].split('\n')[0])
        self.shop_name = data.split("shopName = '")[1].split("'\n")[0]
        self.cookie = data.split("cookie = '")[1].split("'\n")[0]
        self.searchId = data.split("searchId = '")[1].split("'\n")[0]
        self.jd_token = data.split("jd_token = '")[1].split("'\n")[0]
        print(self.cookie)
        print(self.jd_token)
        #print( self.db_info, self.shop_name, self.cookie, self.day, self.searchId, self.jd_token)
        return self.db_info, self.shop_name, self.cookie, self.day, self.searchId, self.jd_token
    def get_ordersId(self):
        self.read_txt()
        self.get_times()
        h = { 'Content - Type':'application / x - www - form - urlencoded'}
        body = {
            'page': 1,
            'pageSize': 200,
            'shopId': 13000723,
            'startTime':self.stat_timestamp,
            'endTime': self.end_timestamp,
            'shopName':self.shop_name,
            'deviceId':'5IE5BGMNVCQ7DOPMXFED7YS2AKYPYNI755RSA7DGILPI5AKRNSLPZI4XAFKBMVV5HGNBEAHJAKEKIYZO7Z2WEML25A',
            'useTime': 5,
            'referer':'jdportal',
            'token': self.jd_token
        }
        url ='https://jdapione.fhd001.com/fhd/jdp/queryIncrementOrderByTime.do'
        r = requests.post(url,body,h)
        order_list = []
        for i in r.json()['data']['list']:
            order_list.append(i['orderSn'])
        # print(order_list)
        return order_list
    def get_jd_respons(self):
        self.session = self.update_session()
        orderid = self.get_ordersId()
        self.list_response = []
        get_ueserId = 'https://jdcsone.fhd001.com/info/getUserBaseInfo.do'
        userid_data = {'searchId': self.searchId, 'searchType': 3}
        id_body = self.session.post(get_ueserId, userid_data)
        print(id_body.text)
        print(id_body.json())
        userid = id_body.json()['data']['userBase']['userId']



        get_shopId = 'https://jdcsone.fhd001.com/info/getThirdPartyInfo.do'
        shopid_data = {'userId': userid}
        shop_body = self.session.post(get_shopId, shopid_data)
        # print(shop_body.json())
        for i in shop_body.json()['data']:
            if i['name'] == self.shop_name:
                self.shopId = i['platformKey']



        get_order_info = 'https://jdcsone.fhd001.com/info/getOrderDetailInfo.do'
        sql_Temolate_list = []
        for id in orderid:
            order_info_body = {'userId': userid, 'shopId': self.shopId, 'platform': 'JD',
                               'orderSn': id}
            info_data = self.session.post(get_order_info, order_info_body)
            get_infoData = str(info_data.json()['data']['orderSyncInfo'])
            responseJson = json.loads(get_infoData)['responseJson']
            sql_updata_template = "UPDATE jd_push_01.yd_pop_order SET orderId = {},responsejson = {} WHERE state = '{}'"
            sql_select_template = 'SELECT * FROM jd_cluster_01.jdp_order_part WHERE orderSn = {}'
            sql_update = sql_updata_template.format(id, json.dumps(responseJson, ensure_ascii=False), str(self.shop_name))
            sel_select = sql_select_template.format(id)
            sql_Temolate_list.append((sql_update, sel_select))
        print(sql_Temolate_list)
        return sql_Temolate_list


    def set_host(self):
        # 'ect/hosts'  Mac的地址
        path = 'C:\Windows\System32\drivers\etc\hosts'
        with open(path,'r')as f:
            content = f.read()
        local ={'do_main':'m.local', 'ip' : '192.168.16.200'}
        jd_host = {'do_main':'jdapione.fhd001.com', 'ip' : '192.168.16.208'}
        jd_pattern = r'\b{}\b'.format(jd_host.get('do_main'))
        local_pattern = r'\b{}\b'.format(local.get('do_main'))
        if re.search(local_pattern,content):
            print('数据库的host做了')
            try:
                if re.search(jd_pattern, content):
                    print('jd的host在208\n修改jdhost')
                    mapping_jd = '{}\t{}'.format('39.96.252.227:443', jd_host.get('do_main'))
                    new_countent = re.sub(jd_pattern, mapping_jd, content)
                    with open(path, 'w') as f:
                        f.write(new_countent)
                else:
                    print('京东host正常')
            except ValueError as e:
                return e
        else:
            print('208数据库不存，进行添加操作')
            mapping = '{}\t{}'.format(local.get('ip'), jd_host.get('do_main'))
            new_content = re.sub(local_pattern, mapping, content)
            with open(path, 'w') as f:
                f.write(new_content)




    def create_connection(self, host, port, user, passwd, db, charset):
        try:
            self.conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset)
            return self.conn.cursor()
        except Exception as e:
            return e

    def select_data(self):
        # if self.set_host():
        #     pass
        self.read_txt()
        sql_txt=self.get_jd_respons()
        db_info = {
            208: [{'host': '192.168.16.200', 'port': 3307, 'user': 'root', 'passwd': '123456qqq','db': 'jd_push_01', 'charset': 'utf8mb4'},
                  {'host': '192.168.16.200', 'port': 3307, 'user': 'root', 'passwd': '123456qqq','db': 'qnjy_cluster_01', 'charset': 'utf8mb4'}],
            209: [{'host': '192.168.16.201', 'port': 3307, 'user': 'root', 'passwd': '123456qqq','db': 'jd_push_01', 'charset': 'utf8mb4'},
                  {'host': '192.168.16.201', 'port': 3307, 'user': 'root', 'passwd': '123456qqq','db': 'qnjy_cluster_01', 'charset': 'utf8mb4'}]
        }
        for key,values in db_info.items():
            if self.db_info == key:
                db_data = values[0]
                # print(db_data)

                self.conn = self.create_connection(host=db_data['host'],
                                                     port=db_data['port'],
                                                     user=db_data['user'],
                                                     passwd=db_data['passwd'],
                                                     db=db_data['db'],
                                                     charset=db_data['charset'])
                count = 0
                print('********************************************************************\n首次操作会同步所有的订单')
                for i in sql_txt:
                    self.conn.execute(i[0])
                    print('已经同步{}条数据\n查询是否同步成功'.format(count+1))
                    try:
                        print('{}'.format(i[1]))
                        self.conn.execute(i[1])
                        result = self.conn.fetchall()
                        count+=1
                        num = 10
                        if not result:
                            for t in range(num):
                                self.conn.execute(i[1])
                                print('预计查询{}次当前第{}次'.format(num,t+1))
                                time.sleep(3)
                                if t+1 == num:
                                    print("已经同步{}次，在jd_cluster_01.jdp_order_part依然未找到该订单".format(num))
                        else:
                            print('同步成功,目前更新{}个订单\n*******************************************************************'.format(count))
                    except ValueError as e:
                            return e

                self.conn.close()
                print('流程结束关闭数据库')


if __name__ == '__main__':
    a = update_jd_orders()
    a.select_data()