import json
import random
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.redis import Redis, get_redis
from app.db.session import get_session
from app.models import Material, Question, Quiz, QuizAttempt, QuizStatus, User
from app.repositories.quiz_repository import QuizRepository
from app.schemas.quiz import (
    AnswerResponse,
    AttemptDetail,
    LeaderboardEntry,
    LeaderboardResponse,
    PublicationRequest,
    PublicationResponse,
    PublicAttemptList,
    PublicAttemptSummary,
    PublicQuizList,
    PublicQuizSummary,
    QuestionResponse,
    QuizResponse,
    SubmitRequest,
    SubmitResponse,
    TrainingRunRequest,
    TrainingRunResponse,
)
from app.services.quiz_grading import grade_quiz

router = APIRouter(tags=["public quizzes"])
Session = Annotated[AsyncSession, Depends(get_session)]


def parse_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(404, "Quiz not found") from None


async def owned_quiz(value: str, user: User, session: AsyncSession) -> tuple[Quiz, Material]:
    quiz = await session.get(Quiz, parse_id(value))
    material = await session.get(Material, quiz.material_id) if quiz else None
    if (
        quiz is None
        or material is None
        or material.deleted_at
        or quiz.user_id != user.id
        or material.user_id != user.id
    ):
        raise HTTPException(404, "Quiz not found")
    return quiz, material


@router.get("/quizzes/{quiz_id}/publication", response_model=PublicationResponse)
async def publication(
    quiz_id: str, current_user: CurrentUser, session: Session
) -> PublicationResponse:
    quiz, material = await owned_quiz(quiz_id, current_user, session)
    return PublicationResponse(
        is_public=quiz.is_public, title=quiz.public_title or material.original_filename
    )


@router.patch("/quizzes/{quiz_id}/publication", response_model=PublicationResponse)
async def publish(
    quiz_id: str, body: PublicationRequest, current_user: CurrentUser, session: Session
) -> PublicationResponse:
    quiz, material = await owned_quiz(quiz_id, current_user, session)
    count = await session.scalar(
        select(func.count()).select_from(Question).where(Question.quiz_id == quiz.id)
    )
    if body.is_public and (quiz.status != QuizStatus.done or not count):
        raise HTTPException(409, "Quiz is not ready yet")
    title = (
        body.title if body.title is not None else quiz.public_title or material.original_filename
    ).strip()
    if not title:
        raise HTTPException(422, "Invalid quiz title")
    quiz.public_title = title
    if body.is_public and not quiz.is_public:
        quiz.published_at = datetime.now(UTC)
    quiz.is_public = body.is_public
    if not body.is_public and material.published_quiz_id == quiz.id:
        material.published_quiz_id = None
    await session.commit()
    return PublicationResponse(is_public=quiz.is_public, title=title)


