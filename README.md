# 多模态智能数据分析平台

## 项目简介

这是一个基于最新AI技术的多模态智能数据分析平台，支持全域语义化检索、智能数据分析建模和结果可视化。

## 技术特点

- 🚀 **多模态支持**: 支持文本、图像、音频、视频等多种数据类型
- 🧠 **智能检索**: 基于LLM的语义化检索和GraphRAG技术
- 📊 **自动建模**: AutoML自动化数据分析和建模
- 🎨 **可视化**: 丰富的数据可视化和交互式分析

## 系统要求

- Windows 11
- NVIDIA RTX 4090 GPU
- 128GB RAM
- Docker Desktop
- Python 3.11+

## 快速开始

1. 克隆项目
```bash
git clone [项目地址]
cd All_Data_Solution_Sys
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 启动Docker服务
```bash
docker-compose up -d
```

4. 运行后端服务
```bash
cd backend
python main.py
```

5. 启动前端
```bash
cd frontend
npm install
npm start
```

## 项目结构

```
All_Data_Solution_Sys/
├── .promptx/              # PromptX配置
├── backend/               # 后端服务
│   ├── api/              # API接口
│   ├── services/         # 业务服务
│   ├── models/           # 数据模型
│   ├── data_ingestion/   # 数据接入
│   ├── semantic_processing/ # 语义处理
│   ├── analysis_modeling/   # 分析建模
│   └── tests/            # 测试代码
├── frontend/             # 前端应用
│   └── src/
│       ├── components/   # 组件
│       ├── pages/        # 页面
│       ├── services/     # 服务
│       └── utils/        # 工具
├── docker/               # Docker配置
├── k8s/                  # Kubernetes配置
├── models/               # AI模型文件
├── docs/                 # 项目文档
└── scripts/              # 脚本工具
```

## 开发团队

- 产品经理：基于PromptX产品经理角色
- 技术架构：多模态AI技术栈
- 开发环境：Cursor IDE

## 许可证

本项目采用 MIT 许可证