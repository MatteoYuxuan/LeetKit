<p align="center">
  <img src="https://img.shields.io/badge/LeetKit-4f46e5?style=for-the-badge&logo=leetcode&logoColor=white" alt="LeetKit">
</p>

<h1 align="center">LeetKit</h1>

<p align="center">
  <strong>你的 LeetCode 个人刷题教练</strong>
</p>

<p align="center">
  记录解题思路 · 智能安排复习 · 一键同步进度 · 可视化成长轨迹
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/MatteoYuxuan/LeetKit?style=social" alt="Stars">
  <img src="https://img.shields.io/github/last-commit/MatteoYuxuan/LeetKit" alt="Last Commit">
  <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/release-v1.2.0-orange" alt="Release">
</p>

---

## 为什么选择 LeetKit？

刷 LeetCode 最怕什么？**刷了忘，忘了刷。**

LeetKit 不只是题库管理，更是你的**个人刷题教练**：

| 痛点 | LeetKit 的解决方案 |
|------|-------------------|
| 刷过的题过几天就忘 | 艾宾浩斯遗忘曲线自动安排复习，在最佳时间点提醒你 |
| 题目分散在各处，难以管理 | 统一管理 3000+ 算法题，按分类/状态/难度多维筛选 |
| 不知道自己哪里薄弱 | 分类掌握度雷达图，一目了然看到短板 |
| 手动维护做题记录太麻烦 | 一键同步 LeetCode 做题进度 |
| 复习时忘了当初怎么做的 | 每道题都有笔记、解题思路、复杂度分析 |

---

## 功能特性

### 智能复习系统

基于**艾宾浩斯遗忘曲线**，在最佳时间点安排复习：

```
第1天 → 第2天 → 第4天 → 第7天 → 第15天 → 第30天
```

- **难度自适应**：Easy 题间隔延长 30%，Hard 题间隔缩短 30%
- **渐进式回退**：忘了不会完全重置，只回退 2 个阶段
- **计时做题**：内置计时器，先做再看答案
- **键盘快捷键**：`1` 忘了 / `2` 模糊 / `3` 掌握

### LeetCode 深度集成

- **Cookie 登录**：加密存储，安全同步你的做题记录
- **一键导入**：3000+ 算法题瞬间入库
- **题单导入**：支持 LeetCode 题单和学习计划 URL
- **自动同步**：题单定期更新，新增题目自动加入
- **进度同步**：已解决的题目自动标记

### 题目管理

- 四种状态：未做 → 在做 → 已解 → 需复盘
- 支持 LCP、LCR、LCS 等特殊题号
- 快速笔记：在列表中直接记录解题印象
- 批量操作：标记状态、导出、删除、加入题单
- 资源附件：为每道题添加链接、PDF、图片等参考资源

### 题单系统

- 创建自定义刷题清单（如"面试必刷 100 题"）
- 从 LeetCode 一键导入题单/学习计划
- 按题号批量添加题目
- 题单内独立的复习统计和复习模式
- 导出分享，跨设备同步

### 数据统计

- **分类掌握度雷达图**：直观展示各分类的薄弱环节
- **难度/状态分布图**：饼图一目了然
- **每日签到热力图**：GitHub 风格，记录你的刷题日历
- **连续签到**：保持学习动力

### 笔记系统

- Markdown 编辑，支持代码高亮
- PDF 附件上传和导出
- 按分类组织，快速检索

### 数据安全

- SQLite 单文件存储，数据完全在你手里
- JSON/CSV 全量导出备份
- LeetCode Cookie Fernet 加密存储
- 自动数据库迁移，升级不丢数据

---

## 快速开始

### 一键启动（推荐）

```bash
git clone https://github.com/MatteoYuxuan/LeetKit.git
cd LeetKit
```

**Windows：** 双击 `start.bat`

**macOS / Linux：**
```bash
chmod +x start.sh
./start.sh
```

脚本会自动创建虚拟环境、安装依赖并启动服务。首次运行约需 1-2 分钟安装依赖。

