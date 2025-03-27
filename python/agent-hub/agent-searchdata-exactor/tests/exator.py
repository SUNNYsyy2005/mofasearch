import crawl4ai
import asyncio
from bs4 import BeautifulSoup
import subprocess
import requests
import os
from datetime import datetime
from urllib.parse import urlparse

# 安装 Playwright 浏览器
def ensure_playwright_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], 
                     check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Playwright 浏览器安装成功！")
        return True
    except Exception as e:
        print(f"无法自动安装 Playwright 浏览器: {e}")
        print("请手动运行命令: playwright install")
        return False

async def extract_website_data_async(url):
    """获取网页HTML内容"""
    try:
        # 使用 AsyncWebCrawler
        async with crawl4ai.AsyncWebCrawler(verbose=True) as crawler:
            wait_for = """() => {
                        return new Promise(resolve => setTimeout(resolve, 3000));
                    }"""
            
            result = await crawler.arun(
                url=url, 
                magic=True, 
                simulate_user=True, 
                override_navigator=True,
                wait_for=wait_for
            )
            
            if not hasattr(result, 'status_code') or result.status_code != 200:
                print(f"请求失败，状态码: {getattr(result, 'status_code', '未知')}")
                return ""
            
            return result.html
            
    except Exception as e:
        print(f"使用 AsyncWebCrawler 失败: {e}")
        # 备用方法
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"备用请求方法也失败: {e}")
            return ""

def extract_formatted_text(html_content):
    """提取网页中的内容，移除非结构性标签但保留其中的文本内容"""
    try:
        # 创建 BeautifulSoup 对象
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除不含内容的标签
        for tag in soup(['script', 'style', 'link', 'meta', 'noscript']):
            tag.decompose()
        
        # 定义要保留的结构性标签
        structural_tags = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',  # 标题
            'p', 'br',                           # 段落和换行
            'ul', 'ol', 'li',                    # 列表
            'table', 'tr', 'td', 'th', 'thead', 'tbody', # 表格
            'blockquote', 'q',                   # 引用
            'img',                               # 图片
            'a',                                 # 链接
            'strong', 'em', 'b', 'i',            # 强调
            'code', 'pre',                       # 代码
            'dl', 'dt', 'dd',                    # 定义列表
            'hr',                                # 水平线
            'body', 'html', 'head', 'title'      # 基本文档结构
        ]
        
        # 处理非结构性标签 - 安全提取所有文本内容
        tags_to_process = []
        for tag in soup.find_all(True):
            if tag.name not in structural_tags:
                tags_to_process.append(tag)
        
        # 从叶子节点开始处理，确保子节点内容不会丢失
        for tag in reversed(tags_to_process):
            try:
                # 检查标签是否仍在文档树中
                if tag.parent is None:
                    continue
                
                # 收集标签中的所有文本（包括嵌套标签中的文本）
                contents = []
                for content in tag.contents:
                    if isinstance(content, str):
                        contents.append(content)
                    else:
                        # 如果是元素，保留它的字符串表示
                        contents.append(str(content))
                
                # 替换标签为其内容（保留嵌套结构）
                new_content = ''.join(contents)
                tag.replace_with(BeautifulSoup(new_content, 'html.parser'))
                
            except Exception as e:
                # 跳过错误标签
                continue
        
        # 移除所有保留标签上的样式相关属性
        for tag in soup.find_all(structural_tags):
            for attr in list(tag.attrs.keys()):
                if attr not in ['href', 'src', 'alt']:
                    del tag[attr]
        
        # 返回结果
        result = {
            'title': soup.title.text.strip() if soup.title else "提取的网页内容",
            'html_content': str(soup.body) if soup.body else str(soup)
        }
        
        return result
    
    except Exception as e:
        print(f"处理HTML内容时出错: {e}")
        return {
            'title': "提取的网页内容",
            'html_content': "<p>无法解析内容</p>"
        }

