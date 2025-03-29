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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
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
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver
 
# 爬取百度搜索结果
def scrape_baidu_results(keyword, max_pages=1):
    """
    爬取百度搜索结果。
    
    参数:
    - keyword (str): 搜索关键词
    - max_pages (int): 要抓取的页数，默认 1 页
    
    返回:
    - results (list): 包含每页搜索结果的列表，格式为 {"title": 标题, "link": 链接}
    """
    driver = init_browser()
    results = []  # 存储所有搜索结果
    try:
        # 打开百度搜索主页
        driver.get("https://www.baidu.com")
        
        # 使用WebDriverWait等待页面加载完成
        try:
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "kw"))
            )
            print("正在打开百度搜索主页...")
            
            # 定位搜索框并输入关键词
            search_box.clear()
            search_box.send_keys(keyword)  # 输入关键词
            print(f"正在搜索关键词: {keyword}")
            time.sleep(1)  # 简短等待
            search_box.send_keys(Keys.RETURN)  # 模拟按下回车键
            
            # 等待搜索结果加载
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"result")]'))
            )
        except TimeoutException:
            print("页面加载超时")
            return []
        
        # 循环获取多页搜索结果
        for page in range(1, max_pages + 1):
            print(f"正在抓取第 {page} 页结果...")
            
            # 滑动到页面底端以确保所有结果加载
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # 使用函数获取当前页面的搜索结果，处理可能的陈旧元素引用
            try:
                page_results = get_page_results(driver)
                results.extend(page_results)
                print(f"已获取 {len(page_results)} 条结果")
            except Exception as e:
                print(f"获取结果时出错: {e}")
            
            # 如果只需要一页或已经是最后一页，则退出循环
            if page >= max_pages:
                break
                
            # 点击"下一页"按钮，使用更安全的方法
            try:
                # 重新查找下一页按钮
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '下一页')]"))
                )
                driver.execute_script("arguments[0].click();", next_button)
                # 等待新页面加载
                time.sleep(rd.randint(2, 3))
                
                # 确认页面已更新
                WebDriverWait(driver, 10).until(
                    EC.staleness_of(next_button)
                )
                
            except Exception as e:
                print(f"无法点击下一页按钮或已到达最后一页: {e}")
                break
    except Exception as e:
        print("发生错误：", e)
    finally:
        driver.quit()  # 关闭浏览器
        print("采集结束！")
    
    # 确保即使出错也至少返回一个空列表
    return results or []

def get_page_results(driver):
    """获取当前页面的搜索结果，处理可能的陈旧元素引用"""
    results = []
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # 使用等待来确保元素已加载
            WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.XPATH, 
                '//div[contains(@class,"result") and contains(@class,"c-container")]//h3/a'))
            )
            
            # 获取所有搜索结果
            search_results = driver.find_elements(By.XPATH, 
                '//div[contains(@class,"result") and contains(@class,"c-container")]//h3/a')
            
            for result in search_results:
                try:
                    # 获取标题和链接
                    title = result.text.strip()
                    link = result.get_attribute("href")
                    
                    # 保存标题和链接到结果列表
                    if title and link:
                        results.append({"title": title, "link": link})
                except StaleElementReferenceException:
                    # 如果元素已过时，跳过这个元素
                    continue
                except Exception as e:
                    print(f"获取元素属性时出错: {e}")
            
            # 如果成功获取了结果，跳出循环
            if results:
                break
        except StaleElementReferenceException:
            # 如果元素已过时，尝试下一次
            print(f"元素已过时，重试 ({attempt+1}/{max_attempts})")
            time.sleep(1)
        except Exception as e:
            print(f"获取搜索结果时出错: {e}")
            break
    
    return results
 
if __name__ == "__main__":
    # 用户输入
    keyword = "LoRa通信技术远距离低功耗抗干扰优势及应用场景"  # 搜索关键词
    max_pages = 1  # 需要抓取的页数
 
    # 调用爬取函数
    results = scrape_baidu_results(keyword, max_pages)
    
    # 以json文件的格式导出结果
    export_results_to_json(results, "baidu_results.json")
