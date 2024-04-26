import datetime
import re
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

    def get_times(self,day):
        stat_time = datetime.date.today()-datetime.timedelta(days=day)
        # print(day)
        stat_timestamp = int(datetime.datetime(stat_time.year,stat_time.month,stat_time.day).timestamp())
        end_timestamp = int(time.time())
        # print(end_timestamp,stat_timestamp)
        return stat_timestamp,end_timestamp

    def read_txt(self):
        # 读取txt文件
        with open(self.patah + '/set_data.txt', 'r', encoding='utf-8', errors='ignore') as file:
            data = file.read()
        # 提取数据
        self.db_info = int(data.split('environment = ')[1].split('\n')[0])
        self.day = int(data.split('day = ')[1].split('\n')[0])
        self.shopname = data.split("shopname = '")[1].split("'\n")[0]
        self.cookie = data.split("cookie = '")[1].split("'\n")[0]
        self.searchId = data.split("searchId = '")[1].split("'\n")[0]
        self.jd_tokne = data.split("jd_token = '")[1].split("'\n")[0]
        # self.orderid = [int(x) for x in data.split("order = ")[1].split('\n')[0].split(',')]
        return self.db_info, self.shopname, self.cookie, self.day, self.searchId,self.jd_tokne

    def get_ordersid(self):
        txt_data = self.read_txt()
        time = self.get_times(txt_data[3])
        h = { 'Content - Type':'application / x - www - form - urlencoded'}
        body = {
            'page': 1,
            'pageSize': 200,
            'shopId': 13000723,
            'startTime':time[0],
            'endTime': time[1],
            'shopName':txt_data[1],
            'deviceId':'5IE5BGMNVCQ7DOPMXFED7YS2AKYPYNI755RSA7DGILPI5AKRNSLPZI4XAFKBMVV5HGNBEAHJAKEKIYZO7Z2WEML25A',
            'useTime': 5,
            'referer':'jdportal',
            'token': txt_data[5]
        }
        url ='https://jdapione.fhd001.com/fhd/jdp/queryIncrementOrderByTime.do'
        r = requests.post(url,body,h)
        # print(r.json()['data'])
        order_list = []
        for i in r.json()['data']['list']:
            order_list.append(i['orderSn'])
        # print(order_list)
        return order_list
    def get_jd_respons(self):
        txt_data = self.read_txt()

        self.shopname = txt_data[1]
        orderid = self.get_ordersid()
        self.searchId = txt_data[4]
        self.list_response = []
        # ,headers,shopName,orderSn
        self.session = self.update_session()
        get_ueserid = 'https://jdcsone.fhd001.com/info/getUserBaseInfo.do'
        userid_data = {'searchId': self.searchId, 'searchType': 3}
        id_body = self.session.post(get_ueserid, userid_data)
        #print(id_body.json())
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
        for id in orderid:
            order_info_body = {'userId': userid, 'shopId': self.shopid, 'platform': 'JD',
                               'orderSn': id}
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
            new_countent = re.sub(local_pattern, mapping, content)
            with open(path, 'w') as f:
                f.write(new_countent)




    def create_connection(self, host, port, user, passwd, db, charset):
        try:
            self.conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset)
            return self.conn.cursor()
        except Exception as e:
            return e

    def select_data(self):
        if self.set_host():
            pass
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
