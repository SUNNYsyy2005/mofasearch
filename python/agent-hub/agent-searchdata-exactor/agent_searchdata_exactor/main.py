from mofa.agent_build.base.base_agent import MofaAgent, run_agent
from .exator import extract_html_sync
import os
from openai import OpenAI
from dotenv import load_dotenv
import time
from mofa.utils.files.read import read_yaml
import json
def count_tokens(text, model=None):
    """估算文本的token数量，汉字0.6token，字母0.3token"""
    cn_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    en_count = len(text) - cn_count
    estimated_tokens = int(cn_count * 0.6 + en_count * 0.3)
    return estimated_tokens

def split_text_by_tokens(text, max_tokens=5000, model=None):
    """将文本按估算token数量分段"""
    # 分段
    segments = []
    current_segment = ""
    current_tokens = 0
    
    for char in text:
        # 估算当前字符的token
        char_token = 0.6 if '\u4e00' <= char <= '\u9fff' else 0.3
        
        # 如果添加这个字符会超过限制，则先保存当前段落
        if current_tokens + char_token > max_tokens and current_segment:
            segments.append(current_segment)
            current_segment = ""
            current_tokens = 0
        
        current_segment += char
        current_tokens += char_token
    
    # 添加最后一个段落
    if current_segment:
        segments.append(current_segment)
    
    return segments

def init_openai_client():
    """初始化OpenAI客户端"""
    # 加载环境变量
    load_dotenv(dotenv_path='.env.secret')
    if os.getenv('LLM_API_KEY') is not None:
        os.environ['OPENAI_API_KEY'] = os.getenv('LLM_API_KEY')

    if os.getenv('LLM_BASE_URL', None) is None:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    else:
        client = OpenAI(
            api_key=os.environ['OPENAI_API_KEY'], 
            base_url=os.getenv('LLM_BASE_URL')
        )
    
    return client

def process_html_with_llm(html_content, task, client=None, model_name=None):
    """使用大模型处理HTML内容"""
    if client is None:
        client = init_openai_client()
    
    if model_name is None:
        model_name = os.getenv('LLM_MODEL_NAME', 'gpt-4o')
    agent_config_dir_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), )
    config_yml = read_yaml(agent_config_dir_path + f'/configs/agent.yml')
    prompt = config_yml.get('agent', {}).get('prompt', '')
    # 准备消息
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "search_task:"+task+"    web_content:"+html_content},
    ]
    #print(messages)
    
    # 调用API
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=True,
    )
    
    # 解析响应 - 使用与agent-planning一致的方式
    reasoning_content = ""
    content = ""
    for chunk in response:
        if chunk.choices[0].delta.reasoning_content:
            think_data = chunk.choices[0].delta.reasoning_content
            if think_data is not None:
                reasoning_content += chunk.choices[0].delta.reasoning_content
        else:
            data = chunk.choices[0].delta.content
            if data is not None:
                content += chunk.choices[0].delta.content
    
    # 打印思考过程和内容
    print("<think> : ", reasoning_content)
    print('-------------')
    print("<content> ", content)
    
    return {
        "reasoning": reasoning_content,
        "content": content
    }

def process_webpage_in_segments(url, task, max_tokens=5000, model_name=None, client=None):
    """分段处理网页内容并汇总结果，仅返回汇总内容字符串"""
    # 获取网页内容
    try:
        result = extract_html_sync(url)
        
        if not result["success"]:
            print(f"提取网页内容失败: {url}")
            return {"url": url, "task": task, "content": "无法获取网页内容"}
        
        # 初始化OpenAI客户端（如果未提供）
        if client is None:
            client = init_openai_client()
        
        # 获取标题和HTML内容
        title = result["title"]
        html_content = result["html_content"]
        
        # 分段
        print(f"开始分段处理网页内容: {title}")
        segments = split_text_by_tokens(html_content, max_tokens=max_tokens, model=model_name)
        print(f"内容已分为 {len(segments)} 段")
        
        # 处理每个段落
        segment_results = []
        for i, segment in enumerate(segments):
            print(f"处理第 {i+1}/{len(segments)} 段内容...")
            # 调用LLM处理
            segment_result = process_html_with_llm(
                segment, 
                task,
                client=client, 
                model_name=model_name
            )
            
            segment_results.append(segment_result)
            print(f"第 {i+1} 段处理完成")
            
            # 添加短暂延迟，避免API限制
            if i < len(segments) - 1:
                time.sleep(1)
        
        # 汇总结果
        print("所有段落处理完成，开始汇总结果...")
        
        # 汇总所有段落的内容
        all_contents = [result["content"] for result in segment_results]
        combined_content = "\n\n".join(all_contents)
        return {
            "url": url,
            "task": task,
            "content": combined_content
        }
    except Exception as e:
        print(f"处理网页 {url} 时发生错误: {str(e)}")
        # 返回错误信息
        return {
            "url": url,
            "task": task,
            "content": f"处理网页时发生错误: {str(e)}"
        }

