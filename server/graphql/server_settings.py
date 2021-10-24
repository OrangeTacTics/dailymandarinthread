from datetime import datetime

import strawberry as s


@s.type
class ServerSettings:
    last_bump: datetime
