/*
 * IRremoteESP8266: IRrecvDumpV2 - dump details of IR codes with IRrecv
 * An IR detector/demodulator must be connected to the input kRecvPin.
 *
 * Copyright 2009 Ken Shirriff, http://arcfn.com
 * Copyright 2017-2019 David Conran
 *
 * Example circuit diagram:
 *  https://github.com/crankyoldgit/IRremoteESP8266/wiki#ir-receiving
 *
 * Changes:
 *   Version 1.2 October, 2020
 *     - Enable easy setting of the decoding tolerance value.
 *   Version 1.0 October, 2019
 *     - Internationalisation (i18n) support.
 *     - Stop displaying the legacy raw timing info.
 *   Version 0.5 June, 2019
 *     - Move A/C description to IRac.cpp.
 *   Version 0.4 July, 2018
 *     - Minor improvements and more A/C unit support.
 *   Version 0.3 November, 2017
 *     - Support for A/C decoding for some protocols.
 *   Version 0.2 April, 2017
 *     - Decode from a copy of the data so we can start capturing faster thus
 *       reduce the likelihood of miscaptures.
 * Based on Ken Shirriff's IrsendDemo Version 0.1 July, 2009,
 */

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <IRremoteESP8266.h>
#include <IRsend.h>
#include <ir_Fujitsu.h>
//#include <ArduinoOTA.h>
#include <ESP8266mDNS.h>
#include <AHT10.h>
#include <Ticker.h>

// Wi-Fi Configuration
const char* ssid = "FronNet";
const char* password = "sszxUoci";

// The Serial connection baud rate.
// i.e. Status message will be sent to the PC at this baud rate.
// Try to avoid slow speeds like 9600, as you will miss messages and
// cause other problems. 115200 (or faster) is recommended.
// NOTE: Make sure you set your Serial Monitor to the same speed.
const uint32_t kBaudRate = 115200;


const uint16_t kIrLed = D5;  // ESP8266 GPIO pin to use. Recommended: 4 (D2).
IRFujitsuAC ac(kIrLed);

unsigned long previousMillis = 0;
const long interval = 2000; // 2 seconds
AHT10 aht;

ESP8266WebServer server(80);

uint8_t fanFromValue(int value) {
  switch (value) {
    case kFujitsuAcFanAuto:
      return kFujitsuAcFanAuto;
    case kFujitsuAcFanHigh:
      return kFujitsuAcFanHigh;
    case kFujitsuAcFanLow:
      return kFujitsuAcFanLow;
    case kFujitsuAcFanMed:
      return kFujitsuAcFanMed;
    case kFujitsuAcFanQuiet:
      return kFujitsuAcFanQuiet;
  }

  return -1;
}

String fanAsString(uint8_t value) {
  switch (value) {
    case kFujitsuAcFanAuto:
      return "Auto";
    case kFujitsuAcFanHigh:
      return "High";
    case kFujitsuAcFanLow:
      return "Low";
    case kFujitsuAcFanMed:
      return "Med";
    case kFujitsuAcFanQuiet:
      return "Quiet";
  }

  return "Error";
}

void TurnOff() {
  digitalWrite(LED_BUILTIN, HIGH);
}

Ticker ledTicker(TurnOff, 1000, 0, MILLIS);

