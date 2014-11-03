/*
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#ifndef LMALLOC_H
#define	LMALLOC_H

#include <malloc.h>
#include <stdlib.h>
#include <assert.h>
#include <stdlib.h>
#include <sys/mman.h>

//allocate 100MB at a time and slice it up on request
#define HUGEPAGE_ALLOC_SIZE (1024 * 1024 * 100)
#define HUGEPAGE_MIN_ALIGN 16

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    char * start;
    char * pos;
    char * end;
}huge_page_data;

void lmalloc(void**, size_t);

#ifdef	__cplusplus
}
#endif

/* void lmalloc(void ** a_ptr, size_t a_size)
 *
 * Custom memory allocator
 */
void lmalloc(void ** a_ptr, size_t a_size)
{
    assert(posix_memalign(a_ptr, 16, a_size) == 0);
}

/* void buffer_alloc(void ** a_ptr, size_t a_size)
 *
 * Custom memory allocator for audio buffers
 */
void buffer_alloc(void ** a_ptr, size_t a_size)
{
    assert(posix_memalign(a_ptr, 64, a_size) == 0);
}

int USE_HUGEPAGES = 1;
int HUGE_PAGE_DATA_COUNT = 0;
huge_page_data HUGE_PAGE_DATA[50];

/* Ensure that any pointers carved out of hugepages meet minimum
 * alignment for SIMD instructions (or maybe cache lines eventually) */
char * hugepage_align(char * a_pos)
{
    return a_pos + (HUGEPAGE_MIN_ALIGN - ((size_t)a_pos % HUGEPAGE_MIN_ALIGN));
}

int alloc_hugepage_data()
{
    huge_page_data * f_data = &HUGE_PAGE_DATA[HUGE_PAGE_DATA_COUNT];
    f_data->start = (char*)mmap(NULL, HUGEPAGE_ALLOC_SIZE,
        PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS |
        MAP_POPULATE | MAP_HUGETLB, -1, 0);
    if(f_data->start == MAP_FAILED)
    {
        printf("Attempt to allocate hugepages failed, falling back to "
            "normal pages\n");
        USE_HUGEPAGES = 0;
        return 0;
    }
    printf("Successfully allocated 100MB of hugepages\n");
    ++HUGE_PAGE_DATA_COUNT;
    f_data->pos = hugepage_align(f_data->start);
    f_data->end = f_data->start + HUGEPAGE_ALLOC_SIZE;
    return 1;
}

/* Only use for things that do not free their memory and get reclaimed
   when the process goes away.
 */
void hpalloc(void ** a_ptr, size_t a_size)
{
    if(USE_HUGEPAGES)
    {
        if(!HUGE_PAGE_DATA_COUNT && !alloc_hugepage_data())
        {
            lmalloc(a_ptr, a_size);
            return;
        }

        // TODO:  Allocate huge pages just for this that can be
        // munmapped...
        if(a_size >= HUGEPAGE_ALLOC_SIZE)
        {
            lmalloc(a_ptr, a_size);
            return;
        }

        int f_i;
        for(f_i = 0; f_i < HUGE_PAGE_DATA_COUNT; ++f_i)
        {
            huge_page_data * f_data = &HUGE_PAGE_DATA[f_i];
            if((f_data->end - f_data->pos) > a_size)
            {
                *a_ptr = f_data->pos;
                f_data->pos = hugepage_align(a_size + f_data->pos);
                return;
            }
        }

        if(alloc_hugepage_data())
        {
            huge_page_data * f_data = &HUGE_PAGE_DATA[f_i];
            *a_ptr = __builtin_assume_aligned(f_data->pos, HUGEPAGE_MIN_ALIGN);
            f_data->pos = hugepage_align(a_size + f_data->pos);
        }
        else
        {
            lmalloc(a_ptr, a_size);
        }
    }
    else
    {
        lmalloc(a_ptr, a_size);
    }
}


#endif	/* LMALLOC_H */

