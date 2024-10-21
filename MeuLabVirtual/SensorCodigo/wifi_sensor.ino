#include <WiFi.h>
#include <WebServer.h>

// Escolha dos pinos do ESP32 para ligar com HC-SR04
const int trigPin = 12;
const int echoPin = 14;

long duracao;
float distancia;

const char* ssid = "ESP32_Hotspot";
const char* senha = "123456789";

WebServer server(80);  // Criando servidor na porta 80

void setup() {
  Serial.begin(115200);

  // Configurando os pinos do HC-SR04
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  Serial.println("HC-SR04 Distance Measurement Started");

  // Set up the ESP32 as an access point
  WiFi.softAP(ssid, senha);

  // Print IP address
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.softAPIP());

  server.on("/", HTTP_GET, handleGetRequest);

  // Start the server
  server.begin();
  Serial.println("HTTP iniciado");
}

void loop() {
  // Limpa trigPin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  
  // Dispara o sensor
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // Ler echoPin
  duracao = pulseIn(echoPin, HIGH);
  
  // Calculando a distancia (d = v * t)
  distancia = (duracao * 0.034) / 2;  // Converter para cm e contabilizar ida/volta

  // Print para confirmar em monitoracao serial
  Serial.print("Distancia: ");
  Serial.print(distancia);
  Serial.println(" cm");
  
  delay(100);  // Delay de 100ms para evitar flooding

  server.handleClient();  
}

// Funcao para GET request
void handleGetRequest() {
  // Converte valor float para string (necessario no http)
  String dados = String(distance, 2);  // '2' para duas casas decimais

  // Envia para o servidor
  server.send(200, "text/plain", dados);
}
