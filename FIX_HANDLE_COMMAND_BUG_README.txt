FridayV8 fix included.

Fixed issue:
NameError: name '_handle_command_core' is not defined

Reason:
The database history wrapper called _handle_command_core(), but friday.py did not rename the original command handler properly.

What to do:
Use this fixed package, extract it, run backend, then run START_TEXT_MODE.bat again.
