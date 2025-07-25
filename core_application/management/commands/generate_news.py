import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

from coreapplication.models import NewsArticle

class Command(BaseCommand):
    help = 'Generate sample Polytechnic News Articles'

    def handle(self, *args, **kwargs):
        categories = ['academic', 'event', 'announcement', 'sports', 'general']
        titles = [
            'New Library Wing Opens at Main Campus',
            'Sports Gala Kicks Off This Friday',
            'Orientation Program for First Years Announced',
            'Academic Calendar for 2025 Released',
            'Polytechnic Launches Innovation Hub'
        ]
        summaries = [
            'A brief look at the new facilities available to students and staff.',
            'Join us for a fun-filled weekend of athletics and competition.',
            'All new students are expected to attend the orientation.',
            'Stay updated on important semester and holiday dates.',
            'Empowering students with state-of-the-art resources.'
        ]
        contents = [
            'Today, the Polytechnic unveiled its new library wing aimed at enhancing learning experiences...',
            'The much-anticipated Sports Gala will include soccer, volleyball, track events, and more...',
            'Orientation for first-year students begins Monday, with keynote speeches from faculty...',
            'The new academic calendar outlines key dates for the upcoming school year, including exams...',
            'The Innovation Hub features 3D printers, robotics labs, and mentoring programs...'
        ]

        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No superuser found. Create one first.'))
            return

        for i in range(10):
            idx = random.randint(0, len(titles) - 1)
            article = NewsArticle.objects.create(
                title=titles[idx] + f" #{i+1}",
                summary=summaries[idx],
                content=contents[idx],
                category=random.choice(categories),
                author=admin_user,
                publish_date=timezone.now(),
                is_published=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created: {article.title}'))
