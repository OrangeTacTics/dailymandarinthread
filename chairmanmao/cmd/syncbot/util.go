package main

import (
    "encoding/base64"
)

func contains(haystack []string, needle string) bool {
    for _, element := range haystack {
        if element == needle {
            return true
        }
    }
    return false
}

func bytesToUriString(data []byte) string {
    return "data:image/png;base64," + base64.StdEncoding.EncodeToString(data)
}

func addModDelOf(desired, current []string) (adds []string, mods []string, dels []string) {
    status := make(map[string] int)
    // +1 add
    //  0 mod
    // -1 del

    for _, v := range desired {
        status[v] += 1
    }

    for _, v := range current {
        status[v] -= 1
    }

    adds = make([]string, 0)
    mods = make([]string, 0)
    dels = make([]string, 0)

    for v, c := range status {
        if c == +1 {
            adds = append(adds, v)
        } else if c == -1 {
            dels = append(dels, v)
        } else {
            mods = append(mods, v)
        }
    }

    return adds, mods, dels
}
