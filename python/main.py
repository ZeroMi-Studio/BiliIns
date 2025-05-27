'''
© Copyrights 2025 Zeromi Studio. All Rights Reserved.

Author:天弃之子
Date:2025/05/24
Time:20:42:19

==============================
前后端交互代码/页面数据分析代码
==============================

请严格遵循开源协议，严禁二次倒卖、贩卖
保留所有权利
'''


import requests
import time
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import commentAcquisition
import json

app = Flask(__name__)
CORS(app)


INIDATA = json.load(open('setting.json', encoding='utf-8'))


def generate_text(model_name, prompt):
    """最简单的 Ollama API 请求函数"""
    response = requests.post(
        f"{INIDATA['AI']['url']}/generate",
        json={
            "model": model_name,
            "prompt": prompt,
            "stream": False  # 禁用流式响应
        }
    )
    return re.sub(r'<think>.*?</think>', '', response.json()['response'], flags=re.DOTALL)


@app.route('/api/getData', methods=['GET'])
def fetch_bilibili_video_info():
    bvid = request.args.get('bvid')
    """获取B站视频信息（基础功能）"""
    if not bvid or not isinstance(bvid, str) or not bvid.startswith('BV'):
        return {"error": "无效的BV号，必须以'BV'开头"}

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
                return {"error": data.get('message', 'API返回异常')}

            video_data = data['data']
            stat = video_data.get('stat', {})

            return {
                'aid': video_data.get('aid'),
                'bvid': video_data.get('bvid'),
                'title': video_data.get('title'),
                'desc': video_data.get('desc'),  # 新增：视频简介
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
                'duration': video_data.get('duration')  # 新增：视频时长
            }

        except requests.RequestException as e:
            if attempt == 2:
                return {"error": f"请求失败: {str(e)}"}
            time.sleep(1)


@app.route('/api/getComment', methods=['GET'])
def get_video_info():
    """获取视频信息（支持AI分析）"""
    try:
        if INIDATA['AI']['type'] == 'ollama':
            bvid = request.args.get('bvid')

            data = commentAcquisition.getData(bvid)
            n = 0
            text = '我是一个视频创作者, 对下列评论内容进行分析, 根据这些评论进行动向分析, 这反映了我的视频的什么问题, 从好处和坏处分别分析(尽量控制在500字以内)\n'
            for x in data:
                text += f"评论{n}: {x['content']}\n"
                n += 1
            return jsonify(generate_text(INIDATA['AI']['AIName'], text))
        else:
            return '当前未启动AI功能'
    except Exception as e:
        return f'AI功能出现错误, 请检查 setting.json 文件; ({e})'


@app.route('/<route>')
def get_page(route):
    try:
        return open('pages/'+route, encoding='utf-8').read()
    except Exception as e:
        return str(e), 404


@app.route('/')
def index():
    try:
        return open('pages/index.html', encoding='utf-8').read()
    except Exception as e:
        return str(e), 404


if __name__ == "__main__":
    import webbrowser
    url = f"http://127.0.0.1:{INIDATA['port']}"
    webbrowser.open(url)  # 使用默认浏览器打开 URL

    app.run(host=INIDATA['host'], port=INIDATA['port'])

# 天弃之子(23238374@qq.com) 的 史之后端.
