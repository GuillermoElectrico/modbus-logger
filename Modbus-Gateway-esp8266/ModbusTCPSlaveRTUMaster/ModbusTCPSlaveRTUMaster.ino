// Include these libraries for using the RS-232 to RS-485 adaptor and Modbus functions
#include <ModbusMaster232.h>

//----------------------------------------------------------------------------------------------------

#define MB_PORT 502
#define SLAVEID 1          // id device rs485 connected.
#define BAUDRATE 9600      //rate de baud a comunicate RS485
#define RS485_ENABLE_PIN 0 //pinul GPIO0 or gpio2

//#define MB_ETHERNET
#define MB_ESP8266

//#define STATIC_MODE  // static IP address config
#ifdef STATIC_MODE
byte ip[]      = { 192, 168, 0, 22 };
byte gateway[] = { 192, 168, 0, 1 };
byte subnet[]  = { 255, 255, 255, 0 };
#endif

#define W_SSID "Telecom-28778737"
#define W_PASSWORD "passwordwificasa47893000"

//----------------------------------------------------------------------------------------------------

#ifdef MB_ETHERNET
#include <Ethernet.h>
#define LED_PIN 13
#endif
#ifdef MB_ESP8266
#define LED_PIN 5
#include <ESP8266WiFi.h>
#endif

//
// MODBUS Function Codes
//
#define MB_FC_NONE 0
#define MB_FC_READ_COILS 1                  //implemented
#define MB_FC_READ_DISCRETE_INPUT 2         //implemented
#define MB_FC_READ_REGISTERS 3              //implemented
#define MB_FC_READ_INPUT_REGISTERS 4        //implemented
#define MB_FC_WRITE_COIL 5                  //implemented
#define MB_FC_WRITE_REGISTER 6              //implemented
#define MB_FC_WRITE_MULTIPLE_COILS 15
#define MB_FC_WRITE_MULTIPLE_REGISTERS 16   //implemented
//
// MODBUS Error Codes
//
#define MB_EC_NONE 0
#define MB_EC_ILLEGAL_FUNCTION 1
#define MB_EC_ILLEGAL_DATA_ADDRESS 2
#define MB_EC_ILLEGAL_DATA_VALUE 3
#define MB_EC_SLAVE_DEVICE_FAILURE 4
//
// MODBUS MBAP offsets
//
#define MB_TCP_TID          0
#define MB_TCP_PID          2
#define MB_TCP_LEN          4
#define MB_TCP_UID          6
#define MB_TCP_FUNC         7
#define MB_TCP_REGISTER_START         8
#define MB_TCP_REGISTER_NUMBER         10

#ifdef MB_ETHERNET
EthernetServer MBServer(MB_PORT);
#endif

#ifdef MB_ESP8266
WiFiServer MBServer(MB_PORT);
#endif

// Instantiate ModbusMaster object as slave ID and set GPIO to RS485_ENABLE_PIN half duplex adaptor.
ModbusMaster232 node(SLAVEID, RS485_ENABLE_PIN);

byte ByteArray[260];
bool ledPinStatus = LOW;

void setup()
{

#ifdef MB_ETHERNET
  byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
#ifndef STATIC_MODE
  // DHCP mode
  if (Ethernet.begin(mac) == 0) {
    while (1);
  }
#else
  // Static Mode
  Ethernet.begin(mac, ip, gateway, subnet);
#endif
  digitalWrite(LED_PIN, HIGH);
#endif

#ifdef MB_ESP8266
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  ledPinStatus = LOW;
  // Static Mode
#ifdef STATIC_MODE
  WiFi.config(IPAddress(ip), IPAddress(gateway), IPAddress(subnet));
#endif
  WiFi.begin(W_SSID, W_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    // Blink the LED
    digitalWrite(LED_PIN, ledPinStatus); // Write LED high/low
    ledPinStatus = (ledPinStatus == HIGH) ? LOW : HIGH;
    delay(100);
  }
  // Start the server
  digitalWrite(LED_PIN, HIGH);
  MBServer.begin();
#endif

  // Initialize Modbus communication baud rate
  node.begin(BAUDRATE);

}

