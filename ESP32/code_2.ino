#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "Coradin";
const char* password = "12345678";
const char* serverURL = "http://192.168.59.30:5000/api/dados";

const int soundSensorPin = 34;
unsigned long lastSendTime = 0;
const int sendInterval = 30000;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  initWiFi();
  pinMode(soundSensorPin, INPUT);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    reconnectWiFi();
    return;
  }

  int rawValue = analogRead(soundSensorPin);
  if (rawValue < 10) rawValue = 10; // evita log(0)

  float nivel_dB = 20 * log10(rawValue); // log direto no valor lido
  nivel_dB = constrain(nivel_dB, 30, 130);

  Serial.print("Raw: ");
  Serial.print(rawValue);
  Serial.print(" | dB: ");
  Serial.println(nivel_dB, 1);

  if (millis() - lastSendTime > sendInterval) {
    sendDataToServer(nivel_dB);
    lastSendTime = millis();
  }

  delay(1000);
}

void initWiFi() {
  WiFi.begin(ssid, password);
  Serial.println("Conectando ao WiFi...");
  
  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startTime < 20000) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConectado! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nFalha na conexão WiFi");
  }
}

void reconnectWiFi() {
  Serial.println("Reconectando ao WiFi...");
  WiFi.disconnect();
  WiFi.reconnect();
  delay(5000);
}

void sendDataToServer(float nivel_dB) {
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  String jsonData = "{\"nivel_ruido\":" + String(nivel_dB, 1) + "}";
  Serial.println("Enviando: " + jsonData);
  
  int httpCode = http.POST(jsonData);
  
  if (httpCode == HTTP_CODE_OK) {
    Serial.println("Dados enviados com sucesso!");
  } else {
    Serial.println("Erro no envio: " + String(httpCode));
  }
  http.end();
}