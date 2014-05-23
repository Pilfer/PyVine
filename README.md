PyVine
======

A simple Vine class written in Python using Requests.

#Usage:

1. Create Vine object
2. Authenticate
3. Make some requests

```python
vine = Vine()
if vine.login("username","password123") == True:
  print "We logged in! Our sessionId is %s" % vine.session_id
  #Do some other requests here
```

Alternatively you could save the vine.session_id and assign it directly so you don't have to send that extra request.

```python
vine = Vine()
vine.session_id = "yoloswag4jesus"
vine.someFunctionHere()
```

Note: This class uses requests and S3Auth. Both can be installed via pip.
