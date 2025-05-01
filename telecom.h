#ifndef TELECOM_H
#define TELECOM_H

#include "telecom-queue.h"

#define TELECOM_RX_LOG_MAX_LINE_LENGTH 255

#define TELECOM_DUTY_CYCLE_EU868 0.01 // 868 MHz in EU, any TX power
#define TELECOM_DUTY_CYCLE_EU434 1.0 // 434 MHz in EU, normal TX power (up to 10 dBm)
#define TELECOM_DUTY_CYCLE_EU434_HPA 0.1 // 434 MHz in EU, high TX power (up to 14 dBm)

#define TELECOM_DUTY_CYCLE_WINDOW_MILLIS 300000 // Over what timespan duty cycle is calculated (300k ms = 5 minutes)

#define TELECOM_TX_MIN_DELAY_MILLIS 100 // Minimum delay between transmitted packets in ms

void telecom_rx(String rxLogFilePath);

void telecom_tx(telecomQueue *queue, float dutyCycle);

#endif