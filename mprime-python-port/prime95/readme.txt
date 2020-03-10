
Welcome to the Great Internet Mersenne Prime Search!

To use this program you must agree to the terms and conditions,
prize rules, etc. at http://mersenne.org/legal/

In case you ever forget, the GIMPS web site is at http://mersenne.org
My email address is woltman@alum.mit.edu.  For networking questions,
contact Scott Kurowski at primenet@mersenne.org.


FILE LIST
---------

readme.txt	This file.
mprime		The program to factor and run Lucas-Lehmer tests on
		Mersenne numbers.
whatsnew.txt	A list of new features in mprime.
stress.txt	A discussion of issues relating to stress testing a computer.
undoc.txt	A list of formerly undocumented and unsupported features.
prime.txt	A file containing your preferences.  The menu choices
		and dialog boxes are used to change your preferences.
local.txt	Like prime.txt, this file contains more preferences.
		The reason there are two files is discussed later.
worktodo.txt	A list of exponents the program will be factoring
		and/or Lucas-Lehmer testing.
results.txt	Mprime writes its results to this file.
prime.log	A text file listing all messages that have been sent
		to the PrimeNet server.
prime.spl	A binary file of messages that have not yet been sent to
		the PrimeNet server.
pNNNNNNN &	Intermediate files produced by mprime to resume
qNNNNNNN	computation where it left off.
eNNNNNNN	Intermediate files produced during ECM factoring.
fNNNNNNN	Intermediate files produced during trial factoring.
mNNNNNNN	Intermediate files produced during P-1 factoring.


WHAT IS THIS PROGRAM?
---------------------

This program is used to find Mersenne Prime numbers.  See
http://www.utm.edu/research/primes/mersenne.shtml for a good
description of Mersenne primes.  Mersenne numbers can be proved
composite (not prime) by either finding a factor or by running
a Lucas-Lehmer primality test.


COMMAND LINE ARGUMENTS
----------------------

These command line arguments can be used to schedule mprime to
run only at certain times of the day or at a different priority.  Note
that raising the program's priority will not make it run any faster
on an idle machine.

-An		Obsolete. 
		This is used to run two or more copies of mprime
		from the same directory.  Using this command line argument
		causes mprime to use a different set of filenames for the
		INI files, the results file, the log file, and the spool file.
		Just use a different value of n for each extra copy of
		mprime you start.
-c		Contact the PrimeNet server then exit.  Useful, for
		scheduling server communication as a cron job or
		as part of a script that dials an ISP.
-d		Prints more detailed information to stdout.  Normally
		mprime does not send any output to stdout.
-m		Bring up the menus to set mprime's preferences.
-t		Run the torture test.  Same as Options/Torture Test.
-v		Print the version number of mprime.
-Wdirectory	This tells mprime to find all its files in a different
		directory than the executable.


INSTRUCTIONS
------------

There are two ways to use this program.  The automatic way uses
a central server, which we call the PrimeNet server, to get work to do
and report your results.  Anyone with Internet access, even dial-up users,
should use this method.  You do not need a permanent connection to the
Internet.

The second method is the manual method.  It requires a little more work
and monitoring.  I recommend this for computers with no Internet access
or with some kind of firewall problem that prevents the automatic method
from working.

If you are running this program at your place of employment, you should
first GET PERMISSION from your network administrator or boss.  This is
especially true if you are installing the software on several machines.
Some companies are reluctant to run any software they are not familiar with.


INSTRUCTIONS FOR THE AUTOMATIC METHOD
-------------------------------------

1)  Download and decompress mprime.tgz.  You've probably done this already
    since you are reading this file.
2)  Connect to the Internet.  Create an account at http://mersenne.org
3)  Run mprime.  You will be see 3 sets of questions:
3a) The first set gathers information about you.  Enter your user ID and
    optionally and computer name.  If you are using several computers,
    use the same user ID but a unique computer name on each machine.  An easy-to-remember user ID will be
    helpful if you plan to visit the PrimeNet server's web page to view
    reports on your progress.
3b) The second set of questions gathers information about your machine.
    Fill in roughly how many hours a day you leave your computer running.
3c) The third set of questions gathers information about using the
    Primenet server.  Note that mprime will never dial-up to connect to
    the Internet, rather it waits for a time when you are already connected
    to contact the server.  Mprime will now contact the PrimeNet server to
    get some work for your computer to do.
