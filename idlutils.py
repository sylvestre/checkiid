import re

# @class IDLDescriptor A descriptor that may be found prefixing an attribute or
#        method in an IDL interface.
#
# Examples of descriptors are things like "notxpcom" and "nostdcall". Typically,
# they prefix a method or attribute in the following way in IDL:
# [notxpcom] long getSomeValue();
#
# This class also holds a list of all the current descriptors loaded, so that
# the list can be searched quickly. This list is a singleton (i.e. static)
# across all IDLDescriptor objects.


class IDLDescriptor:
    # Static list of IDL descriptors
    kDescriptorList = []

    # Create a new IDLDescriptor object. Each IDLDescriptor contains two parts
    # a token, which identifies what the IDL code actually looks like that invokes
    # this descriptor, and a boolean indicating whether the descriptor causes
    # binary compatibility to change (thus requiring a new IID for the interface).
    #
    # @param aToken A string containing the name of the IDLDescriptor, the token
    #        that is used to invoke the descriptor.
    # @param aAffectsBinaryCompat True, if adding or removing this IDLDescriptor
    #        in an interface affects binary compatibility; False, otherwise.
    # @note There is no method of changing an IDLDescriptor object's members after
    #       having constructed it. This is intentional, as IDL descriptors cannot
    #       change from affecting binary compatibility to not affecting binary
    #       compatibility. Similarly, the token names cannot change, as this would
    #       incentivize reuse of IDLDescriptor objects - something that should
    #       be avoided, given how cheap they are to create.
    def __init__(self, aToken, aAffectsBinaryCompat):
        self.mToken = aToken
        self.mBinaryCompat = aAffectsBinaryCompat

    # Return whether or not this IDLDescriptor affects binary compatibility.
    #
    # @returns True, if this IDLDescriptor object represents a descriptor that
    #          affects binary compatibility; False otherwise.
    def affectsBinaryCompatibility(self):
        return self.mBinaryCompat

    # Retrieve the token, or identifier, of the IDLDescriptor object.
    #
    # @returns A string representing the token, or identifier, of the descriptor.
    def getToken(self):
        return self.mToken

    # Determine whether or not the IDL descriptor this object represents appears
    # on a given line.
    #
    # @param aLine The line to check, presumably from an IDL file or patch file.
    # @param aPrinter An optional argument of type PrettyPrinter to route debug
    #        output from this method through.
    #
    # @returns True, if the idl descriptor which this object represents appears in
    #          aLine; False, otherwise.
    def isInLine(self, aLine, aPrinter=None):
        match = re.search("^(\s)*[\+\-](\s)*\[(.*)](.*)", aLine)
        if match:
            splitAttrs = match.group(3).split(",")
            for attr in splitAttrs:
                if aPrinter:
                    aPrinter.debug("Found descriptor: " + attr)
                if attr == self.mToken:
                    return True
        return False

    # Determine if there are any known IDL descriptors in a given line.
    #
    # This method checks the given parameter against all known IDLDescriptor
    # objects (all objects in the list kDescriptorList).
    #
    # @param aLine The line to check, presumably from an IDL file or patch file.
    # @param aPrinter An optional argument of type PrettyPrinter to route debug
    #        output from this method through.
    #
    # @returns True, if any known IDLDescriptor object in kDescriptorList appears
    #          in aLine (checked by calling isInLine() repeatedly); False, if
    #          isInLine(aLine) returns False for every IDLDescriptor in
    #          kDescriptorList.
    #
    # @note This is a static function, so it should be called as:
    #       IDLDescriptor.hasDescriptorsInLine(...)
    def hasDescriptorsInLine(aLine, aPrinter=None):
        for desc in IDLDescriptor.kDescriptorList:
            if desc.isInLine(aLine, aPrinter):
                return True
        return False

    # Determine if any descriptors in a given line affect binary compatibility.
    #
    # @param aLine The line to check, presumably from an IDL file or patch file.
    # @param aPrinter An optional argument of type PrettyPrinter to route debug
    #        output from this method through.
    #
    # @returns True, if hasDescriptorsInLine() returns true for aLine AND one of
    #          the descriptors in kDescriptorList for which isInLine(aLine)
    #          returns true also affects binary compatibility.
    #
    # @note This is a static function, so it should be called as:
    #       IDLDescriptor.areDescriptorsInLineAffectingBinaryCompat(...)
    def areDescriptorsInLineAffectingBinaryCompat(aLine, aPrinter=None):
        for desc in IDLDescriptor.kDescriptorList:
            if desc.isInLine(aLine, aPrinter) and desc.affectsBinaryCompatibility:
                if aPrinter:
                    aPrinter.debug("Descriptor: " + desc.getToken() + " affects binary compatibility.")
                return True

        if aPrinter:
            aPrinter.debug("No descriptors found affecting binary compatibility.")
        return False

    areDescriptorsInLineAffectingBinaryCompat = staticmethod(areDescriptorsInLineAffectingBinaryCompat)
    hasDescriptorsInLine = staticmethod(hasDescriptorsInLine)


