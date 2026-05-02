from datetime import datetime
from typing import Any, Optional
from bson import ObjectId
from pydantic import BaseModel


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        if ObjectId.is_valid(str(v)):
            return str(v)
        raise ValueError(f"Invalid ObjectId: {v}")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Any:
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)


class MongoBaseModel(BaseModel):
    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

    @classmethod
    def from_mongo(cls, data: dict) -> Optional["MongoBaseModel"]:
        if data is None:
            return None
        if "_id" in data:
            data["id"] = str(data.pop("_id"))
        return cls(**_convert_objectids(data))


def _convert_objectids(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _convert_objectids(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_objectids(i) for i in obj]
    return obj
