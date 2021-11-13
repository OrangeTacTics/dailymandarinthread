from datetime import datetime

import strawberry as s


@s.type
class ServerSettings:
    last_bump: datetime
    exams_disabled: bool
    admin_username: str
    bot_username: str
