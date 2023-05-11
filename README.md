# scheduler

Update the alias command:

1.  Navigate to ~/.bashrc
2.  Add: alias schedule='python Schedular/todoist.py'

# Debugging

Issue: day_order was set to -1 for newly entered Todoist tasks Solution: I'm
fairly confident that this is a glich on Todoist's end. What I did was move
around one of the newly entered tasks in the 'today' view.

# Testing

An easy way to test the code on a day (that isn't today for fear of messing up
today's schedule) is to run the scheduler on tomorrow. To do this, add a "+1" to
all the {self.today.day} lines in the code. At the time of this testing, there
are only 4 {self.today.day} lines, and they all appear in the constructor. The
only other thing to do is pass a "True" as the argument in the
self.timeblock_timeline() method. At the time of writing this, there is only 1
line that calls that method, and it's in populate_timeline,. Congrats!
