import time
import httpx
from . import queries

LEETCODE_CN_GRAPHQL_URL = "https://leetcode.cn/graphql/"
LEETCODE_CN_API_URL = "https://leetcode.cn/api/problems/algorithms/"
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.cn",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://leetcode.cn",
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 模块级缓存
_all_problems_cache: list[dict] | None = None
_cache_timestamp: float = 0
CACHE_TTL = 3600  # 1小时


def _normalize_problem(item: dict) -> dict | None:
    """将 REST API 的 stat_status_pairs 条目映射为标准格式"""
    try:
        stat = item["stat"]
        difficulty_level = item.get("difficulty", {}).get("level", 2)
        difficulty_map = {1: "Easy", 2: "Medium", 3: "Hard"}
        total_acs = stat.get("total_acs", 0)
        total_submitted = stat.get("total_submitted", 1)
        return {
            "frontendQuestionId": stat.get("frontend_question_id", ""),
            "title": stat.get("question__title", ""),
            "titleSlug": stat.get("question__title_slug", ""),
            "difficulty": difficulty_map.get(difficulty_level, "Medium"),
            "acRate": round(total_acs / total_submitted * 100, 1) if total_submitted > 0 else 0,
            "paidOnly": item.get("paid_only", False),
            "questionId": stat.get("question_id", 0),
        }
    except (KeyError, TypeError):
        return None


