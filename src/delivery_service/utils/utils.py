from fastapi import Request


def get_session_id(request: Request) -> str:
    session_id = request.cookies.get(
        "session_id") or request.state.session_id

    return session_id
