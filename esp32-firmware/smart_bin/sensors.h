// Pluggable sensor module interface. Add a load cell, ultrasonic, RFID, or camera module by
// implementing this interface and registering an instance in setup() inside smart_bin.ino —
// the core command-dispatch loop never needs to change.
#pragma once
#include <Arduino.h>

class SensorModule {
public:
  virtual void begin() = 0;
  virtual float read() = 0;          // module-specific unit (grams, cm, etc.)
  virtual const char* name() = 0;
  virtual ~SensorModule() {}
};

// --- Load cell (HX711) -------------------------------------------------------------------
// Requires the "HX711" library (bogde/HX711). Wire DOUT/SCK to the pins passed in the constructor.
class LoadCellModule : public SensorModule {
public:
  LoadCellModule(uint8_t doutPin, uint8_t sckPin, float calibrationFactor)
    : _dout(doutPin), _sck(sckPin), _cal(calibrationFactor) {}

  void begin() override {
    // scale.begin(_dout, _sck); scale.set_scale(_cal); scale.tare();
    // Left as a stub: wire up the HX711 library call here when the load cell is installed.
  }

  float read() override {
    // return scale.get_units(5); // grams, averaged over 5 reads
    return -1.0f;  // -1 signals "no reading available" until the library call above is filled in
  }

  const char* name() override { return "load_cell"; }

private:
  uint8_t _dout, _sck;
  float _cal;
};

// --- Ultrasonic fill/deposit sensor (HC-SR04) --------------------------------------------
class UltrasonicModule : public SensorModule {
public:
  UltrasonicModule(uint8_t trigPin, uint8_t echoPin) : _trig(trigPin), _echo(echoPin) {}

  void begin() override {
    pinMode(_trig, OUTPUT);
    pinMode(_echo, INPUT);
  }

  float read() override {
    digitalWrite(_trig, LOW);
    delayMicroseconds(2);
    digitalWrite(_trig, HIGH);
    delayMicroseconds(10);
    digitalWrite(_trig, LOW);
    long duration = pulseIn(_echo, HIGH, 30000);  // 30ms timeout ~5m range
    if (duration == 0) return -1.0f;
    return duration * 0.0343f / 2.0f;  // cm
  }

  const char* name() override { return "ultrasonic"; }

private:
  uint8_t _trig, _echo;
};
