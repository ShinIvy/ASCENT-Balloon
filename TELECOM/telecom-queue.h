#ifndef TELECOM_QUEUE_H
#define TELECOM_QUEUE_H

#include "telecom-packet.h"

#define TELECOM_QUEUE_MAX_LENGTH 1000 // Max number of queued items

typedef struct telecomQueue_node telecomQueue_node; // Need to pre-declare due to recursive declaration below

struct telecomQueue_node {
  telecomPacket *value;
  telecomQueue_node *next;
};

typedef struct {
  telecomQueue_node *head;
} telecomQueue;

int telecomQueue_enqueue(telecomQueue *queue, telecomPacket *packet);

int telecomQueue_dequeue(telecomQueue *queue, telecomPacket *packet);

#endif