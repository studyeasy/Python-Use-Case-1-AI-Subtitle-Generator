from marshmallow import Schema, fields


class HelloResponse(Schema):
    message = fields.String(required=True, metadata={"example": "hello world"})
