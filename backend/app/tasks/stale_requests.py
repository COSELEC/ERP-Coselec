import logging
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.modules.requests_unified.models.request import GenericRequest, RequestStatus, RequestHistory
from app.modules.users.models.user import User
from app.services.notification import create_notification
from app.models.notification import NotificationType
from app.services.email import send_ticket_email

logger = logging.getLogger(__name__)

def notify_stale_requests():
    """
    Cron job to check for stale requests (no action for >= 7 days)
    and dispatch reminder notifications.
    """
    logger.info("Starting stale requests check...")
    db = SessionLocal()
    try:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Find active requests
        active_requests = db.query(GenericRequest).filter(
            GenericRequest.status.notin_([
                RequestStatus.COMPLETED, 
                RequestStatus.REJECTED, 
                RequestStatus.APPROVED
            ])
        ).all()
        
        for request in active_requests:
            # Check the latest history entry
            latest_history = db.query(RequestHistory).filter(
                RequestHistory.request_id == request.id
            ).order_by(RequestHistory.created_at.desc()).first()
            
            # Use history date, or request updated_at/created_at
            last_action_date = latest_history.created_at if latest_history else (request.updated_at or request.created_at)
            
            if last_action_date <= seven_days_ago:
                logger.info(f"Request {request.reference} is stale (last action on {last_action_date})")
                
                # Determine who needs to be reminded. We will remind the current validator(s)
                # For simplicity, remind the requester and if there's a manager/validator, remind them too.
                users_to_remind = set()
                users_to_remind.add(request.requester_id)
                
                if request.requester and request.requester.manager_id:
                    users_to_remind.add(request.requester.manager_id)
                
                for uid in users_to_remind:
                    user = db.get(User, uid)
                    if not user:
                        continue
                    
                    msg = f"Rappel: La demande {request.reference} est en attente depuis plus de 7 jours."
                    
                    # 1 & 3. App Notification / In-App Message
                    create_notification(
                        db=db,
                        user_id=uid,
                        message=msg,
                        type=NotificationType.WARNING,
                        reference_id=request.id
                    )
                    
                    # 2. Email
                    if user.email:
                        subject = f"Rappel - Demande {request.reference} en attente"
                        body = f"<p>Bonjour {user.first_name or user.name},</p><p>{msg}</p>"
                        try:
                            send_ticket_email(email_to=user.email, subject=subject, body=body)
                        except Exception as e:
                            logger.error(f"Failed to send stale request email to {user.email}: {e}")
                            
        db.commit()
    except Exception as e:
        logger.error(f"Error checking stale requests: {e}")
    finally:
        db.close()
