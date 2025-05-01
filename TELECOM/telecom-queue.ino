#include <stdlib.h>
#include "telecom-queue.h"

int telecomQueue_enqueue(telecomQueue *queue, telecomPacket *packet) {
  telecomPacket *queue_packet = (telecomPacket *) malloc(sizeof(telecomPacket));
  if (queue_packet == NULL) return 1;
  memcpy(queue_packet, packet, sizeof(telecomPacket));

  telecomQueue_node *newNode = (telecomQueue_node *) malloc(sizeof(telecomQueue_node));
  if (newNode == NULL) return 1;
  newNode->value = queue_packet;
  newNode->next = NULL;

  if (queue->head != NULL) {
    telecomQueue_node *endNode = queue->head;
    uint32_t depth = 0;
    while (endNode->next != NULL && depth < TELECOM_QUEUE_MAX_LENGTH) {
      endNode = endNode->next;
      depth++;
    }
    if (depth == TELECOM_QUEUE_MAX_LENGTH) return 1; // Queue is full
    endNode->next = newNode;
  } else {
    queue->head = newNode;
  }

  return 0;
}

int telecomQueue_dequeue(telecomQueue *queue, telecomPacket *packet) {
  if (queue->head != NULL) {
    telecomQueue_node *headNode = queue->head;
    telecomPacket *headPacket = headNode->value;
    queue->head = headNode->next;

    memcpy(packet, headPacket, sizeof(telecomPacket));

    free(headPacket);
    free(headNode);

    return 0;
  }
  
  // No packets in queue
  return 1;
}
