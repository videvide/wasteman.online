## Running the application

- [Create a Stripe account](https://dashboard.stripe.com/register)
- Clone the project and install the dependencies
- Set the necessary environment variables from .dummy.env
- Use the shell to create a superuser with strong password
- uv run python manage.py collectstatic
- Start the gunicorn process
- Reverse proxy to gunicorn process 
- Point to static and media root
- Login to /admin with superuser to add posters and paintings


## Make 

- Make sure edit the makefile env_file_path to the existing path.................
- Make sure to set all variables in environment 
  - including hostname, gunicorn_port, and static/media paths...
- Make sure that Caddyfile have all the stuff
- Make sure all processes runs
- If something fails make sure to check permissions on all files 