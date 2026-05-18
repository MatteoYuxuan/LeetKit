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

# 获取用户最近通过的题目
def get_recent_ac_query(user_slug: str):
    return {
        "operationName": "recentACSubmissions",
        "query": """
query recentACSubmissions($userSlug: String!) {
    recentACSubmissions(userSlug: $userSlug) {
        submissionId
        submitTime
        question {
            translatedTitle
            titleSlug
        }
    }
}
""",
        "variables": {"userSlug": user_slug}
    }
