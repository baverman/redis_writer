redis_writer
============

|travis| |coverage| |pyver|

.. |travis| image:: https://travis-ci.org/baverman/redis_writer.svg?branch=master
   :target: https://travis-ci.org/baverman/redis_writer

.. |coverage| image:: https://img.shields.io/badge/coverage-100%25-brightgreen.svg

.. |pyver| image:: https://img.shields.io/badge/python-3.5%2C_3.6-blue.svg

A fast serializer to pipeline data into redis:

.. code:: python

   from redis import StrictRedis
   import redis_writer as rw

   rset = rw.compile('SET', bytes, int)
   rw.execute([rset(b'key%d' % r, r) for r in range(1000)],
              client=StrictRedis())
