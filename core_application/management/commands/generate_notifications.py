from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from coreapplication.models import Notification  # Replace 'yourapp' with the actual app name

User = get_user_model()
import random



class Command(BaseCommand):
    help = 'Generate 10 realistic notifications for students'

    def handle(self, *args, **kwargs):
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR("No users found in the system. Cannot assign notifications."))
            return

        notifications_data = [
            {
                "title": "Mid-Semester Exams Timetable Released",
                "message": "The mid-semester exam timetable is now available on the portal. Please check and prepare accordingly.",
                "type": "exam",
            },
            {
                "title": "Library Closure Notice",
                "message": "The university library will be closed on Friday for fumigation. Plan your studies accordingly.",
                "type": "general",
            },
            {
                "title": "Final Fee Payment Deadline",
                "message": "Students are reminded that the deadline for full fee payment is next Monday. Late payments will attract penalties.",
                "type": "fee",
            },
            {
                "title": "Upcoming Career Fair",
                "message": "Join us for the Career Fair on July 25th at the Main Hall. Meet employers and get career advice.",
                "type": "event",
            },
            {
                "title": "Emergency Water Outage",
                "message": "Due to maintenance work, there will be a temporary water outage in hostels on Wednesday.",
                "type": "emergency",
            },
            {
                "title": "Online Learning Orientation",
                "message": "New students are invited to the online learning orientation this Friday at 10 AM via Zoom.",
                "type": "academic",
            },
            {
                "title": "Call for Research Proposals",
                "message": "The research office is accepting student research proposals for the 2025 academic year.",
                "type": "academic",
            },
            {
                "title": "Important: Student Portal Downtime",
                "message": "The student portal will be down for maintenance this weekend. Ensure you download any required documents before Friday.",
                "type": "general",
            },
            {
                "title": "Bursary Applications Open",
                "message": "Applications for the 2025 bursary program are now open. Submit before August 5th.",
                "type": "fee",
            },
            {
                "title": "Cultural Week Launch",
                "message": "You are invited to the Cultural Week launch event on Monday. Experience music, food, and fashion from different cultures.",
                "type": "event",
            },
        ]

        for data in notifications_data:
            created_by = random.choice(users)
            is_global = random.choice([True, False])
            expires_at = timezone.now() + timedelta(days=random.randint(7, 30))

            notification = Notification.objects.create(
                title=data["title"],
                message=data["message"],
                notification_type=data["type"],
                is_global=is_global,
                created_by=created_by,
                expires_at=expires_at
            )

            if not is_global:
                notification.target_users.set(random.sample(users, min(5, len(users))))

            self.stdout.write(self.style.SUCCESS(f"Notification '{notification.title}' created."))

        self.stdout.write(self.style.SUCCESS("✅ 10 real notifications generated successfully."))