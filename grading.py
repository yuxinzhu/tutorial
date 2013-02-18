# grading.py
# ----------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and Pieter 
# Abbeel in Spring 2013.
# For more info, see http://inst.eecs.berkeley.edu/~cs188/pacman/pacman.html

"Common code for autograders"

import cgi
import time
import sys
import traceback
import pdb

ORIGINAL_STDOUT = None
ORIGINAL_STDERR = None

class WritableNull:
    def write(self, string):
        pass
 
def mutePrint():
    global ORIGINAL_STDOUT, ORIGINAL_STDERR
    import cStringIO
    ORIGINAL_STDOUT = sys.stdout
    #ORIGINAL_STDERR = sys.stderr
    sys.stdout = WritableNull()
    #sys.stderr = WritableNull()

def unmutePrint():
    global ORIGINAL_STDOUT, ORIGINAL_STDERR
    sys.stdout = ORIGINAL_STDOUT
    #sys.stderr = ORIGINAL_STDERR


## code to handle timeouts
import signal
class TimeoutFunctionException(Exception):
    """Exception to raise on a timeout"""
    pass

class TimeoutFunction:

    def __init__(self, function, timeout):
        "timeout must be at least 1 second. WHY??"
        self.timeout = timeout
        self.function = function

    def handle_timeout(self, signum, frame):
        raise TimeoutFunctionException()

    def __call__(self, *args):
        if not 'SIGALRM' in dir(signal):
            return self.function(*args)
        old = signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.timeout)
        # try:
        result = self.function(*args)
        # finally:
        # signal.signal(signal.SIGALRM, old)
        signal.alarm(0)
        return result

