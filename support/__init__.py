from loader import *
from support import support_hand
from support.support_chat import SupportMiddleware


if __name__ == "middlewares":
    dp.middleware.setup(SupportMiddleware())