def save_html_file(url, title, html_content):
    """保存HTML到文件"""
    try:
        # 创建结果目录
        results_dir = os.path.join(os.getcwd(), "extraction_results")
        os.makedirs(results_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = urlparse(url).netloc.replace(".", "_")
        base_filename = f"{domain}_{timestamp}"
        
        # 保存HTML格式数据
        html_file = os.path.join(results_dir, f"{base_filename}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- 源URL: {url} -->\n")
            f.write("<!DOCTYPE html>\n<html>\n<head>\n")
            f.write(f"<title>{title}</title>\n")
            f.write("<meta charset=\"utf-8\">\n")
            f.write("</head>\n<body>\n")
            
            # 添加标题
            f.write(f"<h1>{title}</h1>\n")
            
            # 写入HTML内容
            f.write(html_content)
            
            f.write("</body>\n</html>")
        
        print(f"\n结果已保存到: {html_file}")
        return html_file
    
    except Exception as e:
        print(f"保存结果到文件时出错: {e}")
        return None

async def process_and_save(url):
    """处理并保存网页内容"""
    # 获取HTML
    html_content = await extract_website_data_async(url)
    
    if not html_content:
        print("获取网页内容失败")
        return
    
    # 提取并处理HTML
    result = extract_formatted_text(html_content)
    
    # 显示预览
    title = result['title']
    html_preview = result['html_content'][:300] + "..." if len(result['html_content']) > 300 else result['html_content']
    
    print(f"\n标题: {title}")
    print("\nHTML内容预览:")
    print(html_preview)
    
    # 保存HTML文件
    save_html_file(url, title, result['html_content'])

# 新增API函数
async def extract_html(url):
    """
    提取网页内容为HTML格式
    
    Args:
        url (str): 要提取内容的网页URL
        
    Returns:
        dict: 包含以下键值的字典:
            - title (str): 网页标题
            - html_content (str): 提取的HTML内容
            - success (bool): 是否成功提取
    """
    # 确保安装了浏览器
    ensure_playwright_browsers()
    
    # 获取HTML
    html_content = await extract_website_data_async(url)
    
    if not html_content:
        return {
            "title": "",
            "html_content": "",
            "success": False
        }
    
    # 提取并处理HTML
    result = extract_formatted_text(html_content)
    
    return {
        "title": result['title'],
        "html_content": result['html_content'],
        "success": True
    }

async def extract_and_save_html(url, save_file=True):
    """
    提取网页内容并选择性保存为HTML文件
    
    Args:
        url (str): 要提取内容的网页URL
        save_file (bool, optional): 是否保存文件到本地，默认为True
        
    Returns:
        dict: 包含以下键值的字典:
            - title (str): 网页标题
            - html_content (str): 提取的HTML内容
            - file_path (str): 如果save_file为True，返回保存的文件路径
            - success (bool): 是否成功提取
    """
    # 确保安装了浏览器
    ensure_playwright_browsers()
    
    # 获取HTML
    html_content = await extract_website_data_async(url)
    
    if not html_content:
        return {
            "title": "",
            "html_content": "",
            "file_path": "",
            "success": False
        }
    
    # 提取并处理HTML
    result = extract_formatted_text(html_content)
    
    response = {
        "title": result['title'],
        "html_content": result['html_content'],
        "success": True
    }
    
    # 如果需要保存文件
    if save_file:
        file_path = save_html_file(url, result['title'], result['html_content'])
        response["file_path"] = file_path
    
    return response

# 同步版API函数，方便非异步环境调用
def extract_html_sync(url):
    """同步版本的extract_html函数"""
    return asyncio.run(extract_html(url))

def extract_and_save_html_sync(url, save_file=True):
    """同步版本的extract_and_save_html函数"""
    return asyncio.run(extract_and_save_html(url, save_file))

def main():
    """测试入口函数"""
    # 测试网址
    url = "https://baike.baidu.com/item/Python/407313"
    
    # 调用同步API进行测试
    result = extract_and_save_html_sync(url)
    
    if result["success"]:
        print(f"\n成功提取网页: {result['title']}")
        if "file_path" in result and result["file_path"]:
            print(f"文件已保存到: {result['file_path']}")
    else:
        print("提取网页内容失败")

if __name__ == "__main__":
    main()