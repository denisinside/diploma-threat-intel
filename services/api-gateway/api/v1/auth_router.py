from fastapi import APIRouter, Request
from models.requests.auth_requests import (
    RegisterUserRequest, RegisterCompanyRequest,
    LoginRequest, ResetPasswordRequest, ForgotPasswordRequest,
)
from models.responses.common import MessageResponse
import services.auth_service as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register-company")
async def register_company(body: RegisterCompanyRequest, request: Request) -> dict:
    db = request.app.mongodb
    return await auth_service.register_company(db, body)


@router.post("/register")
async def register(body: RegisterUserRequest, request: Request) -> dict:
    db = request.app.mongodb
    return await auth_service.register_user(db, body)


@router.post("/login")
async def login(body: LoginRequest, request: Request) -> dict:
    db = request.app.mongodb
    return await auth_service.login(db, body)


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, request: Request) -> MessageResponse:
    db = request.app.mongodb
    return await auth_service.reset_password(db, body)


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, request: Request) -> MessageResponse:
    db = request.app.mongodb
    return await auth_service.forgot_password(db, body)
