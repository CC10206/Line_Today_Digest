from fastapi import APIRouter, Depends, Header, HTTPException, Request
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, PostbackEvent, TextMessageContent, WebhookParser

from app.config import settings
from app.linebot.commands import CommandRouter, get_command_router

router = APIRouter()
parser = WebhookParser(settings.line_channel_secret)


@router.post("/callback", include_in_schema=False)
async def callback(
    request: Request,
    x_line_signature: str = Header(...),
    cmd: CommandRouter = Depends(get_command_router),
):
    body = (await request.body()).decode()
    try:
        events = parser.parse(body, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(400, "invalid signature")

    for ev in events:
        if isinstance(ev, MessageEvent) and isinstance(ev.message, TextMessageContent):
            messages = cmd.on_text(ev.message.text.strip())
        elif isinstance(ev, PostbackEvent):
            messages = cmd.on_postback(ev.source.user_id, ev.postback.data)
        else:
            continue
        # TODO: await line_api.reply_message(ReplyMessageRequest(reply_token=ev.reply_token, messages=messages))
    return "OK"
