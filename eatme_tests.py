import os
import eatme
import unittest
import tempfile
from base64 import b64encode

class EatmeTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, eatme.app.config['DATABASE'] = tempfile.mkstemp()
        eatme.app.config['TESTING'] = True
        self.app = eatme.app.test_client()
        eatme.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(eatme.app.config['DATABASE'])

    def test_nologin(self):
        rv = self.app.get('/api/v1/users')
        assert b'Unauthorized Access' in rv.data

    def test_login(self):
        username, password = "admin", "allaccess"
        headers = {
            'Authorization': 'Basic ' + b64encode("{0}:{1}".format(username, password).encode('ascii')).decode('ascii')
        }
        rv = self.app.get('/api/v1/users', headers=headers)
        assert username.encode('ascii') in rv.data


if __name__ == '__main__':
    unittest.main()
