import os

course_id = os.environ['NBGRADER_COURSEID']
c = get_config()

c.CourseDirectory.root = f"/srv/nbgrader/{course_id}"

c.Exchange.course_id = course_id

c.Exchange.root = "/srv/nbgrader/exchange"

c.ExecutePreprocessor.timeout = 300
