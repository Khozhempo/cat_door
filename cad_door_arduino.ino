#include <ServoSmooth.h>
#include <Bounce2.h>

ServoSmooth servo;

#define PIN_LED_GREEN 2
#define PIN_LED_BLUE  3
#define PIN_LED_RED   4
#define PIN_SERVO     5
#define SERVO_POS_STOP 103
#define SERVO_POS_GO   0
#define BUTTON_OUTSIDE 13
#define BUTTON_INSIDE  12
#define NUM_BUTTONS    2 // количество кнопок

Bounce * buttons = new Bounce[NUM_BUTTONS];
const uint8_t BUTTON_PINS[NUM_BUTTONS] = {BUTTON_OUTSIDE, BUTTON_INSIDE};

String inputString = "";         // a String to hold incoming data
bool stringComplete = false;  // whether the string is complete

void setup() {
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_BLUE, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);

  // инициализация пинов с кнопками
  for (int i = 0; i < NUM_BUTTONS; i++) {
    buttons[i].attach( BUTTON_PINS[i] , INPUT_PULLUP  );       //setup the bounce instance for the current button
    buttons[i].interval(25);              // interval in ms
  }

  servo.attach(PIN_SERVO, 600, 2400, SERVO_POS_GO);
  servo.smoothStart();
  servo.setSpeed(90);
  servo.setAccel(0.1);

  digitalWrite(PIN_LED_GREEN, HIGH);
  digitalWrite(PIN_LED_BLUE, LOW);
  digitalWrite(PIN_LED_RED, LOW);

  Serial.begin(9600);
  inputString.reserve(200);
  digitalWrite(PIN_LED_RED, HIGH);
  delay(250);
  digitalWrite(PIN_LED_RED, LOW);
  Serial.println("ready");
  Serial.println("help:\n- door open\n- door close\n- led red on\n- led red off");
}

void loop() {
  boolean state = servo.tick();

  if (stringComplete) {
    Serial.println(inputString);
    if (inputString == "door open\n") {
      Serial.println("opennig door");
      servo.setTargetDeg(SERVO_POS_GO);
      digitalWrite(PIN_LED_GREEN, HIGH);
      digitalWrite(PIN_LED_BLUE, LOW);


    } else if (inputString == "door close\n") {
      Serial.println("closing door");
      servo.setTargetDeg(SERVO_POS_STOP);
      digitalWrite(PIN_LED_GREEN, LOW);
      digitalWrite(PIN_LED_BLUE, HIGH);
    } else if (inputString == "led red on\n") {
      digitalWrite(PIN_LED_RED, HIGH);
    }  else if (inputString == "led red off\n") {
      digitalWrite(PIN_LED_RED, LOW);
    }

    // clear the string:
    inputString = "";
    stringComplete = false;
  }

  // проверка нажатий по кнопкам
  for (int i = 0; i < NUM_BUTTONS; i++)  {
    buttons[i].update();
    if ( buttons[i].fell() ) {
      switch (i) {
        case 0:
          Serial.println("door: out");
          break;
        case 1:
          Serial.println("door: in");
          break;
      }
    }
  }


}


void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}
