"""
Copyright © 2024 Axioma by SimCorp.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.

"""
import datetime
import json
import logging

from axiomapy.axiomaapi import PortfoliosAPI, QuantityType, IdentifierType
from axiomapy.axiomaexceptions import AxiomaRequestValidationError
from axiomapy.odatahelpers import oDataFilterHelper as od

logger = logging.getLogger(__name__)


class Quantity:
    def __init__(self,
                 value: float,
                 scale: QuantityType,
                 currency: str = None):
        self.value = float(value)
        self.scale = scale
        self.currency = currency

    def __str__(self):
        return f'Quantity: {self.value} {self.scale} {self.currency}'

    def get_dict(self):
        my_dict = dict(value=self.value,
                       scale=self.scale.value)
        if self.currency is not None:
            my_dict['currency'] = self.currency
        return my_dict


class Identifier:
    def __init__(self,
                 identifier_type: IdentifierType,
                 identifier_id: str):
        self.identifier_type = identifier_type
        self.identifier_id = identifier_id

    def get_dict(self):
        return dict(type=self.identifier_type.value,
                    value=self.identifier_id)


class Identifiers:
    def __init__(self, identifiers: (list, None) = None):
        self.identifiers = identifiers
        if identifiers is None:
            self.identifiers = list()

    def add_identifier(self, identifier: Identifier):
        self.identifiers.append(identifier)

    def get_identifiers(self):
        return [i.get_dict() for i in self.identifiers]

    def __str__(self):
        return f'Identifiers: {self.get_identifiers()}'


class Position:
    """
    Represents a client's position in Axioma Risk.

    This class encapsulates attributes related to a financial position, enabling the
    storage, comparison, and retrieval of key position details. It supports comparison
    operators for sorting and equality evaluation based on client identifiers. This
    class is designed to ensure encapsulation and validation of its data while
    interacting with external systems or workflows.

    :ivar _client_id: Unique identifier for the client.
    :type _client_id: str
    :ivar _identifiers: Identifiers object representing the position
    :type _identifiers: Identifiers
    :ivar _quantity: Quantity object representing quantities or balances of financial
    instruments.
    :type _quantity: Quantity
    """

    def __init__(self,
                 client_id : str,
                 identifiers : Identifiers = None,
                 quantity : Quantity = None):
        self.client_id = client_id
        self.identifiers = identifiers
        self.quantity = quantity

    def __eq__(self, other):
        return self._client_id == other.client_id

    def __lt__(self, other):
        return self._client_id < other.client_id

    def __gt__(self, other):
        return self._client_id > other.client_id

    def __ge__(self, other):
        return self._client_id >= other.client_id

    def __le__(self, other):
        return self._client_id <= other.client_id

    @property
    def client_id(self) -> str:
        return self._client_id

    @client_id.setter
    def client_id(self, value: str) -> None:
        self._client_id = value

    @property
    def identifiers(self) -> Identifiers:
        return self._identifiers

    @identifiers.setter
    def identifiers(self, value: Identifiers) -> None:
        self._identifiers = value

    @property
    def quantity(self) -> Quantity:
        return self._quantity

    @quantity.setter
    def quantity(self, value: Quantity) -> None:
        self._quantity = value

    def get_position(self) -> dict:
        if self._client_id is None or \
           self._identifiers is None or \
           self._quantity is None:
            raise ValueError('Must fill in all fields for position')
        return dict(client_id=self._client_id,
                    identifiers=self._identifiers,
                    quantity=self._quantity)

    def __str__(self):
        return f'Position: {self._client_id} : {self._quantity.get_dict()}' \
               f' of {self._identifiers.get_identifiers()}'


class Benchmark:
    def __init__(self, name : str,
                 identifiers : Identifiers = None):
        self._name = name
        self._identifiers = identifiers

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def identifiers(self) -> Identifiers:
        return self._identifiers

    @identifiers.setter
    def identifiers(self, value: Identifiers) -> None:
        self._identifiers = value

    def __str__(self):
        return f'Benchmark: {self._name}' \
               f' {self._identifiers.get_identifiers()}'