@router.get("/public-quizzes", response_model=PublicQuizList)
async def public_list(
    current_user: CurrentUser,
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 12,
) -> PublicQuizList:
    visible = (
        Quiz.is_public.is_(True),
        Quiz.status == QuizStatus.done,
        Material.deleted_at.is_(None),
        User.is_active.is_(True),
    )
    question_count = (
        select(func.count())
        .select_from(Question)
        .where(Question.quiz_id == Quiz.id)
        .correlate(Quiz)
        .scalar_subquery()
    )
    base = (
        select(Quiz, User, question_count)
        .join(Material, Material.id == Quiz.material_id)
        .join(User, User.id == Quiz.user_id)
        .where(*visible)
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = await session.execute(
        base.order_by(Quiz.published_at.desc(), Quiz.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    items = []
    for quiz, user, count in rows:
        items.append(
            PublicQuizSummary(
                id=str(quiz.id),
                title=quiz.public_title or "Тест",
                author=" ".join(filter(None, [user.first_name, user.last_name])) or "Пользователь",
                published_at=quiz.published_at or quiz.created_at,
                question_count=count or 0,
            )
        )
    return PublicQuizList(items=items, total=total or 0)


def attempt_summary(attempt: QuizAttempt) -> PublicAttemptSummary:
    return PublicAttemptSummary(
        id=str(attempt.id),
        quiz_id=str(attempt.quiz_id) if attempt.quiz_id else None,
        duration_ms=attempt.duration_ms,
        title=attempt.quiz_snapshot.get("title", "Публичный тест"),
        created_at=attempt.created_at,
        score=attempt.score,
        total=attempt.total,
        correct=attempt.correct,
    )


@router.get("/public-quizzes/attempts", response_model=PublicAttemptList)
async def attempts(
    current_user: CurrentUser,
    session: Session,
    quiz_id: uuid.UUID | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> PublicAttemptList:
    conditions = [QuizAttempt.user_id == current_user.id, QuizAttempt.is_public_attempt.is_(True)]
    if quiz_id is not None:
        conditions.append(QuizAttempt.quiz_id == quiz_id)
    total = await session.scalar(select(func.count()).select_from(QuizAttempt).where(*conditions))
    rows = await session.scalars(
        select(QuizAttempt)
        .where(*conditions)
        .order_by(QuizAttempt.created_at.desc(), QuizAttempt.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return PublicAttemptList(items=[attempt_summary(row) for row in rows], total=total or 0)


@router.get("/public-quizzes/attempts/{attempt_id}", response_model=AttemptDetail)
async def attempt_detail(
    attempt_id: str, current_user: CurrentUser, session: Session, response: Response
) -> AttemptDetail:
    attempt = await session.scalar(
        select(QuizAttempt).where(
            QuizAttempt.id == parse_id(attempt_id),
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.is_public_attempt.is_(True),
        )
    )
    if attempt is None:
        raise HTTPException(404, "Attempt not found")
    response.headers["Cache-Control"] = "no-store"
    summary = attempt_summary(attempt).model_dump(exclude={"title"})
    return AttemptDetail(
        **summary,
        quiz=attempt.quiz_snapshot,
        answers=attempt.answers,
        result=SubmitResponse(
            attempt_id=str(attempt.id),
            duration_ms=attempt.duration_ms,
            score=attempt.score,
            total=attempt.total,
            correct=attempt.correct,
            results=attempt.results,
        ),
    )


async def available_quiz(value: str, session: AsyncSession) -> Quiz:
    qid = parse_id(value)
    exists = await session.scalar(
        select(Quiz.id)
        .join(Material, Material.id == Quiz.material_id)
        .join(User, User.id == Quiz.user_id)
        .where(
            Quiz.id == qid,
            Quiz.is_public.is_(True),
            Quiz.status == QuizStatus.done,
            Material.deleted_at.is_(None),
            User.is_active.is_(True),
        )
    )
    quiz = await QuizRepository(session).get_with_questions(qid) if exists else None
    if quiz is None:
        raise HTTPException(404, "Public quiz not found")
    return quiz


@router.get("/public-quizzes/{quiz_id}", response_model=QuizResponse)
async def public_quiz(
    quiz_id: str, current_user: CurrentUser, session: Session, response: Response
) -> QuizResponse:
    quiz = await available_quiz(quiz_id, session)

    questions = []
    for question in sorted(quiz.questions, key=lambda q: q.order):
        answers = [AnswerResponse(id=str(a.id), text=a.text) for a in question.answers]
        random.shuffle(answers)
        questions.append(
            QuestionResponse(
                id=str(question.id),
                text=question.text,
                question_type=question.question_type,
                order=question.order,
                answers=answers,
            )
        )
    response.headers["Cache-Control"] = "no-store"
    return QuizResponse(
        title=quiz.public_title,
        id=str(quiz.id),
        material_id=str(quiz.material_id),
        status=quiz.status,
        questions=questions,
    )


@router.post("/public-quizzes/{quiz_id}/submit", response_model=SubmitResponse)
async def public_submit(
    quiz_id: str,
    body: SubmitRequest,
    current_user: CurrentUser,
    session: Session,
    redis: Annotated[Redis, Depends(get_redis)],
) -> SubmitResponse:
    quiz = await available_quiz(quiz_id, session)
    if body.quiz_id is not None and body.quiz_id != quiz.id:
        raise HTTPException(422, "Quiz does not match")
    result, snapshot = grade_quiz(quiz, body.answers)
    duration_ms = None
    run_payload = None
    run_key = f"training:{current_user.id}:{quiz.id}"
    if body.run_id is not None:
        existing = await session.scalar(
            select(QuizAttempt).where(
                QuizAttempt.run_id == body.run_id,
                QuizAttempt.user_id == current_user.id,
                QuizAttempt.quiz_id == quiz.id,
            )
        )
        if existing:
            return SubmitResponse(
                attempt_id=str(existing.id),
                duration_ms=existing.duration_ms,
                score=existing.score,
                total=existing.total,
                correct=existing.correct,
                results=existing.results,
            )
        # Compare and consume atomically so a second request cannot record another result.
        run_payload = await redis.eval(
            "local v=redis.call('GET',KEYS[1]); if not v then return nil end; "
            "if cjson.decode(v).run_id~=ARGV[1] then return nil end; "
            "redis.call('DEL',KEYS[1]); return v",
            1,
            run_key,
            str(body.run_id),
        )
        if run_payload is None:
            raise HTTPException(409, "Training session expired")
        started_at = datetime.fromisoformat(json.loads(run_payload)["started_at"])
        duration_ms = max(0, int((datetime.now(UTC) - started_at).total_seconds() * 1000))
    data = snapshot.model_dump(mode="json")
    data["title"] = quiz.public_title or "Публичный тест"
    attempt = QuizAttempt(
        user_id=current_user.id,
        material_id=quiz.material_id,
        quiz_id=quiz.id,
        is_public_attempt=True,
        run_id=body.run_id,
        duration_ms=duration_ms,
        score=result.score,
        total=result.total,
        correct=result.correct,
        quiz_snapshot=data,
        answers=[a.model_dump(mode="json") for a in body.answers],
        results=[r.model_dump(mode="json") for r in result.results],
    )
    session.add(attempt)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        if run_payload is not None:
            remaining = 120
            await redis.set(run_key, run_payload, nx=True, ex=remaining)
        raise
    result.duration_ms = duration_ms
    result.attempt_id = str(attempt.id)
    return result


@router.post("/public-quizzes/{quiz_id}/start", response_model=TrainingRunResponse)
async def start_training(
    quiz_id: str,
    current_user: CurrentUser,
    session: Session,
    redis: Annotated[Redis, Depends(get_redis)],
) -> TrainingRunResponse:
    quiz = await available_quiz(quiz_id, session)
    key = f"training:{current_user.id}:{quiz.id}"
    now = datetime.now(UTC)
    payload = json.dumps({"run_id": str(uuid.uuid4()), "started_at": now.isoformat()})
    await redis.set(key, payload, ex=120)
    data = json.loads(payload)
    return TrainingRunResponse(
        run_id=data["run_id"], started_at=data["started_at"], server_time=datetime.now(UTC)
    )


@router.get("/public-quizzes/{quiz_id}/leaderboard", response_model=LeaderboardResponse)
async def leaderboard(
    quiz_id: str, current_user: CurrentUser, session: Session
) -> LeaderboardResponse:
    quiz = await available_quiz(quiz_id, session)
    best = (
        select(
            QuizAttempt.id,
            QuizAttempt.user_id,
            QuizAttempt.score,
            QuizAttempt.correct,
            QuizAttempt.total,
            QuizAttempt.duration_ms,
            QuizAttempt.created_at,
            func.row_number()
            .over(
                partition_by=QuizAttempt.user_id,
                order_by=(
                    QuizAttempt.score.desc(),
                    QuizAttempt.duration_ms.asc(),
                    QuizAttempt.created_at.asc(),
                    QuizAttempt.id.asc(),
                ),
            )
            .label("pick"),
        )
        .where(
            QuizAttempt.quiz_id == quiz.id,
            QuizAttempt.is_public_attempt.is_(True),
            QuizAttempt.duration_ms.is_not(None),
        )
        .subquery()
    )
    ranked = (
        select(
            best,
            User.first_name,
            User.last_name,
            func.row_number()
            .over(
                order_by=(
                    best.c.score.desc(),
                    best.c.duration_ms.asc(),
                    best.c.created_at.asc(),
                    best.c.id.asc(),
                )
            )
            .label("rank"),
        )
        .join(User, User.id == best.c.user_id)
        .where(best.c.pick == 1, User.is_active.is_(True))
        .subquery()
    )
    count = await session.scalar(select(func.count()).select_from(ranked))
    rows = await session.execute(select(ranked).order_by(ranked.c.rank).limit(20))

    def entry(row) -> LeaderboardEntry:
        return LeaderboardEntry(
            rank=row.rank,
            name=" ".join(filter(None, [row.first_name, row.last_name])) or "Участник",
            score=row.score,
            correct=row.correct,
            total=row.total,
            duration_ms=row.duration_ms,
            is_you=row.user_id == current_user.id,
        )

    mine = (
        await session.execute(select(ranked).where(ranked.c.user_id == current_user.id))
    ).one_or_none()
    return LeaderboardResponse(
        items=[entry(row) for row in rows],
        participants=count or 0,
        my_entry=entry(mine) if mine else None,
    )


@router.post("/public-quizzes/{quiz_id}/cancel", status_code=204)
async def cancel_training(
    quiz_id: str,
    body: TrainingRunRequest,
    current_user: CurrentUser,
    redis: Annotated[Redis, Depends(get_redis)],
) -> None:
    key = f"training:{current_user.id}:{parse_id(quiz_id)}"
    await redis.eval(
        "local v=redis.call('GET',KEYS[1]); if not v then return 0 end; "
        "if cjson.decode(v).run_id~=ARGV[1] then return 0 end; "
        "return redis.call('DEL',KEYS[1])",
        1,
        key,
        str(body.run_id),
    )


@router.post("/public-quizzes/{quiz_id}/heartbeat", status_code=204)
async def training_heartbeat(
    quiz_id: str,
    body: TrainingRunRequest,
    current_user: CurrentUser,
    redis: Annotated[Redis, Depends(get_redis)],
) -> None:
    key = f"training:{current_user.id}:{parse_id(quiz_id)}"
    renewed = await redis.eval(
        "local v=redis.call('GET',KEYS[1]); if not v then return 0 end; "
        "if cjson.decode(v).run_id~=ARGV[1] then return 0 end; "
        "return redis.call('EXPIRE',KEYS[1],120)",
        1,
        key,
        str(body.run_id),
    )
    if not renewed:
        raise HTTPException(409, "Training session expired")
