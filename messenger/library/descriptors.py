"""
descriptors for the project
"""
from ipaddress import ip_address
import portion as p


class ApprovedPort:
    """
    descriptor for port number
    """

    def __set_name__(self, owner_class, property_name):
        self.property_name = property_name
        self.port_range = p.open(1024, 65535)

    def __set__(self, instance, port: int):
        try:
            cp = int(port)
        except ValueError as value_is_not_recognised:
            raise ValueError(f'Supposed port cannot be recognized, passed {type(port).__name__}, '
                             f'should be int or str(int)') from value_is_not_recognised
        else:
            if cp not in self.port_range:
                raise ValueError('Supposed port is out if available range 1024 - 65535')
            instance.__dict__[self.property_name] = cp

    def __get__(self, instance, owner):
        if instance is None:
            return 'Called from class'
        return instance.__dict__.get(self.property_name)


class IpValidation:
    """
    descriptor for checking IP
    """

    def __set_name__(self, owner, property_name):
        self.property_name = property_name

    def __set__(self, instance, value):
        if not value:
            instance.__dict__[self.property_name] = '127.0.0.1'
        else:
            try:
                ip_address(value)
            except ValueError as ip_is_not_recognized:
                raise ValueError(f'Supposed ip {value} seems to be not an ip-address') from \
                    ip_is_not_recognized
            else:
                instance.__dict__[self.property_name] = value

    def __get__(self, instance, owner):
        if instance is None:
            return 'Called from class'
        return instance.__dict__.get(self.property_name)


class Server:
    port = ApprovedPort()
    my_ip = IpValidation()


s = Server()
