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

#ifndef MK_COMPILER_H
#define	MK_COMPILER_H

#include <stdlib.h>
#include <sndfile.h>

#ifdef __APPLE__

#include <libkern/OSAtomic.h>

#define pthread_spinlock_t OSSpinLock
#define pthread_spin_lock OSSpinLockLock
#define pthread_spin_unlock OSSpinLockUnlock

void pthread_spin_init(OSSpinLock * a_lock)
{
    *a_lock = 0;
}

#endif

#ifndef MK_DLL
#include <lo/lo.h>
#endif

#if !defined(CACHE_LINE_SIZE)

#define CACHE_LINE_SIZE 64
#warning "CACHE_LINE_SIZE not defined by compiler defaulting to 64"

#elif (CACHE_LINE_SIZE < 64) || (CACHE_LINE_SIZE > 128)

#undef CACHE_LINE_SIZE
#define CACHE_LINE_SIZE 64
#warning "CACHE_LINE_SIZE < 64 or > 128, using 64 as the cache line size"

#endif

#define likely(x)   __builtin_expect((x),1)
#define unlikely(x) __builtin_expect((x),0)

// LLVM defines __GNUC__ , but doesn't implement it's built-ins
// GCC offers no defines that only mean it's compiled with GCC

#ifdef __clang__
    #define assume_aligned(x, y) (x)
    #define NO_OPTIMIZATION
#else
    #define assume_aligned(x, y) __builtin_assume_aligned((x), (y))
    #define NO_OPTIMIZATION __attribute__((optimize("-O0")))
#endif


#define prefetch __builtin_prefetch
#define PREFETCH_STRIDE 64

#ifdef __linux__

inline void prefetch_range(void *addr, size_t len)
{
    char *cp;
    char *end = (char*)addr + len;

    for(cp = (char*)addr; cp < end; cp += PREFETCH_STRIDE)
    {
        prefetch(cp);
    }
}

#endif

#endif	/* MK_COMPILER_H */