String sendIRCommand(String command, String value) {
  String message = "error";
  if (command == "temp") {
    int val = value.toInt();
    if (val > 10 || val < 30) {
      ac.setTemp(val);
     
      message = "Temperature = " + value;
      Serial.println("Sent IR signal: Temperature " + value);
    } 
    
  } else if (command == "mode") {

    uint8_t mode = -1;
    if (value == "heat") {
      mode = kFujitsuAcModeHeat;
    } else if (value == "cool") {
      mode = kFujitsuAcModeCool;
    } else if (value == "heat_cool") {
      mode = kFujitsuAcModeAuto;
    } else if (value == "dry") {
      mode = kFujitsuAcModeDry;
    } else if (value == "fan_only") {
      mode = kFujitsuAcModeFan;
    }

    if (mode == -1) {
      return message;
    }

    ac.setMode(mode);

    message = "Mode: " + value;
    Serial.println("Sent IR signal: Mode " + value);
  } else if (command == "fan") {

    uint8_t mode = -1;
    // Values from HA
    if (value == "auto") {
      mode = kFujitsuAcFanAuto;
    } else if (value == "low") {
      mode = kFujitsuAcFanLow;
    } else if (value == "medium") {
      mode = kFujitsuAcFanMed;
    } else if (value == "high") {
      mode = kFujitsuAcFanHigh;
    }

    if (mode == -1) {
      return message;
    }

    ac.setFanSpeed(mode);

    message = "Fan: " + value;
    Serial.println("Sent IR signal: Fan " + value);
  } else if (command == "off") {
    ac.setPower(false);
    message = "Power: off";
    Serial.println("Sent IR signal: Power off");
  } else if (command == "on") {
    ac.setPower(true);
    message = "Power: on";
    Serial.println("Sent IR signal: Power on");
  } else if (command == "swing_mode") {
    if (value == "off") {
      ac.setSwing(kFujitsuAcSwingOff);
    } else if (value == "both") {
      ac.setSwing(kFujitsuAcSwingBoth);
    } else if (value == "vertical") {
      ac.setSwing(kFujitsuAcSwingVert);
    } else if (value == "horizontal") {
      ac.setSwing(kFujitsuAcSwingHoriz);
    } else {
      return message;
    }

    message = "Swing mode: " + value;
    Serial.println("Sent IR signal: swing mode " + value);
  } else {
    Serial.println("Unknown command");
    return message;
  }

  ac.send();

  digitalWrite(LED_BUILTIN, LOW);
  ledTicker.resume();

  return message;
}

void handleIRRequest() {
  if (!server.hasArg("command")) {
    server.send(400, "text/plain", "Missing 'command' parameter");
    return;
  }

  String command = server.arg("command");
  Serial.println("Received command: " + command);

  String value = server.arg("value");
  Serial.println("Received value: " + value);

  String message = sendIRCommand(command, value);
  if (message != "error") {
    server.send(200, "text/plain", message);  
  } else {
    server.send(400, "text/plain", "FAILED TO Command: " + command + ", Value: " + value);  
  }
}

void handleTempReques() {
  float humidity = aht.readHumidity();
  float temperature = aht.readTemperature();

  // Respond with JSON data
  String response = "{\"temperature\":";
  response += temperature;
  response += ",\"humidity\":";
  response += humidity;
  response += "}";
  server.send(200, "application/json", response);
}

// void setupOTA() {
//   // ArduinoOTA.setHostname("NodeMCU-Climate"); // Set a custom hostname
//   ArduinoOTA.begin(WiFi.localIP(), WiFi.hostname().c_str(), "password", InternalStorage);
//   Serial.println("OTA Ready");
// }

void setupAC() {
  ac.begin();

  ac.setFanSpeed(kFujitsuAcFanHigh);
  ac.setMode(kFujitsuAcModeHeat);
  ac.setSwing(kFujitsuAcSwingOff);

  Serial.println("IR transmitter initialized");
}

void setupServer() {
  server.on("/send_ir", handleIRRequest);
  server.on("/temp", handleTempReques);
  server.begin();
  Serial.println("HTTP server started");
}

const char* mdnsName = "nodemcu-climate";

void setupMDSN() {
  if (MDNS.begin(mdnsName)) {
      Serial.println("mDNS started");
      Serial.printf("You can access this device at http://%s.local\n", mdnsName);

      MDNS.addService(mdnsName, "tcp", 80);
      MDNS.addServiceTxt(mdnsName, "tcp", "device", "NodeMCU_Climate");
      String macAddress = WiFi.macAddress();
      MDNS.addServiceTxt(mdnsName, "tcp", "mac_address", macAddress);
    }
}

void setupWifi() {
  Serial.println("Connecting to Wi-Fi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected to Wi-Fi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

// This section of code runs only once at start-up.
void setup() {

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Serial.begin(kBaudRate);

  // Wifi setup
  setupWifi();

  // Mdns setup
  setupMDSN();

  // IR transmitter setup
  setupAC();

  // HTTP server setup
  setupServer();

  // OTA Setup
  // setupOTA()
  
  if (! aht.begin()) {
    Serial.println("Could not find AHT? Check wiring");
    // while (1) delay(10);
  } else {
    Serial.println("AHT started");
  }
}

// The repeating section of the code
void loop() {
  //  ArduinoOTA.poll();
   server.handleClient();

   ledTicker.update();

   MDNS.update();
}
