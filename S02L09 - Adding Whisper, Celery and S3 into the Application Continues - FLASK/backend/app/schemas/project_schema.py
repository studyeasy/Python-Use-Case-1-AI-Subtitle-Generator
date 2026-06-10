from marshmallow import Schema, fields


class ProjectSummary(Schema):
    id = fields.String(required=True)
    original_filename = fields.String(required=True)
    language = fields.String(allow_none=True)
    status = fields.String(required=True)
    progress = fields.Integer(required=True)
    error = fields.String(allow_none=True)
    has_srt = fields.Boolean(required=True)
    created_at = fields.String(allow_none=True)
    updated_at = fields.String(allow_none=True)


class ProjectCreateResponse(Schema):
    id = fields.String(required=True)
    status = fields.String(required=True)


class PresignedUrlResponse(Schema):
    url = fields.String(required=True)
