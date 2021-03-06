#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
 aspen.cgi : small script for invoking konoha
   chen_ji, shinpei_NKT, utrhira (C)2011

 version:
  0.0.7 : twitter authentication implemented (chen_ji)
'''

import aspendb
import bugreporter
import cgi
import cgitb; cgitb.enable()
import datetime
import json
import login
import os
import shutil
import signal
import subprocess
import sys
import time
import ConfigParser
import Cookie

class Alarm(Exception):
	pass

def alarm_handler(signum, frame):
	raise Alarm

class Aspen:
	uid = None

	def __init__(self):
		self.cookie = Cookie.SimpleCookie(os.environ.get('HTTP_COOKIE', ''))
		self.field = cgi.FieldStorage()
		self.time = datetime.datetime.now()
		self.method = os.environ['REQUEST_METHOD']
		self.lm = login.LoginManager()
		self.conf = ConfigParser.SafeConfigParser()
		self.conf.read('settings.ini')
		self.konohapath = self.conf.get('path', 'konoha')
		self.gitpath = self.conf.get('path', 'git')
		self.astorage = aspendb.AspenStorage()
		self.base = 'data'
		self.scriptdir = self.base + '/scripts'
		self.bugdir = self.base + '/bugs'
		self.tmpdir = self.base + '/tmp'

	def printText(self, text):
		print 'Content-Type: text/plain\n'
		sys.stdout.write(text)

	def deleteCookie(self, cookie_keys):
		cookie = Cookie.SimpleCookie()
		exptime = self.time + datetime.timedelta(days=-1)
		for key in cookie_keys:
			cookie[key] = ''
			cookie[key]['expires'] = exptime
			cookie[key]['path'] = '/'
		print cookie

	def saveCookie(self, cookies):
		cookie = Cookie.SimpleCookie()
		for c in cookies:
			cookie[c[0]] = c[1]
			cookie[c[0]]['path'] = '/'
		print cookie

	def loginWithTwitter(self):
		self.lm.getRequestToken()
		self.lm.redirectToProvider()

	def authWithSID(self):
		uid = self.astorage.getUID(self.cookie['SID'].value)
		if not uid:
			raise Exception('Failed to authenticate.')
		else:
			self.uid = uid


	def authWithSIDAndRenewSession(self):
		self.asession = self.astorage.authenticateWithSIDAndRenewSession(
				self.cookie['SID'].value)
		if self.asession == None:
			raise Exception('Failed to authenticate and renew.')

	def isSignal(self, r, sig):
		if os.path.isfile('/etc/debian_version'):
			# debian
			return r == 128 + sig
		else:
			# other linux and mac (ok?)
			return r == -sig

	# get current konoha revision
	def setKonohaRevision(self):
		command = 'svnversion %s' % self.konohapath
		p = subprocess.Popen(command,
				shell=True,
				stdout=subprocess.PIPE,
				close_fds=True)
		self.konoha_rev = p.communicate()[0].rstrip('\n')

	# get current aspen version from git hash
	def setAspenVersion(self):
		command = 'git --git-dir=%s log -1 --format="%%h"' % self.gitpath
		p = subprocess.Popen(command,
				shell=True,
				stdout=subprocess.PIPE,
				close_fds=True)
		self.aspen_ver = p.communicate()[0].rstrip('\n')

	# report a script that causes segv as a bug
	def reportBugs(self, body, result):
		br = bugreporter.BugReporter()
		br.setEnvironments(
				self.konoha_rev,
				self.aspen_ver,
				self.astorage.getScreenName(self.cookie['SID'].value),
				self.time)
		br.reportBugs(body, result)

	# store and evaluate current text
	def evalScript(self, filename, script):
		filepath = self.storeScript(filename, script)
		self.setKonohaRevision()
		self.setAspenVersion()
		# exec konoha as subprocess
		starttime = time.time()
		command = '/usr/local/bin/konoha -a ' + filepath
		p = subprocess.Popen(command, shell=True,
				stdin=subprocess.PIPE, stdout=subprocess.PIPE,
				stderr=subprocess.PIPE, close_fds=True)
		tmpdir = self.tmpdir + '/'
		outfilename = tmpdir + self.uid + '.out'
		errfilename = tmpdir + self.uid + '.err'
		# output result
		outfile = open(outfilename, 'w')
		errfile = open(errfilename, 'w')
		# set timeout
		signal.signal(signal.SIGALRM, alarm_handler)
		signal.alarm(3 * 60) # 3 minutes
		MAX_SIZE = 1024 * 50 # 50 KB
		try:
			size = 0
			while p.poll() == None:
				line = p.stdout.readline()
				while line:
					size += len(line)
					if size < MAX_SIZE:
						outfile.write(line)
						outfile.flush()
					else:
						raise Exception('too long output')
					line = p.stdout.readline()
			outfile.close()
			errfile = open(errfilename, 'w')
			errfile.write(p.stderr.read())
			errfile.close()
			signal.alarm(0)
		except Alarm:
			# timeout
			p.terminate()
			errfile = open(errfilename, 'a')
			errfile.write('Konoha was terminated because the program was running \
too long time (more than 3 minutes).')
			errfile.close()
		except Exception:
			p.terminate()
			errfile = open(errfilename, 'a')
			errfile.write('Konoha was terminated because the output text is \
too long (over 50 KB).')
			errfile.close()
		# check if process was killed with signal
		r = p.wait()
		exetime = float(time.time() - starttime)
		command = 'w'
		p = subprocess.Popen(command, shell=True,
				stdin=subprocess.PIPE, stdout=subprocess.PIPE,
				stderr=subprocess.PIPE, close_fds=True)
		loadline = p.stdout.readlines()[0]
		load = loadline[loadline.index('load'):-1]
		msg = ''
		if r == 0:
			#msg = 'Konoha exited normally. <br />'
			pass
		elif self.isSignal(r, signal.SIGSEGV):
			self.reportBugs(open(filepath, 'r').read(),
					'[stdout]\n' + open(outfilename, 'r').read() +
					'\n[stderr]\n' + open(errfilename, 'r').read())
			errfile = open(errfilename, 'a')
			errfile.write('Konoha exited unexpectedly. This script will be reported as \
a bug. Sorry.')
			errfile.close()

			# copy script to 'bugs' dir
			bugfoldername = self.bugdir + '/' + self.uid
			if not os.path.exists(bugfoldername):
				os.makedirs(bugfoldername)
			shutil.copy(filepath, bugfoldername)
		elif self.isSignal(r, signal.SIGTERM):
			pass
		elif self.isSignal(r, signal.SIGABRT):
			errfile = open(errfilename, 'a')
			errfile.write('Konoha aborted. Sorry.')
			errfile.close()
		else:
			errfile = open(errfilename, 'a')
			errfile.write('Konoha exited unexpectedly with signal: %d. Sorry.' % r)
			errfile.close()
		msg += 'time: %s\n' % str(exetime)[0:5]
		msg += '%s\n' % load
		msg += 'Konoha revision: %s\n' % self.konoha_rev
		msg += 'Aspen version hash: %s' % self.aspen_ver
		# return values as a json object
		print 'Content-Type: application/json;charset=UTF-8\n'
		print json.dumps({'item': [
			{'key': 'stderr', 'value': open(errfilename, 'r').read().decode('utf-8', 'replace')},
			{'key': 'stdout', 'value': open(outfilename, 'r').read().decode('utf-8', 'replace')},
			{'key': 'message', 'value': msg}
		]})

	def logoutWithTwitter(self):
		keys = ['SID']
		self.deleteCookie(keys)
		print

	def replyToRewind(self):
		fromsid = self.astorage.rewindSID(self.cookie['SID'].value)
		if fromsid != 'none' and fromsid != '':
			self.saveCookie([('SID', fromsid)])
			self.printScriptWithSID(sid=fromsid)
		else:
			self.printText('oldest')

	def replyToForward(self):
		tosid = self.astorage.forwardSID(self.cookie['SID'].value)
		if tosid is not '':
			self.saveCookie([('SID', tosid)])
			self.printScriptWithSID(sid=tosid)
		else:
			self.printText('latest')

	def new(self):
		self.saveCookie([('SID', self.asession.getSID())])
		self.printText('new')

	def name(self):
		fname = self.field.getvalue('filename')
		if not self.asession == None:
			nameSID(self.asession, fname)
		raise Exception('Failed to name a file.')

	# store current text as a file (named 'filename.k')
	def storeScript(self, filename, script):
		# create script dir
		foldername = self.scriptdir + '/' + self.uid
		if not os.path.exists(foldername):
			os.makedirs(foldername)
		# settle script filename
		filepath = foldername + '/' + filename
		# create script file
		scriptfile = open(filepath, 'w')
		scriptfile.write(script)
		scriptfile.close()
		return filepath

	def printScript(self, filename):
		dirname = self.scriptdir + '/' + self.uid
		filepath = dirname + '/' + str(filename)
		print 'Content-Type: text/plain\n'
		if os.path.isfile(filepath):
			sys.stdout.write(open(filepath, 'r').read())


	def printScriptWithSID(self, uid=None, sid=None):
		if uid == None:
			uid = self.uid
		if sid == None:
			sid = self.cookie['SID'].value
		foldername = self.scriptdir + '/' + uid
		filename = foldername + '/us_' + sid + '.k'
		print 'Content-Type: text/plain\n'
		if os.path.isfile(filename):
			sys.stdout.write(open(filename, 'r').read())

	def printFileList(self):
		userdir = self.scriptdir + '/' + self.uid
		ret = []
		for (root, dirs, files) in os.walk(userdir):
			ret.append(('/' + '/'.join(root.split('/')[3:]), dirs, files))
		print 'Content-Type: application/json;charset=UTF-8\n'
		print json.dumps({'item': ret})

def main():
	a = Aspen()
	mtype = a.field.getvalue('method')
	if a.method == 'POST':
		if mtype == 'eval':
			a.authWithSID()
			a.evalScript(a.field.getvalue('name'), a.field.getvalue('kscript'))
		elif mtype == 'name':
			a.authWithSID()
			a.name()
		elif mtype == 'login':
			a.loginWithTwitter()
		elif mtype == 'save':
			name = a.field.getvalue('name')
			a.authWithSID()
			a.storeScript(name, a.field.getvalue('kscript'))
			a.printText('Script "%s" was saved successfully.' % name);
		else:
			raise Exception('No such method in POST.')
	elif a.method == 'GET':
		if mtype == 'new':
			a.authWithSIDAndRenewSession()
			a.new()
		elif mtype == 'rewind':
			a.authWithSID()
			a.replyToRewind()
		elif mtype == 'forward':
			a.authWithSID()
			a.replyToForward()
		elif mtype == 'logout':
			a.logoutWithTwitter()
		elif mtype == 'load':
			a.authWithSID()
			a.printScript(a.field.getvalue('file'))
		elif mtype == 'getUID':
			a.authWithSID()
			a.printText(a.uid)
		elif mtype == 'open':
			a.authWithSID()
			a.printFileList()
		else:
			raise Exception('No such method in GET.')
	else:
		raise Exception('No such method.')

if __name__ == '__main__':
	main()
