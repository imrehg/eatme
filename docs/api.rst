EatMe API
=========

Registering a new user
----------------------


See the documentation of the `/api/v1/users <#post--api-v1-users>`_ endpoint for info.

Logging in
----------

.. http:post:: /login

   **Example login request:**

   .. sourcecode:: http

      POST /login HTTP/1.0
      Content-Type: application/json

      {
         "email": "user@example.com",
         "password": "secret"
      }

   **Example login response:**

   .. sourcecode:: http

      HTTP/1.0 200 OK
      Content-Type: application/json
      Content-Length: 215
      Set-Cookie: session=.eJwlzjEOwzAIQNG7MGfAxmA7l4kAg9o1aaaqd2-lrv8t_w1HnnE9YH-dd2xwPBfs0AwlyYwXT5tIXZy9U5Zi1edAch9VRWOJNV_lh78sNJbOLJKqGiHcU2drDckwVRY3wgjsSZy1MpYQ9DpbROdOMVRY-qK0CRvcV5z_mQqfL7_IL0c.CffhAg.5HqFMNa2R1qxZoYRFXv7-VZznaE; HttpOnly; Path=/
      Server: Werkzeug/0.11.8 Python/3.5.1
      Date: Tue, 19 Apr 2016 15:32:18 GMT

      {
        "meta": {
          "code": 200
        },
        "response": {
          "user": {
            "authentication_token": "WyIyIiwiYTc2OWNkN2Q3ZTc0Mzg1NzkyYWEyMmQwMDlhNGFjZDAiXQ.CffhAg.wG9FzRpOxHBZmijWAUEf0jSc12g",
            "id": "2"
          }
        }
      }

Logging out
-----------

.. http:get:: /logout

   **Example logout request:**

   .. sourcecode:: http

      GET /logout HTTP/1.0
      Authorization: TOKEN

   **Example logout response:**

   .. sourcecode:: http

      HTTP/1.0 302 FOUND

   Redirection to the front page, can safely ignore it. The specific authorization token or session cookie will
   be invalidated.

API documentation
-----------------

.. autoflask:: eatme:app
:endpoints:
       :blueprints: api
       :undoc-endpoints: home
       :undoc-static:
