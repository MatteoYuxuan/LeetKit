import httpx
from . import queries

LEETCODE_CN_GRAPHQL_URL = "https://leetcode.cn/graphql/"
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.cn",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://leetcode.cn",
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


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

    async def _graphql(self, query: str, variables: dict = None, retries: int = 3) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

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
                    resp.raise_for_status()
                    data = resp.json()

                    # 检查 GraphQL 错误
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

    async def verify_cookie(self) -> dict:
        """验证 cookie 有效性，返回用户信息"""
        data = await self._graphql(queries.VERIFY_COOKIE)
        user_status = data.get("data", {}).get("userStatus", {})
        return {
            "is_signed_in": user_status.get("isSignedIn", False),
            "username": user_status.get("username", ""),
        }

    async def search_problems(
        self,
        keyword: str = None,
        category_slug: str = "",
        limit: int = 50,
        skip: int = 0,
        difficulty: str = None,
        tags: list[str] = None,
    ) -> dict:
        """搜索 LeetCode 题目"""
        filters = {}
        if keyword:
            filters["searchKeywords"] = keyword
        if difficulty:
            filters["difficulty"] = difficulty
        if tags:
            filters["tags"] = tags

        variables = {
            "categorySlug": category_slug,
            "limit": limit,
            "skip": skip,
            "filters": filters,
        }
        data = await self._graphql(queries.SEARCH_PROBLEMS, variables)
        result = data.get("data", {}).get("problemsetQuestionList", {})
        return {
            "total": result.get("total", 0),
            "questions": result.get("questions", []),
        }

    async def get_user_progress(self) -> dict:
        """获取用户做题进度"""
        data = await self._graphql(queries.USER_PROGRESS)
        return data.get("data", {}).get("userProfileQuestionsSolved", [])

    async def get_recent_ac_submissions(self) -> list:
        """获取最近通过的提交"""
        data = await self._graphql(queries.RECENT_AC_SUBMISSIONS)
        return data.get("data", {}).get("recentACSubmissions", [])
