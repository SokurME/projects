#include <Arduino.h>
#include "MelodyPlayer.h"

MelodyPlayer::MelodyPlayer(int pin)
{
  _pin = pin;
}

void MelodyPlayer::init()
{
  pinMode(_pin, OUTPUT);
}

void MelodyPlayer::playStarwars()
{
  beep(a, 500);
  beep(a, 500);
  beep(a, 500);
  beep(f, 350);
  beep(cH, 150);
  beep(a, 500);
  beep(f, 350);
  beep(cH, 150);
  beep(a, 650);

}

void MelodyPlayer::beep(int note, int duration)
{
  tone(_pin, note, duration);
  delay(duration);
  noTone(_pin);
  delay(50);
}
