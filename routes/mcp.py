from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import secrets
import uuid
from datetime import datetime, timedelta

from database import get_db, Agent, ToolCall, Payment, Token
from models import (
    TokenRequest,
    TokenResponse,
    ToolCallResponse, 
    PaymentRequest, 
    PaymentResponse
)
from config import COINBASE_API_KEY

router = APIRouter(prefix="/api/tokens", tags=["tokens"])

@router.post("/create", response_model=TokenResponse)
async def create_token(
    token_request: TokenRequest,
    db: Session = Depends(get_db)
):
    """
    Create an access token for an agent
    """
    try:
        # Verify agent exists
        agent = db.query(Agent).filter(
            Agent.id == token_request.agent_id,
            Agent.is_active == True
        ).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Generate secure token
        token_value = secrets.token_urlsafe(32)
        
        # Calculate expiration
        expires_at = None
        if token_request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=token_request.expires_in_days)
        
        # Create token record
        token = Token(
            token=token_value,
            agent_id=token_request.agent_id,
            user_id=token_request.user_id,
            expires_at=expires_at
        )
        
        db.add(token)
        db.commit()
        db.refresh(token)
        
        return TokenResponse(
            id=token.id,
            token=token.token,
            agent_id=token.agent_id,
            user_id=token.user_id,
            expires_at=token.expires_at,
            created_at=token.created_at
        )
        
    except HTTPException:
        raise
    except Exception as err:
        db.rollback()
        print(f"Error creating token: {err}")
        raise HTTPException(status_code=500, detail="Server error")

@router.get("/tool-call/{tool_call_id}", response_model=ToolCallResponse)
async def get_tool_call(tool_call_id: str, db: Session = Depends(get_db)):
    """
    Get the status and result of a tool call (for monitoring)
    """
    try:
        tool_call = db.query(ToolCall).filter(ToolCall.id == tool_call_id).first()
        
        if not tool_call:
            raise HTTPException(status_code=404, detail="Tool call not found")
        
        return ToolCallResponse(
            id=tool_call.id,
            agent_id=tool_call.agent_id,
            caller_user_id=tool_call.caller_user_id,
            tool_name=tool_call.tool_name,
            parameters=tool_call.parameters,
            result=tool_call.result,
            cost=tool_call.cost,
            payment_status=tool_call.payment_status,
            created_at=tool_call.created_at,
            completed_at=tool_call.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as err:
        print(f"Error getting tool call: {err}")
        raise HTTPException(status_code=500, detail="Server error")

@router.post("/create-payment", response_model=PaymentResponse)
async def create_payment(
    payment_request: PaymentRequest,
    db: Session = Depends(get_db)
):
    """
    Create a payment for a tool call
    """
    try:
        # Get the tool call
        tool_call = db.query(ToolCall).filter(ToolCall.id == payment_request.tool_call_id).first()
        
        if not tool_call:
            raise HTTPException(status_code=404, detail="Tool call not found")
        
        # Create payment record
        payment_id = str(uuid.uuid4())
        payment = Payment(
            id=payment_id,
            tool_call_id=payment_request.tool_call_id,
            amount=payment_request.amount,
            currency=payment_request.currency,
            status="pending"
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        # TODO: Create Coinbase checkout session
        # For now, we'll simulate this
        coinbase_checkout_id = f"checkout_{uuid.uuid4().hex[:8]}"
        payment.coinbase_checkout_id = coinbase_checkout_id
        db.commit()
        
        return PaymentResponse(
            id=payment.id,
            tool_call_id=payment.tool_call_id,
            amount=payment.amount,
            currency=payment.currency,
            coinbase_checkout_id=payment.coinbase_checkout_id,
            status=payment.status,
            created_at=payment.created_at,
            completed_at=payment.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as err:
        db.rollback()
        print(f"Error creating payment: {err}")
        raise HTTPException(status_code=500, detail="Server error")

@router.post("/webhook/payment", response_model=dict)
async def handle_payment_webhook(
    webhook_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Handle payment webhook from Coinbase
    """
    try:
        # TODO: Verify webhook signature
        
        # Extract payment information
        checkout_id = webhook_data.get("checkout_id")
        status = webhook_data.get("status")
        
        if not checkout_id or not status:
            raise HTTPException(status_code=400, detail="Invalid webhook data")
        
        # Find payment by checkout ID
        payment = db.query(Payment).filter(
            Payment.coinbase_checkout_id == checkout_id
        ).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Update payment status
        payment.status = status
        if status == "completed":
            payment.completed_at = datetime.utcnow()
            
            # Update tool call payment status
            tool_call = db.query(ToolCall).filter(
                ToolCall.id == payment.tool_call_id
            ).first()
            if tool_call:
                tool_call.payment_status = "paid"
        
        db.commit()
        
        return {"status": "webhook processed"}
        
    except HTTPException:
        raise
    except Exception as err:
        db.rollback()
        print(f"Error processing webhook: {err}")
        raise HTTPException(status_code=500, detail="Server error") 