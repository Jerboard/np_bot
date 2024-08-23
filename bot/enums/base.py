from enum import Enum


class AddContractStep(str, Enum):
    END_DATE = 'end_date'
    NUM = 'num'
    SUM = 'sum'


class Role(str, Enum):
    ADVERTISER = 'advertiser'
    PUBLISHER = 'publisher'


class JStatus(str, Enum):
    IP = 'ip'
    JURIDICAL = 'juridical'
    PHYSICAL = 'physical'
