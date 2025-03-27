from mofa.agent_build.base.base_agent import MofaAgent, run_agent
from exator import extract_html_sync
import tiktoken
import os
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
import time
from mofa.utils.files.read import read_yaml
def ensure_playwright_browsers():
    """确保Playwright浏览器已安装"""
    try:
        # 运行playwright install命令
        subprocess.run(["python", "-m", "playwright", "install"], 
                      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Playwright 浏览器安装成功！")
        return True
    except Exception as e:
        print(f"无法自动安装 Playwright 浏览器: {e}")
        print("请手动运行命令: python -m playwright install")
        return False

def count_tokens(text, model="gpt-4o"):
    """计算文本的token数量"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # 如果模型不支持，使用cl100k_base编码
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

def split_text_by_tokens(text, max_tokens=5000, model="gpt-4o"):
    """将文本按token数量分段"""
    # 计算token
    encoding = tiktoken.encoding_for_model(model) if model else tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    
    # 分段
    segments = []
    for i in range(0, len(tokens), max_tokens):
        segment_tokens = tokens[i:i+max_tokens]
        segment_text = encoding.decode(segment_tokens)
        segments.append(segment_text)
    
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

def process_html_with_llm(html_content, prompt, client=None, model_name=None):
    """使用大模型处理HTML内容"""
    if client is None:
        client = init_openai_client()
    
    if model_name is None:
        model_name = os.getenv('LLM_MODEL_NAME', 'gpt-4o')
    
    # 准备消息
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": html_content},
    ]
    
    # 调用API
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=True,
    )
    
    # 解析响应
    reasoning_content = ""
    content = ""
    for chunk in response:
        # 尝试获取reasoning_content（如果支持）
        try:
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                think_data = chunk.choices[0].delta.reasoning_content
                if think_data is not None:
                    reasoning_content += think_data
        except:
            pass
        
        # 获取普通内容
        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
            data = chunk.choices[0].delta.content
            if data is not None:
                content += data
    
    return {
        "reasoning": reasoning_content,
        "content": content
    }

def process_webpage_in_segments(url, prompt, max_tokens=5000, model_name=None, client=None):
    """分段处理网页内容并汇总结果，仅返回汇总内容字符串"""
    # 确保安装了Playwright浏览器
    ensure_playwright_browsers()
    
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
        segment_prompt = f"{prompt}\n\n这是文档的第 {i+1}/{len(segments)} 部分。标题: {title}"
        
        # 调用LLM处理
        segment_result = process_html_with_llm(
            segment, 
            segment_prompt, 
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
    
    # 如果内容太长，需要再次总结
    if count_tokens(combined_content) > max_tokens:
        print("汇总结果太长，进行二次总结...")
        
        summary_prompt = f"""以下是对网页"{title}"内容的多段分析结果。
请对这些结果进行综合整理，提供一个连贯的、结构化的总结。保留关键信息并消除重复内容。

分析结果:
{combined_content}
"""
        
        final_result = process_html_with_llm(
            combined_content, 
            summary_prompt, 
            client=client, 
            model_name=model_name
        )
        
        return final_result["content"]
    else:
        return combined_content

@run_agent
def run(agent:MofaAgent):
    # 接收任务参数（网址）
    task = agent.receive_parameter('task')
    
    # 确保安装了Playwright浏览器
    ensure_playwright_browsers()
    
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
        url=task,  # 使用传入的task作为URL
        prompt=analysis_prompt,
        max_tokens=5000,
        model_name=os.getenv('LLM_MODEL_NAME', 'gpt-4o'),
        client=client
    )
    
    # 直接发送汇总内容作为结果
    agent.send_output(agent_output_name='agent_result', agent_result=result)

def main():
    agent = MofaAgent(agent_name='webpage-content-extractor')
    run(agent=agent)

if __name__ == "__main__":
    main()
