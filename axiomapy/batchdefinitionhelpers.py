# -*- coding: utf-8 -*-
"""
Created on Wed Jun 25 15:03:52 2025

@author: MMAD
"""

import copy
import json
import logging

from axiomapy.axiomaexceptions import AxiomaRequestValidationError
from axiomapy.odatahelpers import oDataFilterHelper as od
from axiomapy.axiomaapi import AnalysisDefinitionAPI
from axiomapy.axiomaapi import BatchDefinitionsAPI
from axiomapy import portfoliogrouphelpers


class AnalysisDefinition:
    """
    :ivar _analysisDefinitionName: The name of the analysis definition.
    :type _analysisDefinitionName: str
    :ivar _statisticDefinitions: Objects defining the statistics included in the analysis definition
    :type _statisticDefinitions: list
    :ivar _aggregationLevelDefinitions: Objects defining the aggregation level properties in the analysis definition.
    :type _aggregationLevelDefinitions: list  
    """
    _analysisDefinitionName = None
    _statisticDefinitions = None
    _aggregationLevelDefinitions = None
    
    def __init__(self,
                 name : str):
        self._analysisDefinitionName = name

    @property
    def analysisDefinitionName(self):
        return self._analysisDefinitionName

    @analysisDefinitionName.setter
    def analysisDefinitionName(self, value: str):
        self._analysisDefinitionName = value
        
    def get_analysis_definition(self) -> dict:
        if self._analysisDefinitionName is None:
            raise ValueError('Analysis Definition name cannot be null')     
        return dict(analysisDefinitionName=self._analysisDefinitionName)
    
    def get_analysis_definition_id(self) -> int:
        name=self._analysisDefinitionName
        if name is None:
            raise ValueError('Analysis Definition name cannot be null')
        try:
            r = AnalysisDefinitionAPI.get_analysis_definitions(
                filter_results=od.equals('name', name) + od.and_str + od.equals('team', 'Axioma Standard Views (Readonly)'))
            c = r.json()
            analysisDefinitionId = int(c['items'][0]['id'])
        except AxiomaRequestValidationError as e:
            logging.exception(
                'An Analysis Definition with name : %s was not found %s',
                name, e)
            raise
        self._analysisDefinitionId=analysisDefinitionId
        return analysisDefinitionId
    
        
