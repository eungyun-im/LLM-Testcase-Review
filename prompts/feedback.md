You wrote the test cases below. Automatic checks found gaps in them. Revise the test set so that every finding is resolved.

Requirements:
{requirements}

Inputs:
{inputs}

Possible outputs: {outputs}

Current test cases:

{tests}

Findings:

{feedback}

How to revise:

- For a missing boundary point, add a test that uses that value and choose the other inputs so that the boundary decides the output.
- For a disputed expected result, work the case out again from the requirement text. Change it only if the requirement supports the change.
- For a code change that no test would notice, add a test whose output would differ if the code were changed that way.
- Keep the existing tests that are correct. Give new tests new IDs.

Return the complete revised test set as CSV with exactly this header and nothing after the table:

tc_id,req_id,speed_kph,obstacle_m,sensor_age_ms,expected
