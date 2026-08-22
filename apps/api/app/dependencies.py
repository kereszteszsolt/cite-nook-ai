# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_session

DatabaseSession = Annotated[Session, Depends(get_session)]
