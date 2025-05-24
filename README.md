# BiliIns - 哔哩哔哩创作者数据分析平台

![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

[English](./README_EN.md) | 简体中文

## 📌 项目简介

BiliIns（Bilibili Data Insight）是一个免费开源的哔哩哔哩创作者内容数据分析平台，通过：

- 多维度数据计算与统计
- 历史稿件对比分析
- AI驱动的评论区情感分析
- 可视化数据报表

为UP主提供全面、深入的内容数据分析，帮助优化创作策略。

## ✨ 核心功能

### 📊 综合数据看板
- 稿件基础数据统计（播放、点赞、收藏等）
- 观众互动趋势分析
- 粉丝增长关联分析
- 多稿件横向对比

### 🤖 AI评论分析
- 评论情感极性分析
- 高频关键词提取
- 弹幕内容聚类
- 优质评论自动识别

### 📈 创作建议
- 最佳发布时间预测
- 标签优化建议
- 内容类型推荐
- 竞品对比分析

## 🛠 安装指南

### 环境要求
- Python 3.8+
- Redis 5.0+
- MySQL 5.7+

### 快速开始
```bash
# 克隆项目
git clone https://github.com/yourname/BiliIns.git

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动服务
python app.py


## 🖥 使用说明

1. 登录B站账号（仅读取公开数据）
2. 输入稿件BV号或UP主UID
3. 查看数据分析报告
4. 导出PDF/Excel格式报告

![示例截图](docs/screenshot.png)

## 📚 数据维度

| 模块        | 指标项                     |
|-------------|---------------------------|
| 基础数据    | 播放量、点赞、投币、收藏   |
| 观众分析    | 观看时长、留存率、地域分布 |
| 互动分析    | 评论热词、弹幕密度        |
| 收益分析    | 预估收益、单价趋势        |

## 🤝 参与贡献

欢迎通过以下方式参与项目：
- 提交Pull Request
- 报告Issues
- 完善文档
- 分享使用案例

请先阅读[贡献指南](CONTRIBUTING.md)

## 📄 开源协议

本项目采用 [MIT License](LICENSE)

## 🌐 相关链接

- [项目主页](https://biliins.example.com)
- [API文档](https://docs.biliins.example.com)
- [开发路线图](ROADMAP.md)
- [常见问题](FAQ.md)

---

> 📧 联系邮箱：contact@biliins.example.com  
> 🐦 官方推特：[@BiliIns](https://twitter.com/BiliIns)
