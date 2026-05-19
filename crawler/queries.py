# LeetCode GraphQL 查询集中管理

VERIFY_COOKIE = {
    "operationName": "globalData",
    "query": """
query globalData {
    userStatus {
        username
        isSignedIn
    }
}
""",
    "variables": {}
}

# 获取题目详情
def get_problem_detail_query(title_slug: str) -> dict:
    return {
        "operationName": "questionDetail",
        "query": """
query questionDetail($titleSlug: String!) {
    question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        title
        translatedTitle
        titleSlug
        content
        translatedContent
        difficulty
        topicTags {
            name
            slug
        }
        codeSnippets {
            lang
            langSlug
            code
        }
        stats
        hints
        similarQuestions
    }
}
""",
        "variables": {"titleSlug": title_slug}
    }


# 批量获取题目列表（含中文标题）
def get_all_problems_query(skip: int = 0, limit: int = 100) -> dict:
    return {
        "operationName": "problemsetQuestionList",
        "query": """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
    problemsetQuestionList(categorySlug: $categorySlug, limit: $limit, skip: $skip, filters: $filters) {
        total
        questions {
            frontendQuestionId
            title
            titleCn
            titleSlug
            difficulty
            acRate
            paidOnly
            topicTags {
                name
                slug
            }
        }
    }
}
""",
        "variables": {
            "categorySlug": "",
            "skip": skip,
            "limit": limit,
            "filters": {}
        }
    }


# 获取用户已通过的题目列表
def get_user_solved_query(user_slug: str, skip: int = 0, first: int = 100):
    return {
        "operationName": "userProfileQuestions",
        "query": """
query userProfileQuestions($status: StatusFilterEnum!, $skip: Int!, $first: Int!, $sortField: SortFieldEnum!, $sortOrder: SortingOrderEnum!) {
    userProfileQuestions(status: $status, skip: $skip, first: $first, sortField: $sortField, sortOrder: $sortOrder) {
        totalNum
        questions {
            translatedTitle
            frontendId
            titleSlug
            title
            difficulty
            lastSubmittedAt
            numSubmitted
        }
    }
}
""",
        "variables": {
            "status": "ACCEPTED",
            "skip": skip,
            "first": first,
            "sortField": "LAST_SUBMITTED_AT",
            "sortOrder": "DESCENDING"
        }
    }

# 通过题单 ID 获取题目列表
def get_favorite_question_list_query(favorite_slug: str, skip: int = 0, limit: int = 100) -> dict:
    return {
        "operationName": "favoriteQuestionList",
        "query": """
query favoriteQuestionList($favoriteSlug: String!, $skip: Int, $limit: Int) {
    favoriteQuestionList(favoriteSlug: $favoriteSlug, skip: $skip, limit: $limit) {
        totalLength
        hasMore
        questions {
            questionFrontendId
            title
            translatedTitle
            titleSlug
            difficulty
            paidOnly
        }
    }
}
""",
        "variables": {
            "favoriteSlug": favorite_slug,
            "skip": skip,
            "limit": limit,
        }
    }


# 获取用户做题进度（按难度统计）
def get_user_progress_query(user_slug: str):
    return {
        "operationName": "userQuestionProgress",
        "query": """
query userQuestionProgress($userSlug: String!) {
    userProfileUserQuestionProgress(userSlug: $userSlug) {
        numAcceptedQuestions {
            difficulty
            count
        }
        numFailedQuestions {
            difficulty
            count
        }
        numUntouchedQuestions {
            difficulty
            count
        }
    }
}
""",
        "variables": {"userSlug": user_slug}
    }


# 获取学习计划详情（含所有分组的题目）
def get_study_plan_detail_query(plan_slug: str) -> dict:
    return {
        "operationName": "studyPlanV2Detail",
        "query": """
query studyPlanV2Detail($slug: String!) {
    studyPlanV2Detail(planSlug: $slug) {
        name
        planSubGroups {
            name
            questions {
                questionFrontendId
                title
                translatedTitle
                titleSlug
                difficulty
            }
        }
    }
}
""",
        "variables": {"slug": plan_slug},
    }
