from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .models.database import get_db, OutreachAttempt, FollowUp
from .config import config


class FollowUpScheduler:
    """Background scheduler for automated follow-up reminders"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def start(self):
        """Start the scheduler with periodic tasks"""
        # Check for follow-ups needed every day at 9 AM
        self.scheduler.add_job(
            func=self.check_follow_ups,
            trigger=IntervalTrigger(hours=24),
            id='follow_up_checker',
            name='Check for follow-ups needed',
            replace_existing=True
        )
        print("✅ Follow-up scheduler started")

    def check_follow_ups(self):
        """Check for prospects that need follow-ups and create reminders"""
        print(f"🔍 Checking for follow-ups needed at {datetime.utcnow().isoformat()}")

        try:
            # Get database session
            db_gen = get_db()
            db: Session = next(db_gen)

            now = datetime.utcnow()
            follow_up_threshold = now - timedelta(days=config.FOLLOW_UP_DAYS)

            # Find outreach attempts that need follow-ups
            attempts_needing_followup = db.query(OutreachAttempt).filter(
                OutreachAttempt.sent_at < follow_up_threshold,
                OutreachAttempt.received_response == False,
                OutreachAttempt.status.in_(['sent', 'no_response'])
            ).all()

            follow_ups_created = 0

            for attempt in attempts_needing_followup:
                # Check if follow-up already exists
                existing_followup = db.query(FollowUp).filter(
                    FollowUp.prospect_id == attempt.prospect_id,
                    FollowUp.completed == False
                ).first()

                if not existing_followup:
                    # Create new follow-up reminder
                    follow_up = FollowUp(
                        prospect_id=attempt.prospect_id,
                        scheduled_date=now,
                        reason='no_response',
                        notes=f'No response to {attempt.channel.value} message sent on {attempt.sent_at.date()}'
                    )
                    db.add(follow_up)
                    follow_ups_created += 1

            db.commit()
            print(f"✅ Created {follow_ups_created} new follow-up reminders")

        except Exception as e:
            print(f"❌ Error checking follow-ups: {str(e)}")
        finally:
            db.close()

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("👋 Follow-up scheduler stopped")


# Global scheduler instance
_scheduler = None


def start_scheduler():
    """Start the global scheduler"""
    global _scheduler
    if _scheduler is None:
        _scheduler = FollowUpScheduler()
        _scheduler.start()
    return _scheduler


def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.stop()
        _scheduler = None
