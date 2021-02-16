import unittest, time, os, subprocess
from browserstack.local import Local, BrowserStackLocalError

class TestLocal(unittest.TestCase):
  def setUp(self):
    self.local = Local(os.environ['BROWSERSTACK_ACCESS_KEY'])

  def tearDown(self):
    self.local.stop()

  def test_start_local(self):
    self.local.start()
    self.assertNotEqual(self.local.proc.pid, 0)

  def test_running(self):
    self.assertFalse(self.local.isRunning())
    self.local.start()
    self.assertTrue(self.local.isRunning())

  def test_multiple(self):
    self.assertFalse(self.local.isRunning())
    self.local.start()
    self.assertTrue(self.local.isRunning())
    try:
      self.local2 = Local(os.environ['BROWSERSTACK_ACCESS_KEY'])
      self.local2.start()
    except BrowserStackLocalError as e:
      self.assertIn("Either another browserstack local client is running on your machine or some server is listening on port", str(e))

  def test_verbose(self):
    self.local.start({'v':True, 'only-command':True})
    self.assertIn('-v', self.local._generate_cmd())

  def test_local_folder(self):
    self.local.start({'f':'hello', 'only-command':True})
    self.assertIn('-f', self.local._generate_cmd())
    self.assertIn('hello', self.local._generate_cmd())

  def test_force_kill(self):
    self.local.start(force=True, onlyCommand=True)
    self.assertIn('--force', self.local._generate_cmd())

  def test_only_automate(self):
    self.local.start(onlyAutomate=True, onlyCommand=True)
    self.assertIn('--only-automate', self.local._generate_cmd())

  def test_force_local(self):
    self.local.start(forceLocal=True, onlyCommand=True)
    self.assertIn('--force-local', self.local._generate_cmd())

  def test_custom_boolean_argument(self):
    self.local.start(boolArg1=True, boolArg2=True, onlyCommand=True)
    self.assertIn('--bool-arg1', self.local._generate_cmd())
    self.assertIn('--bool-arg2', self.local._generate_cmd())

  def test_custom_keyval(self):
    self.local.start(customKey1="custom value1", customKey2="custom value2", onlyCommand=True)
    self.assertIn('--custom-key1', self.local._generate_cmd())
    self.assertIn('custom value1', self.local._generate_cmd())
    self.assertIn('--custom-key2', self.local._generate_cmd())
    self.assertIn('custom value2', self.local._generate_cmd())

  def test_proxy(self):
    self.local.start(proxyHost='localhost', proxyPort=2000, proxyUser='hello', proxyPass='test123', onlyCommand=True)
    self.assertIn('--proxy-host', self.local._generate_cmd())
    self.assertIn('localhost', self.local._generate_cmd())
    self.assertIn('--proxy-port', self.local._generate_cmd())
    self.assertIn('2000', self.local._generate_cmd())
    self.assertIn('--proxy-user', self.local._generate_cmd())
    self.assertIn('hello', self.local._generate_cmd())
    self.assertIn('--proxy-pass', self.local._generate_cmd())
    self.assertIn('test123', self.local._generate_cmd())

  def test_force_proxy(self):
    self.local.start(forceProxy=True, onlyCommand=True)
    self.assertIn('--force-proxy', self.local._generate_cmd())

  def test_local_identifier(self):
    self.local.start(localIdentifier='mytunnel', onlyCommand=True)
    self.assertIn('--local-identifier', self.local._generate_cmd())
    self.assertIn('mytunnel', self.local._generate_cmd())

  def test_context_manager(self):
    with Local('BROWSERSTACK_ACCESS_KEY') as local:
      self.assertNotEqual(local.proc.pid, 0)
      time.sleep(5)
