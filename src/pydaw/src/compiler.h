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

#define likely(x)   __builtin_expect((x),1)
#define unlikely(x) __builtin_expect((x),0)

#define prefetch __builtin_prefetch
#define PREFETCH_STRIDE 64

inline void prefetch_range(void *addr, size_t len)
{
    char *cp;
    char *end = addr + len;

    for(cp = addr; cp < end; cp += PREFETCH_STRIDE)
    {
        prefetch(cp);
    }
}

#endif	/* MK_COMPILER_H */

