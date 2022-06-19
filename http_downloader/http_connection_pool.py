import http.client
import collections
import threading

class HTTPConnectionPool:
    def __init__(self, host, conn_num=20):
        self.conns = collections.deque(http.client.HTTPConnection(host, timeout=5) for i in range(conn_num))
        self.cv = threading.Condition()
        self.cond = lambda: bool(self.conns)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def getconn(self):
        with self.cv:
            self.cv.wait_for(self.cond)
            conn = self.conns.popleft()
        return conn

    def returnconn(self, conn):
        with self.cv:
            self.conns.append(conn)
            self.cv.notify()

    def close(self):
        for conn in self.conns:
            conn.close()
