"""
Django management command to migrate JSON data to database
"""
import os
import json
import uuid
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from notification_push.models import Job, ScrapingSession, Notification


class Command(BaseCommand):
    help = 'Migrate JSON data from data/ folder to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be actually migrated'))
        
        # Path to data directory
        data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        
        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f'Data directory not found: {data_dir}'))
            return
        
        # Migrate jobs from extracted_jobs.json
        jobs_file = os.path.join(data_dir, 'extracted_jobs.json')
        if os.path.exists(jobs_file):
            self.migrate_jobs(jobs_file, dry_run)
        
        # Migrate message data (as notifications)
        self.migrate_message_files(data_dir, dry_run)
        
        self.stdout.write(self.style.SUCCESS('Migration completed!'))

    def migrate_jobs(self, jobs_file, dry_run):
        """Migrate jobs from extracted_jobs.json"""
        try:
            with open(jobs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            jobs_data = data.get('jobs', [])
            self.stdout.write(f'Found {len(jobs_data)} jobs to migrate')
            
            migrated_count = 0
            for job_data in jobs_data:
                job_id = job_data.get('id') or f"job_{uuid.uuid4()}"
                
                if not dry_run:
                    # Check if job already exists
                    if Job.objects.filter(job_id=job_id).exists():
                        continue
                    
                    # Parse posted date
                    posted_date = self.parse_date(job_data.get('posted_date'))
                    
                    # Create job
                    Job.objects.create(
                        job_id=job_id,
                        title=job_data.get('title', '')[:500],
                        description=job_data.get('description', ''),
                        client_name=job_data.get('client_name', '')[:255],
                        budget=job_data.get('budget', '')[:100],
                        hourly_rate=job_data.get('hourly_rate', '')[:100],
                        posted_date=posted_date,
                        job_url=job_data.get('job_url', job_data.get('url', '')),
                        location=job_data.get('location', '')[:255],
                        job_type=job_data.get('job_type', '')[:50],
                        selector_used=job_data.get('selector_used', ''),
                        html_snippet=job_data.get('html', '')[:1000],
                    )
                
                migrated_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Migrated {migrated_count} jobs from extracted_jobs.json')
            )
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error migrating jobs: {str(e)}'))

    def migrate_message_files(self, data_dir, dry_run):
        """Migrate message files as scraping sessions and notifications"""
        message_files = []
        
        # Find all message files
        for filename in os.listdir(data_dir):
            if filename.startswith('upwork_messages_') and filename.endswith('.json'):
                message_files.append(os.path.join(data_dir, filename))
        
        self.stdout.write(f'Found {len(message_files)} message files to migrate')
        
        for filepath in message_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract timestamp from filename
                filename = os.path.basename(filepath)
                timestamp_str = filename.replace('upwork_messages_', '').replace('.json', '')
                if 'error_' in timestamp_str:
                    timestamp_str = timestamp_str.replace('error_', '')
                
                session_date = self.parse_filename_date(timestamp_str)
                
                if not dry_run:
                    # Create scraping session
                    session = ScrapingSession.objects.create(
                        session_id=f"session_{timestamp_str}",
                        started_at=session_date,
                        completed_at=session_date,
                        page_url=data.get('pageInfo', {}).get('url', 'https://upwork.com'),
                        total_jobs_found=len(data.get('messages', [])),
                        new_jobs_saved=len(data.get('messages', [])),
                        selector_used=data.get('pageInfo', {}).get('selector_used', ''),
                        status='completed' if data.get('messages') else 'failed',
                        success=bool(data.get('messages')),
                        error_message=data.get('pageInfo', {}).get('error', ''),
                    )
                    
                    # Create notification for this session
                    messages_count = len(data.get('messages', []))
                    if messages_count > 0:
                        Notification.objects.create(
                            notification_id=f"notif_{timestamp_str}",
                            title=f"Messages extracted: {messages_count} messages",
                            message=f"Successfully extracted {messages_count} messages from Upwork",
                            type='success',
                            source='scraper',
                            session=session,
                        )
                    else:
                        error_msg = data.get('pageInfo', {}).get('error', 'No messages found')
                        Notification.objects.create(
                            notification_id=f"notif_error_{timestamp_str}",
                            title="Message extraction failed",
                            message=f"Error: {error_msg}",
                            type='error',
                            source='scraper',
                            session=session,
                        )
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error migrating {filepath}: {str(e)}'))
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Migrated {len(message_files)} message files as scraping sessions')
        )

    def parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str:
            return timezone.now()
        
        # Try different formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
        ]
        
        for fmt in formats:
            try:
                return timezone.datetime.strptime(date_str, fmt)
            except:
                continue
        
        return timezone.now()

    def parse_filename_date(self, timestamp_str):
        """Parse timestamp from filename like '2025-10-14T06-22-28-030Z'"""
        try:
            # Replace dashes with colons and dots for proper ISO format
            iso_str = timestamp_str.replace('-', ':', 2)  # First two dashes become colons
            iso_str = iso_str.replace('-', '.')  # Remaining dashes become dots
            iso_str = iso_str.replace('Z', '+00:00')  # Z to timezone
            
            return timezone.datetime.fromisoformat(iso_str)
        except:
            return timezone.now()