import requests
import pandas as pd
import numpy as np
import folium
from folium.plugins import MiniMap
import requests
import folium
import collections
from IPython.display import display
import math
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup as bs
import os
import time
import pandas as pd
import urllib.request
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, \
	TimeoutException  # 예외처리를 위한 예외들
import csv
import sys
from bs4 import BeautifulSoup


def get_pink_restaurants(center_x, center_y, radius):
	url = 'https://dapi.kakao.com/v2/local/search/category.json'
	params = {
		'category_group_code': 'FD6',  # 음식점 카테고리 코드 'FD6'
		'x': center_x,
		'y': center_y,
		'radius': radius
	}
	headers = {"Authorization": "KakaoAK 4e903055f0fa8e279698b16c8364ddfd"}
	all_data_list = []  # 모든 결과를 저장할 리스트
	
	page = 1  # 페이지 초기값
	
	while True:
		params['page'] = page
		resp = requests.get(url, params=params, headers=headers)
		data = resp.json()
		all_data_list.extend(data['documents'])
		
		if data['meta']['is_end']:
			break  # 더 이상 결과가 없으면 종료
		
		page += 1  # 다음 페이지로 이동
	
	return all_data_list


# 덕성여대 위치
deokseong_lat = 37.652565  # 덕성여대 위도
deokseong_lng = 127.016343  # 덕성여대 경도
radius = 1000  # 반경 1km 설정

# 음식점 데이터 가져오기
restaurants = get_pink_restaurants(deokseong_lng, deokseong_lat, radius)

# 데이터 처리 및 출력
X = []
Y = []
stores = []
road_address = []
place_url = []
ID = []
for place in restaurants:
	X.append(float(place['x']))
	Y.append(float(place['y']))
	stores.append(place['place_name'])
	road_address.append(place['road_address_name'])
	place_url.append(place['place_url'])
	ID.append(place['id'])

df = pd.DataFrame({'ID': ID, 'stores': stores, 'X': X, 'Y': Y, 'road_address': road_address, 'place_url': place_url})
df.to_csv('pink_restaurants_data.csv', index=False)
print('Total number of pink restaurants:', len(df))
print(df.head())

# 지도 생성
map_obj = folium.Map(location=[deokseong_lat, deokseong_lng], zoom_start=15)

# 음식점 위치에 마커 추가
for i in range(len(df)):
	folium.Marker(
		location=[df['Y'][i], df['X'][i]],
		tooltip=df['stores'][i],
		popup=df['place_url'][i],
		icon=folium.Icon(color='pink')
	).add_to(map_obj)

# 지도 저장
map_obj.save("pink_restaurants_map.html")

data = pd.read_csv('C:/Users/yujinlee/PycharmProjects/crawling2/pink_restaurants_data.csv')

restaurant_names = data['stores']
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=chrome_options)

storepackage = []  # storepackage 리스트 정의
timepackage = []
categorypackage = []
driver.get("https://map.naver.com/v5/")
try:
	element = WebDriverWait(driver, 20).until(
		EC.presence_of_element_located((By.CLASS_NAME, "input_search"))
	)  # 입력창이 뜰 때까지 대기
finally:
	pass

#for restaurant_name in restaurant_names[:5]:
for restaurant_name in restaurant_names:
	try:
		search_box = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "input_search")))
		search_box.send_keys(restaurant_name)
		search_box.send_keys(Keys.ENTER)
		time.sleep(7)
		
		search_frame_present = False
		try:
			frame = driver.find_element(By.CSS_SELECTOR, "iframe#searchIframe")
			driver.switch_to.frame(frame)
			search_frame_present = True
		except NoSuchElementException:
			pass
		
		if search_frame_present:
			time.sleep(3)
			try:
				search_element = driver.find_element(By.XPATH,
													 '//*[@id="_pcmap_list_scroll_container"]/ul/li[1]/div[1]/div[2]/a[1]/div/div/span[1]')
				ActionChains(driver).move_to_element(search_element).click().perform()
				time.sleep(5)
				current_window_handle = driver.current_window_handle
				driver.switch_to.window(driver.window_handles[-1])
				WebDriverWait(driver, 10).until(
					EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe#entryIframe")))
			except NoSuchElementException:
				pass
			# 이게 iframe 있는데 내용 없는 경우 즉 포장 안되는경우, 네이버크롤링 안되는 경우라고 생각하기
		else:
			entry_frame = driver.find_element(By.CSS_SELECTOR, "iframe#entryIframe")
			driver.switch_to.frame(entry_frame)
		
		time_clicks = driver.find_elements(By.CLASS_NAME, "_UCia")
		if len(time_clicks) > 1:
			realtime = time_clicks[1]
			realtime.click()
		
		infos = driver.find_elements(By.CSS_SELECTOR, ".vV_z_")
		time.sleep(5)
		categories = driver.find_elements(By.CSS_SELECTOR, ".DJJvD")
		storetimes = driver.find_elements(By.CSS_SELECTOR, ".gKP9i.RMgN0")
		#times = driver.find_elements(By.CSS_SELECTOR, ".A_cdD")

		
		packaging_found = False
		time_found = False
		category_found = False
		for info in infos:
			if "포장" in info.text:
				packaging_info = info.text
				print(info.text)
				packaging_found = True
		
		for category in categories:
			category_info = category.text
			print(category.text)
			category_found = True
			
		for storetime in storetimes:
			#storetime_info = ''.join([storetime.text for storetime in storetimes])
			storetime_info = storetime.text
			print(storetime.text)
			time_found = True
		

		
		if packaging_found:
			storepackage.append(packaging_info)
		else:
			storepackage.append('포장안하는 매장')
		
		if time_found:
			timepackage.append(storetime_info)
		else:
			timepackage.append('시간 안나오는 매장')
		
		if category_found:
			categorypackage.append(category_info)
		else:
			categorypackage.append('카테고리 안나오는 매장')
		
		#menuclick = driver.find_elements(By.CSS_SELECTOR, ".veBoZ")
		
		# for item in menuclick:
		#   if "메뉴" in item.text:
		#      item.click()
		
		driver.switch_to.default_content()
		deletebox = driver.find_element(By.CLASS_NAME, "button_clear")
		deletebox.click()
	
	except NoSuchElementException:
		storepackage.append('이상할때..')

print(storepackage)
new_data = pd.DataFrame({'포장여부': storepackage, '시간여부': timepackage, '카테고리': categorypackage})

data = pd.concat([data, new_data], axis=1)

print(data)
data.to_csv('finaldata.csv', index=False)