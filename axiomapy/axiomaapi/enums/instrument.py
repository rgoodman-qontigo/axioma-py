"""
Copyright © 2024 Axioma by SimCorp.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.

"""
from enum import unique

from axiomapy.entitybase import EnumBase


@unique
class IdentifierType(EnumBase):
    """Enum for the identifier types available for the instruments
    """

    ISIN = "ISIN"
    TICKER = "TICKER"
    Ticker = 'Ticker'
    SEDOL = "SEDOL"
    CUSIP = "CUSIP"
    Currency = "Currency"
    ClientGiven = "ClientGiven"
    AxiomaDataId = "AxiomaDataId"
    Portfolio = "Portfolio"
    PortfolioId = "PortfolioId"
    RedCodeTicker = "RedcodeTicker"
