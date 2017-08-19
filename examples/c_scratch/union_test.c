#include <stdio.h>

typedef union {
    char u8[4];
    unsigned int u32;
} u_t;

//assumes little endian
void printBits(size_t const size, void const * const ptr)
{
    unsigned char *b = (unsigned char*) ptr;
    unsigned char byte;
    int i, j;

    for (i=size-1;i>=0;i--)
    {
        for (j=7;j>=0;j--)
        {
            byte = (b[i] >> j) & 1;
            printf("%u", byte);
        }
        printf(" ");
    }
    puts("");
}


int main(void)
{    
    
    u_t u;
    
    u.u8[0] = 1;
    u.u8[1] = 3;
    u.u8[2] = 7;
    u.u8[3] = 0;

    u.u8[0] = 0xFF;
    u.u8[1] = 0xFF;
    u.u8[2] = 0xFF;
    u.u8[3] = 0;
    
    // Chopping control bits
    u.u8[2] &= 0x3F;
    u.u8[1] &= 0x7F;
    u.u8[0] &= 0x7F;
        
    unsigned int mytest = (u.u8[2] * 128 + u.u8[1]) * 128 + u.u8[0];  // = u.u8[2] * 128 * 128 + u.u8[1] * 128 + u.u8[0]

    printf("Bits from mytest: ");
    printBits(sizeof(mytest), &mytest);
    
    
    printf("u32=%u\n", u.u32);
    printBits(sizeof(u.u32), &u.u32);

    for(int i = 0; i < 3; i++) 
    {
        
    }

    printf("\n");
}

