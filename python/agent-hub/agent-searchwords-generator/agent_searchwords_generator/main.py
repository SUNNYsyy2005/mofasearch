from mofa.agent_build.base.base_agent import MofaAgent, run_agent
import json
from dotenv import load_dotenv
from mofa.utils.files.read import read_yaml
from openai import OpenAI
import os
from pathlib import Path
# 导入测试文件中的搜索函数
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .search import scrape_baidu_results

@run_agent
def run(agent:MofaAgent):
    task = agent.receive_parameter('task')
    if not task or len(task) == 0:
        return
    print("terminal input task", task)
    agent_config_dir_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), )
    config_yml = read_yaml(agent_config_dir_path + f'/configs/agent.yml')
    prompt = config_yml.get('agent', {}).get('prompt', '')
    load_dotenv(dotenv_path='.env.secret')
    if os.getenv('LLM_API_KEY') is not None:
        os.environ['OPENAI_API_KEY'] = os.getenv('LLM_API_KEY')

    if os.getenv('LLM_BASE_URL', None) is None:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    else:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'], base_url=os.getenv('LLM_BASE_URL'), )

    user_input = task
    messages = [
        {"role": "system","content": prompt},
        {"role": "user", "content": user_input},
    ]
    print('LLM_API_KEY', os.getenv('LLM_API_KEY'))
    print('LLM_BASE_URL', os.getenv('LLM_BASE_URL', None))
    print('LLM_MODEL_NAME', os.getenv('LLM_MODEL_NAME', 'gpt-4o'))
    response = client.chat.completions.create(
        model=os.getenv('LLM_MODEL_NAME', 'gpt-4o'),
        messages=messages, stream=True, )
    reasoning_content = ""
    content = ""
    for chunk in response:
        if chunk.choices[0].delta.reasoning_content:
            think_data = chunk.choices[0].delta.reasoning_content
            if think_data is not None:
                reasoning_content += chunk.choices[0].delta.reasoning_content  # **thinking part**
        else:
            data = chunk.choices[0].delta.content
            if data is not None:
                content += chunk.choices[0].delta.content
                    # 移除content中的所有回车符
    content = content.replace('\n', '').replace('\r', '')
    print("Searching:", content)
    # 使用大模型输出作为搜索关键词
    try:
        search_results = scrape_baidu_results(content, max_pages=1)
        print("Search Results:", search_results)
    except Exception as e:
        print(f"搜索发生错误: {e}")
        search_results = []  # 出错时使用空列表

    # 转换为指定的JSON格式
    formatted_results = []
    for result in search_results:
        formatted_results.append({
            "url": result["link"],
            "task": content
        })
    
    # 确保至少有一个结果，如果没有搜索到结果，添加一个默认结果
    if not formatted_results:
        formatted_results.append({
            "url": "https://www.baidu.com/s?wd=" + content.replace(" ", "+"),
            "task": content
        })
    
    formatted_results = formatted_results[0:2]
    # 转换为JSON字符串
    results_json = json.dumps(formatted_results, ensure_ascii=False)
    print("Formatted Results JSON:", results_json)
    # 发送搜索结果作为输出
    agent.send_output(agent_output_name='agent_searchwords_generator_result', agent_result='#'+results_json)
def main():
    agent = MofaAgent(agent_name='agent-searchwords-integration')
    run(agent=agent)
if __name__ == "__main__":
    main()