# @class SpecialBlockType An object representing a type of special block. A
#        special block is a section of code that needs to be interpreted
#        differently than other code. A comment block is an example of a special
#        block.
#
#        Each special block type consists of two strings: the string token
#        identifying the start of the block (e.g. "/*" for a comment block)
#        and a string token identifying the end of the block (e.g. "*/" for a
#        comment block).
class SpecialBlockType:

    # Create a new special block type with a given start and end token.
    #
    # @param aStartToken The string that indicates the start of the special block
    #        of the new type.
    # @param aEndToken The string that indicates the end of the special block of
    #        the new type.
    def __init__(self, aStartToken, aEndToken):
        self.mStartToken = aStartToken
        self.mEndToken = aEndToken

    # Retrieve the string representing the start token of the special block.
    def getStartToken(self):
        return self.mStartToken

    # Retrieve the string representing the end token of the special block.
    def getEndToken(self):
        return self.mEndToken

    # Convert this special block type to a string. This is used for debugging
    # output, mostly.
    def __str__(self):
        return "[SpecialBlockType (" + str(self.mStartToken) + ")]"

    # Compare one special block type to another.
    #
    # @param aOther Another object of type SpecialBlockType to compare to.
    #
    # @returns True, if and only if both the start token and the end token are
    #          equal between this SpecialBlockType and aOther; False, otherwise.
    def __equals__(self, aOther):
        if self.mStartToken == aOther.mStartToken and self.mEndToken == aOther.mEndToken:
            return True
        return False

    # Determines whether a line is the start of an IDL block that requires special
    # handling (e.g. a comment or language specific code block).
    #
    # @param aLine The line to check
    #
    # @returns True, if the line is the start of an IDL block of a given type,
    #          False otherwise
    def isStartOfSpecialBlock(self, aLine):
        # a line is a start of a block comment if it has the start token at the
        # beginning of the line
        match = re.match("^(\s)*" + self.mStartToken, aLine)
        if match:
            return True
        return False

    # Determines whether a line contains a block of this SpecialBlockType
    # completely within it.
    #
    # @param aLine The line to check.
    #
    # @returns True, if aLine contains both the start and end of this
    #          SpecialBlockType; False, otherwise.
    def containsSpecialBlock(self, aLine):
        match = re.match("^(\s)*(.*)" + self.mStartToken + "(.*)" + self.mEndToken + "(\s)*(.*)", aLine)
        if match:
            return True
        return False

    # Determines whether a line is the end of an IDL block that requires special
    # handling (e.g. a comment or language specific code block)
    #
    # @param aLine The line to check
    #
    # @returns True, if the line is the end of an IDL block of a given type,
    #          False otherwise
    def isEndOfSpecialBlock(self, aLine):
        # a line is the end of a block comment if it has */ at the
        # end of the line
        regex = "(.*)" + self.mEndToken + "(\s)*$"
        match = re.match(regex, aLine)
        if match:
            return True
        return False


