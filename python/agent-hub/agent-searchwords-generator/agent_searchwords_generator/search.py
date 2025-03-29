# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 11:49:22 2024
@author: Administrator
"""
 
# 导入相关模块
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json
import random as rd
 
def export_results_to_json(results, file_name="results.json"):
    """
    将抓取的结果以 JSON 格式保存到文件。
    参数:
    - results (list): 包含搜索结果的列表，格式为 {"title": 标题, "link": 链接}
    - file_name (str): 保存的文件名，默认为 "results.json"
    """
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"结果已成功导出到文件: {file_name}")
    except Exception as e:
        print(f"导出结果时发生错误: {e}")
 
# 配置 Selenium 浏览器驱动
def init_browser():
    """
    初始化浏览器设置。
    配置 Chrome 浏览器选项和驱动路径。
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")  # 禁用 GPU 加速（可选）
    # 如需要无头模式，取消以下注释
    chrome_options.add_argument("--headless")
    #service = Service(r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chromedriver.exe")  # 请确保路径正确
    driver = webdriver.Chrome(options=chrome_options)
    return driver
 
# 爬取百度搜索结果
def scrape_baidu_results(keyword, max_pages=1):
    """
    爬取百度搜索结果。
    
    参数:
    - keyword (str): 搜索关键词
    - max_pages (int): 要抓取的页数，默认 3 页
    
    返回:
    - results (list): 包含每页搜索结果的列表，格式为 {"title": 标题, "link": 链接}
    """
    driver = init_browser()
    results = []  # 存储所有搜索结果
    try:
        # 打开百度搜索主页
        driver.get("https://www.baidu.com")
        time.sleep(53)  # 等待页面加载
        print("正在打开百度搜索主页...")
        # 定位搜索框并输入关键词
        search_box = driver.find_element(By.ID, "kw")
        search_box.send_keys(keyword)  # 输入关键词
        print(f"正在搜索关键词: {keyword}")
        time.sleep(2)  # 等待输入完成
        search_box.send_keys(Keys.RETURN)  # 模拟按下回车键
        time.sleep(3)  # 等待搜索结果加载
        
        # 循环获取多页搜索结果
        for page in range(1, max_pages + 1):
            print(f"正在抓取第 {page} 页结果...")
            
            # 滑动到页面底端以确保所有结果加载
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 获取当前页面的搜索结果
            search_results = driver.find_elements(By.XPATH, 
                '//div[contains(@class,"result") and contains(@class,"c-container")]//h3/a')
            
            for result in search_results:
                # 获取标题
                title = result.text.strip()
                # 获取链接
                link = result.get_attribute("href")
                # 保存标题和链接到结果列表
                if title and link:
                    results.append({"title": title, "link": link})
            
            # 点击“下一页”按钮
            try:
                next_button = driver.find_element(By.LINK_TEXT, "下一页 >")
                next_button.click()  # 点击进入下一页
                time.sleep(rd.randint(2, 5))  # 等待页面加载，随机时间等待（尽量模拟人在浏览）
            except Exception as e:
                print("已到达最后一页或无法找到下一页按钮。")
                break
    except Exception as e:
        print("发生错误：", e)
    finally:
        driver.quit()  # 关闭浏览器
        print("采集结束！")
    
    # 返回采集到的所有结果
    return results
 
if __name__ == "__main__":
    # 用户输入
    keyword = "LoRa通信技术远距离低功耗抗干扰优势及应用场景"  # 搜索关键词
    max_pages = 1  # 需要抓取的页数
 
    # 调用爬取函数
    results = scrape_baidu_results(keyword, max_pages)
    
    # 以json文件的格式导出结果
    export_results_to_json(results, "baidu_results.json")
 