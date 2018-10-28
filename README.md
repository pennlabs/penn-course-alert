# Penn Course Alert

Penn Course Alert helps Penn students stay on top of the course registration process by sending them ~~notifications~~
alerts when students drop classes.

Database is MySQL. Set environment variables `db_username`, `db_password`, `db_host` and `db_port` to connect to a remote
DB, or set up a local database with user/password `pca@password` running on `localhost:3306` to test locally.

Dependencies are managed by [`pipenv`](https://pipenv.readthedocs.io/en/latest/), so make sure that's installed globally
before trying to run Penn Course Alert.

1. `git clone https://github.com/pennlabs/PennCourseAlert.git`
2. `cd PennCourseAlert`
3. `pipenv install`
4. `python manage.py migrate`
5. `python manage.py runserver`
6. Open your browser to the port specified in the terminal.

Enjoy!