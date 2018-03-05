from redis import StrictRedis
import redis_writer as rw


class SocketMock:
    def __init__(self, *chunks):
        self.data = list(chunks)

    def sendall(self, data):
        pass

    def recv(self, size):
        return self.data.pop(0)


def test_cmd():
    cmd = rw.compile('SET', bytes, int)
    assert cmd(b'key', 10) == b'*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$2\r\n10\r\n'


def test_varg_cmd():
    cmd = rw.compile('SADD', bytes, [bytes])
    assert cmd(b'key', [b'v1', b'v2']) == b'*4\r\n$4\r\nSADD\r\n$3\r\nkey\r\n$2\r\nv1\r\n$2\r\nv2\r\n'


def test_types():
    assert rw.compile('CMD')() == b'*1\r\n$3\r\nCMD\r\n'
    assert rw.compile(b'CMD')() == b'*1\r\n$3\r\nCMD\r\n'
    assert rw.compile(2)() == b'*1\r\n$1\r\n2\r\n'
    assert rw.compile(2.5)() == b'*1\r\n$8\r\n2.500000\r\n'

    assert rw.compile(str)('CMD') == b'*1\r\n$3\r\nCMD\r\n'
    assert rw.compile(bytes)(b'CMD') == b'*1\r\n$3\r\nCMD\r\n'
    assert rw.compile(int)(2) == b'*1\r\n$1\r\n2\r\n'
    assert rw.compile(float)(2.5) == b'*1\r\n$8\r\n2.500000\r\n'


def test_execute():
    rclient = StrictRedis()
    rclient.delete('boo')
    rclient.delete('foo')

    cmd = rw.compile('SET', bytes, bytes)

    rw.execute([cmd(b'boo', b'bar'), cmd(b'foo', b'baz')], client=rclient)
    assert rclient.get('boo') == b'bar'
    assert rclient.get('foo') == b'baz'

    rw.execute([cmd(b'boo', b'bar1'), cmd(b'foo', b'baz1')],
               sock=rclient.connection_pool.get_connection('MULTI')._sock)
    assert rclient.get('boo') == b'bar1'
    assert rclient.get('foo') == b'baz1'


def test_big_chunk():
    rclient = StrictRedis()
    rclient.delete('boo')
    cmd = rw.compile('SET', bytes, bytes)
    chunk = [cmd(b'boo', b'boo') for _ in range(10000)]

    rw.execute(chunk, client=rclient)


def test_bulk_string_response():
    sock = SocketMock(b'$3\r\nboo\r\n', b'$-1\r\n', b'-ERR boo\r\n')
    cmd = rw.compile('SET', bytes, int)
    chunk = [cmd(b'boo', r) for r in range(3)]
    errors = rw.execute(chunk, sock=sock, fail=False)
    assert errors == [('ERR boo', b'SET boo 2')]


def test_truncated_response():
    sock = SocketMock(b'+OK\r\n', b'-Err', b' INVALID\r\n', b'+OK\r\n')
    cmd = rw.compile('SET', bytes, int)
    chunk = [cmd(b'boo', r) for r in range(3)]
    errors = rw.execute(chunk, sock=sock, fail=False)
    assert errors == [('Err INVALID', b'SET boo 1')]

    sock = SocketMock(b'+OK\r\n', b'-Err', b' INVALID\r\n', b'+OK\r\n')
    try:
        rw.execute(chunk, sock=sock)
    except rw.RedisError as e:
        assert str(e) == "Err INVALID: b'SET boo 1'"