@run_agent
def run(agent:MofaAgent):
    task_json = agent.receive_parameter('agent_searchwords_generator_result')
    if task_json and len(task_json) > 0:
        task_json = task_json[1:]  # 使用切片操作删除第一个字符
    else:
        return
    print(f"接收到的原始任务: {task_json}")
    
    # 初始化OpenAI客户端
    load_dotenv(dotenv_path='.env.secret')
    if os.getenv('LLM_API_KEY') is not None:
        os.environ['OPENAI_API_KEY'] = os.getenv('LLM_API_KEY')

    if os.getenv('LLM_BASE_URL', None) is None:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    else:
        client = OpenAI(
            api_key=os.environ['OPENAI_API_KEY'], 
            base_url=os.getenv('LLM_BASE_URL')
        )
    
    # 打印环境变量信息
    print('LLM_API_KEY', os.getenv('LLM_API_KEY'))
    print('LLM_BASE_URL', os.getenv('LLM_BASE_URL', None))
    print('LLM_MODEL_NAME', os.getenv('LLM_MODEL_NAME', 'gpt-4o'))
    
    # 结果数组
    results = []
    
    # 解析JSON字符串为Python对象
    try:
        # 尝试解析为对象数组
        tasks = json.loads(task_json)
        
        # 判断是否为数组
        if not isinstance(tasks, list):
            tasks = [tasks]  # 如果不是数组，转换为单元素数组
        
        print(f"解析后的任务数组: {tasks}")
        
        # 创建一个集合来跟踪已处理的URL
        processed_urls = set()
        
        # 处理每个任务
        for task_obj in tasks:
            # 提取URL和搜索查询
            url = task_obj.get('url', '')
            search_query = task_obj.get('task', '')
            
            # 参数验证
            if not url:
                error_msg = "任务参数缺少URL字段"
                print(error_msg)
                continue  # 跳过此任务
                
            if not search_query:
                # 如果没有提供查询，可以使用默认值或跳过
                print(f"未提供查询")
                continue
            
            # 检查是否已处理过此URL
            if url in processed_urls:
                print(f"URL已处理过，等待2秒后再次处理: {url}")
                time.sleep(2)  # 添加延迟，确保资源释放
            
            print(f"处理任务 - URL: {url}, 查询: {search_query}")
            
            # 处理网页内容并获取汇总结果
            result = process_webpage_in_segments(
                url=url,
                task=search_query,
                max_tokens=5000,
                model_name=os.getenv('LLM_MODEL_NAME', 'gpt-4o'),
                client=client
            )
            
            # 添加URL到已处理集合
            processed_urls.add(url)
            
            # 将结果添加到结果数组
            results.append(result)
            
    except json.JSONDecodeError as e:
        # 如果JSON解析失败，记录错误
        print(f"JSON解析失败: {e}")
        # 创建一个错误结果
        error_result = {
            "url": "",
            "task": "",
            "content": f"JSON解析错误: {str(e)}"
        }
        results.append(error_result)
    
    # 将结果数组转换为JSON字符串
    results_json = json.dumps(results, ensure_ascii=False)
    print(f"所有处理结果: {results_json}")
    # 发送汇总结果
    agent.send_output(agent_output_name='agent_searchdata_exactor_result', agent_result='#'+results_json)

def main():
    agent = MofaAgent(agent_name='agent-searchdata-exactor')
    run(agent=agent)

if __name__ == "__main__":
    main()
##{"url":"https://blog.csdn.net/fff5565665556655/article/details/144286071","task":"如何安装selenium库？"}
##{"url":"https://www.techphant.cn/blog/88440.html","task":"Rola和Lora有什么区别？"}