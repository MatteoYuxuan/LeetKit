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

RECENT_AC_SUBMISSIONS = {
    "operationName": "recentACSubmissions",
    "query": """
query recentACSubmissions {
    recentACSubmissions {
        title
        titleSlug
        timestamp
    }
}
""",
    "variables": {}
}
