from linebot.v3.messaging import (
    FlexBox,
    FlexBubble,
    FlexButton,
    FlexCarousel,
    FlexMessage,
    FlexText,
    MessageAction,
    PostbackAction,
    QuickReply,
    QuickReplyItem,
    TextMessage,
    URIAction,
)

from app.common.schemas import ArticleSummary


def article_bubble(article: ArticleSummary) -> FlexBubble:
    return FlexBubble(
        body=FlexBox(
            layout="vertical",
            contents=[
                FlexText(text=article.category or "", size="xs", color="#888888"),
                FlexText(text=article.title, weight="bold", size="md", wrap=True),
                FlexText(text=article.summary or "", size="sm", wrap=True, margin="md"),
            ],
        ),
        footer=FlexBox(
            layout="horizontal",
            contents=[
                FlexButton(action=URIAction(label="看原文", uri=article.url)),
                FlexButton(
                    action=PostbackAction(
                        label="相關新聞", data=f"action=related&id={article.id}"
                    )
                ),
            ],
        ),
    )


def article_carousel(articles: list[ArticleSummary]) -> FlexMessage:
    return FlexMessage(
        alt_text="新聞列表",
        contents=FlexCarousel(contents=[article_bubble(a) for a in articles]),
    )


def text_message(text: str, with_quick_reply: bool = False) -> TextMessage:
    if not with_quick_reply:
        return TextMessage(text=text)
    return TextMessage(
        text=text,
        quick_reply=QuickReply(
            items=[
                QuickReplyItem(action=MessageAction(label="今日新聞", text="今日新聞")),
                QuickReplyItem(action=MessageAction(label="科技", text="科技")),
                QuickReplyItem(action=MessageAction(label="財經", text="財經")),
                QuickReplyItem(action=MessageAction(label="推薦", text="推薦")),
            ]
        ),
    )
