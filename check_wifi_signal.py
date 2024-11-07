

#各フロアに何台、どのMAC があるかの情報が無いけど、地図はある。

#2024_trusco\expt_data\20241003


from glob import glob

import cv2

import pandas as pd
import os
import pickle
import numpy as np
import tkinter as tk
import json
import datetime

bibs = None


# bibs -> id 対応
def bibs_files():
    global bibs
    bibs = pd.read_excel("/mnt/bigdata/01_projects/2024_trusco/expt_data/20241003/bibs.xlsx")
#    bibs.describe()
#    print(bibs)
#    for bib in bibs:
#        print(bib)

def subject2id(sub):
    return bibs[bibs["subject"] == sub]["id"].values[0]

# bibs -> id 対応を行ったデータから pickle　を作成
def checkWiFi_files():
    worker_dirs = glob("/mnt/bigdata/01_projects/2024_trusco/expt_data/20241003/wifi/*")
    allpd = pd.DataFrame(columns=["id","time","mac","rssi"])
    for worker in worker_dirs:
        files = glob(worker + "/*.csv")
        subject_id = int(os.path.basename(worker))
        print("Subj:",subject_id,"->", subject2id(subject_id), )
        dfo = pd.DataFrame(columns=["time","mac","rssi"])
        for file in files:
            print(file)
            df = pd.read_csv(file, names=["time","mac","rssi"])
            dfo = pd.concat([dfo,df])
        print(len(dfo))
        dfo['id']=subject2id(subject_id)
        print(dfo)
        allpd = pd.concat([allpd,dfo])
    
    print(len(allpd))
    with open("/mnt/bigdata/01_projects/2024_trusco/expt_data/20241003/wifi/all.pkl","wb") as f:
        pickle.dump(allpd,f)


# bibs -> id 対応を行ったデータから pickle　を作成
def checkBLE_files():
    worker_dirs = glob("/mnt/bigdata/01_projects/2024_trusco/expt_data/20241003/ble/*")
    allpd = pd.DataFrame(columns=["id","time","mac","rssi"])
    for worker in worker_dirs:
        files = glob(worker + "/*.csv")
        subject_id = int(os.path.basename(worker))
        print("Subj:",subject_id,"->", subject2id(subject_id), )
        dfo = pd.DataFrame(columns=["time","mac","rssi"])
        for file in files:
            print(file)
            df = pd.read_csv(file, names=["time","mac","rssi"])
            dfo = pd.concat([dfo,df])
        print(len(dfo))
        dfo['id']=subject2id(subject_id)
        print(dfo)
        allpd = pd.concat([allpd,dfo])
    
    print(len(allpd))
    with open("/mnt/bigdata/01_projects/2024_trusco/expt_data/20241003/ble/all.pkl","wb") as f:
        pickle.dump(allpd,f)
    return allpd


def read_wifi_data():
    with open("/mnt/bigdata/01_projects/2024_trusco/expt_data/20241003/wifi/all.pkl","rb") as f:
        alldp = pickle.load(f)
    return alldp

def read_BLE_data():
    with open("/mnt/bigdata/01_projects/2024_trusco/expt_data/20241003/ble/all.pkl","rb") as f:
        alldp = pickle.load(f)
    return alldp
    
    
    # check unique MACs
#    macs =alldp[alldp["rssi"]>=-45]["mac"].unique()
#    macs.sort()
#    print(macs)
#    print(len(macs))

# 以下は、トラッキング情報と地図のずれを補正するための情報
BASE_X = 3885.356
BASE_Y = 812.703

# １F の地図の全体イメージを読み込み
def read_empty_floor_image():
    img = cv2.imread("/mnt/bigdata/01_projects/2024_trusco/asset/empty_20241003/stitched_20241106105031.jpg")
    print(img.shape)
    return img

def load_json_file(file):
    with open(file, 'r') as f:
        workers = json.load(f)
    return workers

def read_worker_tracks():
    # 正解データ付きが重要！
    workers = load_json_file("/mnt/vanda/01_projects/2024_trusco/20241003-track/1106tracking_result_20241003_worker_body_1100_1200_updated.json")
    return workers


# 無線計測データから、特定のワーカの情報のみを取り出す
def get_worker(workers,workerID):
    workData = []
    for frame in workers:
        for track in frame['tracks']:
            if 'subj_id' in track:
                if track['subj_id']==str(workerID):
                    fid = frame['frame_id']
                    x,y,w,h = track['bbox']
                    t= datetime.datetime(2024,10,3,11,00)+datetime.timedelta(seconds=fid*0.2)                        
                    workItem ={
                        "track": fid,
                        "unix": t.timestamp(),
                        "date": str(t)[:21],
                        "pos": [int(x+w/2-BASE_X),int(y+h/2-BASE_Y)]
                    }
                        
                    workData.append(workItem)
    return workData


# ワーカデータと、無線のMACデータを統合
def draw_img_with(nimg, wg,sorted_mac):
    count = 0
    draw_count = 0
    wg_step = 0
    for row in sorted_mac.itertuples():  #時刻でソート済み
        t = row.time
        while wg_step < len(wg) and t > wg[wg_step]["unix"] :
            wg_step+= 1
            count += 1
#            if count % 100 == 0:
#                print("count up", count, wg_step, t- wg[wg_step]["unix"])
            
        if wg_step >= len(wg):
            break
            
        dt = wg[wg_step]["unix"]
        if abs(t-dt) < 2:
#        print(t,dt)
            x,y = wg[wg_step]['pos']
