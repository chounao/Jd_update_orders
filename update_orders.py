import pymysql
import os
import requests
import json
import time


class update_jd_orders:
    def __init__(self):
        self.patah = os.getcwd()
        self.conn = None  # 初始化数据库连接对象
        self.session = requests.session()

    def update_session(self):
        self.cookie = self.read_txt()[2]
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'Cookie': self.cookie}
        self.session.headers.update(headers)
        return self.session

    def read_txt(self):
        # 读取txt文件
        with open(self.patah + '/set_data.txt', 'r', encoding='utf-8', errors='ignore') as file:
            data = file.read()
        # 提取数据
        self.db_info = int(data.split('environment = ')[1].split('\n')[0])
        self.shopname = data.split("shopname = '")[1].split("'\n")[0]
        self.cookie = data.split("cookie = '")[1].split("'\n")[0]
        self.searchId = data.split("searchId = '")[1].split("'\n")[0]
        self.orderid = [int(x) for x in data.split("order = ")[1].split('\n')[0].split(',')]
        # print(self.db_info, self.shopname, self.cookie, self.orderid,self.searchId)
        return self.db_info, self.shopname, self.cookie, self.orderid, self.searchId

    def get_jd_respons(self):
        txt_data = self.read_txt()
        self.shopname = txt_data[1]
        self.orderid = txt_data[3]
        self.searchId = txt_data[4]
        self.list_response = []
        # ,headers,shopName,orderSn
        self.session = self.update_session()
        get_ueserid = 'https://jdcsone.fhd001.com/info/getUserBaseInfo.do'
        userid_data = {'searchId': self.searchId, 'searchType': 3}
        id_body = self.session.post(get_ueserid, userid_data)
        # print(id_body)
        userid = id_body.json()['data']['userBase']['userId']


        get_shopid = 'https://jdcsone.fhd001.com/info/getThirdPartyInfo.do'
        shopid_data = {'userId': userid}
        shop_body = self.session.post(get_shopid, shopid_data)
        # print(shop_body.json())
        for i in shop_body.json()['data']:
            if i['name'] == self.shopname:
                self.shopid = i['platformKey']


        get_order_info = 'https://jdcsone.fhd001.com/info/getOrderDetailInfo.do'
        sql_temolate_list = []
        for id in self.orderid:
            order_info_body = {'userId': userid, 'shopId': self.shopid, 'platform': 'JD',
                               'orderSn': self.orderid[0]}
            info_data = self.session.post(get_order_info, order_info_body)
            get_infoData = str(info_data.json()['data']['orderSyncInfo'])
            responseJson = json.loads(get_infoData)['responseJson']
            sql_updata_template = "UPDATE jd_push_01.yd_pop_order SET orderId = {},responsejson = {} WHERE state = '{}'"
            sql_select_template = 'SELECT * FROM jd_cluster_01.jdp_order_part WHERE orderSn = {}'
            sql_update = sql_updata_template.format(id, json.dumps(responseJson, ensure_ascii=False), str(self.shopname))
            sel_select = sql_select_template.format(id)
            sql_temolate_list.append((sql_update, sel_select))
        # print(sql_temolate_list)
        return sql_temolate_list



    def create_connection(self, host, port, user, passwd, db, charset):
        try:
            self.conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset)
            return self.conn.cursor()
        except Exception as e:
            return e

    def select_data(self):
        environment = self.read_txt()[0]
        sql_txt=self.get_jd_respons()
        db_info = {
            208: [{'host': '192.168.16.200', 'port': 3307, 'user': 'root', 'passwd': '123456qqq','db': 'jd_push_01', 'charset': 'utf8mb4'},
                  {'host': '192.168.16.200', 'port': 3307, 'user': 'root', 'passwd': '123456qqq','db': 'qnjy_cluster_01', 'charset': 'utf8mb4'}],
            209: [{'host': '192.168.16.201', 'port': 3307, 'user': 'root', 'passwd': '123456qqq','db': 'jd_push_01', 'charset': 'utf8mb4'},
                  {'host': '192.168.16.201', 'port': 3307, 'user': 'root', 'passwd': '123456qqq','db': 'qnjy_cluster_01', 'charset': 'utf8mb4'}]
        }
        for key,values in db_info.items():
            if environment == key:
                db_data = values[0]
                # print(db_data)

                self.conn = self.create_connection(host=db_data['host'],
                                                     port=db_data['port'],
                                                     user=db_data['user'],
                                                     passwd=db_data['passwd'],
                                                     db=db_data['db'],
                                                     charset=db_data['charset'])
                count = 0
                for i in sql_txt:

                    print("订单还未更新到数据库\n********************************************************************\nUPDATE\n********************************************************************\n")
                    self.conn.execute(i[0])
                    print(i[0])
                    try:
                        print('********************************************************************\nSELECT\n********************************************************************\n')
                        self.conn.execute(i[1])
                        result = self.conn.fetchall()
                        print(i[1])

                        count += 1
                        num = 10
                        if not result:
                            for t in range(num):

                                self.conn.execute(i[1])
                                print('预计查询{}次当前第{}次'.format(num,t+1))
                                time.sleep(3)
                                if t+1 == num:
                                    print("在jd_cluster_01.jdp_order_part依然未找到该订单")

                        else:
                            print('已经插入条：{} '.format(count))
                    except ValueError as e:
                            return e

                self.conn.close()
                print('流程结束关闭数据库')


if __name__ == '__main__':
    a = update_jd_orders()
    a.select_data()
