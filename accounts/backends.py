import ssl
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend
from django.conf import settings

# Email Backend for Authentication
class EmailBackend(ModelBackend):
    def authenticate(self, request, username = None, password = None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None


# Custom SMTP Email Backend that handles SSL certificate issues
class CustomSMTPEmailBackend(DjangoEmailBackend):
    """
    Custom email backend that handles SSL certificate issues for development
    """
    
    def open(self):
        """
        Ensure we have a connection to the email server. Return whether or not a
        new connection was required (True or False).
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False

        # If local_hostname is not specified, socket.getfqdn() gets used.
        # For performance, we use the cached FQDN for local_hostname.
        connection_params = {'local_hostname': self.host}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        
        # Handle SSL configuration
        if self.use_ssl:
            # For SSL connections (port 465)
            if settings.DEBUG:
                # Create unverified SSL context for development
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                connection_params['context'] = context
            else:
                connection_params['context'] = ssl.create_default_context()
            
        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )

            # TLS/SSL are mutually exclusive, so only attempt TLS over
            # non-secure connections.
            if not self.use_ssl and self.use_tls:
                self.connection.ehlo()
                if settings.DEBUG:
                    # Use unverified context for TLS in development
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    self.connection.starttls(context=context)
                else:
                    self.connection.starttls(context=ssl.create_default_context())
                self.connection.ehlo()

            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except (ssl.SSLError, OSError) as e:
            if settings.DEBUG:
                print(f"Email SSL Error: {e}")
                print("Attempting connection with relaxed SSL verification...")
                
                # For development: create unverified SSL context
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                try:
                    connection_params['context'] = context
                    self.connection = self.connection_class(
                        self.host, self.port, **connection_params
                    )
                    
                    if not self.use_ssl and self.use_tls:
                        self.connection.ehlo()
                        self.connection.starttls(context=context)
                        self.connection.ehlo()

                    if self.username and self.password:
                        self.connection.login(self.username, self.password)
                    print("✅ Email connection successful with relaxed SSL")
                    return True
                except Exception as e2:
                    print(f"❌ Failed even with relaxed SSL: {e2}")
                    raise e2
            else:
                raise e