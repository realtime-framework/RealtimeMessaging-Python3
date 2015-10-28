## Realtime Cloud Messaging Python 3.x SDK
Part of the [The Realtime® Framework](http://framework.realtime.co), Realtime Cloud Messaging (aka ORTC) is a secure, fast and highly scalable cloud-hosted Pub/Sub real-time message broker for web and mobile apps.

If your application has data that needs to be updated in the user’s interface as it changes (e.g. real-time stock quotes or ever changing social news feed) Realtime Cloud Messaging is the reliable, easy, unbelievably fast, “works everywhere” solution.

## Setup

1. This SDK requires the module websocket.py to be installed. Please process the installation instructions of websocket.py at: [https://github.com/liris/websocket-client](https://github.com/liris/websocket-client)
2. Copy the files `ortc.py` and `ortc_extensibility.py` to your project directory
3. Place in your source code the line: import ortc
4. Follow the sample code in: `example_simple.py` or `example_menu.py`



> NOTE: For simplicity these samples assume you're using a Realtime® Framework developers' application key with the authentication service disabled (every connection will have permission to publish and subscribe to any channel). For security guidelines please refer to the [Security Guide](http://messaging-public.realtime.co/documentation/starting-guide/security.html). 
> 
> **Don't forget to replace `YOUR_APPLICATION_KEY` and `YOUR_APPLICATION_PRIVATE_KEY` with your own application key. If you don't already own a free Realtime® Framework application key, [get one now](https://app.realtime.co/developers/getlicense).**


## API Reference
[http://messaging-public.realtime.co/documentation/python/2.1.0/index.html](http://messaging-public.realtime.co/documentation/python/2.1.0/index.html)


## Authors
- Realtime
- Eduardo Basterrechea
- Armando Ramos