class Portfolio:
    """
    Represents a financial portfolio, managing its properties, positions, and
    interaction with external systems.

    This class is designed to provide a structured representation of a financial
    portfolio, including its metadata (e.g., name, description, currency, and date)
    and associated positions. The portfolio can interact with Axioma Risk APIs to
    manage its state. Positions can also be dynamically managed (added or removed)
    and accurately tracked.

    :ivar _portfolioName: The name of the portfolio.
    :type _portfolioName: str
    :ivar _description: A brief description of the portfolio.
    :type _description: str, optional
    :ivar _currency: The default currency of the portfolio.
    :type _currency: str, optional
    :ivar _portfolioDate: The effective date of the portfolio.
    :type _portfolioDate: datetime.date
    :ivar _portfolioId: The internal identifier of the portfolio in the external system.
    :type _portfolioId: int, optional
    :ivar _benchmark: The benchmark to use for the portfolio.
    :type _benchmark: str, optional
    """

    _portfolioName = None
    _description = None
    _currency = None
    _portfolioDate = None
    _portfolioId = None              # kept internally for tracking portfolio on AxR
    _benchmark = None

    def __init__(self,
                 name : str,
                 date : (str, datetime.date) = None,
                 description : str = None,
                 currency : str = None,
                 positions : list = None,
                 benchmark : Benchmark = None):
        self._description = description
        self._portfolioName = name
        self._currency = currency
        if isinstance(date, str):
            assert len(date) == 10, 'Date must be a string of format YYYY-MM-DD'
            date = datetime.date(int(date[:4]), int(date[5:7]), int(date[8:10]))
        self._portfolioDate = date
        self._my_positions = sorted(positions) if positions is not None else []
        self._benchmark = benchmark

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value

    @property
    def currency(self):
        return self._currency

    @currency.setter
    def currency(self, value: str):
        self._currency = value

    @property
    def portfolioName(self):
        return self._portfolioName

    @portfolioName.setter
    def portfolioName(self, value: str):
        self._portfolioName = value

    @property
    def date(self):
        return self._portfolioDate

    @date.setter
    def date(self, value : (str, datetime.date)):
        if isinstance(value, str):
            assert len(value) == 10, 'Date must be a string of format YYYY-MM-DD'
            value = datetime.date(int(value[:4]), int(value[5:7]), int(value[8:10]))
        self._portfolioDate = value

    @property
    def benchmark(self) -> str or None:
        return self._benchmark

    @benchmark.setter
    def benchmark(self, value : str):
        self._benchmark = value

    @property
    def positions(self) -> list:
        return self._my_positions

    def add_position(self, position : Position) -> None:
        self._my_positions.append(position)
        self._my_positions = sorted(self._my_positions)

    def del_position(self, position : (str, Position)) -> None:
        """
        Delete a position by client_id or Position object.

        :param position: Can be a str containing a client_id or a Position object.
        :return: None
        """
        if isinstance(position, Position):
            position = position.client_id
        for p in self._my_positions:
            if p.client_id == position:
                self._my_positions.remove(p)
                break

    @positions.setter
    def positions(self, value: list[Position]) -> None:
        self._my_positions = sorted(value)

    def put_portfolio(self) -> bool:
        """
        Add or update a portfolio in Axioma Risk.

        This function attempts to add a portfolio defined by the instance's attributes
        to Axioma Risk using the `post_portfolio` method. If a portfolio with the
        same name already exists, it retrieves the existing portfolio's ID and updates
        it using the `put_portfolio` method. The portfolio's ID will be stored in the
        instance attribute `_portfolioId`.

        :raises AxiomaRequestValidationError: If an error occurs while adding or
            updating the portfolio in Axioma Risk that is not related to a duplicate
            resource.
        :raises ConnectionError: If there is an issue communicating with the Axioma
            Risk API during either portfolio creation or update.

        :return: True if the portfolio was successfully added or updated in Axioma Risk.
        :rtype: Boolean
        """
        portfolio_struct = dict(name=self._portfolioName,
                                longName=self._description,
                                defaultCurrency=self._currency)
        try:
            r = PortfoliosAPI.post_portfolio(portfolio=portfolio_struct)
            pId = int(r.headers['location'].split('/')[-1])
        except AxiomaRequestValidationError as e:
            c = (json.loads(e.content))
            if c['message'] == 'Duplicate Resource':
                logger.info('Portfolio already exists--fetching existing portfolio')
                r = PortfoliosAPI.get_portfolios(
                    filter_results=od.equals('name', portfolio_struct['name']))
                c = r.json()
                pId = int(c['items'][0]['id'])
                try:
                    r = PortfoliosAPI.put_portfolio(pId, portfolio=portfolio_struct)
                except AxiomaRequestValidationError as e:
                    logger.exception(
                        'Failed to update portfolio in Axioma Risk %s: %s',
                        pId, e)
                    raise
            else:
                logger.exception('Failed to add portfolio to Axioma Risk: %s', e)
                raise
        logger.info('Portfolio ID is %d', pId)
        self._portfolioId = pId
        return True

    def get_positions_for_date(self, date: (str, datetime.date) = None) -> int:
        """
        Fills the positions of the portfolio with the positions for a specified date.

        :param date: Date to get positions for. YYYY-MM-DD or date object.
        :return: Number of positions in the portfolio after loading.
        """
        if date is None and self._portfolioDate is None:
            raise ValueError('Must set portfolio date')
        if date is not None:
            if isinstance(date, str):
                assert len(date) == 10, 'Date must be a string of format YYYY-MM-DD'
                date = datetime.date(int(date[:4]), int(date[5:7]), int(date[8:10]))
            self._portfolioDate = date
        if self._portfolioId is None:
            self.put_portfolio()
        r = PortfoliosAPI.get_positions_at_date(
            portfolio_id=self._portfolioId,
            as_of_date=str(self._portfolioDate)
        )
        self._my_positions = []
        for p in r.json()['items']:
            identifiers = Identifiers()
            for ident in p['identifiers']:
                my_identifier = Identifier(
                    identifier_type=IdentifierType[ident['type']],
                    identifier_id=ident['value'])
                identifiers.add_identifier(my_identifier)
            self._my_positions.append(Position(
                client_id=p['clientId'],
                identifiers=identifiers,
                quantity=Quantity(scale=QuantityType[p['quantity']['scale']],
                                  value=p['quantity']['value'],
                                  currency=p.get('currency', None))))
        self._my_positions = sorted(self._my_positions)
        return len(self._my_positions)

    def __get_positions(self, date: (str, datetime.date) = None) -> dict:
        if date is None and self._portfolioDate is None:
            raise ValueError('Must set portfolio date')
        if self._portfolioDate is None:
            if isinstance(date, str):
                assert len(date) == 10, 'Date must be a string of format YYYY-MM-DD'
                date = datetime.date(int(date[:4]), int(date[5:7]), int(date[8:10]))
            self._portfolioDate = date
        return dict(
            portfolioDate=self._portfolioDate,
            positions=[p.get_position() for p in self._my_positions]
        )

    def put_positions(self) -> bool:
        """
        Handles the updating of positions within a portfolio in Axioma Risk.

        The method is responsible for deleting existing portfolio positions for a
        specified date and replacing them with new positions provided. To improve
        performance, the new positions are processed in chunks. If errors occur
        during the process, appropriate logs are generated and the method returns a
        failure status.

        :return: Returns ``True`` if all portfolio positions are successfully processed,
                 otherwise returns ``False``.

        :raises Exception: An exception is raised if an unexpected error occurs during
                           the deletion or updating of portfolio positions.

        :rtype: bool
        """
        if self._portfolioId is None:
            if not self.put_portfolio():
                return False
        try:
            logger.info('Deleting positions for portfolio %s on date %s',
                        self._portfolioId, self._portfolioDate)
            delete_positions = PortfoliosAPI.delete_positions(
                portfolio_id=self._portfolioId,
                as_of_date=str(self._portfolioDate))
            if delete_positions.status_code in range(200, 299):
                logger.info(
                    'Successfully deleted positions for portfolio %s on date %s '
                    'with status code %s',
                    self._portfolioId, self._portfolioDate,
                    delete_positions.status_code)
            else:
                logger.error(
                    'Delete positions failed for portfolio %s on date %s with status '
                    'code %s',
                    self._portfolioId, self._portfolioDate,
                    delete_positions.status_code)
                return False
        except Exception as ex:  # pylint: disable=broad-except
            logger.exception(
                'Failed to delete positions for portfolio %s on date %s: %s',
                self._portfolioId, self._portfolioDate, ex)
            return False
        chunk_size = 10000
        chunked_positions = [self._my_positions[i:i + chunk_size]
                             for i in range(0, len(self._my_positions), chunk_size)]
        logger.info(
            'Adding %s positions for portfolio %s on date %s in chunks of max '
            '%s assets',
            len(self._my_positions), self._portfolioId, self._portfolioDate,
            chunk_size)
        try:
            for i, chunk in enumerate(chunked_positions):
                positions = []
                for a in chunk:
                    positions.append(dict(clientId=a.client_id,
                                          identifiers=a.identifiers.get_identifiers(),
                                          quantity=a.quantity.get_dict()))
                patch = PortfoliosAPI.patch_positions(
                    as_of_date=str(self._portfolioDate),
                    portfolio_id=self._portfolioId,
                    positions_upsert=positions,
                    positions_remove=[])
                if patch.status_code in range(200, 299):
                    logger.info(
                        'Successfully patched positions chunk %s of %s with %s '
                        'positions for portfolio %s on date %s with status code %s',
                        i + 1, len(chunked_positions), len(chunk), self._portfolioId,
                        self._portfolioDate, patch.status_code)
                else:
                    logger.error(
                        'Failed to patch positions chunk %s of %s with %s '
                        'positions for portfolio %s on date %s with status code %s',
                        i + 1, len(chunked_positions), len(chunk), self._portfolioId,
                        self._portfolioDate, patch.status_code)
                    return False
        except Exception as ex:  # pylint: disable=broad-except
            logger.exception(
                'Failed to load positions for portfolio %s on date %s: %s',
                self._portfolioId, self._portfolioDate, ex)
            return False

        return True

    def __str__(self):
        positions = 0
        if self._my_positions is not None:
            positions = len(self._my_positions)
        return 'Portfolio: %s on %s, # of positions : %d' \
            % (self._portfolioName, self._portfolioDate, positions)

    def get_position_dates(self):
        if self._portfolioId is None:
            self.put_positions()
        r = PortfoliosAPI.get_position_dates(portfolio_id=self._portfolioId)
        for d in r.json()['items']:
            if 'date' in d:
                yield datetime.date(int(d['date'][:4]),
                                    int(d['date'][5:7]),
                                    int(d['date'][8:10]))

    @classmethod
    def get_all_portfolios(cls) -> list:
        return_list = list()
        all_portfolios = PortfoliosAPI.get_portfolios().json()
        for i in all_portfolios['items']:
            p = Portfolio(name=i['name'],
                          description=i['description'])
            p._portfolioId = int(i['id'])
            return_list.append(p)
        return return_list

    @classmethod
    def get_portfolio_by_name(cls, name : str):
        r = PortfoliosAPI.get_portfolios(
            filter_results=od.equals('name', name))
        c = r.json()
        if len(c['items']) == 0:
            return None
        pId = int(c['items'][0]['id'])
        if 'benchmark' in c['items'][0]:
            b = Benchmark(name=c['items'][0]['benchmark']['name'])
            b.identifiers = Identifiers()
            for i in c['items'][0]['benchmark']['identifiers']:
                my_identifier = Identifier(
                    identifier_type=IdentifierType[i['type']],
                    identifier_id=i['value']
                )
                b.identifiers.add_identifier(my_identifier)
        else:
            b = None
        p = Portfolio(name=name,
                      description=c['items'][0]['description'],
                      currency=c['items'][0].get('defaultCurrency'),
                      benchmark=b)
        p._portfolioId = pId
        return p
