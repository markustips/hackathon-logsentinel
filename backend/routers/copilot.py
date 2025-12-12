"""Copilot chat endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session
import logging
import json
import asyncio

from database import get_session
from models import LogFile, CopilotRequest, CopilotResponse
from agents.graph import run_copilot, run_copilot_streaming

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=CopilotResponse)
async def chat_with_copilot(
    request: CopilotRequest,
    session: Session = Depends(get_session)
):
    """
    Chat with the AI copilot.

    Args:
        request: Chat request
        session: Database session

    Returns:
        Copilot response
    """
    # Verify file exists
    log_file = session.get(LogFile, request.file_id)
    if not log_file:
        raise HTTPException(status_code=404, detail="File not found")

    if log_file.status != "indexed":
        raise HTTPException(status_code=400, detail="File not indexed yet")

    # Run copilot
    logger.info(f"Processing copilot query: {request.message[:100]}")

    try:
        result = await run_copilot(
            file_id=request.file_id,
            user_message=request.message,
            conversation_history=[
                {'role': msg.role, 'content': msg.content}
                for msg in request.history
            ],
            session=session
        )

        return CopilotResponse(
            message=result['message'],
            agent=result['agent'],
            references=result['references'],
            mitre_techniques=[
                {
                    'id': t.get('id', ''),
                    'name': t.get('name', ''),
                    'tactic': t.get('tactic', ''),
                    'url': t.get('url', '')
                }
                for t in result.get('mitre_techniques', [])
            ]
        )

    except Exception as e:
        logger.error(f"Copilot error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Copilot error: {str(e)}")


@router.post("/chat-stream")
async def chat_with_copilot_stream(
    request: CopilotRequest,
    session: Session = Depends(get_session)
):
    """
    Chat with the AI copilot with streaming progress updates.

    Args:
        request: Chat request
        session: Database session

    Returns:
        Server-Sent Events stream
    """
    # Verify file exists
    log_file = session.get(LogFile, request.file_id)
    if not log_file:
        raise HTTPException(status_code=404, detail="File not found")

    if log_file.status != "indexed":
        raise HTTPException(status_code=400, detail="File not indexed yet")

    logger.info(f"Processing streaming copilot query: {request.message[:100]}")

    async def event_generator():
        """Generate Server-Sent Events for progress updates."""
        try:
            # Emit initial status
            yield f"data: {json.dumps({'type': 'status', 'step': 'query_received', 'message': 'Query received'})}\n\n"

            async for event in run_copilot_streaming(
                file_id=request.file_id,
                user_message=request.message,
                conversation_history=[
                    {'role': msg.role, 'content': msg.content}
                    for msg in request.history
                ],
                session=session
            ):
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0)  # Allow other tasks to run

            # Emit completion
            yield f"data: {json.dumps({'type': 'status', 'step': 'complete', 'message': 'Complete'})}\n\n"

        except Exception as e:
            logger.error(f"Streaming copilot error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
