from mofa.agent_build.base.base_agent import MofaAgent, run_agent
import json
from dotenv import load_dotenv
from mofa.utils.files.read import read_yaml
from openai import OpenAI
import os
from pathlib import Path
@run_agent
def run(agent:MofaAgent):
    task = agent.receive_parameter('searchdata_exactor_result')
    if task and len(task) > 0:
        task = task[1:]  # 使用切片操作删除第一个字符
    print("task", task)
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
    print("<think> : ", reasoning_content)
    print('-------------')
    print("<content> ", content)
    agent.send_output(agent_output_name='agent_searchdata_integration_result', agent_result=content)
    
def main():
    agent = MofaAgent(agent_name='agent-searchdata-integration')
    run(agent=agent)
if __name__ == "__main__":
    main()
#{"url":"https://www.techphant.cn/blog/99308.html","task":"lora通信有什么优点"}
#{"url":"https://www.runoob.com/selenium/selenium-install.html","task":"如何安装selenium库"}