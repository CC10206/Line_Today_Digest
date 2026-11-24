# TODO: CommandRouter - on_text(text)、on_postback(user_id, data)
#       只負責「輸入 → 要回的訊息」，不做網路呼叫，方便單元測試（PRD 第 9 節）


class CommandRouter:
    def on_text(self, text: str) -> list:
        raise NotImplementedError

    def on_postback(self, user_id: str, data: str) -> list:
        raise NotImplementedError


def get_command_router() -> CommandRouter:
    raise NotImplementedError
