checkiid.py: A script for checking for IID changes in Mozilla code.
===============================================================================
I. Motivation

Binary compatibility is a difficult issue for any library that allows binary
extensions to be built on top of an API. Because C++ does not specify a binary
format, different compilers produce different generated code from the same
C++ source files. More discussion on this topic is beyond the scope of this
help file, but if you would like to learn more about cross compatibility and
compatibility between different API versions/compilers, a great resource is
"Essential COM", By Don Box.

For the purposes of this discussion, we address the issue of annotation of 
interface definition files that have changed between different versions of 
an API. The annotation for a given interface, typically specified in an
interface description language, or IDL, is a universally unique identifier, or
UUID. This is sometimes also referred to as an interface identifier, or IID.
When a given interface changes, and that change affects the interface's ability
to be compatible in binaries created using the previous version of the
interface, the IID for that interface must also change.

Failure to change an IID when a given interface changes results in a situation
where a compiled C++ interpretation of the interface does not match the
interface expected by a given third-party binary. Likely, this will result in a
crash for the third-party binary.

How does changing the IID help?

The IID of a given interface is used in lieu of the name of the interface in
compiled code. If an IID has changed between versions of the API, the old IID
will no longer be able to be used to find an object of a given type. Thus, the
third-party will need to recompile their code and fix any potential missing
attributes or methods they previously used, rather than these missing pieces
generating a runtime exception (crash) on deployed platforms.

II. Purpose of the Script

Unfortunately, remember how to change IIDs can sometimes be very difficult for
platform engineers. Engineers have a number of things going through their head
at any given time, and mundane tasks like generating a new IID can easily be
overlooked. However, given the severity of such a mistake (a third-party crash),
it's a problem that needs to be addressed.

Fortunately, this is a problem that can be handled programmatically, which is
exactly what this script intends to do. It operates on a set of differences,
or 'diffs', and reports back to the user of the script which interfaces it
believes to have been changed WITHOUT a corresponding IID change.

III. Prerequisites

In order to use the script, the following prerequisites need to be installed on
the user's local machine:

  * Python >= 2.7
  * Mercurial >= 2.6 
  * Python Difflib module
  * Python argparse module
  * Mozilla Code Repository Local Clone

This last one is important - you MUST have a local clone of the mozilla hg
repository on which you want to perform the check. The script not only checks
through differences in hg commits, but also looks at local files in the
repository.

IV. How to Use the Script

There are a few steps that need to be performed before you can utilize the
checkiid script:

  1. Determine the start and end revisions you want to check:
   
     Typically, this step involves looking at tags within the hg repository
     to find a human-readable revision tag that you can use to start and end
     the diff. You can access the tags in any mozilla repo by using:

     > hg tags

  2. Check out the end revision of the code you want to work on:
  
     Because checkiid operates on BOTH the diff generated by hg, as well as the
     local repository files, it can sometimes get confused if the repository
     state isn't in the state that it expects. For the best results, it's useful
     to check out the revision of the repository where your diff will end:

     > hg checkout -r <endrev>

     (Of course, if your end revision is tip, and you're already there, then
     this step isn't necessary).

  3. Get a diff from the repository:

     This step just involves running the hg diff utility so that you can get a
     list of changes between the two revisions you specified. Since we're only
     interested in changes to files that end in .idl, there's no need to get
     changes to any other file:

     > hg diff -r <startrev> -r <endrev> -I "**.idl" > /tmp/firefox.diff

     This will give you a file in /tmp called 'firefox.diff' that lists all the
     changes to files ending in .idl from <startrev> through <endrev>. You can
     call the file anything you wish, but it's usually best to keep it simple.

  4. Run the script:

     Now, all that's left is to run the checkiid script. From your hg repository
     directory, do the following:

     > cat /tmp/firefox.diff | python /path/to/checkiid.py .

V. Interpreting Output
  
Once the script has completed, you will likely have something like the following
output:

ERROR: Interface 'nsIB2GKeyboard', in file 'b2g.idl' needs a new IID
ERROR: Interface 'nsIPrincipal', in file 'nsIPrincipal.idl' needs a new IID
 ... possibly more errors ...

This means that the script has identified two interfaces: 'nsIB2GKeyboard' and
'nsIPrincipal' that it thinks need new IIDs. The script is unlikely to fail in
the false negative direction - that is, it's not likely to be the case that 
the script will fail to report an interface that needs an IID change but doesn't
have one. Instead, it's much more likely that the script will report false
positives - that it will identify interfaces that have been changed and it thinks
need a changed IID when they actually don't.

How do I determine which ones are false positives?

There isn't an easy answer to this question, really. The only way to determine
whether an IID change is necessary is to look through the diff file and utilize
your skills as an engineer to determine if an IID change is needed. Some pointers
are available at this page: https://developer.mozilla.org/en-US/docs/XPIDL#Source_and_Binary_Compatibility

In general, if you're unsure whether an interface needs an IID revision, you
should ask a fellow engineer that knows a bit more about XPCOM. When in doubt, 
err on the side of revising the IID. Remember, changing the IID will force 
third-party add-ons to recompile and redistribute their code (if they use the
interface in question). This is an annoyance, but not as much of an annoyance as
having their application crash unexpectedly after release! 