启动后访问 **http://localhost:8001**

### 手动安装

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动
python main.py
```

### 环境要求

- Python 3.10+
- pip

---

## 使用指南

### 1. 导入题目

进入 **LeetCode 同步** 标签页：

- **一键导入全部题目**：点击"导入全部"，3000+ 算法题瞬间入库
- **导入题单**：粘贴 LeetCode 题单或学习计划 URL
- **同步进度**：Cookie 登录后，点击"同步进度"自动标记已解决的题目

### 2. 管理题目

进入 **题目列表** 标签页：

- 点击行查看详情
- 直接在列表中编辑笔记
- 按难度、状态、分类多维筛选
- 勾选多个题目进行批量操作

### 3. 智能复习

进入 **复习** 标签页：

- 系统自动推荐需要复习的题目
- 点击"去做一遍"启动计时器
- 完成后评分：忘了 / 模糊 / 掌握
- 系统根据评分和难度调整下次复习时间

### 4. 创建题单

进入 **题单** 标签页：

- 创建自定义题单
- 从 LeetCode 导入题单
- 按题号批量添加
- 题单内独立复习

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | FastAPI | 高性能异步 Web 框架 |
| 数据库 | SQLAlchemy + SQLite | 零配置，单文件存储 |
| 前端 | 原生 HTML/CSS/JS | 无框架依赖，轻量快速 |
| 图表 | Chart.js | 饼图、雷达图、柱状图 |
| 爬虫 | httpx + GraphQL | 异步请求 LeetCode API |
| 加密 | cryptography (Fernet) | Cookie 安全存储 |
| PDF | xhtml2pdf | Markdown 转 PDF 导出 |

---

## 项目结构

```
LeetKit/
├── main.py                  # 应用入口，自动迁移，启动服务
├── models.py                # 10 个 SQLAlchemy 数据模型
├── schemas.py               # Pydantic 请求/响应校验
├── crud.py                  # 数据库操作 + 艾宾浩斯算法
├── database.py              # 数据库连接配置
├── security.py              # Fernet 加密/解密
├── routers/                 # 13 个 API 路由模块
│   ├── problems.py          #   题目 CRUD
│   ├── reviews.py           #   复习系统
│   ├── leetcode.py          #   LeetCode 集成
│   ├── problem_lists.py     #   题单管理
│   ├── categories.py        #   分类管理
│   ├── stats.py             #   数据统计
│   ├── notes.py             #   笔记系统
│   ├── resources.py         #   资源附件
│   ├── batch.py             #   批量操作
│   ├── checkin.py           #   每日签到
│   ├── import_export.py     #   导入导出
│   ├── search.py            #   全局搜索
│   └── tags.py              #   标签管理
├── crawler/                 # LeetCode 爬虫
│   ├── leetcode_client.py   #   异步 GraphQL/REST 客户端
│   └── queries.py           #   GraphQL 查询语句
├── static/
│   └── index.html           # 前端单页应用 (~3000 行)
├── data/
│   └── notebook.db          # SQLite 数据库
├── start.bat                # Windows 一键启动
├── start.sh                 # macOS/Linux 一键启动
└── requirements.txt         # Python 依赖
```

---

## API 文档

启动服务后访问 **http://localhost:8001/docs** 查看自动生成的 Swagger API 文档。

---

## 数据备份

```bash
# JSON 全量导出（推荐）
curl http://localhost:8001/api/export/json -o backup.json

# CSV 导出题目
curl http://localhost:8001/api/export/csv -o problems.csv

# CSV 导出笔记
curl http://localhost:8001/api/export/notes/csv -o notes.csv
```

---

## 贡献

欢迎 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建分支 (`git checkout -b feature/amazing-feature`)
3. 提交改动 (`git commit -m 'feat: add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

---

## License

[MIT License](LICENSE) - 自由使用，自由分享。

---

<p align="center">
  如果觉得有用，请给一个 <strong>Star</strong> 支持一下！
</p>
