from uuid import uuid4

import pytest

from bounded_contexts.user.exceptions import CantUpdateAdminUser, CantDeleteYourself
from bounded_contexts.user.schemas import UserUpdate
from bounded_contexts.user.service import (
    _validate_update_request,
    _validate_delete_request,
)
from core.exceptions import AdminRequired


class _UserTest:
    def __init__(self, id, is_super_admin=False, is_admin=False):
        self.id = id
        self.is_super_admin = is_super_admin
        self.is_admin = is_admin
        self.has_admin_privileges = is_super_admin or is_admin
        self.email = None


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
        # Non-admin trying to update player_id → should fail
        (
            _UserTest(id=1),
            _UserTest(id=2),
            UserUpdate(name="Test", email="teste@gmail", player_id=uuid4()),
            AdminRequired,
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


@pytest.mark.parametrize(
    "current_user, user_to_delete, expected_exception",
    [
        # User trying to delete themselves → should fail
        (_UserTest(id=1, is_admin=True), _UserTest(id=1), CantDeleteYourself),
        # Super admin deleting any user → allowed
        (_UserTest(id=1, is_super_admin=True), _UserTest(id=2), None),
        # Non-admin trying to delete another user → should fail
        (_UserTest(id=1), _UserTest(id=2), AdminRequired),
        # Admin deleting non-admin → allowed
        (_UserTest(id=1, is_admin=True), _UserTest(id=2), None),
        # Admin deleting other admin → should fail
        (
            _UserTest(id=1, is_admin=True),
            _UserTest(id=2, is_admin=True),
            CantUpdateAdminUser,
        ),
        # Super admin deleting admin → allowed
        (_UserTest(id=1, is_super_admin=True), _UserTest(id=2, is_admin=True), None),
    ],
)
def test_validate_delete_request(current_user, user_to_delete, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            _validate_delete_request(current_user, user_to_delete)
    else:
        _validate_delete_request(current_user, user_to_delete)
