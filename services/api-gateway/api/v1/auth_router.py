from fastapi import APIRouter, Request, HTTPException
import database.mongo as mongo
import models
from models.requests.auth_requests import RegisterUserRequest, RegisterCompanyRequest, LoginRequest, ResetPasswordRequest, ForgotPasswordRequest
import core.security as security
import services.auth_service as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(request: RegisterUserRequest):
    user = auth_service.register_user(request)
    return user

@router.post("/register-company")
def register_company(request: RegisterCompanyRequest):
    company = auth_service.register_company(request)
    return company

@router.post("/login")
def login(request: LoginRequest):
    user = auth_service.login(request)
    return user

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    user = auth_service.reset_password(request)
    return user

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    user = auth_service.forgot_password(request)
    return user