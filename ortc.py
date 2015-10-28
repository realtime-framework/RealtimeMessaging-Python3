"""ORTC Python API."""

__author__      = "framework@realtime.co"
__copyright__   = "Copyright 2015, Realtime "


import http.client
import re
import random
import string
import time
import threading
import websocket
import json
import threading
from ortc_extensibility import *

MAX_CONNECTION_METADATA_SIZE = 255
MAX_CHANNEL_NAME_SIZE = 100
MAX_MESSAGE_SIZE = 800
MAX_HEARTBEAT_INTERVAL = 30
RECONNECT_INTERVAL = 5
REST_TIMEOUT = 5

states = Private._enum_state(DISCONNECTED=0, CONNECTED=1, CONNECTING=2, RECONNECTING=3, DISCONNECTING=4)

def save_authentication(url, is_cluster, authentication_token, is_private, application_key, time_to_live, private_key, channels_permissions, callback):
    '''Saves the channel and its permissions for the supplied application key and authentication token.

    **Note:** This method will send your Private Key over the Internet. Make sure to use secure connection.

    * *url* - The ORTC server URL.
    * *is_cluster* - Indicates whether the ORTC server is in a cluster.
    * *authentication_token* - The authentication token generated by an application server (for instance: a unique session ID).
    * *is_private* - Indicates whether the authentication token is private.
    * *application_key* - The application key provided when the ORTC service is purchased.
    * *time_to_live* - The authentication token time to live (TTL), in other words, the allowed activity time (in seconds).
    * *private_key* - The private key provided when the ORTC service is purchased.
    * *channels_permissions* - The dictionary containing  channels and their permissions (read or write).
    * *callback* - The callback raised after save authentication have been performed.

    Returns boolean- Indicates whether the authentication was successful.

    Usage:

    >>> def save_authentication_callback(error, result):
    >>>     if result:
    >>>         print 'ORTC Save Authentication success'
    >>>     else:
    >>>         print 'ORTC Save Authentication Error: ' + str(error)
    >>> channels_permissions = {}
    >>> channels_permissions['blue'] = 'r'
    >>> channels_permissions['yellow'] = 'w'
    >>> ortc.save_authentication('https://ortc-developers.realtime.co/server/ssl/2.1', True, 'Your authentication token', False, 'Your application key', 1800, 'Your private key', channels_permissions, save_authentication_callback)
    '''
    if not isinstance(channels_permissions, dict):
        raise OrtcError('Invalid channels permissions')
    post_str = 'AT='+authentication_token+'&AK='+application_key+'&PK='+private_key+'&TTL='+str(time_to_live)+'&PVT='+('1' if is_private==True else '0')+'&TP='+str(len(channels_permissions))
    for k,v in channels_permissions.iteritems():
        if not re.compile('^[\w\-:\/.]+$').match(k):
            raise OrtcError('Invalid channel name: '+k)
        post_str += '&'+k+'='+v
    server = Private._get_cluster(url, application_key) if is_cluster else url
    if server == None:
        raise OrtcError('Error getting server from Cluster')
    server += '/authenticate' if not server[-1] == '/' else 'authenticate'
    def p_thread():
        try:
            from urllib.parse import urlparse
            uri = urlparse(server)
            headers = {}
            headers['User-Agent'] = 'OrtcPythonApi'
            headers['Connection'] = 'keep-alive'
            headers['Content-Length'] = len(post_str)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            conn = httplib.HTTPSConnection(uri.netloc, timeout=REST_TIMEOUT)
            conn.request("POST", uri.path, None, headers)
            conn.send(post_str)
            res = conn.getresponse()
            if res.status == 201:
                callback(None, True)
            else:
                callback(res.read(), False)
        except Exception as e:
            callback(e, False)
    t = threading.Thread(target=p_thread)
    t.setDaemon(True)
    t.start()