#            heat = -(row.rssi+40)*20
#            heat = -(row.rssi+70)*20
            heat = -(row.rssi+85)*20
            if heat> 255:
                heat = 255
            if heat < 0:
                heat = 0
            
            color = (heat, 0, 255 - heat)
            print(count, "diff:", int(t-dt),x,y, heat,color)
#            nimg = cv2.circle(nimg, (x, y), 18,color,-1)
#            nimg = cv2.putText(nimg,str(row.rssi), (x-20, y),  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 3, cv2.LINE_AA)        
            nimg = cv2.circle(nimg, (x, y), 32,color,-1)
            nimg = cv2.putText(nimg,str(row.rssi), (x-20, y),  cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3, cv2.LINE_AA)        
            draw_count+=1
        count += 1
        wg_step+= 1
    return nimg,draw_count


#---

non_1f_macs_list = """
MAC: 108 ac:44:f2:bd:1d:f8 0
MAC: 113 ac:44:f2:bd:1e:00 0
MAC: 114 ac:44:f2:bd:1e:01 0
MAC: 115 ac:44:f2:bd:37:f8 0
MAC: 116 ac:44:f2:bd:31:38 0
MAC: 120 ac:44:f2:bd:49:e1 0
MAC: 121 ac:44:f2:bd:49:e0 0
MAC: 123 ac:44:f2:bd:56:78 0
MAC: 124 ac:44:f2:bd:27:f8 0
MAC: 127 ac:44:f2:bd:30:58 0
MAC: 128 ac:44:f2:bd:29:78 0
MAC: 129 ac:44:f2:bd:55:b8 0
MAC: 131 c2:5d:83:77:d9:f0 0
MAC: 132 ac:44:f2:bd:29:f8 0
MAC: 134 ac:44:f2:bd:5a:58 0
MAC: 136 00:19:3b:22:48:f3 0
MAC: 137 ac:44:f2:bd:21:f8 0
MAC: 139 ac:44:f2:bd:38:01 0
MAC: 142 ac:44:f2:bd:38:00 0
MAC: 143 ac:44:f2:bd:3d:b8 0
MAC: 144 ac:44:f2:ae:70:01 0
MAC: 145 ac:44:f2:bd:56:38 0
MAC: 147 68:e1:dc:ed:7b:a1 0
MAC: 149 68:e1:dc:ef:25:a1 0
MAC: 150 68:e1:dc:ef:25:a2 0
""".split("\n")
non_1f_macs = [x.split()[2] for x in non_1f_macs_list if len(x)>0]



def doit_map():
    bibs_files()
#    checkWiFi_files()
    wifi_data = read_wifi_data()

    workers = read_worker_tracks()
#    workData = get_worker(workers, 3)

    # 特定の基地局についてMapを作ってみたい。

    floor_img = read_empty_floor_image()

    gmac = wifi_data[(wifi_data['rssi']> -50)].groupby(['mac']).size()
    df = gmac.sort_values(ascending=False)[:50]

    mac_list = []
    mac_count = []
    for row in df.items():
        mac_list.append(row[0])
        mac_count.append(row[1])
    
    ct = 101

    for target_mac in mac_list:
#        print("MAC:",ct, target_mac)
        floor_img = read_empty_floor_image()
        draw_sum = 0
        only_mac = wifi_data[(wifi_data['mac'] == target_mac) & ((wifi_data['rssi']> -50))]

        for id in range(1,38):
            macs =  only_mac[only_mac['id']==id].sort_values(['time'])
            if len(macs) > 0:
                print("Working for ID",ct-100,id, len(macs), mac_count[ct-101])            
                newimg,draw_plus = draw_img_with(floor_img,  get_worker(workers,id),macs)
                draw_sum += draw_plus
        print("MAC:",ct, target_mac, draw_sum) 
        cv2.imwrite( f"WIFI:{ct}_{mac_count[ct-101]+10000}_{target_mac}_map.jpg", newimg)
        ct += 1





def doit_map_ble():
    bibs_files()
    ble_data = read_BLE_data()
    workers = read_worker_tracks()

    # 特定の基地局についてMapを作ってみたい。
    floor_img = read_empty_floor_image()

    gmac = ble_data[(ble_data['rssi']> -80)].groupby(['mac']).size()
    df = gmac.sort_values(ascending=False)[:50]

    mac_list = []
    mac_count = []
    for row in df.items():
        mac_list.append(row[0])
        mac_count.append(row[1])
    
    ct = 101

    for target_mac in mac_list:
#        print("MAC:",ct, target_mac)
        floor_img = read_empty_floor_image()
        draw_sum = 0
        only_mac = ble_data[(ble_data['mac'] == target_mac) & ((ble_data['rssi']> -100))]

        for id in range(1,38):
            macs =  only_mac[only_mac['id']==id].sort_values(['time'])
            if len(macs) > 0:
#                print("Working for ID",ct-100,id, len(macs), mac_count[ct-101])            
                newimg,draw_plus = draw_img_with(floor_img,  get_worker(workers,id),macs)
                draw_sum += draw_plus
        print("MAC:",ct, target_mac, draw_sum) 
        if draw_sum > 0:
            cv2.imwrite( f"BLE:{ct}_{mac_count[ct-101]+10000}_{target_mac}_map.jpg", newimg)
        ct += 1


def do_ble_pickle():
    bibs_files()
    ble = checkBLE_files()
    print(ble)


if __name__ == "__main__":
    #print(non_1f_macs)
    #これらの mac が -50db以上であったら、別フロアで作業と認定すべし！
    doit_map_ble()
