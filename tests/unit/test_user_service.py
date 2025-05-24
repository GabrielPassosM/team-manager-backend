import pytest

from bounded_contexts.user.exceptions import CantUpdateAdminUser
from bounded_contexts.user.schemas import UserUpdate
from bounded_contexts.user.service import _validate_update_request
from core.exceptions import AdminRequired


class _UserTest:
    def __init__(self, id, is_super_admin=False, is_admin=False):
        self.id = id
        self.is_super_admin = is_super_admin
        self.is_admin = is_admin


@pytest.mark.parametrize(
    "current_user, user_to_update, user_data, expected_exception",
    [
        # Super admin updating admin -> allowed
        (
            _UserTest(id=1, is_super_admin=True),
            _UserTest(id=2, is_admin=True),
            UserUpdate(name="Test", email="teste@gmail"),
            None,
        ),
        # User updating themselves (without password)
        (
            _UserTest(id=1),
            _UserTest(id=1),
            UserUpdate(name="Test", email="teste@gmail"),
            None,
        ),
        # User updating themselves (with password)
        (
            _UserTest(id=1),
            _UserTest(id=1),
            UserUpdate(name="Test", email="teste@gmail", password="1234"),
            None,
        ),
        # Non-admin trying to update another (without password) → should fail
        (
            _UserTest(id=1),
            _UserTest(id=2),
            UserUpdate(name="Test", email="teste@gmail"),
            AdminRequired,
        ),
        # Non-admin trying to update another (with password) → should fail
        (
            _UserTest(id=1),
            _UserTest(id=2),
            UserUpdate(name="Test", email="teste@gmail", password="1234"),
            AdminRequired,
        ),
        # Admin trying to update non-admin (without password) → allowed
        (
            _UserTest(id=1, is_admin=True),
            _UserTest(id=2),
            UserUpdate(name="Test", email="teste@gmail"),
            None,
        ),
        # Admin trying to update non-admin (with password) → should fail
        (
            _UserTest(id=1, is_admin=True),
            _UserTest(id=2),
            UserUpdate(name="Test", email="teste@gmail", password="1234"),
            AdminRequired,
        ),
        # Admin trying to update another admin → should fail
        (
            _UserTest(id=1, is_admin=True),
            _UserTest(id=2, is_admin=True),
            UserUpdate(name="Test", email="teste@gmail"),
            CantUpdateAdminUser,
        ),
    ],
)
def test_validate_update_request(
    current_user, user_to_update, user_data, expected_exception
):
    if expected_exception:
        with pytest.raises(expected_exception):
            _validate_update_request(current_user, user_to_update, user_data)
    else:
        _validate_update_request(current_user, user_to_update, user_data)
