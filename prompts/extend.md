You wrote test cases for the function described below. Automatic checks found gaps in them. Write additional test cases that close the gaps. Do not repeat or change the existing ones.

Requirements:
{requirements}

Inputs:
{inputs}

Possible outputs: {outputs}

Inputs of the existing test cases:

{tests}

Findings:

{feedback}

How to close them:

- For an input class with no test, add a test whose inputs fall into that class.
- For a missing boundary point, add a test that uses that value and choose the other inputs so that the boundary decides the output.
- For a code change that no test would notice, add a test whose output would differ if the code were changed that way.

Return only the new test cases as CSV with exactly this header and nothing after the table:

tc_id,req_id,speed_kph,obstacle_m,sensor_age_ms,expected

One row per test case. Leave obstacle_m empty when no obstacle is detected. expected must be one of the possible outputs. Every row has exactly six comma-separated fields. The three input columns hold plain numbers, without units and without names. No extra columns and no remarks.
