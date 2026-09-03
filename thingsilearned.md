s3 bucket config 

s3 bucket files that are inside the bucket are encrypted and only decrypted when your code reqeusts them thorugh api w valid credentials

whisper is a speech to text library, you give it an audio file and it returns text that was spoken


## Working rules (collaboration)

1. Explain the plan in plain English and wait for explicit "go" before writing anything.
2. One step at a time — smallest useful change, then stop for review.
3. Show every change as a diff with a short note on why.
4. Never edit more than one file (or one function) without checking in.
5. Ask before installing packages, deleting code, or refactoring anything not asked for.


explain how the upload file endpoint works 

theres a file that has all the routes and then another file that handles the logic

sep 3.
added the logic for finding out how many filler words there are in a text 
adding the logic for a wpm how many words you are saying per section
- each word you represent a midpoint number with that word 
- and then we have 15 second window that tracks the wpm 
- so if in that mid point number there are a lot of numbers within that 15 sec range
- your wpm are higher
added pauses
added a method to combine all the methods above


added reterival chunck whcih is basically a class that holds a certain structure of 
which reterival to get

added a tag method in which based off the metrics of your speech if something goes off
lets say wpm was too high over the threshold or if wpm was below the threshold it attaches a tag