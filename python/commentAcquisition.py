import requests
import time
import re
import jieba
from collections import Counter


def get_bvid_info(bvid):
    """获取B站视频的aid和cid等信息"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://www.bilibili.com/video/{bvid}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()
        if data["code"] == 0:
            aid = data["data"]["aid"]
            cid = data["data"]["cid"]
            title = data["data"]["title"]
            # 获取总评论数
            reply_count = data["data"]["stat"]["reply"]
            return aid, cid, title, reply_count
        else:
            return None, None, None, None
    except requests.exceptions.RequestException as e:
        return None, None, None, None


def get_comments(aid, page=1, size=20):
    """获取B站视频评论"""
    url = f"https://api.bilibili.com/x/v2/reply/main"
    params = {
        "jsonp": "jsonp",
        "next": page,
        "type": 1,
        "oid": aid,
        "mode": 3,  # 3表示按热度排序，2表示按时间排序
        "plat": 1,
        "size": size
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://www.bilibili.com/video/BV{aid}"
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        return response.json()
    except requests.exceptions.RequestException as e:
        return None


def parse_comments(json_data):
    """解析评论数据"""
    comments = []
    if json_data and json_data["code"] == 0:
        replies = json_data["data"]["replies"]
        if replies:
            for reply in replies:
                comment = {
                    "user_name": reply["member"]["uname"],
                    "user_id": reply["member"]["mid"],
                    "content": reply["content"]["message"],
                    "like_count": reply["like"],
                    "reply_count": reply["rcount"],
                    "comment_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reply["ctime"]))
                }
                comments.append(comment)
    return comments


def filter_comments(comments):
    """过滤评论：去除重复次数大于5的评论"""
    # 统计每条评论的出现次数
    content_counts = Counter(comment["content"] for comment in comments)

    # 过滤掉出现次数大于5的评论
    filtered_comments = [comment for comment in comments if content_counts[comment["content"]] <= 5]

    return filtered_comments


def compute_similarity_matrix(comments):
    """计算评论之间的相似度矩阵（纯Python实现）"""
    # 提取评论内容
    contents = [comment["content"] for comment in comments]

    if not contents:
        return []

    # 使用jieba进行分词
    tokenized_docs = [list(jieba.cut(content)) for content in contents]

    # 构建词汇表
    vocabulary = set()
    for doc in tokenized_docs:
        vocabulary.update(doc)
    vocabulary = list(vocabulary)
    word_to_idx = {word: idx for idx, word in enumerate(vocabulary)}

    # 计算词频矩阵
    tf_matrix = []
    for doc in tokenized_docs:
        doc_vector = [0] * len(vocabulary)
        for word in doc:
            if word in word_to_idx:
                doc_vector[word_to_idx[word]] += 1
        tf_matrix.append(doc_vector)

    # 计算逆文档频率
    doc_count = len(tokenized_docs)
    doc_freq = [0] * len(vocabulary)

    for doc_vector in tf_matrix:
        for idx, count in enumerate(doc_vector):
            if count > 0:
                doc_freq[idx] += 1

    idf = []
    for freq in doc_freq:
        if freq == 0:
            idf_val = 0  # 避免除以零
        else:
            idf_val = (doc_count / freq)
        idf.append(idf_val)

    # 计算TF-IDF矩阵
    tfidf_matrix = []
    for doc_vector in tf_matrix:
        tfidf_vector = [tf * idf[idx] for idx, tf in enumerate(doc_vector)]
        tfidf_matrix.append(tfidf_vector)

    # 归一化
    normalized_matrix = []
    for vector in tfidf_matrix:
        magnitude = sum(val ** 2 for val in vector) ** 0.5
        if magnitude == 0:
            normalized_vector = vector  # 避免除以零
        else:
            normalized_vector = [val / magnitude for val in vector]
        normalized_matrix.append(normalized_vector)

    # 计算余弦相似度矩阵
    similarity_matrix = []
    for i, vec1 in enumerate(normalized_matrix):
        row = []
        for j, vec2 in enumerate(normalized_matrix):
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            row.append(dot_product)
        similarity_matrix.append(row)

    return similarity_matrix


def select_diverse_comments(comments, similarity_matrix, target_count=30):
    """选择相似度最低的一组评论"""
    if len(comments) <= target_count:
        return comments

    # 初始化：选择点赞数最高的评论作为第一条
    selected_indices = [max(range(len(comments)), key=lambda i: comments[i]["like_count"])]

    # 逐步选择与已选评论相似度最低的评论
    while len(selected_indices) < target_count:
        # 计算每个未选评论与所有已选评论的平均相似度
        avg_similarities = []
        for i in range(len(comments)):
            if i not in selected_indices:
                # 计算与所有已选评论的平均相似度
                sims = [similarity_matrix[i][j] for j in selected_indices]
                avg_similarities.append((i, sum(sims) / len(sims)))

        # 选择平均相似度最低的评论
        next_index = min(avg_similarities, key=lambda x: x[1])[0]
        selected_indices.append(next_index)

    # 返回选中的评论
    selected_comments = [comments[i] for i in selected_indices]
    return selected_comments


def getData(bvid):
    """主函数"""

    # 验证BV号格式
    bvid_pattern = r'^BV[A-Za-z0-9]{10}$'
    if not re.match(bvid_pattern, bvid):
        return 500, '参数不合法'

    # 获取视频信息，包括总评论数
    aid, cid, title, reply_count = get_bvid_info(bvid)
    if not aid or not cid:
        return 500, '数据异常'

    # 计算总页数（每页20条评论）
    if reply_count:
        total_pages = (reply_count + 19) // 20

        all_comments = []
        page = 1

        # 循环获取所有页评论
        while True:
            json_data = get_comments(aid, page)

            if not json_data or json_data["code"] != 0 or "replies" not in json_data["data"]:
                break

            comments = parse_comments(json_data)
            if not comments:
                break

            all_comments.extend(comments)

            # 检查是否还有下一页
            if len(comments) < 20:
                break

            if page == 30:
                break

            page += 1

        # 输出原始评论总数

        if all_comments:
            # 过滤评论
            filtered_comments = filter_comments(all_comments)

            if filtered_comments:
                # 当评论数量大于30时，选择相似度最低的30条评论
                if len(filtered_comments) > 30:
                    similarity_matrix = compute_similarity_matrix(filtered_comments)
                    final_comments = select_diverse_comments(filtered_comments, similarity_matrix)
                else:
                    final_comments = filtered_comments

                return final_comments
            else:
                return []
        else:
            return []
    else:
        return []