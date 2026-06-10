from marshmallow import Schema, fields


class MeResponse(Schema):
    sub = fields.String(required=True, metadata={"example": "uuid-of-user"})
    username = fields.String(metadata={"example": "alice@example.com"})
    email = fields.String(metadata={"example": "alice@example.com"})
    name = fields.String(metadata={"example": "Alice Example"})
    given_name = fields.String()
    family_name = fields.String()
    email_verified = fields.Boolean()
    roles = fields.List(fields.String(), metadata={"example": ["user"]})
