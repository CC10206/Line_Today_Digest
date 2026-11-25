from fastapi import APIRouter, Depends, Header, HTTPException, Request
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
)
from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import MessageEvent, PostbackEvent, TextMessageContent

from app.config import settings
from app.linebot.commands import CommandRouter, get_command_router

router = APIRouter()
parser = WebhookParser(settings.line_channel_secret)
_configuration = Configuration(access_token=settings.line_channel_access_token)
_api_client: AsyncApiClient | None = None


async def init_line_api() -> None:
    global _api_client
    _api_client = AsyncApiClient(_configuration)


async def close_line_api() -> None:
    global _api_client
    if _api_client is not None:
        await _api_client.close()
        _api_client = None


async def get_line_api() -> AsyncMessagingApi:
    return AsyncMessagingApi(_api_client)


@router.post("/callback", include_in_schema=False)
async def callback(
    request: Request,
    x_line_signature: str = Header(...),
    cmd: CommandRouter = Depends(get_command_router),
    line_api: AsyncMessagingApi = Depends(get_line_api),
):
    body = (await request.body()).decode()
    try:
        events = parser.parse(body, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(400, "invalid signature")

    for ev in events:
        if isinstance(ev, MessageEvent) and isinstance(ev.message, TextMessageContent):
            messages = cmd.on_text(ev.source.user_id, ev.message.text.strip())
        elif isinstance(ev, PostbackEvent):
            messages = cmd.on_postback(ev.source.user_id, ev.postback.data)
        else:
            continue
        await line_api.reply_message(
            ReplyMessageRequest(reply_token=ev.reply_token, messages=messages)
        )
    return "OK"
