import http.client
import json
import ssl
import requests
import csv
import database as db


# Deleting the order from orders and order_ofe_status tables if the order_id matches the value from the sampleorder
# Deleting from both the tables because of foreign key constraint 
def delete_old_orderid_DB():
    with open('sampleorder.json') as f:
        data = json.load(f)
        order_id = data['orderId']
    cur1 = db.con.cursor()
    cur2 = db.con.cursor()
    cur1.execute("select * from order_ofe_status")
    cur2.execute("select * from orders")
    row1 = cur1.fetchall()
    row2 = cur2.fetchall()
    for r in row1:
        if int(r[0]) == int(order_id):
            query = "delete from order_ofe_status where order_id = %s"
            id = order_id
            cur1.execute(query, (id,))
            print('order ofe deleted')
            db.con.commit()
    for r in row2:
        if int(r[0]) == int(order_id):
            query = "delete from orders where id = %s"
            id = order_id
            cur2.execute(query, (id,)) 
            print('orders deleted') 
            db.con.commit()
    

#def new_order_booking
  # Add code to place a new booking from disney
  # Validate status code is 200 and the entry is updated in the orders table
  # Need to do CERTS change and setup properly
def new_order_booking():
    delete_old_orderid_DB()
    with requests.Session() as s:                             # Mock Server  
        url = "https://ofe-mock.jupiter.staging.qubewire.com/studio/ofe/v1/orders/contentorders/"   
        headers = {'Content-type': 'application/json'}
        with open('sample_order.json') as f:
            sample_order = json.load(f)
        conn.request("POST", "/order", json.dumps(sample_order), headers)
        r = conn.getresponse()
        return r.status_code


# Downloading the New/Inflight orders csv and validating the order_id is same from sampleorder and checking in DB
def order_download(order_type):
    with requests.Session() as s:
        if order_type == 'New':
            url = "https://disney-adapter.jupiter.staging.qubewire.com/v1/reports/new-orders"
            with open('auth.txt') as line:
                auth_t = line.readline()
            headers = {
                'authorization': "Bearer " + auth_t,
            }
            r = s.get(url, headers=headers)
            with open('new_order.csv', 'w') as f:
                writer = csv.writer(f)
                for line in r.iter_lines():
                    writer.writerow(line.decode('utf-8').split(','))
            with open('new_order.csv', 'r') as csvFile:
                data = csv.DictReader(csvFile)
                for line in data:
                    OrderID = line['OrderID']

            cur = db.con.cursor()
            cur.execute("select * from orders")
            rows = cur.fetchall()
            for r in rows:
                if int(r[0]) == int(OrderID):
                    return True
            return False

        elif order_type == 'Inflight':
            url = "https://disney-adapter.jupiter.staging.qubewire.com/v1/reports/inflight"
            with open('auth.txt') as line:
                auth_t = line.readline()
            headers = {
                'authorization': "Bearer " + auth_t,
            }
            r = s.get(url, headers=headers)
            with open('inflight.csv', 'w') as f:
                writer = csv.writer(f)
                for line in r.iter_lines():
                    writer.writerow(line.decode('utf-8').split(','))
            with open('inflight.csv', 'r') as csvFile:
                data = csv.DictReader(csvFile)
                for line in data:
                    OrderID = line['OrderID']

            cur = db.con.cursor()
            cur.execute("select * from orders")
            rows = cur.fetchall()
            for r in rows:
                if int(r[0]) == int(OrderID):
                    return True
            return False

            
                


# This function replaces QW status in a new csv file to_upload.csv

def change_status_in_csv(path,column_header,str_to_replace,str_to_replace_with):
    text = open(path, "r")
    text_lst = [i for i in text]
    for row in range(len(text_lst)):
        if(row == 0):
                if (column_header in text_lst[row]):
                    count = str(text_lst[row]).split(column_header+",")[0].count(",")
        else:
                test = str(text_lst[row]).split(",")
                test[count]=test[count].strip()
                if test[count]==str_to_replace:
                    test[count] = str_to_replace_with
                text_lst[row] = ",".join(test)
    text=''.join([i for i in text_lst])
    x = open('to_upload.csv',"w")
    x.writelines(text)
    x.close()



# Upload the updated csv back to Disney
def disney_status_upload(new_status):
    change_status_in_csv('new_order.csv', 'QW Status', " ", new_status)
    with requests.Session() as s:
        url = 'https://disney-adapter.jupiter.staging.qubewire.com/v1/upload'
        with open('auth.txt') as line:
            auth_t = line.readline()
        headers = {
            'authorization': "Bearer " + auth_t,
        }
        with open('to_upload.csv', 'r') as f:
            r = requests.post(url, files={'report.csv': f}, headers=headers)
            return r.status_code

