#!/usr/bin/env python3
"""
Tests for database models and SQLAlchemy setup.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models_sql import Base, User, BannedUser, ProfileChange, Course, Purchase, Receipt


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine for testing."""
    return create_engine("sqlite:///:memory:", echo=False)


@pytest.fixture
def tables(engine):
    """Create all tables in the test database."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine, tables):
    """Create a new database session for a test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_user_model_creation(session):
    """Test User model creation and basic attributes."""
    user = User(
        telegram_user_id=123456789,
        first_name="first",
        last_name="last",
        phone="09120000000",
        province="تهران",
        city="تهران",
        grade="دهم",
        field_of_study="ریاضی",
    )

    session.add(user)
    session.commit()

    # Test retrieval
    retrieved_user = session.query(User).filter_by(telegram_user_id=123456789).first()
    assert retrieved_user is not None
    assert retrieved_user.first_name == "first"
    assert retrieved_user.last_name == "last"
    assert retrieved_user.province == "تهران"
    assert retrieved_user.grade == "دهم"
    assert retrieved_user.field_of_study == "ریاضی"


def test_banned_user_model(session):
    """Test BannedUser model."""
    banned_user = BannedUser(telegram_user_id=987654321)
    session.add(banned_user)
    session.commit()

    retrieved = session.query(BannedUser).filter_by(telegram_user_id=987654321).first()
    assert retrieved is not None
    assert retrieved.telegram_user_id == 987654321


def test_course_model(session):
    """Test Course model."""
    course = Course(
        slug="math-101",
        title="ریاضی پایه",
        type="free",
        grade="دهم",
        price=0,
        extra={"description": "دوره ریاضی پایه دهم"},
    )

    session.add(course)
    session.commit()

    retrieved = session.query(Course).filter_by(slug="math-101").first()
    assert retrieved is not None
    assert retrieved.title == "ریاضی پایه"
    assert retrieved.type == "free"
    assert retrieved.price == 0


def test_purchase_model(session):
    """Test Purchase model with relationships."""
    # Create a user first
    user = User(telegram_user_id=111111111, first_name="test_user", last_name="test_last")
    session.add(user)
    session.flush()  # Get the user ID

    purchase = Purchase(
        user_id=user.id,
        product_type="course",
        product_id="math-101",
        status="pending",
        amount=50000,
        payment_method="card",
    )

    session.add(purchase)
    session.commit()

    retrieved = session.query(Purchase).filter_by(user_id=user.id).first()
    assert retrieved is not None
    assert retrieved.product_type == "course"
    assert retrieved.status == "pending"
    assert retrieved.amount == 50000


def test_profile_change_model(session):
    """Test ProfileChange model."""
    # Create a user first
    user = User(telegram_user_id=222222222, first_name="change_user", last_name="change_last")
    session.add(user)
    session.flush()

    change = ProfileChange(
        user_id=user.id,
        field_name="grade",
        old_value_enc="دهم",
        new_value_enc="یازدهم",
        changed_by=999999999,
    )

    session.add(change)
    session.commit()

    retrieved = session.query(ProfileChange).filter_by(user_id=user.id).first()
    assert retrieved is not None
    assert retrieved.field_name == "grade"
    assert retrieved.old_value_enc == "دهم"
    assert retrieved.new_value_enc == "یازدهم"


def test_model_relationships(session):
    """Test that model relationships work correctly."""
    # Create user
    user = User(telegram_user_id=333333333, first_name="rel_user", last_name="rel_last")
    session.add(user)
    session.flush()

    # Create purchase for user
    purchase = Purchase(
        user_id=user.id, product_type="book", product_id="math-book", status="approved"
    )
    session.add(purchase)

    # Create profile change for user
    change = ProfileChange(
        user_id=user.id,
        field_name="city",
        old_value_enc="اصفهان",
        new_value_enc="شیراز",
        changed_by=888888888,
    )
    session.add(change)

    session.commit()

    # Test relationships
    user_purchases = session.query(Purchase).filter_by(user_id=user.id).all()
    assert len(user_purchases) == 1
    assert user_purchases[0].product_type == "book"

    user_changes = session.query(ProfileChange).filter_by(user_id=user.id).all()
    assert len(user_changes) == 1
    assert user_changes[0].field_name == "city"


def test_model_constraints(session):
    """Test model constraints and unique fields."""
    # Test unique telegram_user_id constraint
    user1 = User(telegram_user_id=444444444, first_name="unique_user1", last_name="unique_last1")
    session.add(user1)
    session.commit()

    # Try to create another user with same telegram_user_id
    user2 = User(
        telegram_user_id=444444444,  # Same ID
        first_name="unique_user2",
        last_name="unique_user2",
    )
    session.add(user2)

    # This should raise an integrity error due to unique constraint
    import pytest
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        session.commit()

    # Rollback to clean state for other tests
    session.rollback()


def test_model_defaults(session):
    """Test model default values."""
    user = User(telegram_user_id=555555555, first_name="default_user", last_name="default_last")

    # Add and flush to trigger default value generation
    session.add(user)
    session.flush()

    # Test that created_at and updated_at are set automatically after flush
    assert user.created_at is not None
    assert user.updated_at is not None

    session.commit()

    # Verify the user was saved
    retrieved = session.query(User).filter_by(telegram_user_id=555555555).first()
    assert retrieved is not None
