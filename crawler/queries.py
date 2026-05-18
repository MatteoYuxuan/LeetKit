# LeetCode GraphQL 查询集中管理

VERIFY_COOKIE = """
query globalData {
    userStatus {
        username
        isSignedIn
    }
}
"""

SEARCH_PROBLEMS = """
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
"""

USER_PROGRESS = """
query userProfileQuestionsSolved {
    userProfileQuestionsSolved {
        difficulty
        count
    }
}
"""

RECENT_AC_SUBMISSIONS = """
query recentACSubmissions {
    recentACSubmissions {
        title
        titleSlug
        timestamp
    }
}
"""
