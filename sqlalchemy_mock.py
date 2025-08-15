#!/usr/bin/env python3
"""
Mock SQLAlchemy module for running tests without sqlalchemy

This provides the basic SQLAlchemy functionality that our test files need
to run without the actual sqlalchemy package.
"""

import sys
from unittest.mock import MagicMock


# Mock SQLAlchemy classes
class Base:
    """Mock SQLAlchemy Base class"""

    metadata = MagicMock()


# Mock SQLAlchemy exceptions
class IntegrityError(Exception):
    """Mock IntegrityError exception"""

    pass


class SQLAlchemyError(Exception):
    """Mock SQLAlchemyError exception"""

    pass


class Engine:
    """Mock SQLAlchemy Engine class"""

    def __init__(self, *args, **kwargs):
        pass

    def dispose(self):
        pass

    @property
    def dialect(self):
        return MagicMock()

    def connect(self):
        """Mock connect method"""
        return MagicMock()


class Session:
    """Mock SQLAlchemy Session class"""

    def __init__(self):
        pass

    def close(self):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass

    def add(self, obj):
        pass

    def query(self, *args):
        return MagicMock()

    def execute(self, *args, **kwargs):
        return MagicMock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SessionLocal:
    """Mock SQLAlchemy SessionLocal class"""

    def __init__(self):
        pass

    def __call__(self):
        return Session()


# Mock User model class with all required attributes
class User:
    """Mock User model class"""

    def __init__(self, **kwargs):
        # Set all attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Set default values for commonly used attributes
        if not hasattr(self, 'id'):
            self.id = kwargs.get('id', 1)
        if not hasattr(self, 'telegram_user_id'):
            self.telegram_user_id = kwargs.get('telegram_user_id', 123456789)
        if not hasattr(self, 'first_name'):
            self.first_name = kwargs.get('first_name', 'Test')
        if not hasattr(self, 'last_name'):
            self.last_name = kwargs.get('last_name', 'User')
        if not hasattr(self, 'phone'):
            self.phone = kwargs.get('phone', '09123456789')
        if not hasattr(self, 'grade'):
            self.grade = kwargs.get('grade', '10')
        if not hasattr(self, 'major'):
            self.major = kwargs.get('major', 'ریاضی')
        if not hasattr(self, 'province'):
            self.province = kwargs.get('province', 'تهران')
        if not hasattr(self, 'city'):
            self.city = kwargs.get('city', 'تهران')
        if not hasattr(self, 'is_approved'):
            self.is_approved = kwargs.get('is_approved', False)
        if not hasattr(self, 'is_banned'):
            self.is_banned = kwargs.get('is_banned', False)


def create_engine(*args, **kwargs):
    """Mock create_engine function"""
    return Engine(*args, **kwargs)


def text(query):
    """Mock text function"""
    return MagicMock()


# Mock SQLAlchemy column types
class Column:
    """Mock SQLAlchemy Column class"""

    def __init__(self, *args, **kwargs):
        pass


class String:
    """Mock SQLAlchemy String class"""

    def __init__(self, *args, **kwargs):
        pass


class Integer:
    """Mock SQLAlchemy Integer class"""

    def __init__(self, *args, **kwargs):
        pass


class Boolean:
    """Mock SQLAlchemy Boolean class"""

    def __init__(self, *args, **kwargs):
        pass


class DateTime:
    """Mock SQLAlchemy DateTime class"""

    def __init__(self, *args, **kwargs):
        pass


class Text:
    """Mock SQLAlchemy Text class"""

    def __init__(self, *args, **kwargs):
        pass


class ForeignKey:
    """Mock SQLAlchemy ForeignKey class"""

    def __init__(self, *args, **kwargs):
        pass


class UniqueConstraint:
    """Mock SQLAlchemy UniqueConstraint class"""

    def __init__(self, *args, **kwargs):
        pass


class BigInteger:
    """Mock SQLAlchemy BigInteger class"""

    def __init__(self, *args, **kwargs):
        pass


class Float:
    """Mock SQLAlchemy Float class"""

    def __init__(self, *args, **kwargs):
        pass


class Date:
    """Mock SQLAlchemy Date class"""

    def __init__(self, *args, **kwargs):
        pass


class Time:
    """Mock SQLAlchemy Time class"""

    def __init__(self, *args, **kwargs):
        pass


class Enum:
    """Mock SQLAlchemy Enum class"""

    def __init__(self, *args, **kwargs):
        pass


class JSON:
    """Mock SQLAlchemy JSON class"""

    def __init__(self, *args, **kwargs):
        pass


class Index:
    """Mock SQLAlchemy Index class"""

    def __init__(self, *args, **kwargs):
        pass


# Mock SQLAlchemy functions
class SelectQuery:
    """Lightweight select/where expression that our DB mock can interpret"""

    def __init__(self, model):
        self.model = model
        self.clauses = []  # list of tuples like (op, field, value)

    def where(self, *predicates):
        # Support multiple equality predicates represented as tuples ("eq", field, value)
        for predicate in predicates:
            if isinstance(predicate, tuple) and len(predicate) == 3 and predicate[0] == "eq":
                self.clauses.append(predicate)
        return self

    def order_by(self, *args, **kwargs):
        # Ignored in mock but kept for chaining compatibility
        return self


def select(model, *args, **kwargs):
    """Return a SelectQuery understandable by database_mock.Session.execute"""
    return SelectQuery(model)


def update(*args, **kwargs):
    """Mock update function"""
    return MagicMock()


def func(*args, **kwargs):
    """Mock func function"""
    return MagicMock()


# Mock func.count specifically
func.count = MagicMock()


# Mock session_scope context manager
class session_scope:
    """Mock session_scope context manager"""

    def __init__(self):
        self.session = Session()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()


# Add to sys.modules so imports work
sys.modules['sqlalchemy'] = sys.modules[__name__]


# Provide a minimal orm module with sessionmaker returning our database session
class orm_module:
    @staticmethod
    def sessionmaker(bind=None):
        def _factory():
            # Use the shared database_mock.Session so objects land in GLOBAL_DB_OBJECTS
            import database_mock as _dbm

            return _dbm.Session()

        return _factory


sys.modules['sqlalchemy.orm'] = orm_module
sys.modules['sqlalchemy.ext.declarative'] = MagicMock()


# Create a proper sqlalchemy.exc module
class sqlalchemy_exc_module:
    IntegrityError = IntegrityError
    SQLAlchemyError = SQLAlchemyError


sys.modules['sqlalchemy.exc'] = sqlalchemy_exc_module
