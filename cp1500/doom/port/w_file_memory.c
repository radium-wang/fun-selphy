/* SPDX-License-Identifier: GPL-2.0-or-later
 * Memory-backed replacement for doomgeneric w_file_stdc.c.
 * Build this file INSTEAD OF w_file_stdc.c; retain upstream w_file.c.
 * The loader owns cp_wad_data and must keep it alive throughout the game.
 */
#include <stddef.h>
#include <string.h>
#include "w_file.h"
#include "z_zone.h"

extern unsigned char *cp_wad_data;
extern unsigned cp_wad_size;

#ifndef CP_WAD_FILENAME
#define CP_WAD_FILENAME "doom1.wad"
#endif

extern wad_file_class_t stdc_wad_file;

static unsigned char lower_ascii(unsigned char ch)
{
    return ch >= 'A' && ch <= 'Z' ? ch + ('a' - 'A') : ch;
}

/* Also usable by the platform's file-existence/stdio shim. */
int cp_wad_path_matches(const char *path)
{
    const char *name = CP_WAD_FILENAME;
    const char *base;
    if (path == NULL || cp_wad_data == NULL || cp_wad_size < 12)
        return 0;
    base = path;
    while (*path != '\0')
    {
        if (*path == '/' || *path == '\\')
            base = path + 1;
        ++path;
    }
    while (*base && *name
        && lower_ascii((unsigned char) *base) == lower_ascii((unsigned char) *name))
    {
        ++base;
        ++name;
    }
    return *base == '\0' && *name == '\0';
}

static wad_file_t *memory_open(char *path)
{
    wad_file_t *wad;
    if (!cp_wad_path_matches(path))
        return NULL;
    if (memcmp(cp_wad_data, "IWAD", 4) != 0
        && memcmp(cp_wad_data, "PWAD", 4) != 0)
        return NULL;
    wad = Z_Malloc(sizeof(*wad), PU_STATIC, NULL);
    wad->file_class = &stdc_wad_file;
    wad->mapped = cp_wad_data;
    wad->length = cp_wad_size;
    return wad;
}

static void memory_close(wad_file_t *wad)
{
    /* Only free the handle: allocation ownership remains with the loader. */
    Z_Free(wad);
}

static size_t memory_read(wad_file_t *wad, unsigned int offset,
                          void *buffer, size_t length)
{
    size_t remaining;
    if (offset >= wad->length || length == 0)
        return 0;
    remaining = wad->length - offset;
    if (length > remaining)
        length = remaining;
    memcpy(buffer, wad->mapped + offset, length);
    return length;
}

wad_file_class_t stdc_wad_file = { memory_open, memory_close, memory_read };
