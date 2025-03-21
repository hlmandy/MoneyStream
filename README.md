# MoneyStream 个人记账系统

## 项目简介

这是一个使用Trae Claude-3.5-Sonnet开发的个人记账系统，旨在帮助用户更好地管理个人财务。系统提供了直观的界面和完整的功能，让用户可以轻松地记录和管理日常收支。

## 主要功能

### 1. 账目管理
- 支持收入和支出记录
- 支持转账记录
- 灵活的账目筛选和查询
- 可视化的账目统计分析

### 2. 类别管理
- 支持自定义收支类别
- 多级类别体系
- 灵活的类别调整功能

### 3. 账户管理
- 支持多种账户类型（借记卡、信用卡、电子钱包、理财等）
- 实时账户余额显示
- 账户信息的增删改查

### 4. 报销退款
- 支持报销记录管理
- 退款流程处理
- 关联交易追踪

## 技术栈

- **前端框架**：Streamlit
- **数据处理**：Pandas
- **数据可视化**：Plotly
- **AI 开发助手**：Trae Claude-3.5-Sonnet

## 使用说明

1. 确保已安装所需依赖：
   ```bash
   pip install streamlit pandas plotly
   ```

2. 运行应用：
   ```bash
   streamlit run Home.py
   ```

## 开发说明

本项目主要由Trae Claude-3.5-Sonnet辅助开发，AI助手在以下方面提供了重要支持：
- 代码编写和优化
- 功能设计和实现
- 问题诊断和修复
- 代码重构和改进

## 项目结构

```
├── Home.py                 # 主页面
├── pages/                  # 功能页面
│   ├── 01_账目明细.py
│   ├── 02_报销退款.py
│   ├── 03_账目统计.py
│   ├── 20_账户管理.py
│   └── 21_类目管理.py
├── Data/                   # 数据文件
└── util.py                # 工具函数
```