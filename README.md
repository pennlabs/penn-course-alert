# Penn Course Alert
[![Coverage Status](https://coveralls.io/repos/github/pennlabs/penn-course-alert/badge.svg?branch=master)](https://coveralls.io/github/pennlabs/penn-course-alert?branch=master)
[![CircleCI](https://circleci.com/gh/pennlabs/penn-course-alert/tree/master.svg?style=svg)](https://circleci.com/gh/pennlabs/penn-course-alert/tree/master)

Penn Course Alert helps Penn students stay on top of the course
registration process by sending them ~~notifications~~ alerts by
text and email when other students drop classes.

The databse used is MySQL. Set the environment variable `DATABASE_URL`,
or set up a local database called `pca` with user/password `pca@password`
running on `localhost:3306` to test locally.

Dependencies are managed by [`pipenv`](https://pipenv.readthedocs.io/en/latest/),
so make sure that's installed globally before trying to run Penn Course Alert.

1. `git clone https://github.com/pennlabs/penn-course-alert.git`
2. `cd penn-course-alert`
3. `pipenv install`
4. `python manage.py migrate`
5. `python manage.py runserver`
6. Open your browser to the port specified in the terminal.

Enjoy!