class BatchDefinition:
    """
    :ivar _batchDefinitionName: The name of the batch definition.
    :type _batchDefinitionName: str
    :ivar _description: A brief description of the batch definition.
    :type _description: str, optional
    :ivar _portfolioGroups: The list of portfolio groups included in the batch definition.
    :type _portfolioGroups: list, portfolio group ids
    :ivar _analysisDefinitions: The analysis definitions associated with the batch definition.
    :type _analysisDefinitions: list, analysis definition ids
    
    """

    _batchDefinitionName = None
    _description = None
    _portfolioGroups = None
    _analysisDefinitions = None

    def __init__(self,
                 name : str,
                 description : str = None,
                 portfolioGroupIds : list = None,
                 analysisDefinitionIds : list = None):
        self._batchDefinitionName = name
        self._description = description
        self._portfolioGroups = portfolioGroupIds
        self._analysisDefinitions = analysisDefinitionIds
        
    @property
    def batchDefinitionName(self):
        return self._batchDefinitionName

    @batchDefinitionName.setter
    def batchDefinitionName(self, value: str):
        self._batchDefinitionName = value
        
    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value
        
    @property
    def portfolioGroups(self):
        return self._portfolioGroups

    @portfolioGroups.setter
    def portfolioGroups(self, value: str):
        self._portfolioGroups = value
        
    @property
    def analysisDefinitions(self):
        return self._analysisDefinitions

    @analysisDefinitions.setter
    def analysisDefinitions(self, value: str):
        self._analysisDefinitions = value
        
    def get_batch_definition(self) -> dict:
        if self._batchDefinitionName is None:
            raise ValueError('Batch Definition name cannot be null')     
        return dict(batchDefinitionName=self._batchDefinitionName,
                    description=self._description,
                    portfolioGroups=self._portfolioGroups,
                    analysisDefinitions=self._analysisDefinitions) 
    
    def add_portfolio_group_to_list(self, portfolio_groups : list) -> None:  #check syntax
        for item in portfolio_groups:
            if isinstance(item, portfoliogrouphelpers.PortfolioGroup):
                if item._portfolioGroupId is None:
                    item.portfoliogrouphelpers.put_portfolio_group()
                if self._portfolioGroups==None:
                    self._portfolioGroups=[]
                self._portfolioGroups.append(item._portfolioGroupId)
            else:
                raise ValueError(f'{item.portfolioName} not found') 
        self._portfolioGroups=list(set(self._portfolioGroups))
        self._portfolioGroups = sorted(self._portfolioGroups)
                
    def remove_portfolio_group(self, portfolio_group: (int, portfoliogrouphelpers.PortfolioGroup)) -> None: #check syntax
        if isinstance(portfolio_group, portfoliogrouphelpers.PortfolioGroup):
            portfolio_group = portfolio_group._portfolioGroupId
        for p in self._portfolioGroups:
            if p == portfolio_group:
                self._portfolioGroups.remove(p)
                break
            
    def add_analysis_definitions_to_list(self, analysis_definitions : list) -> None:  
        for item in analysis_definitions:
            if isinstance(item, AnalysisDefinition):
                item.get_analysis_definition_id()
                if self._analysisDefinitions==None:
                    self._analysisDefinitions=[]
                self._analysisDefinitions.append(item._analysisDefinitionId)
            else:
                raise ValueError(f'{item.analysisDefinitionName} not found') 
        self._analysisDefinitions=list(set(self._analysisDefinitions))
        self._analysisDefinitions = sorted(self._analysisDefinitions)
                
    def remove_analysis_definition(self, analysis_definition: (int, AnalysisDefinition)) -> None:
        if isinstance(analysis_definition, AnalysisDefinition):
            analysis_definition = analysis_definition._analysisDefinitionId
        for item in self._analysisDefinitions:
            if item == analysis_definition:
                self._analysisDefinitions.remove(item)
                break
            
    def get_batch_definition_id(self) -> int:
        name=self._batchDefinitionName
        if name is None:
            raise ValueError('Batch Definition name cannot be null')
        try:
            r = BatchDefinitionsAPI.get_batch_definitions(
                filter_results=od.equals('name', name))
            c = r.json()
            batchDefinitionId = int(c['items'][0]['id'])
        except AxiomaRequestValidationError as e:
            logging.exception(
                 'A Batch Definition with name : %s was not found %s',
                name, e)
            raise
        self._batchDefinitionId=batchDefinitionId
        return batchDefinitionId
   
    def put_batch_definition(self) -> bool:
        """
        """
        batch_definition_struct = dict(name = self._batchDefinitionName,
        description = self._description, 
        portfolioGroupIds=self._portfolioGroups,
        analysisDefinitionIds=self._analysisDefinitions)
        try:
            r = BatchDefinitionsAPI.post_batch_definition(batch_definition=batch_definition_struct)
            _Id = int(r.headers['location'].split('/')[-1])
        except AxiomaRequestValidationError as e:
            c = (json.loads(e.content))
            if c['message'] == 'Duplicate Resource':
                logging.info('Batch definition already exists--fetching existing portfolio')
                r = BatchDefinitionsAPI.get_batch_definitions(
                    filter_results=od.equals('name', batch_definition_struct['name']))
                c = r.json()
                _Id = int(c['items'][0]['id'])
                try:
                    r = BatchDefinitionsAPI.put_portfolio(_Id, batch_definition=batch_definition_struct)
                    print(r.json())
                    assert r.json()['items'][0]['id'] == _Id
                except AxiomaRequestValidationError as e:
                    logging.exception(
                        'Failed to update batch definition in Axioma Risk %s: %s',
                        _Id, e)
                    raise
            else:
                logging.exception('Failed to add batch definition to Axioma Risk: %s', e)
                raise
        logging.info('Batch definition ID is %d', _Id)
        self._batchDefinitionId = _Id
        return True     
    
            
    
    
        
    
        
    