# Sketch with the TCP / RTU bridge code via ESP8266 / MAX485. 

Possibility of using an arduino + shield W5100 ethernet instead of ESP8266 if there is no wifi (or you do not want to depend on wifi and you want to use cable)

It works like a transparent bridge TCP/RTU, being able to have several RTU devices in a single bridge (simplifies and saves the installation a lot)

Using an ESP8266, it is possible to update via ArduinoOTA (optional). Within the sketch, the necessary configuration is detailed.