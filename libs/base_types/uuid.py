from uuid import UUID, uuid4

from libs.base_types.pydantic import PydanticConversor


class BaseUUID(UUID, PydanticConversor):
    def __init__(self, *args):
        """
        Makes UUID behave like ObjectId. Examples:
        # Generate a new uuid:
        > BaseUUID() -> BaseUUID('275619da-a4f9-4832-928d-f532ee1f7ecc')

        # Transform str into uuid and, if it is already uuid, return the same value.:
        > BaseUUID('275619da-a4f9-4832-928d-f532ee1f7ecc') -> BaseUUID('275619da-a4f9-4832-928d-f532ee1f7ecc')
        """

        if not args:
            _id = str(uuid4())
        elif isinstance(args[0], (UUID, str)) or issubclass(self.__class__, BaseUUID):
            _id = str(args[0])
        else:
            raise ValueError(f"You cannot transform a {args[0]} into a UUID")

        super().__init__(_id)

    @staticmethod
    def is_valid(uuid_to_test):
        if isinstance(uuid_to_test, UUID):
            return True

        try:
            uuid_obj = UUID(uuid_to_test, version=4)
        except Exception:
            return False
        return str(uuid_obj) == uuid_to_test