def save_authentication(url, is_cluster, authentication_token, is_private, application_key, time_to_live, private_key, channels_permissions):
    '''Saves the channel and its permissions for the supplied application key and authentication token.

    * *url* - The ORTC server URL.
    * *is_cluster* - Indicates whether the ORTC server is in a cluster.
    * *authentication_token* - The authentication token generated by an application server (for instance: a unique session ID).
    * *is_private* - Indicates whether the authentication token is private.
    * *application_key* - The application key provided when the ORTC service is purchased.
    * *time_to_live* - The authentication token time to live (TTL), in other words, the allowed activity time (in seconds).
    * *private_key* - The private key provided when the ORTC service is purchased.
    * *channels_permissions* - The dictionary containing  channels and their permissions (read or write).

    Returns boolean- Indicates whether the authentication was successful.

    Usage:

    >>> channels_permissions = {}
    >>> channels_permissions['blue'] = 'r'
    >>> channels_permissions['yellow'] = 'w'
    >>> r = ortc.save_authentication('https://ortc-developers.realtime.co/server/ssl/2.1', True, 'Your authentication token', False, 'Your application key', 1800, 'Your private key', channels_permissions)
    >>> print 'Success' if r==True else 'Failed'
    Success
    '''
    if not isinstance(channels_permissions, dict):
        raise OrtcError('Invalid channels permissions')
    post_str = 'AT='+authentication_token+'&AK='+application_key+'&PK='+private_key+'&TTL='+str(time_to_live)+'&PVT='+('1' if is_private==True else '0')+'&TP='+str(len(channels_permissions))
    for k,v in channels_permissions.items():
        if not re.compile('^[\w\-:\/.]+$').match(k):
            raise OrtcError('Invalid channel name: '+k)
        post_str += '&'+k+'='+v
    server = Private._get_cluster(url, application_key) if is_cluster else url
    if server == None:
        raise OrtcError('Error getting server from Cluster')
    server += '/authenticate' if not server[-1] == '/' else 'authenticate'
    from urllib.parse import urlparse
    uri = urlparse(server)
    headers = {}
    headers['User-Agent'] = 'OrtcPythonApi'
    headers['Connection'] = 'keep-alive'
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    conn = http.client.HTTPSConnection(uri.netloc, timeout=REST_TIMEOUT)
    conn.request("POST", uri.path, post_str, headers)
    res = conn.getresponse()
    if res.status == 201:
        return True
    else:
        return False

def presence(url, is_cluster, application_key, authentication_token, channel, callback):
    '''Gets a dictionary indicating the subscriptions number in the specified channel and if active the first 100 unique metadata.
    * *url* - The ORTC server URL.
    * *is_cluster* - Indicates whether the ORTC server is in a cluster.
    * *application_key* - The application key provided when the ORTC service is purchased.
    * *authentication_token* - The authentication token generated by an application server (for instance: a unique session ID).
    * *channel* - The channel name with presence data active.
    * *callback* - The callback with error and result parameters.

    Usage:

    >>> def presence_callback(error, result):
    >>>     if not error == None:
    >>>         print 'ORTC Presence error: ' + error
    >>>     else:
    >>>         print str(result)
    >>> ortc.presence('http://ortc-developers.realtime.co/server/2.1', True, 'Your application key', 'Your authentication token', 'blue', presence_callback)
    '''
    server = Private._prepare_server(url, is_cluster, application_key, callback)
    if server == None: return
    presence_url = server+'presence/'+application_key+'/'+authentication_token+'/'+channel
    def p_thread():
        try:
            from urllib.parse import urlparse
            uri = urlparse(presence_url)
            conn = httplib.HTTPSConnection(uri.netloc, timeout=REST_TIMEOUT)
            conn.request("GET", uri.path)
            res = conn.getresponse()
            if res.status==200:
                callback(None, json.loads(res.read()))
            else:
                callback(str(res.status), None)
        except Exception as e:
            callback(str(e), None)
    t = threading.Thread(target=p_thread)
    t.setDaemon(True)
    t.start()

