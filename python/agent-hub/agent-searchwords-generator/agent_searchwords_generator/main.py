from mofa.agent_build.base.base_agent import MofaAgent, run_agent
import json
from dotenv import load_dotenv
from mofa.utils.files.read import read_yaml
from openai import OpenAI
import os
from pathlib import Path
@run_agent
def run(agent:MofaAgent):
    task = agent.receive_parameter('task')
    def read_markdown_file_basic(file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_text = f.read()
                return markdown_text
        except FileNotFoundError:
            print(f"错误：文件未找到：{file_path}")
            return None
        except Exception as e:
            print(f"读取文件时发生错误：{e}")
            return None

    agent_config_dir_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), )
    config_yml = read_yaml(agent_config_dir_path + f'/configs/agent.yml')
    prompt = config_yml.get('agent', {}).get('prompt', '')
    readme_files = config_yml.get('agent', {}).get('connectors', None)
    readme_data = {}
    if readme_files is not None:
        for file_path in readme_files:
            readme_data.update({Path(file_path).parent.name: read_markdown_file_basic(file_path=file_path)})
    load_dotenv(dotenv_path='.env.secret')
    if os.getenv('LLM_API_KEY') is not None:
        os.environ['OPENAI_API_KEY'] = os.getenv('LLM_API_KEY')

    if os.getenv('LLM_BASE_URL', None) is None:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    else:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'], base_url=os.getenv('LLM_BASE_URL'), )

    user_input = task
    messages = [
        {"role": "system",
         "content": prompt + "  readme_data: " + json.dumps(readme_data)},
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
    agent.send_output('agent_searchwords_integration_results', reasoning_content)
def main():
    agent = MofaAgent(agent_name='agent-searchwords-integration')
    run(agent=agent)
if __name__ == "__main__":
    main()
