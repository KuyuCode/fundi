import json
import typing
from contextlib import AsyncExitStack
from starlette.requests import Request
from fastapi._compat import ModelField
from pydantic.v1.fields import Undefined
from fastapi import HTTPException, params
from fastapi.exceptions import RequestValidationError


async def validate_body(request: Request, stack: AsyncExitStack, body_field: ModelField | None):
    is_body_form = body_field and isinstance(body_field.field_info, params.Form)
    try:
        if body_field:
            if is_body_form:
                form = await request.form()
                stack.push_async_callback(form.close)
                return form

            body_bytes = await request.body()
            if body_bytes:
                json_body: typing.Any = Undefined
                content_type_value = request.headers.get("content-type")

                if not content_type_value:
                    json_body = await request.json()

                else:
                    if content_type_value.count("/") != 1:
                        content_type_value = "text/plain"

                    maintype, subtype = content_type_value.split("/", 1)

                    if maintype == "application":
                        if subtype == "json" or subtype.endswith("+json"):
                            json_body = await request.json()

                if json_body != Undefined:
                    return json_body
                else:
                    return typing.cast(typing.Any, body_bytes)
    except json.JSONDecodeError as e:
        validation_error = RequestValidationError(
            [
                {
                    "type": "json_invalid",
                    "loc": ("body", e.pos),
                    "msg": "JSON decode error",
                    "input": {},
                    "ctx": {"error": e.msg},
                }
            ],
            body=e.doc,
        )
        raise validation_error from e
    except HTTPException:
        # If a middleware raises an HTTPException, it should be raised again
        raise
    except Exception as e:
        http_error = HTTPException(status_code=400, detail="There was an error parsing the body")
        raise http_error from e