4)  If you are using a proxy server you may need to do some further
    configuration.  See the later secion on "SETTING UP A PROXY SERVER".
5)  Configure your startup scripts so that mprime runs every time you
    boot your computer.


MANUAL METHOD INSTRUCTIONS
--------------------------

1)  Visit http://mersenne.org/update/ to create a userid for yourself and
    http://mersenne.org/manual_assignment/ to get an exponent or two to
    work on.  Copy these exponents to a file called worktodo.txt.
2)  Run mprime.  You will be see 2 sets of questions:
2a) The first set of questions gathers information about your machine.
    Fill in roughly how many hours a day you leave your computer running.
2b) The second set of questions gathers information about using the
    Primenet server.  Answer "No" to the first question.
3)  Configure your startup scripts so that mprime runs every time you
    boot your computer.
4)  When done with your exponents, use the web pages again to send the
    file "results.txt" to the PrimeNet server and get more work.


NOTES
-----

Running mprime may significantly increase your electric bill.  The amount
depends on your computer and your local electric rates.

It can take many CPU days to test a large Mersenne number.  This program
can be safely interrupted by using ^C or kill or shutdown to write
intermediate results to disk.  This program also saves intermediate
results to disk every 30 minutes in case there is a power failure.

You can compare your computer's speed with other users by checking the
web page http://mersenne.org/report_benchmarks/.

You can get several reports of your PrimeNet activity at any time
by logging in at http://mersenne.org/.

If you have overclocked your machine, I recommend running the torture
test for a couple of days.  The longer you run the torture test
the greater the chance that you will uncover an error caused by
overheating or overstressed memory.

Depending on the exponent being tested, the program may decide that it
would be wise to invest some time checking for small factors before
running a Lucas-Lehmer test.  Furthermore, the program may start factoring
exponents before a previous Lucas-Lehmer test completes.  This is normal!
The program will resume the Lucas-Lehmer test when the factoring
completes.


SETTING UP A PROXY SERVER
-------------------------

Fill in the proxy information in the Test/Primenet menu choice.

For help, visit http://mersenneforum.org.  Several knowledgeable members
will be glad to help if they can.


SETTING AVAILABLE MEMORY
------------------------

The P-1 factoring step prior to running a Lucas-Lehmer test is more
effective if it is given more memory to work with.  However, if you let
the program use too much memory then the performance of ALL programs will
suffer.  The good news is that 98% of the time the program uses less
than 8MB.  In fact, the program will work just fine if you instruct the
program to use only 8MB or less.

So how do you intelligently choose the available memory settings?  Below
are some steps you might take to figure this out:

1)  Be conservative.  It is better to set the available memory too low
than too high.  Setting the value too high can cause thrashing which
slows down all programs.  Remember, the program will only use the
extra memory in stage 2 of P-1 factoring (about 12 hours a month).

2)  Start with how much memory is installed in your machine.  Allow a
reasonable amount of memory for the OS and whatever background tasks
you run (say 100 or 200MB).  This represents the maximum value you should use.
The program won't let you enter more than 90% of installed memory.

3)  Assuming you run your machine 24 hours a day, what hours of the
day do you not use your computer?  Make these your nighttime hours and
let the program use a lot of memory during these hours.  But reduce this
value if you also run batch jobs at night.

4)  Factor in the information below about minimum, reasonable, and
desirable memory amounts for some sample exponents.

	Exponent	Minimum		Reasonable	Desirable
	--------	-------		----------	---------
	20000000	 40MB		   80MB		 120MB
	33000000	 65MB		  125MB		 185MB
	50000000	 85MB		  170MB		 250MB

For example, my machine is a dual-processor with 512MB of memory.
I guess Linux can survive on 100MB of memory.  Thus, I set the available
memory to (512 - 100) or ~400MB.  This is my nighttime setting.
During the day, I set the available memory to 80MB.  I can always stop
mprime if it is doing P-1 factoring and I detect memory thrashing.  More
casual users will probably want to set the daytime memory to 8MB so they
don't have to worry about mprime impacting system performance.

If at all in doubt, leave the settings at 8MB.  The worst that will
happen is you end up running a Lucas-Lehmer primality test when stage 2
of P-1 factoring would have found a factor.


PROGRAM OUTPUT
--------------

On screen you will see:

Factoring M400037 to 2^54 is 3.02% complete. Clocks: 24235224=0.121 sec.
	This means mprime is trying to find a small factor of 2^400037-1.
	It is 3.02% of the way though looking at factors below 2^54.  When
	this completes it may start looking for factors less than 2^55.
Iteration: 941400 / 1667747 [56.45%].  Per iteration time: 0.109 sec. (21889762 clocks)
	This means mprime just finished the 941400th iteration of a
	Lucas-Lehmer primality test.  The program must execute 1667747
	iterations to complete the primality test.  The average iteration
	took 21889762 "clock cycles" or 0.109 seconds.

The results file and screen will include lines that look like:

M2645701 has a factor: 13412891051374103
	This means to 2^2645701-1 is not prime.  It is divisible
	by 13412891051374103.
M2123027 no factor to 2^57, WV2: 14780E25
	This means 2^2123027-1 has no factors less than 2^57.  The Mersenne
	number may or may not be prime.  A Lucas-Lehmer test is needed
	to determine the primality of the Mersenne number.  WV2 is
	the program version number.  14780E25 is a checksum to guard
	against email transmission errors.
M1992031 is not prime. Res64: 6549369F4962ADE0. WV2: B253EF24,1414032,00000000
	This means 2^1992031-1 is not prime - a Lucas-Lehmer test says so.
	The last 64 bits of the last number in the Lucas-Lehmer sequence
	is 6549369F4962ADE0.  At some future date, another person will verify
	this 64-bit result by rerunning the Lucas-Lehmer test.  WV2 is the
	program	version number.  B253EF24 is a checksum to guard against email
	transmission errors.  1414032 can be ignored it is used as part
	of the double-checking process.  The final 00000000 value is a set
	of 4 counters.  These count the number of errors that occurred during
	the Lucas-Lehmer test.
M11213 is prime! WV2: 579A579A
	This means 2^11213-1 is a Mersenne prime!  WV2 is the program
	version number.  579A579A is a checksum to guard against email
	transmission errors.


RUNNING MPRIME ON SEVERAL COMPUTERS
-----------------------------------

The easiest way to do this is to first set up mprime on one computer.
Next copy all the files to the second computer.  Delete the local.txt
file and worktodo.txt files.  These files contain information that
is specific to the first computer.  Start mprime on the second
computer and optionally use Test/Primenet to give the second computer
a unique computer name.  Repeat this process for all the computers you
wish to run mprime on.

If you do not follow the instruction above, be sure you use 
Test/Primenet to give each computer the same user id and different
computer name.


TEST MENU
---------

The PrimeNet menu choice identifies your computer to the server.
The "Use PrimeNet..." option can be turned on to switch from the
manual method to the automatic method.

The Worker Threads menu choice is used to choose the type of work
you'd like to execute as well as adjust priority and affinity.
You should not need to change the priority.  You might raise the priority
if you just cannot live without a screen saver, or if you are running some
ill-behaved program that is using CPU cycles for no good reason.
The work type should usually be left set to "Whatever makes the most sense".
However, if you are running a slow computer and don't mind waiting several
months for a single Lucas-Lehmer test to complete OR you are running a faster
computer and get better thoughput if one core does an easier type of work,
then choose a different type of work to do.

The Status menu choice will tell you what exponents you are working on.
It will also estimate how long that will take and your chances of finding
a new Mersenne prime.

The Continue menu choice lets you resume prime95 after you have stopped it.

The Stop menu choice lets you stop the program.  When you continue,
you will pick up right where you left off.  This is the same as hitting
the ESC key.

The Exit menu choice lets you exit the program.


ADVANCED MENU
-------------

You should not need to use the Advanced menu.  This menu choice is
provided only for those who are curious to play with.

The Test choice can be used to run a Lucas-Lehmer test on one Mersenne
number.  Enter the Mersenne number's exponent - this must be a prime
number between 5 and 560000000.

The Time choice can be used to see how long each iteration of a Lucas-Lehmer
test will take on your computer and how long it will take to test a
given exponent.  For example, if you want to know how long a Lucas-Lehmer
test will take to test the exponent 876543, choose Advanced/Time and
enter 876543 for 100 iterations.

The ECM choice lets you factor numbers of the form k*b^n+c using the
Elliptic Curve Method of factoring.  ECM requires a minimum of 192 times
the FFT size.  Thus, ECM factoring of F20 which uses a 64K FFT will use
a minimum of 192 * 64K or 12MB of memory.  You can also edit the
worktodo.txt file directly.  For example:
	ECM2=k,b,n,c,B1,B2,curves_to_run