class Grades:
  "A data structure for project grades, along with formatting code to display them"
  def __init__(self, projectName, questionsAndMaxesList, edxOutput=False, muteOutput=False):
    """
    Defines the grading scheme for a project
      projectName: project name
      questionsAndMaxesDict: a list of (question name, max points per question)
    """
    self.questions = [el[0] for el in questionsAndMaxesList]
    self.maxes = dict(questionsAndMaxesList)
    self.points = Counter()
    self.messages = dict([(q, []) for q in self.questions])
    self.project = projectName
    self.start = time.localtime()[1:6]
    self.sane = True # Sanity checks
    self.currentQuestion = None # Which question we're grading
    self.edxOutput = edxOutput
    self.mute = muteOutput
    
    #print 'Autograder transcript for %s' % self.project
    print 'Starting on %d-%d at %d:%02d:%02d' % self.start

  def grade(self, gradingModule, exceptionMap = {}):
    """
    Grades each question
      gradingModule: the module with all the grading functions (pass in with sys.modules[__name__])
    """
    
    for q in self.questions:
      print '\nQuestion %s' % q
      print '=' * (9 + len(q))
      self.currentQuestion = q
      
      if self.mute: mutePrint()
      try:
        TimeoutFunction(getattr(gradingModule, q),120)(self) # Call the question's function
        #TimeoutFunction(getattr(gradingModule, q),1200)(self) # Call the question's function
      except Exception, inst:
        print 'Error on question %s' % str(inst)

        msg = self.getExceptionMessage(q, inst, traceback)
        msg += self.getErrorHints(exceptionMap, inst, q[1])

        self.fail(msg, raw=True)
      except:
        self.fail('Question %s terminated with a string exception.' % q)
      finally:
        if self.mute: unmutePrint()
        
      print '\n### Question %s: %d/%d ###\n' % (q, self.points[q], self.maxes[q])
        

    print '\nFinished at %d:%02d:%02d' % time.localtime()[3:6]
    print "\nProvisional grades\n=================="
    
    for q in self.questions:
      print 'Question %s: %d/%d' % (q, self.points[q], self.maxes[q])
    print '------------------'
    print 'Total: %d/%d' % (self.points.totalCount(), sum(self.maxes.values()))
    print """
Your grades are NOT yet registered.  To register your grades you must
submit your files to the edX website.  The grades obtained through the
edX website are your final grades unless your submission was not in
the spirit of the course,  such as if your submission simply hardcoded
the answers to the tests.   We will screen for this after the deadline.

*If you worked with a partner, you must both submit separately.*
"""
    
    if self.edxOutput:
        self.produceOutput()

  def getExceptionMessage(self, q, inst, traceback):
    """
    Method to format the exception message, this is more complicated because
    we need to cgi.escape the traceback but wrap the exception in a <pre> tag
    """
    msg = """
<h4>
    Question {q} terminated with exception: {exception}
</h4>
<pre>
{traceback}
</pre>
    """.format(
        q=q,
        exception=cgi.escape(str(inst)),
        traceback=cgi.escape(traceback.format_exc())
    )
    return msg

  def getErrorHints(self, exceptionMap, errorInstance, questionNum):
    typeOf = str(type(errorInstance))
    questionName = 'q' + questionNum
    errorHint = ''

    # question specific error hints
    if exceptionMap.get(questionName):
      questionMap = exceptionMap.get(questionName)
      if (questionMap.get(typeOf)):
        errorHint = questionMap.get(typeOf)
    # fall back to general error messages if a question specific
    # one does not exist
    if (exceptionMap.get(typeOf)):
      errorHint = exceptionMap.get(typeOf)

    # dont include the HTML if we have no error hint
    if not errorHint:
      return ''

    return """\n
      <div class="errorHint">
        {hint}
      </div>
    \n
    """.format(hint = errorHint)

  def produceOutput(self):
    edxOutput = open('edx_response.html', 'w')
    edxOutput.write("<div>")

    # first sum
    total_possible = sum(self.maxes.values())
    total_score = sum(self.points.values())
    checkOrX = '<span class="incorrect"/>'
    if (total_score >= total_possible):
        checkOrX = '<span class="correct"/>'
    header = """
        <h3>
            Total score ({total_score} / {total_possible})
        </h3>
    """.format(total_score = total_score,
      total_possible = total_possible,
      checkOrX = checkOrX
    )
    edxOutput.write(header)

    for q in self.questions:
      if len(q) == 2:
          name = q[1]
      else: 
          name = q
      checkOrX = '<span class="incorrect"/>'
      if (self.points[q] == self.maxes[q]):
        checkOrX = '<span class="correct"/>'
      messages = '\n<br/>\n'.join(self.messages[q])
      output = """
        <div class="test">
          <section>
          <div class="shortform">
            Question {q} ({points}/{max}) {checkOrX}
          </div>
        <div class="longform">
          {messages}
        </div>
        </section>
      </div>
      """.format(q = name,
        max = self.maxes[q],
        messages = messages,
        checkOrX = checkOrX,
        points = self.points[q]
      )
      # print "*** output for Question %s " % q[1]
      # print output
      edxOutput.write(output)
    edxOutput.write("</div>")
    edxOutput.close()
    edxOutput = open('edx_grade', 'w')
    edxOutput.write(str(self.points.totalCount()))
    edxOutput.close()

  def fail(self, message, raw=False):
    "Sets sanity check bit to false and outputs a message"
    self.sane = False
    self.assignZeroCredit()
    self.addMessage(message, raw)

  def assignZeroCredit(self):
    self.points[self.currentQuestion] = 0
  
  def addPoints(self, amt):
    self.points[self.currentQuestion] += amt

  def deductPoints(self, amt):
    self.points[self.currentQuestion] -= amt

  def assignFullCredit(self, message="", raw=False):
    self.points[self.currentQuestion] = self.maxes[self.currentQuestion]
    if message != "":
      self.addMessage(message, raw)

  def addErrorMessage(self, message):
    self.addMessage("""
      <div class="errorHint">
        {message}
      </div>
    """.format(message=cgi.escape(message)), raw=True)

  def addMessage(self, message, raw=False):
    if self.mute: unmutePrint()      
    print '*** ' + message
    if self.mute: mutePrint()
    if not raw:
        message = cgi.escape(message)
    self.messages[self.currentQuestion].append(message)

  # TODO: don't need this distinction anymore?
  def addSecretMessage(self, message, raw=False):
    self.addMessage(message, raw=raw)
    # if self.mute: unmutePrint()      
    # print '$$$ ' + message 
    # if self.mute: mutePrint()

  def addMessageToEmail(self, message):
    print "WARNING**** addMessageToEmail is deprecated %s" % message
    for line in message.split('\n'):
      pass
      #print '%%% ' + line + ' %%%'
      #self.messages[self.currentQuestion].append(line)





class Counter(dict):
  """
  Dict with default 0
  """
  def __getitem__(self, idx):
    try:
      return dict.__getitem__(self, idx)
    except KeyError:
      return 0

  def totalCount(self):
    """
    Returns the sum of counts for all keys.
    """
    return sum(self.values())