# A SpecialBlockRange is composed of two numerals indicating lines at which
# the range starts and ends, respectively, as well as a member variable
# indicating the file from which the range was generated.
#
# The following are cases that the SpecialBlockRange handles:
# Block comment range: StartingToken: /*, Ending token: */
# C++-specific range: Starting token {%C++, Ending token: %}
#
# @todo Currently, SpecialBlockRange objects only operate on lines of a file,
#       not on individual chracters within a line. It should be modified to
#       be more granular in the future.
class SpecialBlockRange:

    # A mapping of file paths to special block range objects.
    kFilePathToCommentRangeMap = {}

    # Create a new object of type SpecialBlockRange.
    #
    # @param aStart The line at which the SpecialBlockRange begins.
    # @param aEnd The line at which the SpecialBlockRange ends.
    # @param aFilePath The relative file path where the IDLFile containing the
    #        special block is located. This is used to query the file for context
    #        surrounding a given set of diff output lines.
    def __init__(self, aStart, aEnd, aFilePath):
        self.mStartLine = aStart
        self.mEndLine = aEnd
        self.mFilePath = aFilePath

    # A SpecialBlockRange (x,y) CONTAINS a line number, l, iff l>=x AND l<=y.
    def __contains__(self, x):
        if x >= self.mStartLine and x <= self.mEndLine:
            return True
        return False

    # Retrieve the length of the special block range, in lines.
    def __len__(self):
        return self.getEndLine() - self.getStartLine() + 1

    def __str__(self):
        return "[SpecialBlockRange (" + str(self.mStartLine) + ", " + str(self.mEndLine) + ")]"

    # Retrieve the line number of the start of this SpecialBlockRange.
    #
    # @returns The line number of the start of this SpecialBlockRange.
    def getStartLine(self):
        return self.mStartLine

    # Retrieve the line number of the end of this SpecialBlockRange.
    #
    # @returns The line number of the end of this SpecialBlockRange.
    def getEndLine(self):
        return self.mEndLine

    # @returns The relative file path where the IDLFile containing the
    #          special block is located.
    def getFilePath(self):
        return self.mFilePath

    # Create a set of objects representing ranges in a given IDL file.
    #
    # @param aFilePath The location on disk of the IDL file for which to construct
    #        ranges of special blocks.
    # @param aPrinter An optional argument of type PrettyPrinter to route debug
    #        output from this method through.
    def getRangesForFilePath(aFilePath, aPrinter=None):
        if aFilePath not in SpecialBlockRange.kFilePathToCommentRangeMap:
            SpecialBlockRange.findAllSpecialBlocksForFile(aFilePath, aPrinter)

        return SpecialBlockRange.kFilePathToCommentRangeMap[aFilePath]

    # Find all the special block ranges for a file, given the file path.aFilePath
    # This method does not return anything, instead it populates the
    # SpecialBlockRange.kFilePathToCommentRangeMap static member variable.
    #
    # This will raise an IOError if aFilePath cannot be found. This usually only
    # happens if the hg repository is in a different state/commit than what the
    # script is expecting (the end revision is different).
    #
    # @param aFilePath A string representing the path on disk of the file to
    #        check.
    # @param aPrinter An optional argument of type PrettyPrinter to route debug
    #        output from this method through.
    def findAllSpecialBlocksForFile(aFilePath, aPrinter=None):

        aPrinter.debug("Starting findAllSpecialBlocksForFile")

        if aFilePath not in SpecialBlockRange.kFilePathToCommentRangeMap.keys():
            SpecialBlockRange.kFilePathToCommentRangeMap[aFilePath] = []

        parseFile = open(aFilePath)

        lineNo = 0
        commentType = SpecialBlockType("\/\*", "\*\/")
        cppType = SpecialBlockType("\%{\s*C\+\+", "\%\}")

        # This is a stack of (SpecialBlockType, integer) tuples that represents
        # the last type seen along with the line number at which it was seen, so
        # we can correctly handle nested types.
        blockStack = []

        # for each line in the file path
        for line in parseFile:
            lineNo = lineNo + 1

            # if the line contains a comment block, then we just ignore it right now
            # because we're not smart enough to handle offsets within a comment block.
            if commentType.containsSpecialBlock(line):
                aPrinter.debug("(" + aFilePath + ", Line " + str(lineNo) + "): A comment block starts and ends on this line.")
                continue

            # if the line is the start of a special block range, document it
            if (commentType.isStartOfSpecialBlock(line)):
                aPrinter.debug("Pushing to stack: " + str(commentType) + ", lastLineNo: " + str(lineNo))

                blockStack.append((commentType, lineNo))

            # if the line is the end of a block comment, create a SpecialBlockRange
            # and add it to the map
            if (commentType.isEndOfSpecialBlock(line)):
                if len(blockStack) == 0:
                    aPrinter.debug("(" + aFilePath + ", Line " + str(lineNo) + "): An error occurred while trying to pop from the stack.")

                    # Right now, we just skip this line because we don't know what to do with it otherwise.
                    # Once Ticket #90 (http://www.glasstowerstudios.com/trac/JMozTools/ticket/90)
                    # is fixed, we can do something more intelligent here.
                    continue

                (lastSeenType, lastLineNo) = blockStack.pop()

                aPrinter.debug("Popped from stack. Last seen type: " + str(lastSeenType) + ", lastLineNo: " + str(lastLineNo))

                if lastSeenType == commentType:
                    blockRange = SpecialBlockRange(lastLineNo, lineNo, aFilePath)
                    SpecialBlockRange.kFilePathToCommentRangeMap[aFilePath].append(blockRange)
                else:
                    aPrinter.debug("Pushing to stack: " + str(lastSeenType) + ", lastLineNo: " + str(lastLineNo))

                    blockStack.push((lastSeenType, lastLineNo))

            # if the line is the start of a cpp-specific code block
            if cppType.isStartOfSpecialBlock(line):

                aPrinter.debug("Pushing to stack: " + str(cppType) + ", lastLineNo: " + str(lineNo))

                blockStack.append((cppType, lineNo))

            if cppType.isEndOfSpecialBlock(line):
                if len(blockStack) == 0:
                    aPrinter.debug("(" + aFilePath + ", Line " + str(lineNo) + "): An error occurred while trying to pop from the stack.")

                (lastSeenType, lastLineNo) = blockStack.pop()

                aPrinter.debug("Popped from stack. Last seen type: " + str(lastSeenType) + ", lastLineNo: " + str(lastLineNo))

                if lastSeenType == cppType:
                    blockRange = SpecialBlockRange(lastLineNo, lineNo, aFilePath)
                    SpecialBlockRange.kFilePathToCommentRangeMap[aFilePath].append(blockRange)
                else:
                    aPrinter.debug("Pushing to stack: " + str(lastSeenType) + ", lastLineNo: " + str(lastLineNo))
                    blockStack.push((lastSeenType, lastLineNo))

        parseFile.close()

    # Make the getRanges and findAllComments methods static.
    findAllSpecialBlocksForFile = staticmethod(findAllSpecialBlocksForFile)
    getRangesForFilePath = staticmethod(getRangesForFilePath)