void loop()
{
  boolean flagClientConnected = 0;
  byte byteFN = MB_FC_NONE;
  int Start;
  int WordDataLength;
  int ByteDataLength;
  int MessageLength;

  //****************** Read from socket ****************
#ifdef MB_ETHERNET
  EthernetClient client = MBServer.available();
#endif
#ifdef MB_ESP8266
  WiFiClient client = MBServer.available();
#endif

  while (client.connected()) {
    if (client.available())
    {
      flagClientConnected = 1;
      int i = 0;
      while (client.available())
      {
        ByteArray[i] = client.read();
        i++;
      }
#ifdef MB_ESP8266
      client.flush();
#endif
      byteFN = ByteArray[MB_TCP_FUNC];
      Start = word(ByteArray[MB_TCP_REGISTER_START], ByteArray[MB_TCP_REGISTER_START + 1]);
      WordDataLength = word(ByteArray[MB_TCP_REGISTER_NUMBER], ByteArray[MB_TCP_REGISTER_NUMBER + 1]);
    }

    // Handle request

    switch (byteFN) {
      case MB_FC_NONE:
        {
        }
        break;


      case MB_FC_READ_COILS:  // 01 Read Coils
        {
          ByteDataLength = WordDataLength * 2;
          ByteArray[5] = ByteDataLength + 3; //Number of bytes after this one.
          ByteArray[8] = ByteDataLength;     //Number of bytes after this one (or number of bytes of data).

          int result = node.readCoils(Start, WordDataLength);

          for (int i = 0; i < WordDataLength; i++)
          {
            if (result == 0) {
              ByteArray[ 9 + i * 2] = highByte(node.getResponseBuffer(i));
              ByteArray[10 + i * 2] =  lowByte(node.getResponseBuffer(i));
            }
          }

          MessageLength = ByteDataLength + 9;
          client.write((const uint8_t *)ByteArray, MessageLength);
          client.stop();
          node.clearResponseBuffer(); // Clear the response buffer
          byteFN = MB_FC_NONE;
        }
        break;


      case MB_FC_READ_DISCRETE_INPUT:  // 02 Read Discrete Input
        {
          ByteDataLength = WordDataLength * 2;
          ByteArray[5] = ByteDataLength + 3; //Number of bytes after this one.
          ByteArray[8] = ByteDataLength;     //Number of bytes after this one (or number of bytes of data).

          int result = node.readDiscreteInputs(Start, WordDataLength);

          for (int i = 0; i < WordDataLength; i++)
          {
            if (result == 0) {
              ByteArray[ 9 + i * 2] = highByte(node.getResponseBuffer(i));
              ByteArray[10 + i * 2] =  lowByte(node.getResponseBuffer(i));
            }
          }

          MessageLength = ByteDataLength + 9;
          client.write((const uint8_t *)ByteArray, MessageLength);
          client.stop();
          node.clearResponseBuffer(); // Clear the response buffer
          byteFN = MB_FC_NONE;
        }
        break;

      case MB_FC_READ_REGISTERS:  // 03 Read Holding Registers
        {
          ByteDataLength = WordDataLength * 2;
          ByteArray[5] = ByteDataLength + 3; //Number of bytes after this one.
          ByteArray[8] = ByteDataLength;     //Number of bytes after this one (or number of bytes of data).

          int result = node.readHoldingRegisters(Start, WordDataLength);

          for (int i = 0; i < WordDataLength; i++)
          {
            if (result == 0) {
              ByteArray[ 9 + i * 2] = highByte(node.getResponseBuffer(i));
              ByteArray[10 + i * 2] =  lowByte(node.getResponseBuffer(i));
            }
          }

          MessageLength = ByteDataLength + 9;
          client.write((const uint8_t *)ByteArray, MessageLength);
          client.stop();
          node.clearResponseBuffer(); // Clear the response buffer
          byteFN = MB_FC_NONE;
        }
        break;

      case MB_FC_READ_INPUT_REGISTERS:  // 04 Read Input Registers
        {
          ByteDataLength = WordDataLength * 2;
          ByteArray[5] = ByteDataLength + 3; //Number of bytes after this one.
          ByteArray[8] = ByteDataLength;     //Number of bytes after this one (or number of bytes of data).

          int result = node.readInputRegisters(Start, WordDataLength);

          for (int i = 0; i < WordDataLength; i++)
          {
            if (result == 0) {
              ByteArray[ 9 + i * 2] = highByte(node.getResponseBuffer(i));
              ByteArray[10 + i * 2] =  lowByte(node.getResponseBuffer(i));
            }
          }
          MessageLength = ByteDataLength + 9;
          client.write((const uint8_t *)ByteArray, MessageLength);
          client.stop();
          node.clearResponseBuffer(); // Clear the response buffer
          byteFN = MB_FC_NONE;
        }
        break;

      case MB_FC_WRITE_COIL:  // 05 Write Coils
        {
          int result =  node.writeSingleCoil(Start, ByteArray[MB_TCP_REGISTER_NUMBER + 1]);
          ByteArray[5] = 6; //Number of bytes after this one.
          MessageLength = 12;
          client.write((const uint8_t *)ByteArray, MessageLength);
          client.stop();
          node.clearTransmitBuffer(); // Clear the response buffer
          byteFN = MB_FC_NONE;
        }
        break;

      case MB_FC_WRITE_REGISTER:  // 06 Write Holding Register
        {
          int result =  node.writeSingleRegister(Start, word(ByteArray[MB_TCP_REGISTER_NUMBER], ByteArray[MB_TCP_REGISTER_NUMBER + 1]));
          ByteArray[5] = 6; //Number of bytes after this one.
          MessageLength = 12;
          client.write((const uint8_t *)ByteArray, MessageLength);
          client.stop();
          node.clearTransmitBuffer(); // Clear the response buffer
          byteFN = MB_FC_NONE;
        }
        break;

      case MB_FC_WRITE_MULTIPLE_REGISTERS:    //16 Write Multiple Registers
        {
          ByteDataLength = WordDataLength * 2;
          ByteArray[5] = ByteDataLength + 3; //Number of bytes after this one.
          for (int i = 0; i < WordDataLength; i++)
          {
            int result =  node.writeSingleRegister(Start + i, word(ByteArray[ 13 + i * 2], ByteArray[14 + i * 2]));
          }
          MessageLength = 12;
          client.write((const uint8_t *)ByteArray, MessageLength);
          client.stop();
          node.clearTransmitBuffer(); // Clear the response buffer
          byteFN = MB_FC_NONE;
        }
        break;

    }

  }
  client.stop();
  if (flagClientConnected == 1) {
    flagClientConnected = 0;
  }
}