class LeetCodeClient:
    def __init__(self, cookie: str = None):
        self.cookie = cookie
        self.headers = {**DEFAULT_HEADERS}
        if cookie:
            self.headers["Cookie"] = cookie
            csrf_token = self._extract_csrf_token(cookie)
            if csrf_token:
                self.headers["x-csrftoken"] = csrf_token

    def _extract_csrf_token(self, cookie: str) -> str:
        for item in cookie.split(";"):
            item = item.strip()
            if item.startswith("csrftoken="):
                return item.split("=", 1)[1]
        return ""

    async def _graphql(self, payload: dict, retries: int = 3) -> dict:
        last_error = None
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    resp = await client.post(
                        LEETCODE_CN_GRAPHQL_URL,
                        json=payload,
                        headers=self.headers,
                    )
                    if resp.status_code == 403:
                        raise Exception("Cookie 已过期，请重新登录")
                    if resp.status_code == 401:
                        raise Exception("未授权，请检查 Cookie")
                    if resp.status_code == 400:
                        text = resp.text[:200] if resp.text else ""
                        raise Exception(f"请求格式错误: {text}")
                    resp.raise_for_status()
                    data = resp.json()

                    if "errors" in data:
                        error_msg = data["errors"][0].get("message", "未知错误")
                        raise Exception(f"GraphQL 错误: {error_msg}")

                    return data
            except httpx.TimeoutException:
                last_error = Exception("请求超时，请检查网络连接")
                if attempt == retries - 1:
                    raise last_error
            except Exception as e:
                last_error = e
                if attempt == retries - 1:
                    raise

        raise last_error

    async def _http_get(self, url: str, retries: int = 3) -> dict:
        last_error = None
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    resp = await client.get(url, headers=DEFAULT_HEADERS)
                    resp.raise_for_status()
                    return resp.json()
            except httpx.TimeoutException:
                last_error = Exception("请求超时，请检查网络连接")
                if attempt == retries - 1:
                    raise last_error
            except Exception as e:
                last_error = e
                if attempt == retries - 1:
                    raise

        raise last_error

    async def fetch_all_problems(self, include_paid: bool = False) -> list[dict]:
        """通过 REST API 获取所有算法题目（带缓存）"""
        global _all_problems_cache, _cache_timestamp

        now = time.time()
        if _all_problems_cache is not None and now - _cache_timestamp < CACHE_TTL:
            problems = _all_problems_cache
        else:
            data = await self._http_get(LEETCODE_CN_API_URL)
            raw_pairs = data.get("stat_status_pairs", [])
            problems = []
            for item in raw_pairs:
                normalized = _normalize_problem(item)
                if normalized:
                    problems.append(normalized)
            _all_problems_cache = problems
            _cache_timestamp = now

        if not include_paid:
            problems = [p for p in problems if not p.get("paidOnly")]

        return problems

    async def search_problems(
        self,
        keyword: str = None,
        difficulty: str = None,
        limit: int = 50,
        skip: int = 0,
    ) -> dict:
        """搜索 LeetCode 题目（本地过滤）"""
        all_problems = await self.fetch_all_problems()

        filtered = all_problems
        if difficulty:
            difficulty_lower = difficulty.lower()
            filtered = [p for p in filtered if p["difficulty"].lower() == difficulty_lower]

        if keyword:
            kw = keyword.lower()
            filtered = [
                p for p in filtered
                if kw in p["title"].lower()
                or kw in p["titleSlug"].lower()
                or kw in p["frontendQuestionId"].lower()
            ]

        total = len(filtered)
        page = filtered[skip: skip + limit]
        return {"total": total, "questions": page}

    async def get_problem_detail(self, title_slug: str) -> dict:
        """通过 GraphQL 获取单题详情"""
        payload = queries.get_problem_detail_query(title_slug)
        data = await self._graphql(payload)
        return data.get("data", {}).get("question", {})

    async def fetch_all_problem_titles(self) -> dict[str, str]:
        """批量获取所有题目的中文标题，返回 {frontendQuestionId: titleCn}"""
        result = {}
        skip = 0
        limit = 100
        total = None

        while True:
            payload = queries.get_all_problems_query(skip=skip, limit=limit)
            data = await self._graphql(payload)
            ql = data.get("data", {}).get("problemsetQuestionList", {})

            if total is None:
                total = ql.get("total", 0)

            questions = ql.get("questions", [])
            if not questions:
                break

            for q in questions:
                fid = q.get("frontendQuestionId", "")
                title_cn = q.get("titleCn", "")
                if fid and title_cn:
                    result[fid] = title_cn

            skip += limit
            if skip >= total:
                break

        return result

    async def fetch_all_problems_with_tags(self, include_paid: bool = False) -> list[dict]:
        """通过 GraphQL API 获取所有算法题目（含 topicTags）"""
        all_problems = []
        skip = 0
        limit = 100
        total = None

        while True:
            payload = queries.get_all_problems_query(skip=skip, limit=limit)
            data = await self._graphql(payload)
            ql = data.get("data", {}).get("problemsetQuestionList", {})

            if total is None:
                total = ql.get("total", 0)

            questions = ql.get("questions", [])
            if not questions:
                break

            for q in questions:
                # 跳过付费题
                if not include_paid and q.get("paidOnly", False):
                    continue

                # 提取 topicTags
                topic_tags = []
                for tag in q.get("topicTags", []):
                    topic_tags.append({
                        "name": tag.get("name", ""),
                        "slug": tag.get("slug", ""),
                    })

                all_problems.append({
                    "frontendQuestionId": q.get("frontendQuestionId", ""),
                    "title": q.get("title", ""),
                    "titleCn": q.get("titleCn", ""),
                    "titleSlug": q.get("titleSlug", ""),
                    "difficulty": q.get("difficulty", "Medium"),
                    "acRate": q.get("acRate", 0),
                    "paidOnly": q.get("paidOnly", False),
                    "topicTags": topic_tags,
                })

            skip += limit
            if skip >= total:
                break

        return all_problems

    async def verify_cookie(self) -> dict:
        """验证 cookie 有效性，返回用户信息"""
        data = await self._graphql(queries.VERIFY_COOKIE)
        user_status = data.get("data", {}).get("userStatus", {})
        return {
            "is_signed_in": user_status.get("isSignedIn", False),
            "username": user_status.get("username", ""),
        }

    async def get_user_progress(self, user_slug: str) -> dict:
        """获取用户做题进度"""
        payload = queries.get_user_progress_query(user_slug)
        data = await self._graphql(payload)
        return data.get("data", {}).get("userProfileUserQuestionProgress", {})

    async def get_user_solved_problems(self, user_slug: str, limit: int = 100) -> list:
        """获取用户已解决的题目列表"""
        payload = queries.get_user_solved_query(user_slug, skip=0, first=limit)
        data = await self._graphql(payload)
        result = data.get("data", {}).get("userProfileQuestions", {})
        return result.get("questions", [])
