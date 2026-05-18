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

SEARCH_PROBLEMS = {
    "operationName": "problemsetQuestionList",
    "query": """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
    problemsetQuestionList: questionList(categorySlug: $categorySlug, limit: $limit, skip: $skip, filters: $filters) {
        total
        questions {
            frontendQuestionId: questionFrontendId
            title
            titleCn
            difficulty
            topicTags {
                name
                nameTranslated
            }
            status
            acRate
            titleSlug
        }
    }
}
""",
    "variables": {
        "categorySlug": "",
        "skip": 0,
        "limit": 50,
        "filters": {}
    }
}

# 获取用户已通过的题目列表
def get_user_solved_query(user_slug: str, skip: int = 0, first: int = 100):
    return {
        "operationName": "userProfileQuestions",
        "query": """
query userProfileQuestions($status: StatusFilterEnum!, $skip: Int!, $first: Int!) {
    userProfileQuestions(status: $status, skip: $skip, first: $first) {
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
            "userSlug": user_slug,
            "status": "ACCEPTED",
            "skip": skip,
            "first": first
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
