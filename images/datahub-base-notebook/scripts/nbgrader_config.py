import os

course_id = os.environ['NBGRADER_COURSEID']
c = get_config()

c.CourseDirectory.root = f"/srv/nbgrader/{course_id}"

c.Exchange.course_id = course_id

c.Exchange.root = "/srv/nbgrader/exchange"

c.ExecutePreprocessor.timeout = 300

c.ClearSolutions.begin_solution_delimeter = "BEGIN MY SOLUTION"
c.ClearSolutions.end_solution_delimeter = "END MY SOLUTION"
c.ClearSolutions.code_stub = {
    "R": "# your code here\nfail() # No Answer - remove if you provide an answer",
    "python": "# your code here\nraise NotImplementedError",
    "javascript": "// your code here\nthrow new Error();"
}