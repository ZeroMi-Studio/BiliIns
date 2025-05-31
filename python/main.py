import requests
import time
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import commentAcquisition
import json
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)

INIDATA = json.load(open('setting.json', encoding='utf-8'))


def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]


class LogModule:  # 日志生成
    def __init__(self):
        self.content = f'日志模块初始化 时间[{get_time()}]\n'
        self.file_name = f'logs/BiliIns-{time.time()}.log'
        threading.Thread(target=self.save_log).start()
        print(self.content)

    def __add__(self, other, title='日志输出'):
        try:
            self.content += f'{title} 时间[{get_time()}]: {other}\n'
            print(f'{title} 时间[{get_time()}]: {other}\n')
        except Exception as _:
            self.content += f'日志模块异常 时间[{get_time()}]: {str(_)}\n'

    def error(self, text):
        self.content += f'ERROR====={get_time()}=====ERROR\n{text}\n\n'
        open(self.file_name, 'w', encoding='utf-8').write(self.content)
        print(f'请阅读或提交日志 {self.file_name}')

    def warning(self, text):
        self.content += f'warning====={get_time()}=====warning\n{text}\nwarning==========warning\n\n'

    def save_log(self):
        while True:
            open(self.file_name, 'w', encoding='utf-8').write(self.content)
            time.sleep(10)


def verify_completeness(content, template=None, name=''):  # 验证配置信息函数
    if template is None:
        template = {'IP': {"host": None, "port": None}}

    for x in template:
        if not (x in list(content.keys())):
            return False, (name, x)

        if type(template[x]) == dict:
            data = verify_completeness(content[x], template[x], name + '/' + x)
            if not data[0]:
                return data

    return True, None


def generate_text_ollama(model_name, prompt):
    response = requests.post(  # 访问ai
        f"{INIDATA['AI']['url']}/generate",
        json={
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
    )
    return re.sub(r'<think>.*?</think>', '', response.json()['response'], flags=re.DOTALL)


def generate_text_deepseek(model_name, prompt):
    # 发送POST请求
    response = requests.post(
        url="https://api.deepseek.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {INIDATA['AI']['key']}"  # 根据DeepSeek要求的格式设置
        },
        data=json.dumps(
            {
                "model": model_name,  # 指定模型名称
                "messages": [
                    {"role": "system", "content": ""},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
        )
    )
    log_module + f'{response.json()}'
    return response.json()['choices'][0]['message']['content']


@app.route('/api/getData', methods=['GET'])
def fetch_bilibili_video_info():
    bvid = request.args.get('bvid')
    log_module + f'获取{bvid}信息'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/',
    }

    for attempt in range(3):
        try:
            response = requests.get(
                "https://api.bilibili.com/x/web-interface/view",
                params={'bvid': bvid},
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get('code') != 0 or 'data' not in data:
                log_module.warning(data.get('message', 'API返回异常'))
                return {"error": data.get('message', 'API返回异常')}, 400
                
            video_data = data['data']
            stat = video_data.get('stat', {})

            return {
                'code': 200,
                'aid': video_data.get('aid'),
                'bvid': bvid,
                'title': video_data.get('title'),
                'desc': video_data.get('desc'),
                'view': stat.get('view'),
                'danmaku': stat.get('danmaku'),
                'reply': stat.get('reply'),
                'favorite': stat.get('favorite'),
                'coin': stat.get('coin'),
                'share': stat.get('share'),
                'like': stat.get('like'),
                'dislike': stat.get('dislike', 0),
                'ctime': video_data.get('ctime'),
                'pubdate': video_data.get('pubdate'),
                'duration': video_data.get('duration')
            }

        except requests.RequestException as _:
            if attempt == 2:
                log_module.warning(f"请求失败, 请检查网络连接; {str(_)}")
                return {"error": f"请求失败, 请检查网络连接; {str(_)}"}, 500
            time.sleep(1)
        except Exception as _:
            log_module.warning(f"请求程序错误; {str(_)}")
            return {"error": f"请求程序错误; {str(_)}"}, 500


@app.route('/api/getComment', methods=['GET'])
def get_video_info():
    """AI分析"""
    try:
        if INIDATA['AI']['type'] == 'ollama':
            bvid = request.args.get('bvid')
            log_module + f'视频{bvid} 尝试调用ollama'
            data = commentAcquisition.get_data(bvid, INIDATA['AI']['SampleQuantity'])
            n = 0
            text = INIDATA['AI']['text'] + '\n'
            for x in data:
                text += f"评论{n}: {x['content']}\n"
                n += 1
            return jsonify(generate_text_ollama(INIDATA['AI']['AIName'], text))

        elif INIDATA['AI']['type'] == 'deepseek':
            bvid = request.args.get('bvid')
            log_module + f'视频{bvid} 尝试调用deepseek'
            data = commentAcquisition.get_data(bvid, INIDATA['AI']['SampleQuantity'])
            n = 0
            text = INIDATA['AI']['text'] + '\n'
            for x in data:
                text += f"评论{n}: {x['content']}\n"
                n += 1

            return jsonify(generate_text_deepseek(INIDATA['AI']['AIName'], text))

        else:
            log_module + f"AI类型不可用({INIDATA['AI']['type']}), 请检查配置文件 AI/type 项"
            return f"AI类型不可用({INIDATA['AI']['type']}), 请检查配置文件 AI/type 项"

    except Exception as _:
        log_module.warning(f'AI功能出现异常, 请检查环境; {_}')
        return f'AI功能出现异常, 请检查环境; ({_})'


@app.route('/<route>')
def get_page(route):
    try:
        return open('pages/' + route, encoding='utf-8').read()
    except Exception as e:
        return str(e), 404


@app.route('/')
def index():
    try:
        return open('pages/index.html', encoding='utf-8').read()
    except Exception as e:
        return str(e), 404


log_module = LogModule()
state, arge = verify_completeness(INIDATA)  # 验证配置文件基础信息完整性
if not state:
    log_module.error(f'setting.json缺少关键参数 {arge[0]} 中缺少参数 {arge[1]}')

try:
    if __name__ == "__main__":
        import webbrowser

        url = f"http://127.0.0.1:{INIDATA['IP']['port']}"
        webbrowser.open(url)  # 使用默认浏览器打开 URL

        app.run(host=INIDATA['IP']['host'], port=INIDATA['IP']['port'])

except Exception as _:
    log_module.error(f'程序出现严重异常导致程序结束 错误信息:{str(_)}')
