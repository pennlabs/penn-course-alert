web: gunicorn PennCourseAlert.wsgi
beat: celery -A PennCourseAlert beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
queuer: celery worker -A PennCourseAlert -Q celery -linfo
notifier: celery worker -A PennCourseAlert -Q alerts -linfo