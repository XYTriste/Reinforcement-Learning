#include <stdio.h>
#include <stdlib.h>

union obj {
    union obj* free_list_link;
    char client_data[1];
};

#define BLOCK_SIZE 1
#define NUM_BLOCKS 10

union obj* free_list = NULL;

// ��ʼ����������
void initialize_free_list() {
    for (int i = 0; i < NUM_BLOCKS; i++) {
        union obj* new_node = (union obj*)malloc(sizeof(union obj));
        if (new_node == NULL) {
            fprintf(stderr, "Memory allocation error\n");
            exit(1);
        }
        new_node->free_list_link = free_list;
        free_list = new_node;
    }
}

// �����ڴ��
void* allocate_block() {
    if (free_list == NULL) {
        fprintf(stderr, "Out of memory\n");
        exit(1);
    }

    union obj* allocated_block = free_list;
    free_list = free_list->free_list_link;
    return allocated_block->client_data;
}

// �ͷ��ڴ��
void deallocate_block(void* block) {
    union obj* deallocated_block = (union obj*)((char*)block - offsetof(union obj, client_data));
    deallocated_block->free_list_link = free_list;
    free_list = deallocated_block;
}

int main() {
    initialize_free_list();

    // �����ڴ��
    void* block1 = allocate_block();
    void* block2 = allocate_block();

    // ʹ���ڴ��
    printf("Memory blocks allocated\n");

    // �ͷ��ڴ��
    deallocate_block(block1);
    deallocate_block(block2);
    printf("Memory blocks deallocated\n");

    return 0;
}
