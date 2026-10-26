# 教务管理系统 API（edu-admin-api）

一个**用来练手接口自动化测试**的最小后端：学生 / 课程 / 成绩三张表，9 个接口。
后端自己写（代码量很小），测试用 pytest + requests。

> 目标：两周内做出一个「能跑、能测、能给别人看」的项目，写进简历。
>
> **每天具体做什么 → [docs/7天手册.md](docs/7天手册.md)**（含代码框架、验收标准、卡住了怎么办）

## 技术栈

- Python 3.12 + FastAPI + SQLite
- pytest + requests + pytest-html（本机没有 Java，Allure 用不了）
- GitHub Actions（提交自动跑测试）

## 怎么跑起来

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

浏览器打开 <http://127.0.0.1:8000/docs>，能看到自动生成的接口文档就说明跑通了。

## 数据表设计

**students（学生）**

| 字段 | 类型 | 约束 |
|---|---|---|
| id | INTEGER | 主键，自增 |
| student_no | TEXT | 唯一，非空（学号） |
| name | TEXT | 非空 |
| class_name | TEXT | 班级 |
| created_at | TEXT | 创建时间 |

**courses（课程）**

| 字段 | 类型 | 约束 |
|---|---|---|
| id | INTEGER | 主键，自增 |
| name | TEXT | 非空 |
| credit | REAL | 学分，1–10 |
| teacher | TEXT | 任课教师 |

**scores（成绩）**

| 字段 | 类型 | 约束 |
|---|---|---|
| id | INTEGER | 主键，自增 |
| student_id | INTEGER | 外键 → students.id |
| course_id | INTEGER | 外键 → courses.id |
| score | REAL | 0–100 |
| term | TEXT | 学期，如 2026-2027-1 |

## 接口清单（共 9 个）

| # | 方法 | 路径 | 说明 | 状态码 |
|---|---|---|---|---|
| 1 | GET | `/health` | 健康检查 | 200 |
| 2 | POST | `/students` | 新增学生 | 201 / 400 / 409 |
| 3 | GET | `/students` | 学生列表 | 200 |
| 4 | GET | `/students/{sid}` | 学生详情 | 200 / 404 |
| 5 | PUT | `/students/{sid}` | 修改学生 | 200 / 404 |
| 6 | DELETE | `/students/{sid}` | 删除学生 | 204 / 404 |
| 7 | POST | `/courses` | 新增课程 | 201 / 400 |
| 8 | POST | `/scores` | 录入成绩 | 201 / 400 / 404 |
| 9 | GET | `/students/{sid}/scores` | 查某学生所有成绩 | 200 / 404 |

**故意留的坑（正好用来练测试）**

- 学号重复 → 409
- 分数 101 或 -1 → 400
- 学分 0 或 11 → 400
- 给不存在的学生录成绩 → 404
- 姓名为空字符串 → 400
- 删除不存在的学生 → 404

## 测试怎么跑

```bash
pytest -v
pytest -v --html=reports/report.html --self-contained-html
```

> 跑测试前，uvicorn 要先开着。

## 进度（做完一项就打勾，commit 一次）

- [*] Day 1：`/health` + 学生新增 / 列表 / 详情（3 个接口）
- [ ] Day 2：补齐学生改删 + 课程 + 成绩（9 个接口）
- [ ] Day 3：pytest 跑通 5 条用例
- [ ] Day 4：扩到 20 条（缺参 / 类型错 / 不存在 / 重复）
- [ ] Day 5：YAML 数据驱动 + 三层断言
- [ ] Day 6：pytest-html 报告 + GitHub Actions
- [ ] Day 7：补到 35 条以上 + README 截图 + 1 分钟演示

## 备注

- 每周至少 4 次 commit，提交信息写清楚做了什么。
- 写完每个接口，先用 `/docs` 页面手动调一遍，确认能用再写测试。
