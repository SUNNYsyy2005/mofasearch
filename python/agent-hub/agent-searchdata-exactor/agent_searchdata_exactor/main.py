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
    print(messages)
    
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
    result = extract_html_sync(url)
    
    if not result["success"]:
        return "无法获取网页内容"
    
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
        # 构建包含段落信息的提示
        #segment_prompt = f"{prompt}\n\n这是文档的第 {i+1}/{len(segments)} 部分。标题: {title}"
        
        # 调用LLM处理
        segment_result = process_html_with_llm(
            segment, 
            task,
            #segment_prompt, 
            client=client, 
            model_name=model_name
        )
        
        segment_results.append(segment_result)
        print(f"第 {i+1} 段处理完成")
        #print("-------------")
        #print(segment_result["content"])
        #print("-------------")
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

@run_agent
def run(agent:MofaAgent):
    task_json = agent.receive_parameter('task')
    if task_json and len(task_json) > 0:
        task_json = task_json[1:]  # 使用切片操作删除第一个字符
    else:
        return
    print(f"接收到的原始任务: {task_json}")
    
    # 解析JSON字符串为Python对象
    try:
        task_obj = json.loads(task_json)     
        print(f"解析后的任务对象: {task_obj}")
        # 提取URL和搜索查询
        url = task_obj.get('url', '')
        search_query = task_obj.get('task', '')
        
        # 参数验证
        if not url:
            error_msg = "任务参数缺少URL字段"
            print(error_msg)
            url = "https://opencamp.cn/gosim/camp/MoFA2025"  # 默认URL
            return
            
        if not search_query:
            # 如果没有提供查询，可以使用默认值或返回错误
            search_query = "2025 MoFA Search AI 报名人数是多少"
            print(f"未提供查询，使用默认查询: {search_query}")
        
    except json.JSONDecodeError as e:
        # 如果JSON解析失败，尝试将整个字符串作为URL处理
        print(f"JSON解析失败: {e}")
        url = "https://opencamp.cn/gosim/camp/MoFA2025"
        search_query = "2025 MoFA Search AI 报名人数是多少"  # 默认查询
    print(f"最终使用的URL: {url}")
    print(f"最终使用的搜索查询: {search_query}")
    # 设置提示语
    agent_config_dir_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), )
    config_yml = read_yaml(agent_config_dir_path + f'/configs/agent.yml')
    analysis_prompt = config_yml.get('agent', {}).get('prompt', '')
    
    # 初始化OpenAI客户端（参照main.py的方式）
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
    
    # 处理网页内容并获取汇总结果
    result = process_webpage_in_segments(
        url=url,
        task=search_query,
        max_tokens=5000,
        model_name=os.getenv('LLM_MODEL_NAME', 'gpt-4o'),
        client=client
    )
    result_json = json.dumps(result, ensure_ascii=False)
    print(f"处理结果: {result_json}")
    # 直接发送汇总内容作为结果
    agent.send_output(agent_output_name='agent_searchdata_exactor_result', agent_result='#'+result_json)

def main():
    agent = MofaAgent(agent_name='agent-searchdata-exactor')
    run(agent=agent)

if __name__ == "__main__":
    main()
##{"url":"https://blog.csdn.net/fff5565665556655/article/details/144286071","task":"如何安装selenium库？"}
##{"url":"https://www.techphant.cn/blog/88440.html","task":"Rola和Lora有什么区别？"}