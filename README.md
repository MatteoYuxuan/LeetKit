<p align="center">
  <img src="https://img.shields.io/badge/LeetKit-4f46e5?style=for-the-badge&logo=leetcode&logoColor=white" alt="LeetKit">
  <br>
  <strong>你的 LeetCode 刷题笔记本</strong>
  <br>
  <sub>记录 · 复习 · 进阶</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/MatteoYuxuan/LeetKit?style=social" alt="Stars">
  <img src="https://img.shields.io/github/last-commit/MatteoYuxuan/LeetKit" alt="Last Commit">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## 为什么选择 LeetKit？

刷 LeetCode 最怕什么？**刷了忘，忘了刷。**

LeetKit 帮你：
- 📝 **记录**每道题的解题思路、复杂度分析
- 🧠 **艾宾浩斯遗忘曲线**自动安排复习，科学对抗遗忘
- 🔄 **一键同步** LeetCode 做题进度，告别手动维护
- 📊 **可视化统计**刷题进度，看到自己的成长

> 不只是题库管理，更是你的**个人刷题教练**。

---

## 功能亮点

### 智能复习系统

基于艾宾浩斯遗忘曲线，在最佳时间点提醒你复习：

```
第1天 → 第2天 → 第4天 → 第7天 → 第15天 → 第30天
```

每次复习后根据掌握程度调整节奏，真正实现**高效记忆**。

### LeetCode 深度集成

- 🔐 Cookie 登录，同步你的做题记录
- 📥 一键导入 3000+ 算法题
- 🏷️ 自动获取中文标题和标签
- 🔗 题号直达 LeetCode 原题

### 灵活的组织方式

- **分类**：数组、动态规划、二叉树...19 个默认分类
- **标签**：自定义标签，打造专属知识体系
- **题单**：创建个性化刷题清单（如"面试必刷 100 题"）
- **笔记**：支持 Markdown，记录解题思路

### 全局搜索

题号、标题、笔记内容...毫秒级全文搜索，快速定位。

---

## 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装

```bash
# 克隆项目
git clone https://github.com/MatteoYuxuan/LeetKit.git
cd LeetKit

# 创建虚拟环境（推荐）
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动
python main.py
```

打开浏览器访问 `http://127.0.0.1:8000`，开始你的刷题之旅！

### Windows 用户

双击 `start.bat` 即可一键启动。

---

## 功能详解

<details>
<summary><strong>📋 题目管理</strong></summary>

- 记录题号、标题、难度、状态（未做/在做/已解/需复盘）
- 支持 LCP、LCR、LCS 等特殊题号
- 批量操作：标记状态、导出、删除
- 按难度/状态/分类/标签多维筛选
</details>

<details>
<summary><strong>🧠 智能复习</strong></summary>

- 艾宾浩斯遗忘曲线自动调度
- 复习时显示解题笔记，支持"显示/隐藏答案"
- 四级掌握程度反馈（完全不会/比较模糊/基本记得/非常熟练）
- 复习时间线，一目了然
</details>

<details>
<summary><strong>🔄 LeetCode 同步</strong></summary>

- Cookie 登录，安全验证
- 同步已解决题目状态
- 批量导入全部算法题
- 同步中文标题
</details>

<details>
<summary><strong>📊 数据统计</strong></summary>

- 难度分布饼图
- 状态分布饼图
- 解题进度趋势
- 分类统计柱状图
</details>

<details>
<summary><strong>📁 导入导出</strong></summary>

- JSON 全量备份/恢复
- CSV 题目导出
- CSV 笔记导出
</details>

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + SQLite |
| 前端 | 原生 HTML/CSS/JS + Chart.js |
| 爬虫 | httpx + GraphQL |

轻量、快速、零配置。SQLite 单文件存储，数据就在你手里。

---

## 项目结构

```
LeetKit/
├── main.py              # 应用入口
├── models.py            # 数据模型
├── schemas.py           # Pydantic 校验
├── crud.py              # 数据库操作
├── database.py          # 数据库连接
├── routers/             # API 路由
│   ├── problems.py      # 题目管理
│   ├── reviews.py       # 复习系统
│   ├── leetcode.py      # LeetCode 同步
│   └── ...
├── crawler/             # LeetCode 爬虫
│   ├── leetcode_client.py
│   └── queries.py
├── static/
│   └── index.html       # 前端单页应用
├── data/                # SQLite 数据库
└── requirements.txt
```

---

## 截图

> 欢迎提交 PR 添加截图

<!-- ![Dashboard](screenshots/dashboard.png) -->
<!-- ![Review](screenshots/review.png) -->

---

## 贡献

欢迎 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的改动 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

---

## License

MIT License - 自由使用，自由分享。

---

<p align="center">
  如果觉得有用，请给一个 ⭐ Star 支持一下！
</p>