def enable_presence(url, is_cluster, application_key, private_key, channel, metadata, callback):
    '''Enables presence for the specified channel with first 100 unique metadata if true.

    **Note:** This method will send your Private Key over the Internet. Make sure to use secure connection.

    * *url* - The ORTC server URL.
    * *is_cluster* - Indicates whether the ORTC server is in a cluster.
    * *application_key* - The application key provided when the ORTC service is purchased.
    * *private_key* - The private key provided when the ORTC service is purchased.
    * *channel* - The channel name to activate presence.
    * *metadata* - Defines if to collect first 100 unique metadata (boolean).
    * *callback* - The callback with error and result parameters.

    Usage:

    >>> def presence_callback(error, result):
    >>>     if not error == None:
    >>>         print 'ORTC Presence error: ' + error
    >>>     else:
    >>>         print str(result)
    >>> ortc.enable_presence('http://ortc-developers.realtime.co/server/2.1', True, 'Your application key', 'Your private key', 'blue', True, presence_callback)
    '''
    server = Private._prepare_server(url, is_cluster, application_key, callback)
    if server == None: return
    presence_url = server+'presence/enable/'+application_key+'/'+channel
    content = 'privatekey='+private_key+ ('&metadata=1' if metadata else '&metadata=0')
    Private._rest_post_request(presence_url, content, callback)

def disable_presence(url, is_cluster, application_key, private_key, channel, callback):
    '''Disables presence for the specified channel.

    **Note:** This method will send your Private Key over the Internet. Make sure to use secure connection.

    * *url* - The ORTC server URL.
    * *is_cluster* - Indicates whether the ORTC server is in a cluster.
    * *application_key* - The application key provided when the ORTC service is purchased.
    * *private_key* - The private key provided when the ORTC service is purchased.
    * *channel* - The channel name to disable presence.
    * *callback* - The callback with error and result parameters.

    Usage:

    >>> def presence_callback(error, result):
    >>>     if not error == None:
    >>>         print 'ORTC Presence error: ' + error
    >>>     else:
    >>>         print str(result)
    >>> ortc.disable_presence('http://ortc-developers.realtime.co/server/2.1', True, 'Your application key', 'Your private key', 'blue', presence_callback)
    '''
    server = Private._prepare_server(url, is_cluster, application_key, callback)
    if server == None: return
    presence_url = server+'presence/disable/'+application_key+'/'+channel
    content = 'privatekey='+private_key
    Private._rest_post_request(presence_url, content, callback)


