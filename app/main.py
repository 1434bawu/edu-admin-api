import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.db import get_conn, init_db

init_db()
app = FastAPI(title="教务管理系统 API", version="0.1.0")


# ==================== 请求体模型 ====================
# BaseModel 负责“格式校验”：字段缺了、类型不对 → FastAPI 自动返回 422
# 业务规则（学分 1-10、分数 0-100）在接口里自己判断 → 返回 400

class StudentIn(BaseModel):
    stu_id: str
    stu_name: str
    class_name: str = ""


class CourseIn(BaseModel):
    cs_name: str
    credit: float
    teacher: str = ""


class ScoreIn(BaseModel):
    student_id: int
    course_id: int
    score: float
    term: str = "2026-2027-1"


# ==================== 健康检查 ====================
@app.get("/health")
def health():
    """服务活着就返回 ok，给监控和冒烟测试用。"""
    return {"status": "ok"}


# ==================== 学生 ====================
@app.get("/students")
def get_students(stu_id: str | None = None):
    """学生列表。带 ?stu_id=xxx 就是按学号搜索。"""
    conn = get_conn()
    try:
        if stu_id:
            rows = conn.execute(
                "SELECT * FROM students WHERE stu_id=?", (stu_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM students").fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


@app.get("/students/{sid}")
def get_student(sid: int):
    """学生详情。sid 是数据库主键 id，不是学号。"""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return dict(row)


@app.post("/students", status_code=201)
def add_stu(stu: StudentIn):
    """新增学生。学号重复 → 409。"""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO students (stu_id, stu_name, class_name) VALUES (?, ?, ?)",
            (stu.stu_id, stu.stu_name, stu.class_name),
        )
        conn.commit()
        sid = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="学号已存在")
    finally:
        conn.close()
    return get_student(sid)


@app.put("/students/{sid}")
def update_student(sid: int, stu: StudentIn):
    """修改学生。不存在 → 404；学号改成别人的 → 409。"""
    conn = get_conn()
    try:
        row = conn.execute("SELECT id FROM students WHERE id=?", (sid,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="学生不存在")
        try:
            conn.execute(
                "UPDATE students SET stu_id=?, stu_name=?, class_name=? WHERE id=?",
                (stu.stu_id, stu.stu_name, stu.class_name, sid),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="学号已被占用")
    finally:
        conn.close()
    return get_student(sid)


@app.delete("/students/{sid}", status_code=204)
def delete_student(sid: int):
    """删除学生。不存在 → 404；有成绩记录 → 409（外键挡住）。"""
    conn = get_conn()
    try:
        row = conn.execute("SELECT id FROM students WHERE id=?", (sid,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="学生不存在")
        try:
            conn.execute("DELETE FROM students WHERE id=?", (sid,))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="该学生已有成绩记录，不能删除")
    finally:
        conn.close()
    return None          # 204 不能带响应体


# ==================== 课程 ====================
@app.post("/courses", status_code=201)
def create_course(course: CourseIn):
    """新增课程。学分不在 1-10 → 400。"""
    if not course.cs_name.strip():
        raise HTTPException(status_code=400, detail="课程名不能为空")
    if not (1 <= course.credit <= 10):
        raise HTTPException(status_code=400, detail="学分必须在 1-10 之间")

    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO courses (cs_name, credit, teacher) VALUES (?, ?, ?)",
            (course.cs_name, course.credit, course.teacher),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM courses WHERE id=?", (cur.lastrowid,)
        ).fetchone()
    finally:
        conn.close()
    return dict(row)


# ==================== 成绩 ====================
@app.post("/scores", status_code=201)
def create_score(data: ScoreIn):
    """录入成绩。分数越界 → 400；学生/课程不存在 → 404；重复录入 → 409。"""
    if not (0 <= data.score <= 100):
        raise HTTPException(status_code=400, detail="分数必须在 0-100 之间")

    conn = get_conn()
    try:
        # 成绩必须挂在真实的学生和课程上，否则就是孤儿数据
        if conn.execute(
            "SELECT id FROM students WHERE id=?", (data.student_id,)
        ).fetchone() is None:
            raise HTTPException(status_code=404, detail="学生不存在")
        if conn.execute(
            "SELECT id FROM courses WHERE id=?", (data.course_id,)
        ).fetchone() is None:
            raise HTTPException(status_code=404, detail="课程不存在")

        try:
            cur = conn.execute(
                "INSERT INTO scores (student_id, course_id, score, term) VALUES (?, ?, ?, ?)",
                (data.student_id, data.course_id, data.score, data.term),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="该学生该课程本学期已有成绩")

        row = conn.execute(
            "SELECT * FROM scores WHERE id=?", (cur.lastrowid,)
        ).fetchone()
    finally:
        conn.close()
    return dict(row)


@app.get("/students/{sid}/scores")
def get_student_scores(sid: int):
    """查某学生所有成绩。要 JOIN courses 才能拿到课程名。"""
    conn = get_conn()
    try:
        if conn.execute(
            "SELECT id FROM students WHERE id=?", (sid,)
        ).fetchone() is None:
            raise HTTPException(status_code=404, detail="学生不存在")

        rows = conn.execute(
            """
            SELECT s.id, c.cs_name AS course_name, c.credit, s.score, s.term
            FROM scores AS s
            JOIN courses AS c ON s.course_id = c.id
            WHERE s.student_id = ?
            ORDER BY s.id
            """,
            (sid,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