The P-1 choice lets you factor numbers of the form k*b^n+c using
the P-1 method of factoring.  You can also edit the worktodo.txt file
directly.  For example:
	Pminus1=k,b,n,c,B1,B2

Round off checking.  This option will slow the program down by several percent.
This option displays the smallest and largest "convolution error".  The
convolution error must be less than 0.49 or the results will be incorrect.
There really is no good reason to turn this option on.

The Manual Communication menu choice should only be used if the
automatic detection of an Internet connection is not working for you.
Using this option means you have to remember to communicate with the
server every week or two (by using this same menu choice).

The Unreserve Exponent choice lets you tell the server to unreserve
an exponent you have been assigned.  You might do this if a second computer
you had been running GIMPS on died or if you had been assigned an exponent
of one work type (such as a first-time-test) and now you have switched to
another work type (such as 10,000,000 digit numbers).  Any work you have
done on the unreserved exponent will be lost.

The Quit GIMPS menu choice is used when you no longer want this computer
to work on the GIMPS project.  You may rejoin at a later date.
If you are a PrimeNet user your unfinished work will be returned to the
server.  If you are a manual user, you need to send me email containing
your results.txt file.


OPTIONS MENU
------------

The CPU menu choice tells you what CPU the program has detected and
lets you set how much memory the program can use (see the earlier section
on "Setting available memory".

The Preferences menu choice lets you control how often a line is
written to the main window and how often a line is written to
the results file.  It also lets you change how often
intermediate files (to guard against power failure and crashes)
are created.  You can control how often the program checks to
see if you are connected to the Internet.  The program polls
whenever it has new data to send to or work to get from the PrimeNet
server.  If you are low on disk space, you can select one intermediate 
file instead of two.  However, if you crash in the middle of writing
the one intermediate file, you may have to restart an exponent from
scratch.  You can also tell the program to be quiet, rather than 
beeping like crazy, if a new Mersenne prime is found.

The Torture Test choice will run a continuous self test.  This is great
for testing machines for hardware problems.  See the file stress.txt
for a more in-depth discussion of stress testing and hardware problems.

The Benchmark choice times the program on several FFT lengths.  You can
then compare your computer's speed to others list at
http://mersenne.org/report_benchmarks/


POSSIBLE HARDWARE FAILURE
-------------------------

If the message "Possible hardware failure, consult the readme file."
appears in the results.txt file, then the program's error-checking has
detected a problem.  After waiting 5 minutes, the program will continue
testing from the last save file.

Could it be a software problem?  If the error is ILLEGAL SUMOUT, then 
it is very likely a true hardware error.  Although, it is impossible
to rule out an OS error corrupting part of mprime's address space.
The good news is that the program recovers very well from ILLEGAL SUMOUT
errors.

The other two errors messages, SUMINP != SUMOUT and ROUND OFF > 0.40 are
caused by one of two things:
	1)  For reasons too complicated to go into here, the program's error
	checking is not	perfect.  Some errors can be missed and some correct
	results flagged as an error.  If you get the message "Disregard last
	error..." upon continuing from the last save file, then you may have
	found the rare case where a good result was flagged as an error.
	2)  A true hardware error.

If you do not get the "Disregard last error..." message or this happens
more than once, then your machine is a good candidate for a torture test.
See the stress.txt file for more information.

Running the program on a computer with hardware problems may produce
incorrect results.  This won't hurt the GIMPS project since all results
will be double-checked.  However, you could be wasting your CPU time.
If you are getting several errors during each primality test, then I
recommend using your machine to factor Mersenne numbers or run one of
the many less strenuous distributed computing projects available.


LUCAS-LEHMER DETAILS
--------------------

This program uses the Lucas-Lehmer primality test to see if 2**p-1 is prime.
The Lucas sequence is defined as:
	L[1] = 4
	L[n+1] = (L[n]**2 - 2) mod (2**p - 1)
2**p-1 is prime if and only if L[p-1] = 0.

This program uses a discrete weighted transform (see Mathematics of
Computation, January 1994) to square numbers in the Lucas-Lehmer sequence.


DISCLAIMER
----------

THIS PROGRAM AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF
ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
PARTICULAR PURPOSE.


THANKS
------

Happy hunting and thanks for joining the search,
George Woltman
woltman@alum.mit.edu

