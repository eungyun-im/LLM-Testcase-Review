Write the decision rules of the function described below as a table.

Requirements:
{requirements}

The requirements are built from these conditions. For a given input, each is either yes or no:
{conditions}

Possible outputs: {outputs}

A program will apply the rules. It checks them from the top and uses the first rule whose conditions are all met. Respect the order the notes prescribe.

Return CSV with exactly this header and nothing after the table:

rule,when,then

One row per rule, in the order they are checked. In `when`, list the conditions the rule needs as ID=yes or ID=no, separated by semicolons, for example `C-SPEED-LOW=yes; C-OBSTACLE=no`. The last rule has `otherwise` in `when`. `then` is one of the possible outputs. No remarks.