class OrtcClient(object):
    """A class representing an ORTC Client"""

    @property
    def announcement_subchannel(self):
        '''The client announcement subchannel

        Usage:

        >>> ortc_client.announcement_subchannel = 'announcement_subchannel'
        '''
        return self._announcement_subchannel
    @announcement_subchannel.setter
    def announcement_subchannel(self, announcement_subchannel):
        self._announcement_subchannel = announcement_subchannel

    @property
    def connection_metadata(self):
        '''The client connection metadata

        Usage:

        >>> ortc_client.connection_metadata = 'My metadata'
        '''
        return self._connection_metadata
    @connection_metadata.setter
    def connection_metadata(self, connection_metadata):
        self._connection_metadata = connection_metadata

    @property
    def is_connected(self):
        '''Indicates whether the client is connected (read only)

        Usage:

        >>> ortc_client.is_connected
        False
        '''
        return True if self._state == states.CONNECTED else False

    @property
    def url(self):
        '''The server URL

        Usage:

        >>> ortc_client.url = "https://ortc-developers-euwest1-S0001.realtime.co:443"
        '''
        return self._url
    @url.setter
    def url(self, url):
        self._url = url

    @property
    def cluster_url(self):
        '''The cluster server URL

        Usage:

        >>> ortc_client.cluster_url = "https://ortc-developers.realtime.co/server/ssl/2.1"
        '''
        return self._cluster_url
    @cluster_url.setter
    def cluster_url(self, cluster_url):
        self._cluster_url = cluster_url

    @property
    def session_id(self):
        '''The client session identifier (read only)

        Usage:

        >>> print ortc_client.session_id
        4RtV2sq0
        '''
        return self._session_id

    def __init__(self):
        self.app_key = None
        self.auth_token = None
        self._announcement_subchannel = ''
        self._connection_metadata = ''
        self._state = states.DISCONNECTED
        self._url = None
        self._cluster_url = None
        self._session_id = None
        self._permissions = {}
        self._channels = {}
        self._ws = None
        self._messages_buffer = {}
        self.heartbeat_timer = None
        self.reconnecting_thread = None
        self.heartbeat_thread = None
        self.got_heartbeat = False
        self.keep_running = True

    def connect(self, application_key, authentication_token='PM.Anonymous'):
        '''Connects the client using the supplied application key and authentication token.

        * *application_key* - Your ORTC application key.
        * *authentication_token* - Your ORTC authentication token, this parameter is optional.

        Usage:

        >>> import ortc
        >>> ortc_client = ortc.OrtcClient()
        >>> ortc_client.connect('Your application key', 'Your authentication token')
        '''
        self.app_key = application_key
        self.auth_token = authentication_token
        if self.is_connected:
            Private._call_exception_callback(self, 'Already connected')
        elif self._state == states.CONNECTING:
            Private._call_exception_callback(self, 'Already trying to connect')
        elif not isinstance(self.app_key, str) or len(self.app_key)<1:
            Private._call_exception_callback(self, 'Wrong Application Key')
        elif self.url == None and self.cluster_url == None:
            Private._call_exception_callback(self, 'URL and Cluster URL are null or empty')
        elif not self.url == None and not Private._validate_url(self.url):
            Private._call_exception_callback(self, 'Invalid URL')
        elif not self.cluster_url == None and not Private._validate_url(self.cluster_url):
            Private._call_exception_callback(self, 'Invalid Cluster URL')
        elif not Private._validate_input(self.app_key):
            Private._call_exception_callback(self, 'Application Key has invalid characters')
        elif not Private._validate_input(self.auth_token):
            Private._call_exception_callback(self, 'Authentication Token has invalid characters')
        elif not self.announcement_subchannel == None and not Private._validate_input(self.announcement_subchannel):
            Private._call_exception_callback(self, 'Announcement Subchannel has invalid characters')
        elif len(self.connection_metadata) > MAX_CONNECTION_METADATA_SIZE:
            exception_message = 'Metadata exceeds the limit of '+ str(MAX_CONNECTION_METADATA_SIZE) + ' bytes'
            Private._call_exception_callback(self, exception_message)
        else:
            if not self._state == states.RECONNECTING:
                self._state = states.CONNECTING
            server = Private._get_cluster(self.cluster_url, self.app_key) if not self.cluster_url == None else self.url
            if server == None:
                if not self._state == states.RECONNECTING:
                    self._state = states.DISCONNECTED
                Private._call_exception_callback(self, 'Host is not reachable')
                print("Not reachable")
                return None

            rand_str = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(8))
            self._session_id = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(16))
            from random import randint
            ws_url = 'ws'+server[4:]+'/broadcast/'+str(randint(0,1000))+'/'+rand_str+'/websocket'
            self.keep_running = True
            from websocket import create_connection
            self._ws = create_connection(ws_url)
            def runloop():
                while self.keep_running:
                    try:
                        r = self._ws.recv()
                        self._on_message(self._ws, r)
                    except Exception as e:
                        print(e)
                        pass
            self.main_loop = threading.Thread(target=runloop)
            self.main_loop.setDaemon(True)
            self.main_loop.start()

    def disconnect(self):
        '''Disconnects the client.

        Usage:

        >>> ortc_client.disconnect()
        '''
        if not self.is_connected and not self._state==states.RECONNECTING:
            Private._call_exception_callback(self, 'Not connected')
            return
        self._channels.clear()
        self._state=states.DISCONNECTING
        self.monit_heartbeat = False
        self.keep_running = False
        self._ws.close()
        if self.on_disconnected_callback:
            self.on_disconnected_callback(self)

    def is_subscribed(self, channel):
        '''Indicates whether the client is subscribed to the supplied channel.

        * *channel* - The channel name.

        Returns *boolean* - Indicates whether the client is subscribed to the supplied channel.

        Usage:

        >>> print ortc_client.is_subscribed('blue')
        True

        '''
        if channel in self._channels:
            if self._channels[channel].is_subscribed:
                return True
        return False

    def subscribe(self, channel, subscribe_on_reconnect, on_message):
        '''Subscribes to the supplied channel to receive messages sent to it.

        * *channel* - The channel name.
        * *subscribe_on_reconnect* -Indicates whether the client should subscribe to the channel when reconnected (if it was previously subscribed when connected).
        * *on_message* - The callback called when a message arrives at the channel.

        Usage:

        >>> def on_message(sender, channel, message):
        >>>     print 'Message received on ('+channel+'): ' + message
        >>> ortc_client.subscribe('blue', True, on_message)
        '''
        if not self.is_connected:
            Private._call_exception_callback(self, 'Not connected')
        elif not isinstance(channel, str) or len(channel)<1:
            Private._call_exception_callback(self, 'Channel is null or empty or not a string')
        elif not Private._validate_input(channel):
            Private._call_exception_callback(self, 'Channel has invalid characters')
        elif channel in self._channels and self._channels[channel].is_subscribed:
            Private._call_exception_callback(self, 'Already subscribing to the channel \''+channel+'\'')
        elif len(channel) > MAX_CHANNEL_NAME_SIZE:
            Private._call_exception_callback(self, 'Channel size exceeds the limit of ' + str(MAX_CHANNEL_NAME_SIZE) + ' characters')
        elif not hasattr(on_message, '__call__'):
            Private._call_exception_callback(self, 'The argument \'onMessageCallback\' must be a function')
        else:
            has_permission, phash = Private._check_permission(self._permissions, channel)
            if not has_permission:
                Private._call_exception_callback(self, 'No permissions found to subscribe channel: '+channel)
                return
            ch = Channel(channel, subscribe_on_reconnect, on_message)
            ch.is_subscribing = True
            self._channels[channel] = ch
            self._ws.send(json.dumps('subscribe;'+self.app_key+';'+self.auth_token+';'+channel+';'+phash))


    def unsubscribe(self, channel):
        '''Unsubscribes from the supplied channel to stop receiving messages sent to it.

        * *channel* - The channel name.

        Usage:

        >>> ortc_client.unsubscribe('blue')
        '''
        if not self.is_connected:
            Private._call_exception_callback(self, 'Not connected')
        elif not isinstance(channel, str) or len(channel)<1:
            Private._call_exception_callback(self, 'Channel is null or empty or not a string')
        elif not Private._validate_input(channel):
            Private._call_exception_callback(self, 'Channel has invalid characters')
        elif not channel in self._channels:
            Private._call_exception_callback(self, 'Not subscribed to the channel \''+channel+'\'')
        elif len(channel) > MAX_CHANNEL_NAME_SIZE:
            Private._call_exception_callback(self, 'Channel size exceeds the limit of ' + str(MAX_CHANNEL_NAME_SIZE) + ' characters')
        else:
            self._channels[channel].subscribe_on_reconnected = False
            self._ws.send(json.dumps('unsubscribe;'+self.app_key+';'+channel))


    def send(self, channel, message):
        '''Sends the supplied message to the supplied channel.

        * *channel* - The channel name.
        * *message* - The message to send.

        Usage:

        >>> ortc_client.send('blue', 'This is a message')
        '''
        if not self.is_connected:
            Private._call_exception_callback(self, 'Not connected')
        elif not isinstance(channel, str) or len(channel)<1:
            Private._call_exception_callback(self, 'Channel is null or empty or not a string')
        elif not Private._validate_input(channel):
            Private._call_exception_callback(self, 'Channel has invalid characters')
        elif not isinstance(message, str) or len(message)<1:
            Private._call_exception_callback(self, 'Message is null or empty or not a string')
        elif len(channel) > MAX_CHANNEL_NAME_SIZE:
            Private._call_exception_callback(self, 'Channel size exceeds the limit of ' + str(MAX_CHANNEL_NAME_SIZE) + ' characters')
        else:
            has_permission, phash = Private._check_permission(self._permissions, channel)
            if not has_permission:
                Private._call_exception_callback(self, 'No permissions found to send to channel: '+channel)
                return
            message_id = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(8))
            parts = [message[i:i+MAX_MESSAGE_SIZE] for i in range(0, len(message), MAX_MESSAGE_SIZE)]
            for i, p in enumerate(parts):
                try:
                    self._ws.send(json.dumps('send;'+self.app_key+';'+self.auth_token+';'+channel+';'+phash+';'+message_id+'_'+str(i+1)+'-'+str(len(parts))+'_'+p))
                except Exception as e:
                    Private._call_exception_callback(self, str(e))

    def set_on_exception_callback(self, callback):
        '''Sets the callback which occurs when there is an exception.

        * *callback* - Method to be interpreted when there is an exception.

        Usage:

        >>> def on_exception(sender, exception):
        >>>     print 'Exception: ' + exception
        >>> ortc_client.set_on_exception_callback(on_exception)
        '''
        self.on_exception_callback = callback

    def set_on_connected_callback(self, callback):
        '''Sets the callback which occurs when the client connects.

        * *callback* - Method to be interpreted when the client connects.

        Usage:

        >>> def on_connected(sender):
        >>>     print 'Connected'
        >>> ortc_client.set_on_connected_callback(on_connected)
        '''
        self.on_connected_callback = callback

    def set_on_disconnected_callback(self, callback):
        '''Sets the callback which occurs when the client disconnects.

        * *callback* - Method to be interpreted when the client disconnects.

        Usage:

        >>> def on_disconnected(sender):
        >>>     print 'Disconnected'
        >>> ortc_client.set_on_disconnected_callback(on_disconnected)
        '''
        self.on_disconnected_callback = callback

    def set_on_reconnected_callback(self, callback):
        '''Sets the callback which occurs when the client reconnects.

        * *callback* - Method to be interpreted when the client reconnects.

        Usage:

        >>> def on_reconnected(sender):
        >>>     print 'Reconnected'
        >>> ortc_client.set_on_reconnected_callback(on_reconnected)
        '''
        self.on_reconnected_callback = callback

    def set_on_reconnecting_callback(self, callback):
        '''Sets the callback which occurs when the client attempts to reconnect.

        * *callback* - Method to be interpreted when the client attempts to reconnect.

        Usage:

        >>> def on_reconnecting(sender):
        >>>     print 'Reconnecting'
        >>> ortc_client.set_on_reconnecting_callback(on_reconnecting)
        '''
        self.on_reconnecting_callback = callback

    def set_on_subscribed_callback(self, callback):
        '''Sets the callback which occurs when the client subscribes to a channel.

        * *callback* - Method to be interpreted when the client subscribes to a channel.

        Usage:

        >>> def on_subscribed(sender, channel):
        >>>     print 'Subscribed to: ' + channel
        >>> ortc_client.set_on_subscribed_callback(on_subscribed)
        '''
        self.on_subscribed_callback = callback

    def set_on_unsubscribed_callback(self, callback):
        '''Sets the callback which occurs when the client unsubscribes from a channel.

        * *callback* - Method to be interpreted when the client unsubscribes from a channel.

        Usage:

        >>> def on_unsubscribed(sender, channel):
        >>>     print 'Unsubscribed from: ' + channel
        >>> ortc_client.set_on_unsubscribed_callback(on_unsubscribed)
        '''
        self.on_unsubscribed_callback = callback


    def presence(self, channel, callback):
        '''Gets a dictionary indicating the subscriptions number in the specified channel and if active the first 100 unique metadata.
        * *channel* - The channel name with presence data active.
        * *callback* - The callback with error and result parameters.

        Usage:

        >>> def presence_callback(error, result):
        >>>     if not error == None:
        >>>         print 'ORTC Presence error: ' + error
        >>>     else:
        >>>         print str(result)
        >>> ortc_client.presence('blue', presence_callback)
        '''
        is_ok, server = Private._prepare_server_internal(self.url, self.cluster_url, self.app_key, callback)
        if is_ok:
            presence(server, False, self.app_key, self.auth_token, channel, callback)

    def enable_presence(self, private_key, channel, metadata, callback):
        '''Enables presence for the specified channel with first 100 unique metadata if true.

        **Note:** This method will send your Private Key over the Internet. Make sure to use secure connection.

        * *private_key* - The private key provided when the ORTC service is purchased.
        * *channel* - The channel name to activate presence.
        * *metadata* - Defines if to collect first 100 unique metadata (boolean).
        * *callback* - The callback with error and result parameters.

        Usage:

        >>> def presence_callback(error, result):
        >>>     if not error == None:
        >>>         print 'ORTC Presence error: ' + error
        >>>     else:
        >>>         print str(result)
        >>> ortc_client.enable_presence('Your private key', 'blue', True, presence_callback)
        '''
        is_ok, server = Private._prepare_server_internal(self.url, self.cluster_url, self.app_key, callback)
        if is_ok:
            enable_presence(server, False, self.app_key, private_key, channel, metadata, callback)

    def disable_presence(self, private_key, channel, callback):
        '''Disables presence for the specified channel.

        **Note:** This method will send your Private Key over the Internet. Make sure to use secure connection.

        * *private_key* - The private key provided when the ORTC service is purchased.
        * *channel* - The channel name to disable presence.
        * *callback* - The callback with error and result parameters.

        Usage:

        >>> def presence_callback(error, result):
        >>>     if not error == None:
        >>>         print 'ORTC Presence error: ' + error
        >>>     else:
        >>>         print str(result)
        >>> ortc_client.disable_presence('Your private key', 'blue', presence_callback)
        '''
        is_ok, server = Private._prepare_server_internal(self.url, self.cluster_url, self.app_key, callback)
        if is_ok:
            disable_presence(server, False, self.app_key, private_key, channel, callback)

    def _on_message(self, ws, message):
        self.got_heartbeat = True
        if message=='o':
            self._ws.send(json.dumps('validate;'+self.app_key+';'+self.auth_token+';'+self.announcement_subchannel+';'+self.session_id+';'+self.connection_metadata+';'))
        elif message=='h':
             pass
        else:
            self._parse_message(message)


    def _start_heartbeat_monitor(self):
        self.monit_heartbeat = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_monitor)
        self.heartbeat_thread.setDaemon(True)
        self.heartbeat_thread.start()


    def _heartbeat_monitor(self):
        counter = 0
        while self.monit_heartbeat:
            time.sleep(1)
            counter +=1
            if self.got_heartbeat:
                counter = 0
                self.got_heartbeat = False
            if counter > MAX_HEARTBEAT_INTERVAL:
                self.monit_heartbeat = False
                self._heartbeat_failed()

    def _heartbeat_failed(self):
        self.keep_running = False
        if not self._ws==None:
            self._ws.close()
        self._state = states.RECONNECTING
        for k in self._channels.keys():
            self._channels[k].is_subscribing = False
            self._channels[k].is_subscribed = False
            if not self._channels[k].subscribe_on_reconnecting:
                del self._channels[k]
        if self.on_reconnecting_callback:
            self.on_reconnecting_callback(self)
        from threading import Thread
        self.reconnecting_thread = Thread(target=self._reconnecting_loop)
        self.reconnecting_thread.setDaemon(True)
        self.reconnecting_thread.start()

    def _reconnecting_loop(self):
        counter = 1
        while not self.is_connected and not self._state==states.DISCONNECTING:
            if counter > RECONNECT_INTERVAL:
                if not self._state == states.DISCONNECTING:
                    self.connect(self.app_key, self.auth_token)
                counter = 0
            time.sleep(1)
            counter += 1

    def _parse_message(self, message):
        res = re.search(r'^a?\["\{\\"ch\\":\\"(.*)\\",\\"m\\":\\"([\s\S]*?)\\"\}"\]$', message)
        rmg = res.groups() if not res == None else []
        if not rmg == []:
            channel =  rmg[0]
            if not channel in self._channels: return
            raw_message = rmg[1]
            res = re.search(r'^(.[^_]*)_(.[^-]*)-(.[^_]*)_([\s\S]*?)$', raw_message)
            if not res == None:
                ret = res.groups()
                message_id = ret[0]
                message_count = int(ret[1])
                message_total = int(ret[2])
                message_part = ret[3]
                if message_count==1 and message_total==1:
                    self._channels[channel].callback(self, channel,  Private._remove_slashes(message_part))
                else:
                    if not message_id in self._messages_buffer:
                        self._messages_buffer[message_id] = MultiMessage(message_total)
                    self._messages_buffer[message_id].set_part(message_count-1, message_part)
                    if self._messages_buffer[message_id].is_ready():
                        all_message = self._messages_buffer[message_id].get_all_message()
                        del self._messages_buffer[message_id]
                        self._channels[channel].callback(self, channel, Private._remove_slashes(all_message))
            else:
                self._channels[channel].callback(self, channel, Private._remove_slashes(raw_message))

        res = re.search(r'^a\["\{\\"op\\":\\"([^"]+)\\",\\"(.*)\}"\]$', message)
        ret = res.groups() if not res == None else []
        if not ret == []: #operation
            operation = ret[0]
            params = ret[1]
            if operation == 'ortc-validated':
                pgrp = re.search(r'^up\\":{1}(.*),\\"set\\":(.*)', params).groups()
                if pgrp[0] == 'null':
                    self._permissions = {}
                else:
                    self._permissions = json.loads(pgrp[0].replace(r'\"', r'"'))
                if self._state == states.RECONNECTING:
                    self._state = states.CONNECTED
                    for n, ch in self._channels.iteritems():
                        self.subscribe(ch.name, True, ch.callback)
                    if self.on_reconnected_callback:
                        self.on_reconnected_callback(self)
                else:
                    self._state = states.CONNECTED
                    if self.on_connected_callback:
                        self.on_connected_callback(self)
                self._start_heartbeat_monitor()
            if operation == 'ortc-subscribed':
                channel = re.search(r'^ch\\":\\"(.*)\\"$', params).groups()[0]
                if channel in self._channels:
                    self._channels[channel].is_subscribing = False
                    self._channels[channel].is_subscribed = True
                    if self.on_subscribed_callback:
                        self.on_subscribed_callback(self, channel)
            if operation == 'ortc-unsubscribed':
                channel = re.search(r'^ch\\":\\"(.*)\\"$', params).groups()[0]
                if channel in self._channels:
                    del self._channels[channel]
                    if self.on_unsubscribed_callback:
                        self.on_unsubscribed_callback(self, channel)
            if operation == 'ortc-error':
                pgrp = re.search(r'ex\\":\\"(.*)\\"\}$', params).groups()
                Private._call_exception_callback(self, pgrp[0])

