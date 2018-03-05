from hiredis import Reader, ReplyError

STR = b'$%d\r\n%b\r\n'
RAW = b'%b'


def len_pair(name):
    return ['len({})'.format(name), name]


def len_cnv_pair(name):
    return ['len({}_cnv)'.format(name), '{}_cnv'.format(name)]


def raw_fmt_arg(name):
    return ['{}_cnv'.format(name)]


def cnv_int(name):
    return '{0}_cnv = b"%d" % {0}'.format(name)


def cnv_str(name):
    return '{0}_cnv = {0}.encode()'.format(name)


def cnv_float(name):
    return '{0}_cnv = b"%f" % {0}'.format(name)


def cnv_bytes_list(name):
    return r'{0}_cnv = b"".join(b"$%d\r\n%b\r\n" % (len(r), r) for r in {0})'.format(name)


def static_str(data):
    data = data.encode()
    return STR % (len(data), data), False, None


def static_bytes(data):
    return STR % (len(data), data), False, None


def static_int(data):
    data = str(data).encode()
    return STR % (len(data), data), False, None


def static_float(data):
    data = b'%f' % data
    return STR % (len(data), data), False, None


TYPES = {
    bytes: (STR, len_pair, None),
    str: (STR, len_cnv_pair, cnv_str),
    int: (STR, len_cnv_pair, cnv_int),
    float: (STR, len_cnv_pair, cnv_float),
    (list, bytes): (RAW, raw_fmt_arg, cnv_bytes_list),
}

INSTANCES = {
    bytes: static_bytes,
    str: static_str,
    int: static_int,
    float: static_float,
}


def compile(*args):
    input_args = []
    cnv = []
    if type(args[-1]) is list:
        fmt_args = ['{} + len(vargs)'.format(len(args) - 1)]
        fmt = b'*%d\r\n'
    else:
        fmt_args = []
        fmt = b'*%d\r\n' % len(args)

    for i, a in enumerate(args):
        if type(a) is type:
            aname = 'arg{}'.format(i)
            tpl, nfn, cfn = TYPES[a]
        elif type(a) is list:
            aname = 'vargs'
            tpl, nfn, cfn = TYPES[(list, a[0])]
        else:
            aname = 'arg{}'.format(i)
            tpl, nfn, cfn = INSTANCES[type(a)](a)

        if nfn:
            input_args.append(aname)
            fmt_args.extend(nfn(aname))

        if cfn:
            cnv.append(cfn(aname))

        fmt += tpl

    ctx = {}

    body = ('def __fn({args}):\n'
            '    {cnv}\n'
            '    return {fmt} % ({fmt_args})')

    code = body.format(args=', '.join(input_args),
                       cnv='; '.join(cnv),
                       fmt=repr(fmt),
                       fmt_args=', '.join(fmt_args))

    exec(code, ctx, ctx)
    return ctx['__fn']


class RedisError(Exception):
    def __init__(self, msg, cmd):
        super().__init__('{}: {}'.format(msg, cmd))


def execute(commands, client=None, sock=None, fail=True):
    assert client or sock, 'client or sock is required'

    if client:
        conn = client.connection_pool.get_connection('MULTI')
        conn.send_packed_command([b''.join(commands)])
        sock = conn._sock
    else:
        sock.sendall(b''.join(commands))

    try:
        errors = []
        cnt = len(commands)
        reader = Reader()
        while cnt > 0:
            data = sock.recv(16384)
            if not data:
                break  # pragma: no cover

            reader.feed(data)
            while True:
                r = reader.gets()
                if r is False:
                    break
                if type(r) is ReplyError:
                    errors.append((str(r), parse_cmd(commands[len(commands) - cnt])))
                cnt -= 1
    finally:
        client and client.connection_pool.release(conn)

    if errors and fail:
        raise RedisError(*errors[0])

    return errors


def parse_cmd(data):
    result = []
    pos = 0
    while True:
        len_start = data.find(b'\r\n$', pos)
        if len_start < 0:
            break
        len_start += 3

        len_end = data.find(b'\r\n', len_start)
        if len_end < 0:
            break  # pragma: no cover
        length = int(data[len_start:len_end])
        str_start = len_end + 2
        result.append(data[str_start:str_start + length])
        pos = str_start + length

    return b' '.join(result)
