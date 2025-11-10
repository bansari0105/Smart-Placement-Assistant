"""
Notification Service - Generates various types of notifications for applications
- Countdown notifications for deadlines
- Interview reminders
- Status updates
- Application confirmations
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from firebase_admin import firestore

logger = logging.getLogger(__name__)


class NotificationService:
    """Service to generate and manage notifications for applications."""
    
    def __init__(self, db: firestore.Client):
        self.db = db
    
    def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = 'info',
        application_id: Optional[str] = None,
        company_name: Optional[str] = None,
        is_read: bool = False
    ) -> str:
        """
        Create a notification in Firestore.
        
        Args:
            user_id: User ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification ('deadline', 'interview', 'status', 'info', 'reminder')
            application_id: Optional application ID
            company_name: Optional company name
            is_read: Whether notification is read
        
        Returns:
            Notification document ID
        """
        try:
            notification_data = {
                'userId': user_id,
                'title': title,
                'message': message,
                'type': notification_type,
                'applicationId': application_id,
                'companyName': company_name,
                'isRead': is_read,
                'createdAt': firestore.SERVER_TIMESTAMP,
            }
            
            doc_ref = self.db.collection('notifications').document()
            doc_ref.set(notification_data)
            logger.info(f"Created notification for user {user_id}: {title}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    def generate_application_notifications(self, application_data: Dict) -> List[str]:
        """
        Generate notifications when an application is created.
        
        Args:
            application_data: Application data dict with userId, companyName, deadline, etc.
        
        Returns:
            List of notification IDs created
        """
        notification_ids = []
        user_id = application_data.get('userId')
        company_name = application_data.get('companyName') or application_data.get('company')
        application_id = application_data.get('id') or application_data.get('applicationId')
        deadline = application_data.get('deadline')
        interview_date = application_data.get('interview_date') or application_data.get('interviewDate')
        
        if not user_id or not company_name:
            return notification_ids
        
        # 1. Application confirmation notification
        confirmation_id = self.create_notification(
            user_id=user_id,
            title='Application Submitted',
            message=f'Your application for {company_name} has been submitted successfully!',
            notification_type='info',
            application_id=application_id,
            company_name=company_name
        )
        if confirmation_id:
            notification_ids.append(confirmation_id)
        
        # 2. Deadline countdown notification (if deadline exists)
        if deadline:
            deadline_id = self._create_deadline_notification(
                user_id=user_id,
                company_name=company_name,
                deadline=deadline,
                application_id=application_id
            )
            if deadline_id:
                notification_ids.append(deadline_id)
        
        # 3. Interview reminder notification (if interview date exists)
        if interview_date:
            interview_id = self._create_interview_notification(
                user_id=user_id,
                company_name=company_name,
                interview_date=interview_date,
                application_id=application_id
            )
            if interview_id:
                notification_ids.append(interview_id)
        
        return notification_ids
    
    def _create_deadline_notification(
        self,
        user_id: str,
        company_name: str,
        deadline: str,
        application_id: Optional[str] = None
    ) -> Optional[str]:
        """Create deadline countdown notification."""
        try:
            # Parse deadline date
            if isinstance(deadline, str):
                deadline_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            else:
                deadline_date = deadline
            
            # Calculate days remaining
            now = datetime.now(deadline_date.tzinfo) if deadline_date.tzinfo else datetime.now()
            days_remaining = (deadline_date - now).days
            
            if days_remaining < 0:
                # Deadline passed
                title = 'Deadline Passed'
                message = f'The application deadline for {company_name} has passed.'
                notification_type = 'reminder'
            elif days_remaining == 0:
                # Deadline today
                title = 'Deadline Today!'
                message = f'⏰ The application deadline for {company_name} is TODAY! Submit your application now.'
                notification_type = 'deadline'
            elif days_remaining == 1:
                # Deadline tomorrow
                title = 'Deadline Tomorrow!'
                message = f'⏰ Only 1 day left! The application deadline for {company_name} is tomorrow.'
                notification_type = 'deadline'
            elif days_remaining <= 3:
                # Deadline in 2-3 days
                title = f'{days_remaining} Days Left!'
                message = f'⏰ Only {days_remaining} days left! The application deadline for {company_name} is approaching.'
                notification_type = 'deadline'
            elif days_remaining <= 7:
                # Deadline in a week
                title = f'{days_remaining} Days Remaining'
                message = f'📅 {days_remaining} days are left for {company_name} application deadline. Prepare your documents!'
                notification_type = 'reminder'
            else:
                # Deadline more than a week away
                title = f'{days_remaining} Days Remaining'
                message = f'📅 {days_remaining} days are left for {company_name} application deadline.'
                notification_type = 'reminder'
            
            return self.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                application_id=application_id,
                company_name=company_name
            )
        except Exception as e:
            logger.error(f"Error creating deadline notification: {e}")
            return None
    
    def _create_interview_notification(
        self,
        user_id: str,
        company_name: str,
        interview_date: str,
        application_id: Optional[str] = None
    ) -> Optional[str]:
        """Create interview reminder notification."""
        try:
            # Parse interview date
            if isinstance(interview_date, str):
                interview_datetime = datetime.fromisoformat(interview_date.replace('Z', '+00:00'))
            else:
                interview_datetime = interview_date
            
            # Calculate days until interview
            now = datetime.now(interview_datetime.tzinfo) if interview_datetime.tzinfo else datetime.now()
            days_until = (interview_datetime - now).days
            
            if days_until < 0:
                # Interview passed
                return None
            elif days_until == 0:
                # Interview today
                title = 'Interview Today!'
                message = f'🎯 Your interview with {company_name} is TODAY! Good luck!'
                notification_type = 'interview'
            elif days_until == 1:
                # Interview tomorrow
                title = 'Interview Tomorrow!'
                message = f'🎯 Your interview with {company_name} is tomorrow. Prepare well!'
                notification_type = 'interview'
            elif days_until <= 3:
                # Interview in 2-3 days
                title = f'Interview in {days_until} Days'
                message = f'🎯 Your interview with {company_name} is in {days_until} days. Start preparing!'
                notification_type = 'interview'
            else:
                # Interview more than 3 days away
                title = f'Interview Scheduled'
                message = f'📅 Your interview with {company_name} is scheduled in {days_until} days.'
                notification_type = 'reminder'
            
            return self.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                application_id=application_id,
                company_name=company_name
            )
        except Exception as e:
            logger.error(f"Error creating interview notification: {e}")
            return None
    
    def check_and_update_deadline_notifications(self, user_id: str) -> int:
        """
        Check all applications for a user and update/create deadline notifications.
        This should be called periodically (e.g., daily).
        
        Returns:
            Number of notifications created/updated
        """
        try:
            applications = self.db.collection('applications').where(
                'userId', '==', user_id
            ).where('status', 'in', ['applied', 'pending']).get()
            
            notifications_created = 0
            
            for app_doc in applications:
                app_data = app_doc.to_dict()
                app_data['id'] = app_doc.id
                
                deadline = app_data.get('deadline')
                if deadline:
                    # Check if notification already exists for this deadline
                    existing_notifications = self.db.collection('notifications').where(
                        'userId', '==', user_id
                    ).where('applicationId', '==', app_doc.id).where(
                        'type', '==', 'deadline'
                    ).get()
                    
                    # Only create if no recent deadline notification exists
                    if not existing_notifications:
                        notification_id = self._create_deadline_notification(
                            user_id=user_id,
                            company_name=app_data.get('companyName') or app_data.get('company'),
                            deadline=deadline,
                            application_id=app_doc.id
                        )
                        if notification_id:
                            notifications_created += 1
            
            return notifications_created
        except Exception as e:
            logger.error(f"Error checking deadline notifications: {e}")
            return 0
    
    def create_status_update_notification(
        self,
        user_id: str,
        company_name: str,
        old_status: str,
        new_status: str,
        application_id: Optional[str] = None
    ) -> Optional[str]:
        """Create notification when application status changes."""
        status_messages = {
            'accepted': f'🎉 Congratulations! Your application for {company_name} has been accepted!',
            'rejected': f'Your application for {company_name} was not selected this time. Keep applying!',
            'shortlisted': f'✅ Great news! You have been shortlisted for {company_name}.',
            'interview_scheduled': f'📅 Your interview with {company_name} has been scheduled.',
            'under_review': f'Your application for {company_name} is under review.',
        }
        
        message = status_messages.get(new_status, f'Your application status for {company_name} has been updated to {new_status}.')
        
        return self.create_notification(
            user_id=user_id,
            title='Application Status Update',
            message=message,
            notification_type='status',
            application_id=application_id,
            company_name=company_name
        )

