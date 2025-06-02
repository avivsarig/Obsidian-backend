import logging

from fastapi import Request

from app.src.core.exceptions.base_exceptions import BaseAPIException

logger = logging.getLogger(__name__)


def send_alert_if_needed(
    exc: BaseAPIException,
    request: Request,
    request_id: str | None,
) -> None:
    if not hasattr(exc, "should_alert") or not exc.should_alert:
        return

    logger.critical(
        "Alert-worthy exception occurred",
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "alert": True,
        },
        exc_info=exc,
    )

    # TODO: Integrate with monitoring services
    # send_to_sentry(exc, request, request_id)
    # send_to_datadog(exc, request, request_id)
    # send_slack_notification(exc, request, request_id)
