web: gunicorn PennCourseAlert.wsgi
beat: celery -A PennCourseAlert beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
celery: celery worker -A PennCourseAlert -Q alerts,celery -linfo
notifier: celery worker -A PennCourseAlert -Q alerts -linfo